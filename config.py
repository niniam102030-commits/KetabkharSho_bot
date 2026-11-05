import os
import logging
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()


class Config:
    """کلاس مدیریت تنظیمات سراسری پروژه کتابخوارشو"""

    def __init__(self) -> None:
        self.BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
        self.API_URL: str = os.getenv("API_URL", "https://tapi.bale.ai").strip().rstrip("/")

        raw_admin_ids: str = os.getenv("ADMIN_IDS", "").strip()
        self.ADMIN_IDS: List[str] = [
            adm.strip() for adm in raw_admin_ids.split(",") if adm.strip()
        ]

        self.ARCHIVE_CHANNEL: str = os.getenv("ARCHIVE_CHANNEL", "").strip()
        self.DATABASE_URL: str = os.getenv(
            "DATABASE_URL", "sqlite:///./data/ketabkharsho.db"
        ).strip()

        self.DEFAULT_FLOOR: int = self._get_int("DEFAULT_FLOOR", 10)
        self.LEAGUE_DURATION: int = self._get_int("LEAGUE_DURATION", 40)
        self.DEFAULT_HALF_COUPONS: int = self._get_int("DEFAULT_HALF_COUPONS", 5)
        self.DEFAULT_ONE_MIN_COUPONS: int = self._get_int("DEFAULT_ONE_MIN_COUPONS", 1)

        self.REMINDER_HOUR: int = self._get_int("REMINDER_HOUR", 22)
        self.DAILY_REPORT_HOUR: int = self._get_int("DAILY_REPORT_HOUR", 8)
        self.ADMIN_REPORT_HOUR: int = self._get_int("ADMIN_REPORT_HOUR", 1)
        self.WEEKLY_REPORT_HOUR: int = self._get_int("WEEKLY_REPORT_HOUR", 2)

        self.DEBUG: bool = os.getenv("DEBUG", "False").strip().lower() in (
            "true",
            "1",
            "yes",
            "on",
        )
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").strip().upper()

        # ساخت پوشه‌های موردنیاز پروژه
        self._ensure_directories()

    @staticmethod
    def _get_int(env_key: str, default: int) -> int:
        val = os.getenv(env_key)
        if val is None or not val.strip():
            return default
        try:
            return int(val.strip())
        except ValueError:
            return default

    def _ensure_directories(self) -> None:
        """ایجاد دایرکتوری‌های داده، بکاپ و گزارش‌های اکسل"""
        for folder in ("./data", "./backups", "./reports"):
            Path(folder).mkdir(parents=True, exist_ok=True)

        if self.DATABASE_URL.startswith("sqlite:///"):
            db_file_path = self.DATABASE_URL.replace("sqlite:///", "", 1)
            db_parent = Path(db_file_path).parent
            db_parent.mkdir(parents=True, exist_ok=True)

    def validate(self) -> None:
        """اعتبارسنجی مقادیر حیاتی تنظیمات در بدو اجرای برنامه"""
        if not self.BOT_TOKEN:
            raise ValueError("خطا: متغیر محیطی BOT_TOKEN در فایل .env تنظیم نشده است.")
        if not self.ADMIN_IDS:
            raise ValueError("خطا: متغیر محیطی ADMIN_IDS در فایل .env تنظیم نشده است.")
        if self.DEFAULT_FLOOR < 1:
            raise ValueError("خطا: مقدار DEFAULT_FLOOR باید حداقل 1 دقیقه باشد.")
        if self.LEAGUE_DURATION < 1:
            raise ValueError("خطا: مقدار LEAGUE_DURATION باید حداقل 1 روز باشد.")
        for hour_name, hour_val in [
            ("REMINDER_HOUR", self.REMINDER_HOUR),
            ("DAILY_REPORT_HOUR", self.DAILY_REPORT_HOUR),
            ("ADMIN_REPORT_HOUR", self.ADMIN_REPORT_HOUR),
            ("WEEKLY_REPORT_HOUR", self.WEEKLY_REPORT_HOUR),
        ]:
            if not (0 <= hour_val <= 23):
                raise ValueError(f"خطا: ساعت {hour_name} باید عددی بین 0 تا 23 باشد.")

    def is_super_admin(self, user_id: str | int) -> bool:
        """بررسی مدیر ارشد بودن کاربر"""
        return str(user_id).strip() in self.ADMIN_IDS


settings = Config()

# تنظیمات پایه لاگینگ
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)