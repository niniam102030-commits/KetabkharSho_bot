import os
from pathlib import Path
import asyncio
import logging
import secrets
from typing import Any

from aiohttp import FormData
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.methods import TelegramMethod
from aiogram.types import InputFile, ErrorEvent

from config import settings
from database import init_db, get_db, get_system_state
from services import DateService
from admin_handlers import admin_router
from handlers import (
    user_router,
    midnight_job,
    send_daily_admin_reports,
    send_daily_user_reports,
    send_study_reminders,
    send_startup_notification,
)
from weekly_report import send_weekly_reports
from scheduler import setup_scheduler

logger = logging.getLogger(__name__)


class BaleAiohttpSession(AiohttpSession):
    """
    نشست اختصاصی سازگار با پیام‌رسان بله و تلگرام.
    سرور پیام‌رسان بله در هنگام آپلود فایل‌های Multipart (مانند اکسل) در صورتی که
    نام فیلدها یا نام فایل فارسی URL-Encode شود (quote_fields=True پیش‌فرض aiohttp)،
    یا فایل به جای نام اصلی فیلد (مانند document) با attach:// کلید تصادفی ارسال شود،
    خطای «failed to get HTTP URL content» برمی‌گرداند.
    این کلاس با نگه‌داشتن نام مستقیم فیلد فایل و تنظیم quote_fields=False در FormData
    مشکل ارسال اسناد در پیام‌رسان بله را به طور کامل رفع می‌کند.
    """

    def build_form_data(self, bot: Bot, method: TelegramMethod[Any]) -> FormData:
        form = FormData(quote_fields=False)
        files: dict[str, InputFile] = {}
        for key, value in method.model_dump(warnings=False).items():
            if isinstance(value, InputFile):
                files[key] = value
                continue
            value = self.prepare_value(value, bot=bot, files=files)
            if value is None:
                continue
            form.add_field(key, value)
        for key, value in files.items():
            if hasattr(value, "path") and getattr(value, "path", None) and os.path.exists(value.path):
                file_payload: Any = Path(value.path).read_bytes()
            elif hasattr(value, "data") and isinstance(getattr(value, "data", None), (bytes, bytearray)):
                file_payload = bytes(value.data)
            else:
                file_payload = value.read(bot)
            form.add_field(
                key,
                file_payload,
                filename=value.filename or (os.path.basename(value.path) if hasattr(value, "path") else key),
            )
        return form


async def run_startup_catchups(bot: Bot) -> None:
    """
    بررسی و اجرای جبرانی جاب‌های جاافتاده در بدو روشن شدن ربات (در صورت خاموشی سرور در ساعات اجرای جاب).
    """
    now_ir = DateService.now_iran()
    today_str = DateService.today_str()
    current_hour = now_ir.hour

    with get_db() as db:
        last_midnight = get_system_state(db, "last_daily_job_date")
        last_admin_rep = get_system_state(db, "last_daily_admin_report_date")
        last_weekly_rep = get_system_state(db, "last_weekly_report_date")
        last_user_rep = get_system_state(db, "last_daily_user_report_date")
        last_reminder = get_system_state(db, "last_reminder_date")

    # ۱. جبران جاب نیمه‌شب (ثبت غیبت روزهای گذشته و بروزرسانی روز چله)
    if last_midnight != today_str:
        logger.info("اجرای جبرانی جاب نیمه‌شب (midnight_job) در استارتاپ...")
        try:
            await midnight_job(bot)
        except Exception as exc:
            logger.error(f"خطا در اجرای جبرانی midnight_job: {exc}", exc_info=True)

    # ۲. جبران گزارش بامداد ادمین‌ها
    if current_hour >= settings.ADMIN_REPORT_HOUR and last_admin_rep != today_str:
        logger.info("اجرای جبرانی گزارش روزانه ادمین‌ها (send_daily_admin_reports) در استارتاپ...")
        try:
            await send_daily_admin_reports(bot)
        except Exception as exc:
            logger.error(f"خطا در اجرای جبرانی send_daily_admin_reports: {exc}", exc_info=True)

    # ۳. جبران گزارش هفتگی روزهای جمعه (در پایتون جمعه برابر با weekday == 4 است)
    if (
        now_ir.weekday() == 4
        and current_hour >= settings.WEEKLY_REPORT_HOUR
        and last_weekly_rep != today_str
    ):
        logger.info("اجرای جبرانی گزارش هفتگی جمعه (send_weekly_reports) در استارتاپ...")
        try:
            await send_weekly_reports(bot)
        except Exception as exc:
            logger.error(f"خطا در اجرای جبرانی send_weekly_reports: {exc}", exc_info=True)

    # ۴. جبران کارنامه صبحگاهی کاربران و بررسی پایان چله ۴۰ روزه
    if current_hour >= settings.DAILY_REPORT_HOUR and last_user_rep != today_str:
        logger.info("اجرای جبرانی کارنامه صبحگاهی کاربران (send_daily_user_reports) در استارتاپ...")
        try:
            await send_daily_user_reports(bot)
        except Exception as exc:
            logger.error(f"خطا در اجرای جبرانی send_daily_user_reports: {exc}", exc_info=True)

    # ۵. جبران یادآوری شبانه
    if current_hour >= settings.REMINDER_HOUR and last_reminder != today_str:
        logger.info("اجرای جبرانی یادآوری شبانه (send_study_reminders) در استارتاپ...")
        try:
            await send_study_reminders(bot)
        except Exception as exc:
            logger.error(f"خطا در اجرای جبرانی send_study_reminders: {exc}", exc_info=True)


async def main() -> None:
    """نقطه ورود اصلی برنامه، راه‌اندازی دیتابیس، زمان‌بند و شروع Polling"""
    settings.validate()
    init_db()

    api_server = TelegramAPIServer.from_base(settings.API_URL)
    session = BaleAiohttpSession(api=api_server)
    bot = Bot(token=settings.BOT_TOKEN, session=session)

    dp = Dispatcher()

    # ثبت هندلر خطای سراسری جهت جلوگیری از توقف ربات در خطاهای پیش‌بینی‌نشده شبکه یا API
    @dp.error()
    async def global_error_handler(event: ErrorEvent) -> bool:
        logger.error(
            f"خطای سراسری مدیریت‌شده در پردازش آپدیت: {event.exception}",
            exc_info=settings.DEBUG,
        )
        return True

    # ثبت روترهای مدیریت و کاربران
    dp.include_router(admin_router)
    dp.include_router(user_router)

    # راه‌اندازی زمان‌بند خودکار و اجرای جبرانی جاب‌های جاافتاده
    scheduler = setup_scheduler(bot)
    await run_startup_catchups(bot)

    # ارسال پیام فعال‌سازی ربات به همراه تاریخ شمسی و ساعت دقیق به وقت ایران به تمامی ادمین‌ها
    await send_startup_notification(bot)

    logger.info(
        f"ربات باشگاه کتابخوانی «کتابخوارشو» متصل به {settings.API_URL} آماده دریافت پیام‌هاست..."
    )

    try:
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        logger.info("در حال خاموش کردن زمان‌بند و بستن نشست ربات...")
        if scheduler.running:
            scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("ربات به صورت دستی متوقف شد.")