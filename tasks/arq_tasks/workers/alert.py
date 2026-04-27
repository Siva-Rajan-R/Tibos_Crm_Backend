import pytz
from datetime import datetime
from icecream import ic
from infras.primary_db.main import AsyncLocalSession
from infras.primary_db.repos.setting_repo import SettingsRepo
from core.data_formats.enums.dd_enums import SettingsEnum
from services.email_service import send_email

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
    else:
        ic("[alert] pending dues alert FAILED to send")


# ─────────────────────────────────────────────
#  REPORT SCHEDULE (daily / weekly / monthly)
# ─────────────────────────────────────────────
async def send_report_schedule(ctx):
    """
    Runs every minute via ARQ cron.
    Checks daily / weekly / monthly schedule config and sends the pending-dues
    email on the configured cadence, reusing recipients + template from the
    PENDING_DUES_ALERT settings.
    """
    redis = ctx["redis"]
    now = _now_ist()
    current_hhmm = now.strftime("%H:%M")
    current_weekday = now.strftime("%A")          # e.g. "Monday"
    current_day_of_month = now.day
    today = now.strftime("%Y-%m-%d")

    async with AsyncLocalSession() as session:
        sched_result = await SettingsRepo(session=session).getby_name(name=SettingsEnum.REPORT_SCHEDULE)
        dues_result  = await SettingsRepo(session=session).getby_name(name=SettingsEnum.PENDING_DUES_ALERT)

    sched_rows = sched_result.get("settings", [])
    dues_rows  = dues_result.get("settings",  [])

    if not sched_rows or not dues_rows:
        return

    schedule = dict(sched_rows[0]).get("datas", {})
    dues_cfg  = dict(dues_rows[0]).get("datas",  {})

    recipients = dues_cfg.get("recipients", [])
    html       = dues_cfg.get("email_template_html", "")

    if not recipients or not html:
        return

    async def _try_send(cadence: str, subject_prefix: str):
        dedup_key = f"report:{cadence}:sent:{today}"
        if await _already_sent_today(redis, dedup_key):
            return
        ic(f"[report] sending {cadence} report to {recipients}")
        success = await send_email(
            client_ip="scheduler",
            reciver_emails=recipients,
            subject=f"{subject_prefix} — Pending Dues Report",
            body=html,
            is_html=True,
        )
        if success:
            await _mark_sent(redis, dedup_key)
            ic(f"[report] {cadence} report sent successfully")

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
