import pytz
import os
from datetime import datetime, date, timedelta
from icecream import ic

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://dev-crm.tibos.in")
from infras.primary_db.main import AsyncLocalSession
from infras.primary_db.repos.setting_repo import SettingsRepo
from infras.primary_db.repos.order_repo import OrdersRepo
from infras.primary_db.models.order import Orders, OrdersPaymentInvoiceInfo
from infras.primary_db.models.customer import Customers
from core.data_formats.enums.dd_enums import SettingsEnum
from core.data_formats.enums.order_enums import InvoiceStatus
from services.email_service import send_email
from services.redis_pub_sub import notify as sse_notify
from services.sse import sse_msg_builder
from infras.primary_db.models.user import Users
from templates.email.alert_report import (
    get_combined_report_html,
    get_payment_summary_html,
    get_payment_pending_html,
    get_pending_invoice_alert_html,
    get_activation_date_alert_html,
    get_pending_dues_breakdown_html,
)
from sqlalchemy import select, func, cast, Date, and_

IST = pytz.timezone("Asia/Kolkata")


def _now_ist():
    return datetime.now(IST)


async def _already_sent_today(redis, key: str) -> bool:
    return bool(await redis.get(key))


async def _mark_sent(redis, key: str):
    # expire at midnight IST: seconds remaining in the day + 60s buffer
    now = _now_ist()
    seconds_left = (24 - now.hour) * 3600 - now.minute * 60 - now.second + 60
    await redis.setex(key, seconds_left, "1")


async def _notify_recipients(session, recipients: list, title: str, description: str, type: str, url: str = None):
    """Sends SSE notification to all recipients and all Super Admins."""
    # 1. Notify specific recipients
    user_ids = set()
    if recipients:
        stmt = select(Users.id).where(Users.email.in_(recipients), Users.is_deleted == False)
        ids = (await session.execute(stmt)).scalars().all()
        user_ids.update(ids)

    # 2. Also notify all Super Admins as fallback/monitoring
    admin_stmt = select(Users.id).where(Users.role == "SUPER_ADMIN", Users.is_deleted == False)
    admin_ids = (await session.execute(admin_stmt)).scalars().all()
    user_ids.update(admin_ids)

    if not user_ids:
        ic("[sse] no users found to notify")
        return

    for uid in user_ids:
        msg = sse_msg_builder(title=title, description=description, type=type, url=url)
        await sse_notify(client_id=uid, data=msg)
        ic(f"[sse] notification sent to {uid}: {title}")


async def _get_global_config(session):
    result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.GLOBAL_ALERTS)
    rows = result.get("settings", [])
    if rows:
        return dict(rows[0]).get("datas", {})
    return None

async def _get_sender_email(session, global_cfg=None):
    """Helper to retrieve the configured sender email from global settings."""
    if not global_cfg:
        global_cfg = await _get_global_config(session)
    if global_cfg:
        return global_cfg.get("sender_email")
    return None


# ─────────────────────────────────────────────
#  PENDING DUES DAILY ALERT
# ─────────────────────────────────────────────
async def _send_pending_dues_email(session, recipients, categories, subject="Pending Dues Breakdown Alert", sender_email=None):
    """Helper to fetch data and send the breakdown email."""
    try:
        repo = OrdersRepo(session=session, user_role="SUPER_ADMIN", cur_user_id="scheduler")
        res = await repo.get(cursor=0, limit=1)

        counts = {
            "tds_pending":      {"count": res.get("tds_pendings", 0),      "amount": res.get("tds_amounts", 0)},
            "not_paid":         {"count": res.get("not_paid_pendings", 0),  "amount": res.get("not_paid_amounts", 0)},
            "gst_pending":      {"count": res.get("gst_pendings", 0),      "amount": res.get("gst_amounts", 0)},
            "short_pending":    {"count": res.get("short_pendings", 0),    "amount": res.get("short_amounts", 0)},
            "half_pending":     {"count": res.get("half_pendings", 0),     "amount": res.get("half_amounts", 0)},
        }

        # Filter categories based on config
        if not categories:
            # Default to all if none selected
            categories = list(counts.keys())

        html = get_pending_dues_breakdown_html(
            categories=categories,
            counts=counts,
            total_dues=res.get("tot_pending_dues", 0),
            total_amounts=res.get("tot_pending_amounts", 0)
        )

        if not sender_email:
            sender_email = await _get_sender_email(session)
        success = await send_email(
            client_ip="scheduler",
            reciver_emails=recipients,
            subject=subject,
            body=html,
            is_html=True,
            sender_email_id=sender_email
        )
        return success
    except Exception as e:
        ic(f"[alert] error generating/sending pending dues email: {e}")
        return False


async def send_pending_dues_alert(ctx, force=False):
    """
    Runs every minute via ARQ cron (if still in cron) OR called from send_report_schedule.
    Sends the pending-dues breakdown email.
    Redis key prevents double-sends within the same calendar day.
    """
    redis = ctx["redis"]
    now = _now_ist()
    current_hhmm = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")

    async with AsyncLocalSession() as session:
        global_cfg = await _get_global_config(session)
        if global_cfg:
            enabled = global_cfg.get("dues_enabled", False)
            # Use global schedule if called from there, otherwise fallback to dues_time if it exists
            alert_time = global_cfg.get("dues_time", "09:00")
            recipients = global_cfg.get("recipients", [])
            categories = global_cfg.get("dues_categories", [])
        else:
            alert_result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.PENDING_DUES_ALERT)
            rows = alert_result.get("settings", [])
            if not rows: return
            config = dict(rows[0]).get("datas", {})
            enabled = config.get("enabled", False)
            alert_time = config.get("time", "09:00")
            recipients = config.get("recipients", [])
            categories = config.get("categories", [])

    if not enabled:
        return
        
    if not force and alert_time != current_hhmm:
        return

    dedup_key = f"alert:pending_dues:sent:{today}"
    if await _already_sent_today(redis, dedup_key):
        ic(f"[alert] pending dues already sent today ({today}), skipping")
        return

    if not recipients:
        ic("[alert] pending dues: no recipients configured, skipping")
        return

    ic(f"[alert] sending pending dues alert to {recipients}")
    
    sender_email = await _get_sender_email(session, global_cfg)
    success = await _send_pending_dues_email(
        session=session,
        recipients=recipients,
        categories=categories,
        sender_email=sender_email
    )

    if success:
        await _mark_sent(redis, dedup_key)
        ic("[alert] pending dues alert sent successfully")
        
        # SSE Notification
        await _notify_recipients(
            session=session,
            recipients=recipients,
            title="Pending Dues Alert",
            description="The daily pending dues breakdown has been generated.",
            type="Alert",
            url=f"{FRONTEND_URL}/orders"
        )
    else:
        ic("[alert] pending dues alert FAILED to send")


# ─────────────────────────────────────────────
#  REPORT SCHEDULE (daily / weekly / monthly)
#  Sends LIVE Payment Summary + Payment Pending
# ─────────────────────────────────────────────
async def send_report_schedule(ctx):
    """
    Runs every minute via ARQ cron.
    Checks daily / weekly / monthly schedule config and sends separate
    Payment Summary + Payment Pending reports generated from live DB data.
    """
    redis = ctx["redis"]
    now = _now_ist()
    current_hhmm = now.strftime("%H:%M")
    current_weekday = now.strftime("%A")          # e.g. "Monday"
    current_day_of_month = now.day
    today = now.strftime("%Y-%m-%d")

    async with AsyncLocalSession() as session:
        global_cfg = await _get_global_config(session)
        if global_cfg:
            recipients = global_cfg.get("recipients", [])
            report_schedule_config = global_cfg
        else:
            sched_result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.REPORT_SCHEDULE)
            sched_rows = sched_result.get("settings", [])
            if not sched_rows: return
            report_schedule_config = dict(sched_rows[0]).get("datas", {})
            recipients = report_schedule_config.get("recipients", [])

    if not recipients:
        ic("[report] no recipients configured, skipping")
        return

    async def _try_send(cadence: str, subject_prefix: str):
        dedup_key = f"report:{cadence}:sent:{today}"
        if await _already_sent_today(redis, dedup_key):
            return

        # Generate live report data
        try:
            to_date = now.date()
            from_date = to_date.replace(day=1)
            from_date_iso = from_date.strftime("%Y-%m-%d")
            to_date_iso = to_date.strftime("%Y-%m-%d")
            report_types = []
            if report_schedule_config.get("payment_summary_enabled", True):
                report_types.append("payment_summary")
            if report_schedule_config.get("payment_pending_enabled", True):
                report_types.append("payment_pending")

            async with AsyncLocalSession() as session:
                repo = OrdersRepo(session=session, user_role="SUPER_ADMIN", cur_user_id="scheduler")

                if "payment_summary" in report_types:
                    data = await repo.get_order_tracking_report(from_date=from_date, to_date=to_date)
                    html = get_payment_summary_html(
                        report_data=data,
                        from_date_iso=from_date_iso,
                        to_date_iso=to_date_iso
                    )
                    sender_email = await _get_sender_email(session, global_cfg)
                    await send_email(
                        client_ip="scheduler",
                        reciver_emails=recipients,
                        subject=f"[{subject_prefix}] Payment Summary Report",
                        body=html,
                        is_html=True,
                        sender_email_id=sender_email
                    )

                if "payment_pending" in report_types:
                    min_days = report_schedule_config.get("payment_pending_min_days")
                    try:
                        min_days = int(min_days) if min_days is not None else 0
                    except:
                        min_days = 0

                    # Use All-Time for pending report to ensure all outstanding items are captured
                    # but use ACTIVATION_DATE for consistency with frontend
                    data = await repo.get_payment_pending_report(from_date=from_date, to_date=to_date, min_days_pending=min_days, date_by='ACTIVATION_DATE')
                    html = get_payment_pending_html(
                        report_data=data,
                        from_date_iso=from_date_iso,
                        to_date_iso=to_date_iso,
                        min_days_pending=min_days
                    )
                    sender_email = await _get_sender_email(session, global_cfg)
                    await send_email(
                        client_ip="scheduler",
                        reciver_emails=recipients,
                        subject=f"[{subject_prefix}] Payment Pending Report",
                        body=html,
                        is_html=True,
                        sender_email_id=sender_email
                    )
            
            # --- Also trigger other enabled Alerts (Dues, Invoice, Activation) ---
            # These will only send once per day due to their internal deduplication logic
            await send_pending_dues_alert(ctx, force=True)
            await send_pending_invoice_alert(ctx, force=True)
            await send_activation_date_alert(ctx, force=True)

            await _mark_sent(redis, dedup_key)
            ic(f"[report] {cadence} reports and alerts sent successfully")
            
            # SSE Notification
            async with AsyncLocalSession() as session:
                await _notify_recipients(
                    session=session,
                    recipients=recipients,
                    title=f"{subject_prefix} Sent",
                    description=f"Automated {cadence} reports and alerts have been dispatched.",
                    type="info"
                )
            return True

        except Exception as e:
            ic(f"[report] error generating {cadence} report data: {e}")
            return

    # Daily
    daily_cfg = report_schedule_config.get("daily", {})
    if daily_cfg.get("enabled") and daily_cfg.get("time") == current_hhmm:
        await _try_send("daily", "Daily Summary")

    # Weekly
    weekly_cfg = report_schedule_config.get("weekly", {})
    if weekly_cfg.get("enabled") and weekly_cfg.get("day") == current_weekday and weekly_cfg.get("time") == current_hhmm:
        await _try_send("weekly", "Weekly Digest")

    # Monthly
    monthly_cfg = report_schedule_config.get("monthly", {})
    configured_day = monthly_cfg.get("day")
    if isinstance(configured_day, str):
        try: configured_day = int(configured_day)
        except ValueError: configured_day = None

    if monthly_cfg.get("enabled") and monthly_cfg.get("time") == current_hhmm and configured_day == current_day_of_month:
        await _try_send("monthly", "Monthly Report")


# ─────────────────────────────────────────────
#  PENDING INVOICE ALERT
#  Orders where invoice is still INCOMPLETED
#  after N days since order creation
# ─────────────────────────────────────────────
async def send_pending_invoice_alert(ctx, force=False):
    """
    Runs every minute via ARQ cron (if still in cron) OR called from send_report_schedule.
    Queries orders older than configured days_after_order_created with incomplete invoices.
    Sends to REPORT_SCHEDULE recipients.
    """
    redis = ctx["redis"]
    now = _now_ist()
    current_hhmm = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")
    dedup_key = f"alert_sent:pending_invoice:{today}"

    if await _already_sent_today(redis, dedup_key):
        return

    # Load config
    async with AsyncLocalSession() as session:
        global_cfg = await _get_global_config(session)
        if global_cfg:
            enabled = global_cfg.get("invoice_enabled", False)
            alert_time = global_cfg.get("invoice_time", "09:00")
            days_threshold = global_cfg.get("invoice_days", 1)
            recipients = global_cfg.get("recipients", [])
        else:
            alert_result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.PENDING_INVOICE_ALERT)
            sched_result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.REPORT_SCHEDULE)
            
            alert_rows = alert_result.get("settings", [])
            sched_rows = sched_result.get("settings", [])
            if not alert_rows: return
            
            config = dict(alert_rows[0]).get("datas", {})
            enabled = config.get("enabled", False)
            alert_time = config.get("time", "09:00")
            days_threshold = config.get("days_after_order_created", 1)
            
            sched_config = dict(sched_rows[0]).get("datas", {}) if sched_rows else {}
            recipients = sched_config.get("recipients", [])

    if not enabled:
        return
        
    if not force and alert_time != current_hhmm:
        return

    # Also check pending dues alert recipients as fallback
    if not recipients:
        async with AsyncLocalSession() as session:
            dues_result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.PENDING_DUES_ALERT)
        dues_rows = dues_result.get("settings", [])
        if dues_rows:
            dues_config = dict(dues_rows[0]).get("datas", {})
            recipients = dues_config.get("recipients", [])

    if not recipients:
        ic("[alert] pending invoice: no recipients, skipping")
        return

    cutoff_date = (now - timedelta(days=days_threshold)).date()

    # Query flagged orders
    try:
        async with AsyncLocalSession() as session:
            stmt = (
                select(
                    Orders.ui_id.label("order_id"),
                    Customers.name.label("customer_name"),
                    func.coalesce(
                        func.nullif(func.trim(Customers.owner), ''),
                        'Others'
                    ).label("owner_name"),
                    func.date(func.timezone("Asia/Kolkata", Orders.created_at)).label("created_date"),
                    (func.current_date() - func.date(func.timezone("Asia/Kolkata", Orders.created_at))).label("days_since_created"),
                    OrdersPaymentInvoiceInfo.invoice_status.label("invoice_status"),
                )
                .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                .join(OrdersPaymentInvoiceInfo, OrdersPaymentInvoiceInfo.order_id == Orders.id, isouter=True)
                .where(
                    Orders.is_deleted == False,
                    func.date(func.timezone("Asia/Kolkata", Orders.created_at)) <= cutoff_date,
                    OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.INCOMPLETED.value,
                )
                .order_by(func.date(func.timezone("Asia/Kolkata", Orders.created_at)).asc())
                .limit(100)
            )

            rows = (await session.execute(stmt)).mappings().all()

        flagged_orders = []
        for row in rows:
            flagged_orders.append({
                "order_id": row["order_id"] or "-",
                "customer_name": row["customer_name"] or "-",
                "owner_name": row["owner_name"] or "-",
                "created_date": str(row["created_date"]) if row["created_date"] else "-",
                "days_since_created": int(row["days_since_created"]) if row["days_since_created"] else 0,
                "invoice_status": row["invoice_status"] or "-",
            })

    except Exception as e:
        ic(f"[alert] pending invoice query error: {e}")
        return

    if not flagged_orders:
        ic("[alert] pending invoice: no flagged orders, skipping")
        return

    html = get_pending_invoice_alert_html(
        flagged_orders=flagged_orders,
        days_threshold=days_threshold,
    )

    ic(f"[alert] sending pending invoice alert ({len(flagged_orders)} orders) to {recipients}")
    sender_email = await _get_sender_email(session, global_cfg)
    success = await send_email(
        client_ip="scheduler",
        reciver_emails=recipients,
        subject=f"Pending Invoice Alert — {len(flagged_orders)} Orders Flagged",
        body=html,
        is_html=True,
        sender_email_id=sender_email
    )

    if success:
        await _mark_sent(redis, dedup_key)
        ic("[alert] pending invoice alert sent successfully")
        
        # SSE Notification
        async with AsyncLocalSession() as session:
            await _notify_recipients(
                session=session,
                recipients=recipients,
                title="Pending Invoice Alert",
                description=f"{len(flagged_orders)} orders are flagged for incomplete invoices.",
                type="Alert",
                url=f"{FRONTEND_URL}/orders"
            )


# ─────────────────────────────────────────────
#  ACTIVATION DATE ALERT
#  Orders approaching or past activation date
# ─────────────────────────────────────────────
async def send_activation_date_alert(ctx, force=False):
    """
    Runs every minute via ARQ cron (if still in cron) OR called from send_report_schedule.
    Queries orders with activation dates within the configured before/after window.
    Sends to REPORT_SCHEDULE recipients.
    """
    redis = ctx["redis"]
    now = _now_ist()
    current_hhmm = now.strftime("%H:%M")
    today_str = now.strftime("%Y-%m-%d")
    today_date = now.date()
    dedup_key = f"alert_sent:activation_date:{today_str}"

    if await _already_sent_today(redis, dedup_key):
        return

    # Load config
    async with AsyncLocalSession() as session:
        global_cfg = await _get_global_config(session)
        if global_cfg:
            enabled = global_cfg.get("activation_enabled", False)
            alert_time = global_cfg.get("activation_time", "09:00")
            days_before = global_cfg.get("activation_before", 2)
            days_after = global_cfg.get("activation_after", 2)
            recipients = global_cfg.get("recipients", [])
        else:
            alert_result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.ACTIVATION_DATE_ALERT)
            sched_result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.REPORT_SCHEDULE)
            
            alert_rows = alert_result.get("settings", [])
            sched_rows = sched_result.get("settings", [])
            if not alert_rows: return
            
            config = dict(alert_rows[0]).get("datas", {})
            enabled = config.get("enabled", False)
            alert_time = config.get("time", "09:00")
            days_before = config.get("days_before_activation", 2)
            days_after = config.get("days_after_activation", 2)
            
            sched_config = dict(sched_rows[0]).get("datas", {}) if sched_rows else {}
            recipients = sched_config.get("recipients", [])

    if not enabled:
        return
        
    if not force and alert_time != current_hhmm:
        return

    if not recipients:
        async with AsyncLocalSession() as session:
            dues_result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.PENDING_DUES_ALERT)
        dues_rows = dues_result.get("settings", [])
        if dues_rows:
            dues_config = dict(dues_rows[0]).get("datas", {})
            recipients = dues_config.get("recipients", [])

    if not recipients:
        ic("[alert] activation date: no recipients, skipping")
        return

    # activation_date is stored in delivery_info->delivery_date
    activation_date_field = cast(Orders.delivery_info["delivery_date"].astext, Date)

    # Upcoming: activation_date is between today and today + days_before
    upcoming_start = today_date
    upcoming_end = today_date + timedelta(days=days_before)

    # Overdue: activation_date is between today - days_after and today, and not activated
    overdue_start = today_date - timedelta(days=days_after * 10)  # look back further
    overdue_end = today_date - timedelta(days=1)

    try:
        async with AsyncLocalSession() as session:
            # Upcoming activations
            upcoming_stmt = (
                select(
                    Orders.ui_id.label("order_id"),
                    Customers.name.label("customer_name"),
                    func.coalesce(
                        func.nullif(func.trim(Customers.owner), ''),
                        'Others'
                    ).label("owner_name"),
                    activation_date_field.label("activation_date"),
                    (activation_date_field - func.current_date()).label("days_diff"),
                )
                .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                .where(
                    Orders.is_deleted == False,
                    Orders.activated == False,
                    activation_date_field >= upcoming_start,
                    activation_date_field <= upcoming_end,
                )
                .order_by(activation_date_field.asc())
                .limit(100)
            )
            upcoming_rows = (await session.execute(upcoming_stmt)).mappings().all()

            # Overdue activations
            overdue_stmt = (
                select(
                    Orders.ui_id.label("order_id"),
                    Customers.name.label("customer_name"),
                    func.coalesce(
                        func.nullif(func.trim(Customers.owner), ''),
                        'Others'
                    ).label("owner_name"),
                    activation_date_field.label("activation_date"),
                    (func.current_date() - activation_date_field).label("days_diff"),
                )
                .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                .where(
                    Orders.is_deleted == False,
                    Orders.activated == False,
                    activation_date_field >= overdue_start,
                    activation_date_field <= overdue_end,
                    (func.current_date() - activation_date_field) >= days_after,
                )
                .order_by(activation_date_field.asc())
                .limit(100)
            )
            overdue_rows = (await session.execute(overdue_stmt)).mappings().all()

        upcoming_orders = [
            {
                "order_id": r["order_id"] or "-",
                "customer_name": r["customer_name"] or "-",
                "owner_name": r["owner_name"] or "-",
                "activation_date": str(r["activation_date"]) if r["activation_date"] else "-",
                "days_diff": int(r["days_diff"]) if r["days_diff"] else 0,
            }
            for r in upcoming_rows
        ]

        overdue_orders = [
            {
                "order_id": r["order_id"] or "-",
                "customer_name": r["customer_name"] or "-",
                "owner_name": r["owner_name"] or "-",
                "activation_date": str(r["activation_date"]) if r["activation_date"] else "-",
                "days_diff": int(r["days_diff"]) if r["days_diff"] else 0,
            }
            for r in overdue_rows
        ]

    except Exception as e:
        ic(f"[alert] activation date query error: {e}")
        return

    if not upcoming_orders and not overdue_orders:
        ic("[alert] activation date: no orders to flag, skipping")
        return

    html = get_activation_date_alert_html(
        upcoming_orders=upcoming_orders,
        overdue_orders=overdue_orders,
        days_before=days_before,
        days_after=days_after,
    )

    total_flagged = len(upcoming_orders) + len(overdue_orders)
    ic(f"[alert] sending activation date alert ({total_flagged} orders) to {recipients}")
    sender_email = await _get_sender_email(session, global_cfg)
    success = await send_email(
        client_ip="scheduler",
        reciver_emails=recipients,
        subject=f"Activation Date Alert — {len(upcoming_orders)} Upcoming, {len(overdue_orders)} Overdue",
        body=html,
        is_html=True,
        sender_email_id=sender_email
    )

    if success:
        await _mark_sent(redis, dedup_key)
        ic("[alert] activation date alert sent successfully")
        
        # SSE Notification
        async with AsyncLocalSession() as session:
            await _notify_recipients(
                session=session,
                recipients=recipients,
                title="Activation Date Alert",
                description=f"{total_flagged} orders are approaching or past activation.",
                type="Alert",
                url=f"{FRONTEND_URL}/orders"
            )


# ─────────────────────────────────────────────
#  MANUAL TEST REPORT TRIGGER
# ─────────────────────────────────────────────
async def run_test_report(ctx, report_type: str, recipients: list):
    """
    Manually triggered task to send a test report/alert.
    """
    ic(f"[test-report] triggering {report_type} for {recipients}")
    now = _now_ist()
    today_date = now.date()

    async with AsyncLocalSession() as session:
        global_cfg = await _get_global_config(session)
        sender_email = await _get_sender_email(session, global_cfg)

        if report_type == "payment_combined":
            to_date = now.date()
            from_date = to_date.replace(day=1)
            from_date_iso = from_date.strftime("%Y-%m-%d")
            to_date_iso = to_date.strftime("%Y-%m-%d")

            repo = OrdersRepo(session=session, user_role="SUPER_ADMIN", cur_user_id="manual-trigger")

            # 1. Summary & Pending
            if not global_cfg or global_cfg.get("payment_summary_enabled", True):
                summary_data = await repo.get_order_tracking_report(from_date=from_date, to_date=to_date)
                html_summary = get_payment_summary_html(report_data=summary_data, from_date_iso=from_date_iso, to_date_iso=to_date_iso)
                await send_email(client_ip="manual-trigger", reciver_emails=recipients, subject="[Test] Payment Summary Report", body=html_summary, is_html=True, sender_email_id=sender_email)

            if not global_cfg or global_cfg.get("payment_pending_enabled", True):
                min_days = global_cfg.get("payment_pending_min_days") if global_cfg else 0
                try:
                    min_days = int(min_days) if min_days is not None else 0
                except:
                    min_days = 0

                # Use current month for consistency with daily reports
                pending_data = await repo.get_payment_pending_report(from_date=from_date, to_date=to_date, min_days_pending=min_days, date_by='ACTIVATION_DATE')
                html_pending = get_payment_pending_html(report_data=pending_data, from_date_iso=from_date_iso, to_date_iso=to_date_iso, min_days_pending=min_days)
                await send_email(client_ip="manual-trigger", reciver_emails=recipients, subject="[Test] Payment Pending Report", body=html_pending, is_html=True, sender_email_id=sender_email)

            # 2. Check for other enabled alerts (Global Config with Legacy Fallback)
            
            # --- Pending Dues ---
            dues_enabled = False
            dues_categories = []
            if global_cfg:
                dues_enabled = global_cfg.get("dues_enabled", False)
                dues_categories = global_cfg.get("dues_categories", [])
            else:
                d_res = await SettingsRepo(session=session).getby_name(name=SettingsEnum.PENDING_DUES_ALERT)
                d_rows = d_res.get("settings", [])
                if d_rows:
                    d_cfg = dict(d_rows[0]).get("datas", {})
                    dues_enabled = d_cfg.get("enabled", False)
                    dues_categories = d_cfg.get("categories", [])
            
            if dues_enabled:
                await _send_pending_dues_email(
                    session=session,
                    recipients=recipients,
                    categories=dues_categories,
                    subject="[Test] Pending Dues Breakdown",
                    sender_email=sender_email
                )

            # --- Pending Invoices ---
            invoice_enabled = False
            if global_cfg:
                invoice_enabled = global_cfg.get("invoice_enabled", False)
            else:
                i_res = await SettingsRepo(session=session).getby_name(name=SettingsEnum.PENDING_INVOICE_ALERT)
                i_rows = i_res.get("settings", [])
                if i_rows:
                    invoice_enabled = dict(i_rows[0]).get("datas", {}).get("enabled", False)
            
            if invoice_enabled:
                await run_test_report(ctx, "pending_invoice", recipients)

            # --- Activation Date ---
            activation_enabled = False
            if global_cfg:
                activation_enabled = global_cfg.get("activation_enabled", False)
            else:
                a_res = await SettingsRepo(session=session).getby_name(name=SettingsEnum.ACTIVATION_DATE_ALERT)
                a_rows = a_res.get("settings", [])
                if a_rows:
                    activation_enabled = dict(a_rows[0]).get("datas", {}).get("enabled", False)
            
            if activation_enabled:
                await run_test_report(ctx, "activation_date", recipients)

            return True

        elif report_type == "pending_dues":
            result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.PENDING_DUES_ALERT)
            rows = result.get("settings", [])
            categories = []
            if rows:
                categories = dict(rows[0]).get("datas", {}).get("categories", [])
            
            return await _send_pending_dues_email(
                session=session,
                recipients=recipients,
                categories=categories,
                subject="[Test] Pending Dues Breakdown"
            )

        elif report_type == "pending_invoice":
            alert_result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.PENDING_INVOICE_ALERT)
            config = dict(alert_result.get("settings", [{}])[0]).get("datas", {})
            days_threshold = config.get("days_after_order_created", 1)
            cutoff_date = (now - timedelta(days=days_threshold)).date()

            stmt = (
                select(
                    Orders.ui_id.label("order_id"),
                    Customers.name.label("customer_name"),
                    func.coalesce(func.nullif(func.trim(Customers.owner), ''), 'Others').label("owner_name"),
                    func.date(func.timezone("Asia/Kolkata", Orders.created_at)).label("created_date"),
                    (func.current_date() - func.date(func.timezone("Asia/Kolkata", Orders.created_at))).label("days_since_created"),
                    OrdersPaymentInvoiceInfo.invoice_status.label("invoice_status"),
                )
                .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                .join(OrdersPaymentInvoiceInfo, OrdersPaymentInvoiceInfo.order_id == Orders.id, isouter=True)
                .where(
                    Orders.is_deleted == False,
                    func.date(func.timezone("Asia/Kolkata", Orders.created_at)) <= cutoff_date,
                    OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.INCOMPLETED.value,
                )
                .order_by(func.date(func.timezone("Asia/Kolkata", Orders.created_at)).asc())
                .limit(100)
            )
            rows = (await session.execute(stmt)).mappings().all()
            flagged_orders = [dict(r) for r in rows]
            if not flagged_orders:
                html = "<p>No flagged orders found for this test.</p>"
            else:
                html = get_pending_invoice_alert_html(flagged_orders=flagged_orders, days_threshold=days_threshold)
            subject = "[Test] Pending Invoice Alert"

        elif report_type == "activation_date":
            alert_result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.ACTIVATION_DATE_ALERT)
            config = dict(alert_result.get("settings", [{}])[0]).get("datas", {})
            days_before = config.get("days_before_activation", 2)
            days_after = config.get("days_after_activation", 2)
            activation_date_field = cast(Orders.delivery_info["delivery_date"].astext, Date)

            upcoming_stmt = (
                select(
                    Orders.ui_id.label("order_id"), Customers.name.label("customer_name"),
                    func.coalesce(func.nullif(func.trim(Customers.owner), ''), 'Others').label("owner_name"),
                    activation_date_field.label("activation_date"),
                    (activation_date_field - func.current_date()).label("days_diff"),
                )
                .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                .where(Orders.is_deleted == False, Orders.activated == False, activation_date_field >= today_date, activation_date_field <= today_date + timedelta(days=days_before))
                .limit(100)
            )
            upcoming_rows = (await session.execute(upcoming_stmt)).mappings().all()

            overdue_stmt = (
                select(
                    Orders.ui_id.label("order_id"), Customers.name.label("customer_name"),
                    func.coalesce(func.nullif(func.trim(Customers.owner), ''), 'Others').label("owner_name"),
                    activation_date_field.label("activation_date"),
                    (func.current_date() - activation_date_field).label("days_diff"),
                )
                .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                .where(Orders.is_deleted == False, Orders.activated == False, activation_date_field < today_date, (func.current_date() - activation_date_field) >= days_after)
                .limit(100)
            )
            overdue_rows = (await session.execute(overdue_stmt)).mappings().all()

            html = get_activation_date_alert_html(
                upcoming_orders=[dict(r) for r in upcoming_rows],
                overdue_orders=[dict(r) for r in overdue_rows],
                days_before=days_before,
                days_after=days_after
            )
            subject = "[Test] Activation Date Alert"
        else:
            ic(f"[test-report] unknown report type: {report_type}")
            return False

        success = await send_email(
            client_ip="manual-trigger",
            reciver_emails=recipients,
            subject=subject,
            body=html,
            is_html=True,
            sender_email_id=sender_email
        )
        return success
