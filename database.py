import os
import uuid
import shutil
import sqlite3
import asyncio
import logging
import threading
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Generator, Optional, List, Callable, TypeVar, Any, Dict, Tuple

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


_BACKUP_LOCK = threading.RLock()


def reload_superadmins_from_db() -> None:
    """بارگذاری مجدد سوپرادمین‌های پایدار از جدول system_state به حافظه"""
    with get_db() as db:
        extra_sas = (
            db.query(SystemState.key)
            .filter(
                SystemState.key.startswith("superadmin_", autoescape=True),
                SystemState.value == "1",
            )
            .all()
        )
        for r in extra_sas:
            uid = r[0][len("superadmin_"):].strip()
            if uid:
                settings.add_super_admin(uid)


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

    with _BACKUP_LOCK:
        backup_dir = Path(settings.BACKUP_DIR)
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        uniq = uuid.uuid4().hex[:6]
        backup_file = backup_dir / f"ketabkharsho_backup_{timestamp}_{uniq}.db"
        try:
            src_conn = sqlite3.connect(str(db_path), timeout=30)
            dst_conn = sqlite3.connect(str(backup_file), timeout=30)
            try:
                with dst_conn:
                    src_conn.backup(dst_conn, pages=256, sleep=0.05)
            finally:
                dst_conn.close()
                src_conn.close()
            logger.info(f"نسخه پشتیبان دیتابیس ایجاد شد: {backup_file}")

            backups = sorted(
                backup_dir.glob("ketabkharsho_backup_*.db"),
                key=lambda p: p.stat().st_mtime,
            )
            if len(backups) > 30:
                for old_bkp in backups[:-30]:
                    try:
                        old_bkp.unlink()
                    except OSError:
                        pass
            return str(backup_file)
        except Exception as exc:
            if backup_file.exists():
                try:
                    backup_file.unlink()
                except OSError:
                    pass
            logger.error(f"خطا در تهیه بکاپ دیتابیس: {exc}")
            return None


def get_live_sqlite_path() -> Optional[Path]:
    """دریافت مسیر واقعی فایل SQLite فعال"""
    if not settings.is_sqlite or not settings.DATABASE_URL.startswith("sqlite:///"):
        return None
    db_file_str = settings.DATABASE_URL.replace("sqlite:///", "", 1)
    return Path(db_file_str)


def validate_sqlite_file(file_path: str) -> Tuple[bool, str, Dict[str, int]]:
    """
    اعتبارسنجی فایل دیتابیس SQLite:
    بررسی امضای فایل، دستور PRAGMA integrity_check و وجود جداول کلیدی ربات.
    """
    path = Path(file_path)
    if not path.exists() or path.stat().st_size < 100:
        return False, "فایل وجود ندارد یا حجم آن بسیار کم و نامعتبر است.", {}

    stats: Dict[str, int] = {
        "groups_count": 0,
        "leagues_count": 0,
        "users_count": 0,
        "logs_count": 0,
        "fines_count": 0,
    }

    try:
        with open(path, "rb") as fh:
            if fh.read(16) != b"SQLite format 3\x00":
                return False, "امضای فایل با فرمت استاندارد SQLite 3 مطابقت ندارد.", {}
    except OSError as exc:
        return False, f"خطا در خواندن فایل دیتابیس: {exc}", {}

    try:
        try:
            conn = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True, timeout=10)
        except sqlite3.OperationalError:
            conn = sqlite3.connect(str(path), timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            integrity = conn.execute("PRAGMA integrity_check;").fetchone()
            if not integrity or str(integrity[0]).lower() != "ok":
                return False, "فایل دیتابیس آسیب‌دیده است (Integrity check failed).", {}

            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            if not any(k in tables for k in ("users", "leagues", "groups")):
                return False, "جداول استاندارد ربات کتابخوارشو در فایل یافت نشد.", {}

            if "groups" in tables:
                stats["groups_count"] = conn.execute("SELECT count(*) FROM groups").fetchone()[0]
            if "leagues" in tables:
                stats["leagues_count"] = conn.execute("SELECT count(*) FROM leagues").fetchone()[0]
            if "users" in tables:
                stats["users_count"] = conn.execute("SELECT count(*) FROM users").fetchone()[0]
            if "activity_logs" in tables:
                stats["logs_count"] = conn.execute("SELECT count(*) FROM activity_logs").fetchone()[0]
            if "fine_records" in tables:
                stats["fines_count"] = conn.execute("SELECT count(*) FROM fine_records").fetchone()[0]

            return True, "فایل پایگاه داده معتبر است.", stats
        finally:
            conn.close()
    except Exception as exc:
        return False, f"خطا در اعتبارسنجی فایل دیتابیس: {exc}", {}


def restore_database_replace(uploaded_file_path: str) -> Tuple[bool, str, Dict[str, int]]:
    """
    جایگزینی و بازیابی کامل پایگاه داده فعال با فایل آپلودشده.
    پیش از جایگزینی، یک نسخه پشتیبان امن خودکار از پایگاه داده فعال تهیه می‌شود.
    """
    live_path = get_live_sqlite_path()
    if not live_path:
        return False, "پایگاه داده فعال SQLite یافت نشد.", {}

    val_ok, val_msg, stats = validate_sqlite_file(uploaded_file_path)
    if not val_ok:
        return False, f"فایل نامعتبر است: {val_msg}", {}

    with _BACKUP_LOCK:
        if live_path.exists() and live_path.stat().st_size > 0:
            emergency_bkp = backup_database()
            if not emergency_bkp:
                return False, "تهیه نسخه پشتیبان اضطراری پیش از جایگزینی ناموفق بود؛ عملیات متوقف شد.", {}

        engine.dispose()

        try:
            src_conn = sqlite3.connect(uploaded_file_path, timeout=30)
            dst_conn = sqlite3.connect(str(live_path), timeout=60)
            try:
                with dst_conn:
                    src_conn.backup(dst_conn, pages=256, sleep=0.05)
            finally:
                dst_conn.close()
                src_conn.close()

            chk = sqlite3.connect(str(live_path), timeout=30)
            try:
                chk.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            finally:
                chk.close()

            engine.dispose()
            Base.metadata.create_all(bind=engine)
            _run_migrations()
            _ensure_indexes()
            reload_superadmins_from_db()

            logger.info(f"پایگاه داده با موفقیت با فایل {uploaded_file_path} جایگزین شد.")
            return True, "پایگاه داده با موفقیت جایگزین و بازیابی شد.", stats
        except Exception as exc:
            logger.error(f"خطا در جایگزینی کامل دیتابیس: {exc}", exc_info=True)
            return False, f"خطا در جایگزینی دیتابیس: {exc}", {}


def _get_table_columns_info(conn: sqlite3.Connection, table_name: str) -> Dict[str, Dict[str, Any]]:
    rows = conn.execute(f"PRAGMA table_info({table_name});").fetchall()
    return {
        r[1]: {
            "type": r[2],
            "notnull": bool(r[3]),
            "default": r[4],
            "pk": bool(r[5]),
        }
        for r in rows
    }


COMMON_COLUMN_DEFAULTS: Dict[str, Any] = {
    "is_finished": 0,
    "is_deleted": 0,
    "is_active": 1,
    "reminder_enabled": 1,
    "archive_enabled": 1,
    "fines_enabled": 0,
    "fine_absent_amount": 0,
    "fine_late_amount": 0,
    "is_waived": 0,
    "is_frozen": 0,
    "floor": 10,
    "current_day": 1,
    "cycle_number": 1,
    "password": "1234",
    "half_coupons": settings.DEFAULT_HALF_COUPONS,
    "one_min_coupons": settings.DEFAULT_ONE_MIN_COUPONS,
    "streak": 0,
    "no_study_days": 0,
    "points": 0.0,
    "total_minutes": 0,
    "total_pages": 0,
    "today_minutes": 0,
    "today_pages": 0,
    "today_points": 0.0,
    "today_half_used": 0,
    "today_one_min_used": 0,
    "absent_days_list": "",
    "late_days_list": "",
    "minutes": 0,
    "pages": 0,
    "points_earned": 0.0,
    "half_coupon_used": 0,
    "one_min_coupon_used": 0,
    "amount": 0,
    "status": "active",
}


def _prepare_row_for_destination(
    dst_info: Dict[str, Dict[str, Any]],
    row_dict: Dict[str, Any],
    defaults: Dict[str, Any],
) -> Dict[str, Any]:
    final_dict: Dict[str, Any] = {}
    for col, info in dst_info.items():
        if col in row_dict and row_dict[col] is not None:
            final_dict[col] = row_dict[col]
        elif info["notnull"] and info["default"] is None:
            final_dict[col] = defaults.get(col, 0)
    return final_dict


def restore_database_merge(uploaded_file_path: str) -> Tuple[bool, str, Dict[str, int]]:
    """
    ادغام هوشمند و افزودن داده‌های جدید از فایل پایگاه داده آپلودشده به پایگاه داده فعال:
    مجموعه‌ها، رمزها، ادمین‌ها، لیگ‌ها، چله‌ها، کاربران، امتیازات، لاگ‌ها و جریمه‌ها.
    پیش از اعمال، بکاپ امن خودکار گرفته می‌شود.
    """
    live_path = get_live_sqlite_path()
    if not live_path or not live_path.exists():
        return False, "پایگاه داده فعال SQLite یافت نشد.", {}

    val_ok, val_msg, _ = validate_sqlite_file(uploaded_file_path)
    if not val_ok:
        return False, f"فایل نامعتبر است: {val_msg}", {}

    with _BACKUP_LOCK:
        emergency_bkp = backup_database()
        if not emergency_bkp and live_path.stat().st_size > 0:
            return False, "تهیه نسخه پشتیبان اضطراری پیش از ادغام ناموفق بود؛ عملیات متوقف شد.", {}

        engine.dispose()

        summary: Dict[str, int] = {
            "groups": 0,
            "admins": 0,
            "leagues": 0,
            "fine_managers": 0,
            "cycles": 0,
            "users": 0,
            "logs": 0,
            "fines": 0,
            "payments": 0,
            "results": 0,
            "messages": 0,
            "terms": 0,
        }

        src_conn = sqlite3.connect(uploaded_file_path, timeout=30)
        src_conn.row_factory = sqlite3.Row
        dst_conn = sqlite3.connect(str(live_path), timeout=60)
        dst_conn.row_factory = sqlite3.Row

        try:
            src_tables = {
                r[0]
                for r in src_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            cycle_id_map: Dict[int, int] = {}

            with dst_conn:
                if "groups" in src_tables:
                    dst_cols = _get_table_columns_info(dst_conn, "groups")
                    for row in src_conn.execute("SELECT * FROM groups").fetchall():
                        g_dict = dict(row)
                        exists = dst_conn.execute(
                            "SELECT id FROM groups WHERE id = ?", (g_dict["id"],)
                        ).fetchone()
                        if exists:
                            dst_conn.execute(
                                "UPDATE groups SET name = ?, password = ?, is_deleted = ? WHERE id = ?",
                                (
                                    g_dict["name"],
                                    g_dict["password"] if g_dict.get("password") is not None else "1234",
                                    g_dict["is_deleted"] if g_dict.get("is_deleted") is not None else 0,
                                    g_dict["id"],
                                ),
                            )
                        else:
                            final_g = _prepare_row_for_destination(dst_cols, g_dict, COMMON_COLUMN_DEFAULTS)
                            cols = list(final_g.keys())
                            placeholders = ", ".join(["?"] * len(cols))
                            dst_conn.execute(
                                f"INSERT INTO groups ({', '.join(cols)}) VALUES ({placeholders})",
                                [final_g[c] for c in cols],
                            )
                            summary["groups"] += 1

                if "group_admins" in src_tables:
                    dst_cols = _get_table_columns_info(dst_conn, "group_admins")
                    for row in src_conn.execute("SELECT * FROM group_admins").fetchall():
                        ga_dict = dict(row)
                        exists = dst_conn.execute(
                            "SELECT id FROM group_admins WHERE group_id = ? AND user_id = ?",
                            (ga_dict["group_id"], ga_dict["user_id"]),
                        ).fetchone()
                        if not exists:
                            final_ga = _prepare_row_for_destination(dst_cols, ga_dict, COMMON_COLUMN_DEFAULTS)
                            cols = [k for k in final_ga.keys() if k != "id"]
                            placeholders = ", ".join(["?"] * len(cols))
                            dst_conn.execute(
                                f"INSERT INTO group_admins ({', '.join(cols)}) VALUES ({placeholders})",
                                [final_ga[c] for c in cols],
                            )
                            summary["admins"] += 1

                if "leagues" in src_tables:
                    dst_cols = _get_table_columns_info(dst_conn, "leagues")
                    for row in src_conn.execute("SELECT * FROM leagues").fetchall():
                        l_dict = dict(row)
                        exists = dst_conn.execute(
                            "SELECT id, fine_absent_amount, fine_late_amount FROM leagues WHERE id = ?",
                            (l_dict["id"],),
                        ).fetchone()
                        if exists:
                            dst_conn.execute(
                                """
                                UPDATE leagues SET
                                    name = ?, floor = ?, start_shamsi = ?, current_day = ?,
                                    is_deleted = ?, is_active = ?, cycle_number = ?,
                                    fines_enabled = ?, fine_absent_amount = ?, fine_late_amount = ?,
                                    archive_enabled = ?
                                WHERE id = ?
                                """,
                                (
                                    l_dict["name"],
                                    l_dict["floor"] if l_dict.get("floor") is not None else 10,
                                    l_dict.get("start_shamsi"),
                                    l_dict["current_day"] if l_dict.get("current_day") is not None else 1,
                                    l_dict["is_deleted"] if l_dict.get("is_deleted") is not None else 0,
                                    l_dict["is_active"] if l_dict.get("is_active") is not None else 1,
                                    l_dict["cycle_number"] if l_dict.get("cycle_number") is not None else 1,
                                    l_dict["fines_enabled"] if l_dict.get("fines_enabled") is not None else 0,
                                    l_dict["fine_absent_amount"] if l_dict.get("fine_absent_amount") is not None else exists["fine_absent_amount"],
                                    l_dict["fine_late_amount"] if l_dict.get("fine_late_amount") is not None else exists["fine_late_amount"],
                                    l_dict["archive_enabled"] if l_dict.get("archive_enabled") is not None else 1,
                                    l_dict["id"],
                                ),
                            )
                        else:
                            final_l = _prepare_row_for_destination(dst_cols, l_dict, COMMON_COLUMN_DEFAULTS)
                            cols = list(final_l.keys())
                            placeholders = ", ".join(["?"] * len(cols))
                            dst_conn.execute(
                                f"INSERT INTO leagues ({', '.join(cols)}) VALUES ({placeholders})",
                                [final_l[c] for c in cols],
                            )
                            summary["leagues"] += 1

                if "league_fine_managers" in src_tables:
                    dst_cols = _get_table_columns_info(dst_conn, "league_fine_managers")
                    for row in src_conn.execute("SELECT * FROM league_fine_managers").fetchall():
                        fm_dict = dict(row)
                        tg_val = fm_dict.get("telegram_id") or fm_dict.get("user_id")
                        if not tg_val:
                            continue
                        fm_dict["telegram_id"] = str(tg_val)
                        exists = dst_conn.execute(
                            "SELECT id FROM league_fine_managers WHERE league_id = ? AND telegram_id = ?",
                            (fm_dict["league_id"], fm_dict["telegram_id"]),
                        ).fetchone()
                        if not exists:
                            final_fm = _prepare_row_for_destination(dst_cols, fm_dict, COMMON_COLUMN_DEFAULTS)
                            cols = [k for k in final_fm.keys() if k != "id"]
                            placeholders = ", ".join(["?"] * len(cols))
                            dst_conn.execute(
                                f"INSERT INTO league_fine_managers ({', '.join(cols)}) VALUES ({placeholders})",
                                [final_fm[c] for c in cols],
                            )
                            summary["fine_managers"] += 1

                if "cycles" in src_tables:
                    dst_cols = _get_table_columns_info(dst_conn, "cycles")
                    for row in src_conn.execute("SELECT * FROM cycles").fetchall():
                        c_dict = dict(row)
                        src_cid = c_dict.get("id")
                        exists = dst_conn.execute(
                            "SELECT id FROM cycles WHERE league_id = ? AND cycle_number = ?",
                            (c_dict["league_id"], c_dict.get("cycle_number", 1)),
                        ).fetchone()
                        if exists:
                            if src_cid is not None:
                                cycle_id_map[int(src_cid)] = int(exists["id"])
                        else:
                            final_c = _prepare_row_for_destination(dst_cols, c_dict, COMMON_COLUMN_DEFAULTS)
                            cols = [k for k in final_c.keys() if k != "id"]
                            placeholders = ", ".join(["?"] * len(cols))
                            cur = dst_conn.execute(
                                f"INSERT INTO cycles ({', '.join(cols)}) VALUES ({placeholders})",
                                [final_c[c] for c in cols],
                            )
                            if src_cid is not None:
                                cycle_id_map[int(src_cid)] = int(cur.lastrowid)
                            summary["cycles"] += 1

                if "users" in src_tables:
                    dst_cols = _get_table_columns_info(dst_conn, "users")
                    for row in src_conn.execute("SELECT * FROM users").fetchall():
                        u_dict = dict(row)
                        exists = dst_conn.execute(
                            "SELECT id, half_coupons, one_min_coupons, is_active FROM users WHERE id = ?",
                            (u_dict["id"],),
                        ).fetchone()
                        if exists:
                            half_val = (
                                int(u_dict["half_coupons"])
                                if u_dict.get("half_coupons") is not None
                                else int(exists["half_coupons"])
                            )
                            one_val = (
                                int(u_dict["one_min_coupons"])
                                if u_dict.get("one_min_coupons") is not None
                                else int(exists["one_min_coupons"])
                            )
                            active_val = (
                                int(u_dict["is_active"])
                                if u_dict.get("is_active") is not None
                                else int(exists["is_active"])
                            )
                            dst_conn.execute(
                                """
                                UPDATE users SET
                                    name = ?, first_name = ?, last_name = ?, league_id = ?,
                                    points = MAX(points, ?),
                                    total_minutes = MAX(total_minutes, ?),
                                    total_pages = MAX(total_pages, ?),
                                    streak = MAX(streak, ?),
                                    half_coupons = ?, one_min_coupons = ?,
                                    is_active = ?
                                WHERE id = ?
                                """,
                                (
                                    u_dict["name"],
                                    u_dict.get("first_name"),
                                    u_dict.get("last_name"),
                                    u_dict.get("league_id"),
                                    float(u_dict["points"] if u_dict.get("points") is not None else 0.0),
                                    int(u_dict["total_minutes"] if u_dict.get("total_minutes") is not None else 0),
                                    int(u_dict["total_pages"] if u_dict.get("total_pages") is not None else 0),
                                    int(u_dict["streak"] if u_dict.get("streak") is not None else 0),
                                    half_val,
                                    one_val,
                                    active_val,
                                    u_dict["id"],
                                ),
                            )
                        else:
                            final_u = _prepare_row_for_destination(dst_cols, u_dict, COMMON_COLUMN_DEFAULTS)
                            cols = list(final_u.keys())
                            placeholders = ", ".join(["?"] * len(cols))
                            dst_conn.execute(
                                f"INSERT INTO users ({', '.join(cols)}) VALUES ({placeholders})",
                                [final_u[c] for c in cols],
                            )
                            summary["users"] += 1

                if "activity_logs" in src_tables:
                    dst_cols = _get_table_columns_info(dst_conn, "activity_logs")
                    for row in src_conn.execute("SELECT * FROM activity_logs").fetchall():
                        a_dict = dict(row)
                        if a_dict.get("cycle_id") is not None:
                            a_dict["cycle_id"] = cycle_id_map.get(int(a_dict["cycle_id"]), a_dict["cycle_id"])
                        exists = dst_conn.execute(
                            "SELECT id FROM activity_logs WHERE user_id = ? AND league_id = ? AND log_date = ?",
                            (a_dict["user_id"], a_dict.get("league_id"), a_dict["log_date"]),
                        ).fetchone()
                        if not exists:
                            final_a = _prepare_row_for_destination(dst_cols, a_dict, COMMON_COLUMN_DEFAULTS)
                            cols = [k for k in final_a.keys() if k != "id"]
                            placeholders = ", ".join(["?"] * len(cols))
                            dst_conn.execute(
                                f"INSERT INTO activity_logs ({', '.join(cols)}) VALUES ({placeholders})",
                                [final_a[c] for c in cols],
                            )
                            summary["logs"] += 1

                if "fine_records" in src_tables:
                    dst_cols = _get_table_columns_info(dst_conn, "fine_records")
                    for row in src_conn.execute("SELECT * FROM fine_records").fetchall():
                        fr_dict = dict(row)
                        if fr_dict.get("cycle_id") is not None:
                            fr_dict["cycle_id"] = cycle_id_map.get(int(fr_dict["cycle_id"]), fr_dict["cycle_id"])
                        exists = dst_conn.execute(
                            "SELECT id FROM fine_records WHERE user_id = ? AND league_id = ? AND COALESCE(cycle_id, -1) = COALESCE(?, -1) AND league_day = ? AND kind = ?",
                            (
                                fr_dict["user_id"],
                                fr_dict.get("league_id"),
                                fr_dict.get("cycle_id"),
                                fr_dict.get("league_day"),
                                fr_dict["kind"],
                            ),
                        ).fetchone()
                        if not exists:
                            final_fr = _prepare_row_for_destination(dst_cols, fr_dict, COMMON_COLUMN_DEFAULTS)
                            cols = [k for k in final_fr.keys() if k != "id"]
                            placeholders = ", ".join(["?"] * len(cols))
                            dst_conn.execute(
                                f"INSERT INTO fine_records ({', '.join(cols)}) VALUES ({placeholders})",
                                [final_fr[c] for c in cols],
                            )
                            summary["fines"] += 1

                if "fine_payments" in src_tables:
                    dst_cols = _get_table_columns_info(dst_conn, "fine_payments")
                    for row in src_conn.execute("SELECT * FROM fine_payments").fetchall():
                        fp_dict = dict(row)
                        if fp_dict.get("recorded_by") is None and fp_dict.get("approved_by") is not None:
                            fp_dict["recorded_by"] = fp_dict["approved_by"]
                        exists = dst_conn.execute(
                            "SELECT id FROM fine_payments WHERE user_id = ? AND league_id = ? AND amount = ? AND COALESCE(created_at, '') = COALESCE(?, '')",
                            (
                                fp_dict["user_id"],
                                fp_dict.get("league_id"),
                                fp_dict.get("amount", 0),
                                fp_dict.get("created_at"),
                            ),
                        ).fetchone()
                        if not exists:
                            final_fp = _prepare_row_for_destination(dst_cols, fp_dict, COMMON_COLUMN_DEFAULTS)
                            cols = [k for k in final_fp.keys() if k != "id"]
                            placeholders = ", ".join(["?"] * len(cols))
                            dst_conn.execute(
                                f"INSERT INTO fine_payments ({', '.join(cols)}) VALUES ({placeholders})",
                                [final_fp[c] for c in cols],
                            )
                            summary["payments"] += 1

                if "cycle_results" in src_tables:
                    dst_cols = _get_table_columns_info(dst_conn, "cycle_results")
                    for row in src_conn.execute("SELECT * FROM cycle_results").fetchall():
                        cr_dict = dict(row)
                        if cr_dict.get("cycle_id") is not None:
                            cr_dict["cycle_id"] = cycle_id_map.get(int(cr_dict["cycle_id"]), cr_dict["cycle_id"])
                        exists = dst_conn.execute(
                            "SELECT id FROM cycle_results WHERE cycle_id = ? AND user_id = ?",
                            (cr_dict.get("cycle_id"), cr_dict["user_id"]),
                        ).fetchone()
                        if not exists:
                            final_cr = _prepare_row_for_destination(dst_cols, cr_dict, COMMON_COLUMN_DEFAULTS)
                            cols = [k for k in final_cr.keys() if k != "id"]
                            placeholders = ", ".join(["?"] * len(cols))
                            dst_conn.execute(
                                f"INSERT INTO cycle_results ({', '.join(cols)}) VALUES ({placeholders})",
                                [final_cr[c] for c in cols],
                            )
                            summary["results"] += 1

                if "group_messages" in src_tables:
                    dst_cols = _get_table_columns_info(dst_conn, "group_messages")
                    for row in src_conn.execute("SELECT * FROM group_messages").fetchall():
                        gm_dict = dict(row)
                        m_key = gm_dict.get("msg_key") or gm_dict.get("key")
                        m_text = gm_dict.get("custom_text") if gm_dict.get("custom_text") is not None else gm_dict.get("text")
                        if not m_key or m_text is None:
                            continue
                        gm_dict["msg_key"] = m_key
                        gm_dict["custom_text"] = m_text
                        exists = dst_conn.execute(
                            "SELECT id FROM group_messages WHERE group_id = ? AND msg_key = ?",
                            (gm_dict["group_id"], m_key),
                        ).fetchone()
                        if exists:
                            dst_conn.execute(
                                "UPDATE group_messages SET custom_text = ? WHERE id = ?",
                                (m_text, exists["id"]),
                            )
                        else:
                            final_gm = _prepare_row_for_destination(dst_cols, gm_dict, COMMON_COLUMN_DEFAULTS)
                            cols = [k for k in final_gm.keys() if k != "id"]
                            placeholders = ", ".join(["?"] * len(cols))
                            dst_conn.execute(
                                f"INSERT INTO group_messages ({', '.join(cols)}) VALUES ({placeholders})",
                                [final_gm[c] for c in cols],
                            )
                            summary["messages"] += 1

                if "group_terms" in src_tables:
                    dst_cols = _get_table_columns_info(dst_conn, "group_terms")
                    for row in src_conn.execute("SELECT * FROM group_terms").fetchall():
                        gt_dict = dict(row)
                        t_key = gt_dict.get("term_key") or gt_dict.get("key")
                        t_val = gt_dict.get("custom_term") if gt_dict.get("custom_term") is not None else gt_dict.get("value")
                        if not t_key or t_val is None:
                            continue
                        gt_dict["term_key"] = t_key
                        gt_dict["custom_term"] = t_val
                        exists = dst_conn.execute(
                            "SELECT id FROM group_terms WHERE group_id = ? AND term_key = ?",
                            (gt_dict["group_id"], t_key),
                        ).fetchone()
                        if exists:
                            dst_conn.execute(
                                "UPDATE group_terms SET custom_term = ? WHERE id = ?",
                                (t_val, exists["id"]),
                            )
                        else:
                            final_gt = _prepare_row_for_destination(dst_cols, gt_dict, COMMON_COLUMN_DEFAULTS)
                            cols = [k for k in final_gt.keys() if k != "id"]
                            placeholders = ", ".join(["?"] * len(cols))
                            dst_conn.execute(
                                f"INSERT INTO group_terms ({', '.join(cols)}) VALUES ({placeholders})",
                                [final_gt[c] for c in cols],
                            )
                            summary["terms"] += 1

                src_state_table = (
                    "system_state"
                    if "system_state" in src_tables
                    else ("system_states" if "system_states" in src_tables else None)
                )
                if src_state_table:
                    for row in src_conn.execute(f"SELECT * FROM {src_state_table}").fetchall():
                        ss_dict = dict(row)
                        exists = dst_conn.execute(
                            "SELECT key FROM system_state WHERE key = ?", (ss_dict["key"],)
                        ).fetchone()
                        if not exists:
                            dst_conn.execute(
                                "INSERT INTO system_state (key, value) VALUES (?, ?)",
                                (ss_dict["key"], ss_dict.get("value")),
                            )

            dst_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            logger.info(f"ادغام هوشمند پایگاه داده با موفقیت انجام شد: {summary}")
            return True, "عملیات ادغام هوشمند با موفقیت تکمیل شد.", summary
        except Exception as exc:
            logger.error(f"خطا در ادغام هوشمند دیتابیس: {exc}", exc_info=True)
            return False, f"خطا در ادغام دیتابیس: {exc}", summary
        finally:
            dst_conn.close()
            src_conn.close()
            engine.dispose()


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

        # ۲. ثبت تمام ADMIN_IDS به عنوان ادمین گروه ۱ و بارگذاری سوپرادمین‌های پایدار
        extra_sas = (
            db.query(SystemState.key)
            .filter(
                SystemState.key.startswith("superadmin_", autoescape=True),
                SystemState.value == "1",
            )
            .all()
        )
        for r in extra_sas:
            uid = r[0][len("superadmin_"):].strip()
            if uid:
                settings.add_super_admin(uid)

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
            cyc = get_or_create_active_cycle(db, lg, default_start_shamsi=today_shamsi)
            # پالایش هوشمند کلیه لاگ‌ها و امتیازات مربوط به قبل از تاریخ شروع در هر شرایط زمانی دیپلوی
            from handlers import cleanse_prestart_activity_and_scores
            cleanse_prestart_activity_and_scores(db, lg, cyc)
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