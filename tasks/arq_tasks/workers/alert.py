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
    get_pending_invoice_alert_html,
    get_activation_date_alert_html,
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


# ─────────────────────────────────────────────
#  PENDING DUES DAILY ALERT
# ─────────────────────────────────────────────
async def send_pending_dues_alert(ctx):
    """
    Runs every minute via ARQ cron.
    Sends the pending-dues breakdown email when the configured IST time matches.
    Redis key prevents double-sends within the same calendar day.
    """
    redis = ctx["redis"]
    now = _now_ist()
    current_hhmm = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")

    async with AsyncLocalSession() as session:
        result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.PENDING_DUES_ALERT)

    rows = result.get("settings", [])
    if not rows:
        return

    config = dict(rows[0]).get("datas", {})

    if not config.get("enabled"):
        return

    if config.get("time") != current_hhmm:
        return

    dedup_key = f"alert:pending_dues:sent:{today}"
    if await _already_sent_today(redis, dedup_key):
        ic(f"[alert] pending dues already sent today ({today}), skipping")
        return

    recipients = config.get("recipients", [])
    html = config.get("email_template_html", "")

    if not recipients:
        ic("[alert] pending dues: no recipients configured, skipping")
        return
    if not html:
        ic("[alert] pending dues: no email_template_html stored, skipping")
        return

    ic(f"[alert] sending pending dues alert to {recipients} at {current_hhmm} IST")
    success = await send_email(
        client_ip="scheduler",
        reciver_emails=recipients,
        subject="Pending Dues Breakdown Alert",
        body=html,
        is_html=True,
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
            url=f"{FRONTEND_URL}/reports"
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
    Checks daily / weekly / monthly schedule config and sends a combined
    Payment Summary + Payment Pending report generated from live DB data.
    Recipients are stored in REPORT_SCHEDULE settings.
    """
    redis = ctx["redis"]
    now = _now_ist()
    current_hhmm = now.strftime("%H:%M")
    current_weekday = now.strftime("%A")          # e.g. "Monday"
    current_day_of_month = now.day
    today = now.strftime("%Y-%m-%d")

    async with AsyncLocalSession() as session:
        sched_result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.REPORT_SCHEDULE)

    sched_rows = sched_result.get("settings", [])

    if not sched_rows:
        return

    schedule = dict(sched_rows[0]).get("datas", {})

    recipients = schedule.get("recipients", [])

    if not recipients:
        ic("[report] no recipients configured, skipping")
        return

    async def _try_send(cadence: str, subject_prefix: str):
        dedup_key = f"report:{cadence}:sent:{today}"
        if await _already_sent_today(redis, dedup_key):
            return

        ic(f"[report] generating {cadence} report data...")

        # Generate live report data
        try:
            # Use the first day of the current month as the start date
            # This aligns perfectly with the frontend default behavior
            to_date = now.date()
            from_date = to_date.replace(day=1)

            async with AsyncLocalSession() as session:
                repo = OrdersRepo(session=session, user_role="SUPER_ADMIN", cur_user_id="scheduler")

                payment_summary_data = await repo.get_order_tracking_report(
                    from_date=from_date,
                    to_date=to_date
                )

                payment_pending_data = await repo.get_payment_pending_report(
                    from_date=from_date,
                    to_date=to_date
                )

            html = get_combined_report_html(
                payment_summary_data=payment_summary_data,
                payment_pending_data=payment_pending_data,
                cadence=subject_prefix,
                from_date_str=from_date.strftime("%d %b %Y"),
                to_date_str=to_date.strftime("%d %b %Y"),
                from_date_iso=from_date.strftime("%Y-%m-%d"),
                to_date_iso=to_date.strftime("%Y-%m-%d")
            )

        except Exception as e:
            ic(f"[report] error generating {cadence} report data: {e}")
            return

        ic(f"[report] sending {cadence} report to {recipients}")
        success = await send_email(
            client_ip="scheduler",
            reciver_emails=recipients,
            subject=f"{subject_prefix} — Payment Summary & Pending Report",
            body=html,
            is_html=True,
        )
        if success:
            await _mark_sent(redis, dedup_key)
            ic(f"[report] {cadence} report sent successfully")
            
            # SSE Notification
            async with AsyncLocalSession() as session:
                await _notify_recipients(
                    session=session,
                    recipients=recipients,
                    title=f"{subject_prefix} Report Ready",
                    description=f"The {cadence} business report for {today} has been generated.",
                    type="Report",
                    url=f"{FRONTEND_URL}/report-view/payment_summary"
                )

    # ── daily ──
    daily = schedule.get("daily", {})
    if daily.get("enabled") and daily.get("time") == current_hhmm:
        await _try_send("daily", "Daily")

    # ── weekly ──
    weekly = schedule.get("weekly", {})
    if (
        weekly.get("enabled")
        and weekly.get("time") == current_hhmm
        and weekly.get("day") == current_weekday
    ):
        await _try_send("weekly", "Weekly")

    # ── monthly ──
    monthly = schedule.get("monthly", {})
    # frontend stores the day as int (1-28)
    configured_day = monthly.get("day")
    if isinstance(configured_day, str):
        try:
            configured_day = int(configured_day)
        except ValueError:
            configured_day = None

    if (
        monthly.get("enabled")
        and monthly.get("time") == current_hhmm
        and configured_day == current_day_of_month
    ):
        await _try_send("monthly", "Monthly")


# ─────────────────────────────────────────────
#  PENDING INVOICE ALERT
#  Orders where invoice is still INCOMPLETED
#  after N days since order creation
# ─────────────────────────────────────────────
async def send_pending_invoice_alert(ctx):
    """
    Runs every minute via ARQ cron.
    Checks at 09:00 IST daily. Queries orders older than
    configured days_after_order_created with incomplete invoices.
    Sends to REPORT_SCHEDULE recipients.
    """
    redis = ctx["redis"]
    now = _now_ist()
    current_hhmm = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")

    # Load config
    async with AsyncLocalSession() as session:
        alert_result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.PENDING_INVOICE_ALERT)
        sched_result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.REPORT_SCHEDULE)

    alert_rows = alert_result.get("settings", [])
    sched_rows = sched_result.get("settings", [])

    if not alert_rows:
        return

    config = dict(alert_rows[0]).get("datas", {})

    if not config.get("enabled"):
        return

    # Check time — default 09:00
    alert_time = config.get("time", "09:00")
    if alert_time != current_hhmm:
        return

    dedup_key = f"alert:pending_invoice:sent:{today}"
    if await _already_sent_today(redis, dedup_key):
        return

    # Get recipients from report schedule
    recipients = []
    if sched_rows:
        sched_config = dict(sched_rows[0]).get("datas", {})
        recipients = sched_config.get("recipients", [])

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

    days_threshold = config.get("days_after_order_created", 1)
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
    success = await send_email(
        client_ip="scheduler",
        reciver_emails=recipients,
        subject=f"Pending Invoice Alert — {len(flagged_orders)} Orders Flagged",
        body=html,
        is_html=True,
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
async def send_activation_date_alert(ctx):
    """
    Runs every minute via ARQ cron.
    Checks at 09:00 IST daily. Queries orders with activation dates
    within the configured before/after window.
    Sends to REPORT_SCHEDULE recipients.
    """
    redis = ctx["redis"]
    now = _now_ist()
    current_hhmm = now.strftime("%H:%M")
    today_str = now.strftime("%Y-%m-%d")
    today_date = now.date()

    # Load config
    async with AsyncLocalSession() as session:
        alert_result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.ACTIVATION_DATE_ALERT)
        sched_result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.REPORT_SCHEDULE)

    alert_rows = alert_result.get("settings", [])
    sched_rows = sched_result.get("settings", [])

    if not alert_rows:
        return

    config = dict(alert_rows[0]).get("datas", {})

    if not config.get("enabled"):
        return

    # Check time — default 09:00
    alert_time = config.get("time", "09:00")
    if alert_time != current_hhmm:
        return

    dedup_key = f"alert:activation_date:sent:{today_str}"
    if await _already_sent_today(redis, dedup_key):
        return

    # Get recipients from report schedule
    recipients = []
    if sched_rows:
        sched_config = dict(sched_rows[0]).get("datas", {})
        recipients = sched_config.get("recipients", [])

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

    days_before = config.get("days_before_activation", 2)
    days_after = config.get("days_after_activation", 2)

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
    success = await send_email(
        client_ip="scheduler",
        reciver_emails=recipients,
        subject=f"Activation Date Alert — {len(upcoming_orders)} Upcoming, {len(overdue_orders)} Overdue",
        body=html,
        is_html=True,
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
