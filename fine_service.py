"""
سرویس سیستم جریمه هر لیگ (دفتر جریمه پایدار).

اصول طراحی:
- جریمه‌ها در جدول FineRecord ذخیره می‌شوند (مبلغ در لحظه ثبت ثابت می‌ماند) تا با ریست شمارنده‌های
  چله جدید از بین نروند و بدهی‌های پرداخت‌نشده باقی بماند.
- هم‌گام‌سازی (sync) فقط رکوردهای چله فعال را اضافه/حذف می‌کند؛ رکوردهای چله‌های قبلی دست‌نخورده می‌مانند.
- حذف جریمه توسط مسئول به صورت «بخشودگی» (is_waived) انجام می‌شود تا دوباره خودکار ساخته نشود.
- بدهی هر پروفایل = مجموع جریمه‌های بخشوده‌نشده − مجموع پرداخت‌ها.
"""
import logging
import threading
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import (
    User,
    League,
    FineRecord,
    FinePayment,
    LeagueFineManager,
)
from services import AbsenceService, DateService

logger = logging.getLogger(__name__)

KIND_ABSENT = "absent"
KIND_LATE = "late"
KIND_LABELS = {KIND_ABSENT: "غیبت", KIND_LATE: "عدم اعلام"}

# سقف منطقی مبلغ ورودی (تومان) برای جلوگیری از خطای تایپی/سرریز
MAX_AMOUNT = 1_000_000_000


def format_toman(amount: Any) -> str:
    """۱۲۳۴۵۶ -> «۱۲۳,۴۵۶ تومان» (با ارقام فارسی)"""
    try:
        n = int(amount)
    except (TypeError, ValueError):
        n = 0
    s = f"{n:,}"
    s = s.translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
    return f"{s} تومان"


def parse_amount(raw: str) -> Optional[int]:
    """تبدیل ورودی کاربر (ارقام فارسی/عربی، ویرگول) به عدد صحیح مثبت یا صفر؛ در صورت نامعتبر بودن None"""
    if raw is None:
        return None
    s = DateService.normalize_digits(str(raw).strip())
    for ch in (",", "٬", "،", " ", "_"):
        s = s.replace(ch, "")
    if not (s.isascii() and s.isdigit()):
        return None
    val = int(s)
    if val > MAX_AMOUNT:
        return None
    return val


# ---------------------------------------------------------------------------
# مدیریت مسئولین جریمه
# ---------------------------------------------------------------------------

def get_manager_ids(db: Session, league_id: str) -> List[str]:
    rows = (
        db.query(LeagueFineManager.telegram_id)
        .filter(LeagueFineManager.league_id == league_id)
        .all()
    )
    return [str(r[0]) for r in rows]


def is_fine_manager(db: Session, league_id: str, telegram_id: Any) -> bool:
    return (
        db.query(LeagueFineManager.id)
        .filter(
            LeagueFineManager.league_id == league_id,
            LeagueFineManager.telegram_id == str(telegram_id),
        )
        .first()
        is not None
    )


def add_manager(db: Session, league_id: str, telegram_id: Any) -> bool:
    """افزودن مسئول؛ True اگر جدید بوده است"""
    if is_fine_manager(db, league_id, telegram_id):
        return False
    db.add(LeagueFineManager(league_id=league_id, telegram_id=str(telegram_id)))
    db.commit()
    return True


def set_group_fine_manager(
    db: Session, group_id: int, telegram_id: Any, auto_enable: bool = False
) -> int:
    """
    تعیین یک شخص به عنوان مسئول جریمه برای تمامی لیگ‌های یک مجموعه (گروه).
    اگر auto_enable=True باشد، جریمه را برای لیگ‌های فاقد جریمه فعال نیز روشن می‌کند.
    خروجی: تعداد لیگ‌های منتسب‌شده.
    """
    leagues = (
        db.query(League)
        .filter(League.group_id == group_id, League.is_deleted == False)
        .all()
    )
    assigned = 0
    for lg in leagues:
        if not is_fine_manager(db, lg.id, telegram_id):
            db.add(LeagueFineManager(league_id=lg.id, telegram_id=str(telegram_id)))
            assigned += 1
        if auto_enable and not lg.fines_enabled:
            lg.fines_enabled = True
            sync_league_fines(db, lg, commit=False)
    if assigned or auto_enable:
        db.commit()
    return assigned


def remove_manager(db: Session, league_id: str, telegram_id: Any) -> bool:
    deleted = (
        db.query(LeagueFineManager)
        .filter(
            LeagueFineManager.league_id == league_id,
            LeagueFineManager.telegram_id == str(telegram_id),
        )
        .delete(synchronize_session=False)
    )
    db.commit()
    return bool(deleted)


def get_managed_leagues(db: Session, telegram_id: Any) -> List[League]:
    """لیگ‌های فعال دارای جریمه فعال که این شخص مسئول جریمه آن‌هاست"""
    return (
        db.query(League)
        .join(LeagueFineManager, LeagueFineManager.league_id == League.id)
        .filter(
            LeagueFineManager.telegram_id == str(telegram_id),
            League.fines_enabled == True,
            League.is_deleted == False,
        )
        .order_by(League.name.asc())
        .all()
    )


def get_all_manager_tg_ids(db: Session) -> set:
    """شناسه تلگرام تمام مسئولین جریمه لیگهای فعال دارای جریمه (با یک کوئری)"""
    rows = (
        db.query(LeagueFineManager.telegram_id)
        .join(League, LeagueFineManager.league_id == League.id)
        .filter(League.fines_enabled == True, League.is_deleted == False)
        .distinct()
        .all()
    )
    return {str(r[0]) for r in rows}


def is_manager_of_user_league(db: Session, telegram_id: Any, league_id: Optional[str]) -> bool:
    """آیا این شخص برای لیگ مشخص (و فعال بودن جریمه) مسئول جریمه است؟"""
    if not league_id:
        return False
    lg = db.query(League).filter(League.id == league_id).first()
    if not lg or not lg.fines_enabled or lg.is_deleted:
        return False
    return is_fine_manager(db, league_id, telegram_id)


def league_has_fines(db: Session, league_id: Optional[str]) -> bool:
    if not league_id:
        return False
    lg = db.query(League).filter(League.id == league_id).first()
    return bool(lg and lg.fines_enabled and not lg.is_deleted)


# ---------------------------------------------------------------------------
# هم‌گام‌سازی خودکار جریمه‌ها با غیبت‌ها و عدم‌اعلام‌ها
# ---------------------------------------------------------------------------

_SYNC_LOCK = threading.RLock()


def sync_league_fines(db: Session, league: League, commit: bool = True) -> int:
    """نسخه ایمن در برابر اجرای همزمان (جلوگیری از رکوردهای جریمه تکراری)"""
    with _SYNC_LOCK:
        return _sync_league_fines_impl(db, league, commit)


def _sync_league_fines_impl(db: Session, league: League, commit: bool = True) -> int:
    """
    هم‌گام‌سازی رکوردهای جریمه چله فعال لیگ با absent_days_list / late_days_list کاربران.
    - برای هر روز غیبت/عدم‌اعلام جدید (و فقط وقتی مبلغ آن نوع > 0 باشد) رکورد جدید با مبلغ فعلی ساخته می‌شود.
    - رکوردهای چله فعال که دیگر در لیست‌ها نیستند (مثلاً با ثبت دیرهنگام) حذف می‌شوند (به جز بخشوده‌شده‌ها).
    خروجی: تعداد تغییرات.
    """
    if not league or not league.fines_enabled:
        return 0

    from database import get_or_create_active_cycle  # جلوگیری از import حلقوی

    cycle = get_or_create_active_cycle(db, league)
    amounts = {
        KIND_ABSENT: int(league.fine_absent_amount or 0),
        KIND_LATE: int(league.fine_late_amount or 0),
    }

    users = (
        db.query(User)
        .filter(User.league_id == league.id, User.is_active == True)
        .all()
    )
    existing_rows = (
        db.query(FineRecord)
        .filter(FineRecord.league_id == league.id, FineRecord.cycle_id == cycle.id)
        .all()
    )
    existing: Dict[tuple, FineRecord] = {}
    for rec in existing_rows:
        existing[(rec.user_id, rec.kind, int(rec.league_day))] = rec

    desired_keys = set()
    changes = 0
    for u in users:
        absent_days = set(AbsenceService.parse_days_list(u.absent_days_list))
        late_days = set(AbsenceService.parse_days_list(u.late_days_list))
        for kind, days in ((KIND_ABSENT, absent_days), (KIND_LATE, late_days)):
            for d in days:
                key = (u.id, kind, int(d))
                desired_keys.add(key)
                if key not in existing and amounts[kind] > 0:
                    db.add(
                        FineRecord(
                            league_id=league.id,
                            user_id=u.id,
                            cycle_id=cycle.id,
                            kind=kind,
                            league_day=int(d),
                            amount=amounts[kind],
                        )
                    )
                    changes += 1

    active_user_ids = {u.id for u in users}
    for key, rec in existing.items():
        # فقط رکوردهای کاربران فعال لیگ بررسی می‌شوند؛ کاربر غیرفعال/منتقل‌شده دفتر خود را حفظ می‌کند
        if key[0] not in active_user_ids:
            continue
        if key not in desired_keys and not rec.is_waived and not rec.is_frozen:
            db.delete(rec)
            changes += 1

    if commit and changes:
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            logger.warning(f"رکورد جریمه تکراری برای لیگ {league.id} نادیده گرفته شد.")
            return 0
    elif commit:
        db.flush()
    return changes


def sync_all_enabled_leagues(db: Session) -> None:
    """هم‌گام‌سازی تمام لیگ‌های دارای جریمه فعال (جاب نیمه‌شب)"""
    leagues = (
        db.query(League)
        .filter(League.fines_enabled == True, League.is_deleted == False)
        .all()
    )
    for lg in leagues:
        try:
            sync_league_fines(db, lg)
        except Exception as exc:
            db.rollback()
            logger.warning(f"خطا در هم‌گام‌سازی جریمه لیگ {lg.id}: {exc}")


# ---------------------------------------------------------------------------
# محاسبه بدهی‌ها
# ---------------------------------------------------------------------------

def _sum_map(db: Session, league_id: str) -> Dict[str, Dict[str, int]]:
    fines = dict(
        db.query(FineRecord.user_id, func.coalesce(func.sum(FineRecord.amount), 0))
        .filter(FineRecord.league_id == league_id, FineRecord.is_waived == False)
        .group_by(FineRecord.user_id)
        .all()
    )
    paid = dict(
        db.query(FinePayment.user_id, func.coalesce(func.sum(FinePayment.amount), 0))
        .filter(FinePayment.league_id == league_id)
        .group_by(FinePayment.user_id)
        .all()
    )
    result: Dict[str, Dict[str, int]] = {}
    for uid in set(fines) | set(paid):
        result[uid] = {"fines": int(fines.get(uid, 0)), "paid": int(paid.get(uid, 0))}
    return result


def get_user_balance(db: Session, league_id: str, user_id: str) -> Dict[str, int]:
    total_fines = (
        db.query(func.coalesce(func.sum(FineRecord.amount), 0))
        .filter(
            FineRecord.league_id == league_id,
            FineRecord.user_id == user_id,
            FineRecord.is_waived == False,
        )
        .scalar()
    )
    total_paid = (
        db.query(func.coalesce(func.sum(FinePayment.amount), 0))
        .filter(FinePayment.league_id == league_id, FinePayment.user_id == user_id)
        .scalar()
    )
    fines_i = int(total_fines or 0)
    paid_i = int(total_paid or 0)
    return {"fines": fines_i, "paid": paid_i, "owed": max(0, fines_i - paid_i)}


def get_debtors(db: Session, league: League, include_inactive: bool = False) -> List[Dict[str, Any]]:
    """
    فهرست بدهکاران لیگ به ترتیب بیشترین بدهی.
    به‌صورت پیش‌فرض فقط کاربران فعال لیگ؛ با include_inactive=True کاربران حذف‌شده/منتقل‌شده
    که بدهی پرداخت‌نشده دارند هم برگردانده می‌شوند (برای مسئول جریمه).
    هر آیتم: {user, fines, paid, owed, active}
    """
    sums = _sum_map(db, league.id)
    if not sums:
        return []
    query = db.query(User).filter(User.id.in_(list(sums.keys())))
    if not include_inactive:
        query = query.filter(User.league_id == league.id, User.is_active == True)
    users = query.all()
    out: List[Dict[str, Any]] = []
    for u in users:
        s = sums.get(u.id)
        if not s:
            continue
        owed = s["fines"] - s["paid"]
        if owed > 0:
            is_active_here = bool(u.is_active and u.league_id == league.id)
            out.append(
                {
                    "user": u,
                    "fines": s["fines"],
                    "paid": s["paid"],
                    "owed": owed,
                    "active": is_active_here,
                }
            )
    out.sort(key=lambda x: (-x["owed"], x["user"].get_display_name()))
    return out


def total_owed(debtors: List[Dict[str, Any]]) -> int:
    return sum(int(d["owed"]) for d in debtors)


def record_payment(
    db: Session,
    league_id: str,
    user_id: str,
    amount: int,
    recorded_by: Any,
) -> int:
    """
    ثبت پرداخت؛ مبلغ به بدهی فعلی محدود می‌شود (پرداخت اضافه ثبت نمی‌شود).
    خروجی: مبلغ واقعاً ثبت‌شده (۰ یعنی بدهی ندارد/مبلغ نامعتبر).
    """
    if amount <= 0:
        return 0
    bal = get_user_balance(db, league_id, user_id)
    applied = min(int(amount), bal["owed"])
    if applied <= 0:
        return 0
    db.add(
        FinePayment(
            league_id=league_id,
            user_id=user_id,
            amount=applied,
            recorded_by=str(recorded_by),
        )
    )
    db.commit()
    return applied


def get_user_fine_records(db: Session, league_id: str, user_id: str) -> List[FineRecord]:
    return (
        db.query(FineRecord)
        .filter(FineRecord.league_id == league_id, FineRecord.user_id == user_id)
        .order_by(FineRecord.cycle_id.desc(), FineRecord.league_day.desc(), FineRecord.id.desc())
        .all()
    )


def toggle_waive(db: Session, record_id: int, league_id: str, by: Any) -> Optional[FineRecord]:
    """بخشودن/بازگرداندن یک جریمه؛ فقط اگر رکورد متعلق به همین لیگ باشد"""
    rec = (
        db.query(FineRecord)
        .filter(FineRecord.id == record_id, FineRecord.league_id == league_id)
        .first()
    )
    if not rec:
        return None
    rec.is_waived = not bool(rec.is_waived)
    rec.waived_by = str(by) if rec.is_waived else None
    db.commit()
    return rec


def freeze_user_fines(db: Session, user_id: Any, commit: bool = True) -> int:
    """
    فریز کردن تمام رکوردهای جریمه یک پروفایل پیش از ریست آمار (بازگشت به لیگ / انتقال)،
    تا هم‌گام‌سازی خودکار آنها را حذف نکند. خروجی: تعداد رکوردهای فریز‌شده.
    """
    n = (
        db.query(FineRecord)
        .filter(FineRecord.user_id == str(user_id), FineRecord.is_frozen == False)
        .update({FineRecord.is_frozen: True}, synchronize_session=False)
    )
    if commit and n:
        db.commit()
    return int(n or 0)


def count_active_fine_kinds(db: Session, league_id: str, user_id: str) -> Dict[str, int]:
    """تعداد غیبت/عدم‌اعلام بخشوده‌نشده (کل دفتر) برای نمایش در جزئیات"""
    rows = (
        db.query(FineRecord.kind, func.count(FineRecord.id))
        .filter(
            FineRecord.league_id == league_id,
            FineRecord.user_id == user_id,
            FineRecord.is_waived == False,
        )
        .group_by(FineRecord.kind)
        .all()
    )
    return {k: int(c) for k, c in rows}
