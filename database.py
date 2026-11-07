import os
import shutil
import sqlite3
import asyncio
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Generator, Optional, List, Callable, TypeVar, Any

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from config import settings

T = TypeVar("T")
from models import (
    Base,
    Group,
    GroupAdmin,
    User,
    League,
    Cycle,
    SystemState,
)

logger = logging.getLogger(__name__)

# تنظیم موتور SQLite با پشتیبانی از چندرشته‌ای و WAL Mode
IS_SQLITE: bool = settings.is_sqlite

if IS_SQLITE:
    # حالت توسعه/تست: SQLite با پشتیبانی چندرشته‌ای و WAL Mode
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 30},
        pool_pre_ping=True,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record) -> None:
        """فعال‌سازی WAL Mode و کلیدهای خارجی؛ فقط برای SQLite"""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA busy_timeout=30000;")
        cursor.execute("PRAGMA temp_store=MEMORY;")
        cursor.close()
else:
    # حالت تولید: PostgreSQL با کانکشن پولینگ استاندارد
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """مدیریت نشست دیتابیس به صورت Context Manager ایمن"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _run_sync_db_callable(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    with get_db() as db:
        return func(db, *args, **kwargs)


async def run_db(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """اجرای غیرمسدودکننده عملیات دیتابیس در ترد مجزا با asyncio.to_thread"""
    return await asyncio.to_thread(_run_sync_db_callable, func, *args, **kwargs)


def _backup_postgres() -> Optional[str]:
    """
    پشتیبان‌گیری PostgreSQL با pg_dump (در صورت PG_DUMP_ENABLED=true).
    در غیر این صورت صرفاً لاگ می‌شود تا بکاپ توسط زیرساخت (cron/managed backup) مدیریت گردد.
    """
    if not settings.PG_DUMP_ENABLED:
        logger.info(
            "دیتابیس PostgreSQL است؛ بکاپ فایلی انجام نشد (PG_DUMP_ENABLED=false). "
            "بکاپ را از طریق pg_dump زمان‌بندی‌شده یا سرویس مدیریت‌شده انجام دهید."
        )
        return None

    pg_dump_bin = shutil.which("pg_dump")
    if not pg_dump_bin:
        logger.warning("ابزار pg_dump روی سرور یافت نشد؛ بکاپ PostgreSQL انجام نشد.")
        return None

    try:
        url = make_url(settings.DATABASE_URL)
        backup_dir = Path(settings.BACKUP_DIR)
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file = backup_dir / f"ketabkharsho_pg_backup_{timestamp}.dump"

        cmd = [pg_dump_bin, "--format=custom", "--no-owner", "--file", str(out_file)]
        if url.host:
            cmd += ["--host", str(url.host)]
        if url.port:
            cmd += ["--port", str(url.port)]
        if url.username:
            cmd += ["--username", str(url.username)]
        cmd += ["--dbname", str(url.database or "")]

        env = dict(os.environ)
        if url.password:
            env["PGPASSWORD"] = str(url.password)

        subprocess.run(cmd, env=env, check=True, timeout=600, capture_output=True)
        logger.info(f"نسخه پشتیبان PostgreSQL ایجاد شد: {out_file}")

        backups = sorted(
            backup_dir.glob("ketabkharsho_pg_backup_*.dump"), key=lambda p: p.stat().st_mtime
        )
        if len(backups) > 30:
            for old_bkp in backups[:-30]:
                try:
                    old_bkp.unlink()
                except OSError:
                    pass
        return str(out_file)
    except Exception as exc:
        logger.error(f"خطا در تهیه بکاپ PostgreSQL: {exc}")
        return None


def backup_database() -> Optional[str]:
    """تهیه نسخه پشتیبان خودکار: فایلی برای SQLite و pg_dump اختیاری برای PostgreSQL"""
    if not settings.is_sqlite:
        return _backup_postgres()
    if not settings.DATABASE_URL.startswith("sqlite:///"):
        return None
    db_file_str = settings.DATABASE_URL.replace("sqlite:///", "", 1)
    db_path = Path(db_file_str)
    if not db_path.exists() or db_path.stat().st_size == 0:
        return None

    backup_dir = Path(settings.BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"ketabkharsho_backup_{timestamp}.db"
    try:
        src_conn = sqlite3.connect(str(db_path), timeout=30)
        dst_conn = sqlite3.connect(str(backup_file))
        try:
            with dst_conn:
                src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
            src_conn.close()
        logger.info(f"نسخه پشتیبان دیتابیس ایجاد شد: {backup_file}")

        # نگهداری حداکثر ۳۰ نسخه پشتیبان اخیر جهت جلوگیری از پر شدن دیسک
        backups = sorted(backup_dir.glob("ketabkharsho_backup_*.db"), key=lambda p: p.stat().st_mtime)
        if len(backups) > 30:
            for old_bkp in backups[:-30]:
                try:
                    old_bkp.unlink()
                except OSError:
                    pass
        return str(backup_file)
    except Exception as exc:
        logger.error(f"خطا در تهیه بکاپ دیتابیس: {exc}")
        return None


def _run_migrations() -> None:
    """بررسی و افزودن خودکار ستون‌های احتمالی جاافتاده در دیتابیس‌های قدیمی (فقط SQLite)"""
    if not IS_SQLITE:
        return
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    migrations = {
        "groups": [
            ("password", "VARCHAR(8) DEFAULT '1234' NOT NULL"),
            ("is_deleted", "BOOLEAN DEFAULT 0 NOT NULL"),
            ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL"),
        ],
        "group_admins": [
            ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL"),
        ],
        "group_messages": [
            ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL"),
        ],
        "group_terms": [
            ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL"),
        ],
        "users": [
            ("telegram_id", "VARCHAR(100)"),
            ("group_id", "INTEGER DEFAULT 1"),
            ("first_name", "VARCHAR(255)"),
            ("last_name", "VARCHAR(255)"),
            ("league_id", "VARCHAR(50)"),
            ("points", "FLOAT DEFAULT 0.0"),
            ("total_minutes", "INTEGER DEFAULT 0"),
            ("total_pages", "INTEGER DEFAULT 0"),
            ("streak", "INTEGER DEFAULT 0"),
            ("no_study_days", "INTEGER DEFAULT 0"),
            ("absent_days_list", "VARCHAR(500) DEFAULT ''"),
            ("late_days_list", "VARCHAR(500) DEFAULT ''"),
            ("half_coupons", "INTEGER DEFAULT 5"),
            ("one_min_coupons", "INTEGER DEFAULT 1"),
            ("user_floor", "INTEGER"),
            ("last_log_date", "VARCHAR(10)"),
            ("today_minutes", "INTEGER DEFAULT 0"),
            ("today_pages", "INTEGER DEFAULT 0"),
            ("today_points", "FLOAT DEFAULT 0.0"),
            ("today_half_used", "INTEGER DEFAULT 0"),
            ("today_one_min_used", "INTEGER DEFAULT 0"),
            ("is_active", "BOOLEAN DEFAULT 1"),
            ("reminder_enabled", "BOOLEAN DEFAULT 1"),
        ],
        "leagues": [
            ("telegram_id", "VARCHAR(100)"),
            ("group_id", "INTEGER DEFAULT 1"),
            ("floor", "INTEGER DEFAULT 10"),
            ("start_shamsi", "VARCHAR(10)"),
            ("current_day", "INTEGER DEFAULT 1"),
            ("is_active", "BOOLEAN DEFAULT 1"),
            ("is_finished", "BOOLEAN DEFAULT 0"),
            ("is_deleted", "BOOLEAN DEFAULT 0"),
            ("archive_enabled", "BOOLEAN DEFAULT 1 NOT NULL"),
            ("cycle_number", "INTEGER DEFAULT 1 NOT NULL"),
            ("fines_enabled", "BOOLEAN DEFAULT 0 NOT NULL"),
            ("fine_absent_amount", "INTEGER DEFAULT 0 NOT NULL"),
            ("fine_late_amount", "INTEGER DEFAULT 0 NOT NULL"),
        ],
        "fine_records": [
            ("is_frozen", "BOOLEAN DEFAULT 0 NOT NULL"),
        ],
        "activity_logs": [
            ("league_id", "VARCHAR(50)"),
            ("cycle_id", "INTEGER"),
            ("cycle_number", "INTEGER DEFAULT 1"),
            ("league_day", "INTEGER DEFAULT 1"),
            ("pages", "INTEGER DEFAULT 0"),
            ("points_earned", "FLOAT DEFAULT 0.0"),
            ("half_coupon_used", "INTEGER DEFAULT 0"),
            ("one_min_coupon_used", "INTEGER DEFAULT 0"),
            ("log_date", "VARCHAR(10)"),
            ("log_hour", "INTEGER"),
        ],
    }

    with engine.begin() as conn:
        for table_name, columns in migrations.items():
            if table_name in existing_tables:
                existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
                for col_name, col_def in columns:
                    if col_name not in existing_cols:
                        try:
                            conn.execute(
                                text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}")
                            )
                            logger.info(f"ستون {col_name} به جدول {table_name} اضافه شد.")
                        except Exception as exc:
                            logger.warning(f"عدم امکان افزودن ستون {col_name} به {table_name}: {exc}")

        # مقداردهی اولیه telegram_id برای رکوردهای قدیمی احتمالی
        if "users" in existing_tables:
            conn.execute(
                text("UPDATE users SET telegram_id = id WHERE telegram_id IS NULL OR telegram_id = ''")
            )


def _run_postgres_fine_migrations() -> None:
    """افزودن ستون‌های جریمه به جدول leagues در PostgreSQL (idempotent)"""
    if IS_SQLITE:
        return
    statements = [
        "ALTER TABLE leagues ADD COLUMN IF NOT EXISTS fines_enabled BOOLEAN DEFAULT FALSE NOT NULL",
        "ALTER TABLE leagues ADD COLUMN IF NOT EXISTS fine_absent_amount INTEGER DEFAULT 0 NOT NULL",
        "ALTER TABLE leagues ADD COLUMN IF NOT EXISTS fine_late_amount INTEGER DEFAULT 0 NOT NULL",
        "ALTER TABLE fine_records ADD COLUMN IF NOT EXISTS is_frozen BOOLEAN DEFAULT FALSE NOT NULL",
    ]
    for stmt in statements:
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception as exc:
            logger.warning(f"عدم امکان اجرای مایگریشن جریمه ({stmt}): {exc}")


def get_or_create_active_cycle(db: Session, league: League, default_start_shamsi: Optional[str] = None) -> Cycle:
    """تضمین وجود دقیقاً یک چله (Cycle) فعال برای لیگ و برگرداندن آن"""
    active_cycles = (
        db.query(Cycle)
        .filter(Cycle.league_id == league.id, Cycle.status == "active")
        .order_by(Cycle.cycle_number.desc(), Cycle.id.desc())
        .all()
    )
    if active_cycles:
        primary_cycle = active_cycles[0]
        dirty = False
        if len(active_cycles) > 1:
            for extra_cycle in active_cycles[1:]:
                extra_cycle.status = "finished"
                if not extra_cycle.finished_at:
                    extra_cycle.finished_at = datetime.now(timezone.utc)
            dirty = True
        if league.start_shamsi and primary_cycle.start_shamsi != league.start_shamsi:
            primary_cycle.start_shamsi = league.start_shamsi
            dirty = True
        if league.cycle_number and primary_cycle.cycle_number != league.cycle_number:
            primary_cycle.cycle_number = league.cycle_number
            dirty = True
        if dirty:
            db.commit()
        return primary_cycle

    from services import DateService

    start_shamsi = league.start_shamsi or default_start_shamsi or DateService.today_shamsi()
    if not league.start_shamsi:
        league.start_shamsi = start_shamsi

    cycle_num = league.cycle_number if league.cycle_number and league.cycle_number > 0 else 1
    current_day = league.current_day if league.current_day and league.current_day > 0 else 1

    new_cycle = Cycle(
        league_id=league.id,
        cycle_number=cycle_num,
        start_shamsi=start_shamsi,
        current_day=current_day,
        status="active",
    )
    db.add(new_cycle)
    db.commit()
    db.refresh(new_cycle)
    return new_cycle


_INDEX_DDL = [
    ("ix_users_league_active", "users", "league_id, is_active"),
    ("ix_users_tg_active", "users", "telegram_id, is_active"),
    ("ix_users_group_active", "users", "group_id, is_active"),
    ("ix_leagues_group_flags", "leagues", "group_id, is_deleted, is_active"),
    ("ix_cycles_league_status", "cycles", "league_id, status"),
    ("ix_group_admins_group_user", "group_admins", "group_id, user_id"),
    ("ix_actlog_user_league_date", "activity_logs", "user_id, league_id, log_date"),
    ("ix_actlog_league_cycle_day", "activity_logs", "league_id, cycle_id, league_day"),
    ("ix_actlog_league_date", "activity_logs", "league_id, log_date"),
]


def _ensure_indexes() -> None:
    """ساخت ایندکس‌های ترکیبی (idempotent) روی SQLite و PostgreSQL"""
    for idx_name, table, cols in _INDEX_DDL:
        try:
            # هر ایندکس در تراکنش جداگانه تا خطای احتمالی PostgreSQL بقیه را خراب نکند
            with engine.begin() as conn:
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({cols})"))
        except Exception as exc:
            logger.warning(f"عدم امکان ساخت ایندکس {idx_name}: {exc}")

    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ux_fine_record_key ON fine_records "
                    "(league_id, user_id, cycle_id, kind, league_day)"
                )
            )
    except Exception as exc:
        logger.warning(
            f"عدم امکان ساخت ایندکس یکتای جریمه (احتمالاً رکورد تکراری وجود دارد): {exc}"
        )


def _sync_postgres_sequences(db: Session) -> None:
    """
    همگام‌سازی sequence ها در PostgreSQL پس از درج دستی رکورد با id مشخص (مثل گروه ۱)،
    تا درج بعدی با خطای کلید تکراری مواجه نشود.
    """
    if IS_SQLITE:
        return
    for table in (
        "groups",
        "group_admins",
        "cycles",
        "activity_logs",
        "cycle_results",
        "group_messages",
        "group_terms",
        "league_fine_managers",
        "fine_records",
        "fine_payments",
    ):
        try:
            db.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table}), 0) + 1, false)"
                )
            )
        except Exception as exc:
            db.rollback()
            logger.warning(f"عدم امکان همگام‌سازی sequence جدول {table}: {exc}")
    db.commit()


def init_db() -> None:
    """راه‌اندازی اولیه دیتابیس، بکاپ‌گیری، مایگریشن، ساخت گروه ۱ و تضمین چله‌های فعال"""
    backup_database()
    Base.metadata.create_all(bind=engine)
    _run_migrations()
    _run_postgres_fine_migrations()
    _ensure_indexes()

    from services import DateService

    with get_db() as db:
        # ۱. تضمین وجود گروه پیش‌فرض شماره ۱
        default_group = db.query(Group).filter(Group.id == 1).first()
        if not default_group:
            # بررسی عدم تداخل رمز 1234 با گروه فعال دیگر
            conflict_group = (
                db.query(Group)
                .filter(Group.password == "1234", Group.is_deleted == False)
                .first()
            )
            default_pwd = "1234" if not conflict_group else "12345678"
            default_group = Group(
                id=1,
                name="مدرسه مجازی امام حسین ع",
                password=default_pwd,
                is_deleted=False,
            )
            db.add(default_group)
            db.commit()
            db.refresh(default_group)
            logger.info("گروه پیش‌فرض شماره ۱ (مدرسه مجازی امام حسین ع) ایجاد شد.")

        for weak_group in db.query(Group).filter(Group.is_deleted == False).all():
            if len(weak_group.password or "") < 6:
                logger.warning(
                    f"رمز مجموعه «{weak_group.name}» (ID={weak_group.id}) کمتر از ۶ رقم است؛ "
                    "قبل از ثبتنام عمومی آن را با دستور pg تغییر دهید."
                )

        _sync_postgres_sequences(db)

        # ۲. ثبت تمام ADMIN_IDS به عنوان ادمین گروه ۱
        for admin_id in settings.ADMIN_IDS:
            exists = (
                db.query(GroupAdmin)
                .filter(GroupAdmin.group_id == 1, GroupAdmin.user_id == str(admin_id))
                .first()
            )
            if not exists:
                db.add(GroupAdmin(group_id=1, user_id=str(admin_id)))
        db.commit()

        # ۳. تضمین وجود چله فعال برای تمام لیگ‌های فعال
        active_leagues = (
            db.query(League)
            .filter(League.is_deleted == False, League.is_active == True)
            .all()
        )
        today_shamsi = DateService.today_shamsi()
        for lg in active_leagues:
            if not lg.group_id:
                lg.group_id = 1
            if not lg.start_shamsi:
                lg.start_shamsi = today_shamsi
            get_or_create_active_cycle(db, lg, default_start_shamsi=today_shamsi)
        db.commit()


# ---------------------------------------------------------------------------
# توابع کمکی مدیریت وضعیت سیستم و چندپروفایلی (Multi-Profile Helpers)
# ---------------------------------------------------------------------------

def get_system_state(db: Session, key: str, default: Optional[str] = None) -> Optional[str]:
    """دریافت مقدار یک کلید از جدول SystemState"""
    record = db.query(SystemState).filter(SystemState.key == key).first()
    if record and record.value is not None:
        return record.value
    return default


def set_system_state(db: Session, key: str, value: str, commit: bool = True) -> None:
    """ذخیره یا به‌روزرسانی یک کلید در جدول SystemState (با commit=False فقط flush می‌شود)"""
    record = db.query(SystemState).filter(SystemState.key == key).first()
    if record:
        record.value = str(value)
        record.updated_at = datetime.now(timezone.utc)
    else:
        record = SystemState(key=key, value=str(value))
        db.add(record)
    if commit:
        db.commit()
    else:
        db.flush()


def get_user_profiles(db: Session, telegram_id: str | int, only_active: bool = True) -> List[User]:
    """دریافت تمام پروفایل‌های یک شخص واقعی بر اساس telegram_id"""
    tg_id = str(telegram_id).strip()
    query = db.query(User).filter(User.telegram_id == tg_id)
    if only_active:
        query = query.filter(User.is_active == True)
    return query.order_by(User.created_at.asc()).all()


def set_active_user_id(db: Session, telegram_id: str | int, user_id: str) -> None:
    """تنظیم پروفایل فعال فعلی کاربر در SystemState"""
    tg_id = str(telegram_id).strip()
    set_system_state(db, f"active_profile_{tg_id}", str(user_id))


def get_active_user(db: Session, telegram_id: str | int) -> Optional[User]:
    """
    دریافت پروفایل فعال فعلی کاربر بر اساس SystemState.
    اگر پروفایل ذخیره شده وجود نداشت یا غیرفعال بود، اولین پروفایل فعال کاربر را برمی‌گرداند.
    """
    tg_id = str(telegram_id).strip()
    active_prof_id = get_system_state(db, f"active_profile_{tg_id}")
    if active_prof_id:
        user = (
            db.query(User)
            .filter(User.id == active_prof_id, User.is_active == True)
            .first()
        )
        if user:
            return user

    # جستجوی اولین پروفایل فعال
    profiles = get_user_profiles(db, tg_id, only_active=True)
    if profiles:
         chosen = profiles[0]
         set_active_user_id(db, tg_id, chosen.id)
         return chosen

    # بررسی وجود رکورد مستقیم با id == telegram_id (حتی اگر غیرفعال شده یا تازه ثبت‌نام می‌کند)
    return db.query(User).filter(User.telegram_id == tg_id).first()


def generate_new_profile_id(db: Session, telegram_id: str | int, group_id: Optional[int] = None, league_id: Optional[str] = None) -> str:
    """
    تولید شناسه یکتا برای پروفایل کاربر مطابق معماری چندپروفایلی:
    - اولین پروفایل: id = telegram_id
    - پروفایل‌های بعدی: id = f"{telegram_id}_g{group_id}" یا f"{telegram_id}_{league_id}"
    """
    tg_id = str(telegram_id).strip()
    base_user = db.query(User).filter(User.id == tg_id).first()
    if not base_user:
        return tg_id

    if league_id:
        candidate = f"{tg_id}_{league_id}"
        if not db.query(User).filter(User.id == candidate).first():
            return candidate

    if group_id:
        candidate = f"{tg_id}_g{group_id}"
        if not db.query(User).filter(User.id == candidate).first():
            return candidate

    # در صورت وجود پروفایل‌های بیشتر در همان مجموعه/لیگ
    counter = 2
    while True:
        suffix = f"_{league_id}_{counter}" if league_id else f"_g{group_id or 1}_{counter}"
        candidate = f"{tg_id}{suffix}"
        if not db.query(User).filter(User.id == candidate).first():
            return candidate
        counter += 1


def is_group_password_unique(db: Session, password: str, exclude_group_id: Optional[int] = None) -> bool:
    """بررسی یکتا بودن رمز عبور در بین تمام مجموعه‌های فعال (is_deleted == False)"""
    query = db.query(Group).filter(
        Group.password == str(password).strip(),
        Group.is_deleted == False,
    )
    if exclude_group_id is not None:
        query = query.filter(Group.id != exclude_group_id)
    return query.first() is None


def get_admin_group_ids(db: Session, telegram_id: str | int) -> List[int]:
    """برگرداندن لیست آیدی مجموعه‌هایی که کاربر به آن‌ها دسترسی مدیریت دارد"""
    tg_id = str(telegram_id).strip()
    if settings.is_super_admin(tg_id):
        groups = db.query(Group).filter(Group.is_deleted == False).order_by(Group.id.asc()).all()
        return [g.id for g in groups]

    admin_rows = db.query(GroupAdmin).filter(GroupAdmin.user_id == tg_id).all()
    if not admin_rows:
        return []
    group_ids = [r.group_id for r in admin_rows]
    active_groups = (
        db.query(Group)
        .filter(Group.id.in_(group_ids), Group.is_deleted == False)
        .order_by(Group.id.asc())
        .all()
    )
    return [g.id for g in active_groups]


def is_user_admin(db: Session, telegram_id: str | int, group_id: Optional[int] = None) -> bool:
    """بررسی اینکه آیا کاربر سوپرادمین یا ادمین مجموعه است"""
    tg_id = str(telegram_id).strip()
    if settings.is_super_admin(tg_id):
        return True
    allowed_groups = get_admin_group_ids(db, tg_id)
    if group_id is not None:
        return group_id in allowed_groups
    return len(allowed_groups) > 0