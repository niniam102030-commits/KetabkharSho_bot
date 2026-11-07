import logging
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import settings
from services import IRAN_TZ
from handlers import (
    midnight_job,
    send_daily_admin_reports,
    send_daily_user_reports,
    send_study_reminders,
)
from weekly_report import send_weekly_reports

logger = logging.getLogger(__name__)


async def _run_safe_job(job_func, bot: Bot, job_name: str) -> None:
    """اجرای ایمن جاب‌های زمان‌بندی‌شده بدون متوقف کردن کل زمان‌بند در صورت بروز استثنا"""
    try:
        await job_func(bot=bot)
    except Exception as exc:
        logger.error(f"خطای مدیریت‌شده در اجرای جاب «{job_name}»: {exc}", exc_info=True)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """
    تنظیم و راه‌اندازی AsyncIOScheduler بر اساس منطقه زمانی Asia/Tehran
    برای اجرای خودکار ۵ جاب اصلی باشگاه کتابخوارشو.
    """
    scheduler = AsyncIOScheduler(timezone=IRAN_TZ)

    # ۱. ساعت 00:00 نیمه‌شب: ثبت غیبت‌ها، ترمیم زنجیره، صفر کردن آمار امروز و بروزرسانی روز چله
    scheduler.add_job(
        _run_safe_job,
        trigger=CronTrigger(hour=0, minute=0, timezone=IRAN_TZ),
        kwargs={"job_func": midnight_job, "bot": bot, "job_name": "midnight_daily_job"},
        id="midnight_daily_job",
        replace_existing=True,
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )

    # ۲. ساعت 01:00 بامداد (قابل تنظیم با ADMIN_REPORT_HOUR): ارسال جدول آرشیو روزانه به ادمین‌ها
    scheduler.add_job(
        _run_safe_job,
        trigger=CronTrigger(hour=settings.ADMIN_REPORT_HOUR, minute=0, timezone=IRAN_TZ),
        kwargs={
            "job_func": send_daily_admin_reports,
            "bot": bot,
            "job_name": "daily_admin_report_job",
        },
        id="daily_admin_report_job",
        replace_existing=True,
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )

    # ۳. ساعت 02:00 بامداد روزهای جمعه (قابل تنظیم با WEEKLY_REPORT_HOUR): گزارش هفتگی و اکسل
    scheduler.add_job(
        _run_safe_job,
        trigger=CronTrigger(
            day_of_week="fri",
            hour=settings.WEEKLY_REPORT_HOUR,
            minute=0,
            timezone=IRAN_TZ,
        ),
        kwargs={
            "job_func": send_weekly_reports,
            "bot": bot,
            "job_name": "friday_weekly_report_job",
        },
        id="friday_weekly_report_job",
        replace_existing=True,
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )

    # ۴. ساعت 08:00 صبح (قابل تنظیم با DAILY_REPORT_HOUR): کارنامه صبحگاهی کاربران و بررسی پایان چله ۴۰ روزه
    scheduler.add_job(
        _run_safe_job,
        trigger=CronTrigger(hour=settings.DAILY_REPORT_HOUR, minute=0, timezone=IRAN_TZ),
        kwargs={
            "job_func": send_daily_user_reports,
            "bot": bot,
            "job_name": "daily_user_morning_report_job",
        },
        id="daily_user_morning_report_job",
        replace_existing=True,
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )

    # ۵. ساعت 22:00 شب (قابل تنظیم با REMINDER_HOUR): ارسال یادآوری شبانه به افراد ثبت‌نکرده
    scheduler.add_job(
        _run_safe_job,
        trigger=CronTrigger(hour=settings.REMINDER_HOUR, minute=0, timezone=IRAN_TZ),
        kwargs={
            "job_func": send_study_reminders,
            "bot": bot,
            "job_name": "night_study_reminder_job",
        },
        id="night_study_reminder_job",
        replace_existing=True,
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info(
        "زمان‌بند (AsyncIOScheduler) با منطقه زمانی Asia/Tehran فعال شد: "
        f"Midnight=00:00 | AdminReport={settings.ADMIN_REPORT_HOUR:02d}:00 | "
        f"WeeklyFri={settings.WEEKLY_REPORT_HOUR:02d}:00 | "
        f"MorningReport={settings.DAILY_REPORT_HOUR:02d}:00 | "
        f"Reminder={settings.REMINDER_HOUR:02d}:00"
    )
    return scheduler