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
        raw_db_url: str = os.getenv(
            "DATABASE_URL", "sqlite:///./data/ketabkharsho.db"
        ).strip()
        self.DATABASE_URL: str = self._normalize_database_url(raw_db_url)

        # تنظیمات QueuePool مخصوص PostgreSQL
        self.DB_POOL_SIZE: int = self._get_int("DB_POOL_SIZE", 20)
        self.DB_MAX_OVERFLOW: int = self._get_int("DB_MAX_OVERFLOW", 30)
        self.DB_POOL_TIMEOUT: int = self._get_int("DB_POOL_TIMEOUT", 30)
        self.DB_POOL_RECYCLE: int = self._get_int("DB_POOL_RECYCLE", 1800)

        # پشتیبان‌گیری
        self.BACKUP_DIR: str = os.getenv("BACKUP_DIR", "./backups").strip() or "./backups"
        self.PG_DUMP_ENABLED: bool = os.getenv("PG_DUMP_ENABLED", "false").strip().lower() in (
            "true",
            "1",
            "yes",
            "on",
        )

        # ارسال پلکانی (Staggered) و خواندن دسته‌ای از دیتابیس
        self.BROADCAST_BATCH_SIZE: int = max(1, self._get_int("BROADCAST_BATCH_SIZE", 40))
        self.BROADCAST_MSG_DELAY: float = max(0.0, self._get_float("BROADCAST_MSG_DELAY", 0.05))
        self.BROADCAST_BATCH_PAUSE: float = max(0.0, self._get_float("BROADCAST_BATCH_PAUSE", 1.0))
        self.DB_CHUNK_SIZE: int = max(50, self._get_int("DB_CHUNK_SIZE", 500))

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
    def _normalize_database_url(url: str) -> str:
        """یکسان‌سازی آدرس PostgreSQL با درایور psycopg2 (SQLAlchemy 2.x)"""
        if url.startswith("postgres://"):
            return "postgresql+psycopg2://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            return "postgresql+psycopg2://" + url[len("postgresql://"):]
        return url

    @property
    def is_sqlite(self) -> bool:
        """آیا دیتابیس فعلی SQLite است (حالت توسعه/تست)؟"""
        return self.DATABASE_URL.startswith("sqlite")

    @staticmethod
    def _get_float(env_key: str, default: float) -> float:
        val = os.getenv(env_key)
        if val is None or not val.strip():
            return default
        try:
            return float(val.strip())
        except ValueError:
            return default

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