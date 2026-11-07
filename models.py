import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Index,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def generate_league_id() -> str:
    """تولید شناسه ۸ کاراکتری یکتا برای لیگ‌ها"""
    return str(uuid.uuid4())[:8]


class Group(Base):
    """مدل مجموعه‌ها (مدارس، مساجد، باشگاه‌ها)"""

    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    password = Column(String(8), nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class GroupAdmin(Base):
    """مدل مدیران اختصاصی هر مجموعه"""

    __tablename__ = "group_admins"
    __table_args__ = (
        Index("ix_group_admins_group_user", "group_id", "user_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(
        Integer, ForeignKey("groups.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class User(Base):
    """
    مدل کاربران (پشتیبانی از معماری چندپروفایلی Multi-Profile).
    برای اولین پروفایل: id == telegram_id
    برای پروفایل‌های بعدی: id == f"{telegram_id}_g{group_id}" یا f"{telegram_id}_{league_id}"
    """

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_league_active", "league_id", "is_active"),
        Index("ix_users_tg_active", "telegram_id", "is_active"),
        Index("ix_users_group_active", "group_id", "is_active"),
    )

    id = Column(String(100), primary_key=True, index=True)
    telegram_id = Column(String(100), index=True, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), index=True, nullable=True)
    name = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    league_id = Column(String(50), nullable=True, index=True)

    points = Column(Float, default=0.0, nullable=False)
    total_minutes = Column(Integer, default=0, nullable=False)
    total_pages = Column(Integer, default=0, nullable=False)
    streak = Column(Integer, default=0, nullable=False)
    no_study_days = Column(Integer, default=0, nullable=False)
    absent_days_list = Column(String(500), default="", nullable=False)
    late_days_list = Column(String(500), default="", nullable=False)

    half_coupons = Column(Integer, default=5, nullable=False)
    one_min_coupons = Column(Integer, default=1, nullable=False)
    user_floor = Column(Integer, nullable=True)

    last_log_date = Column(String(10), nullable=True)
    today_minutes = Column(Integer, default=0, nullable=False)
    today_pages = Column(Integer, default=0, nullable=False)
    today_points = Column(Float, default=0.0, nullable=False)
    today_half_used = Column(Integer, default=0, nullable=False)
    today_one_min_used = Column(Integer, default=0, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    reminder_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def get_effective_floor(self, league_floor: int) -> int:
        """برگرداندن میثاق اختصاصی کاربر در صورت وجود، در غیر این صورت کف لیگ"""
        if self.user_floor is not None and self.user_floor > 0:
            return int(self.user_floor)
        return int(league_floor) if league_floor and league_floor > 0 else 10

    def get_display_name(self) -> str:
        """
        نام نمایشی در جدول لیگ:
        اگر first_name و last_name دارد: "{first_name[0]}. {last_name}"
        اگر فقط last_name دارد: "{last_name}"
        در غیر این صورت: "{name}"
        """
        fn = (self.first_name or "").strip()
        ln = (self.last_name or "").strip()
        if fn and ln:
            return f"{fn[0]}. {ln}"
        if ln:
            return ln
        return (self.name or "کاربر").strip()


class League(Base):
    """مدل لیگ‌های کتابخوانی هر مجموعه"""

    __tablename__ = "leagues"
    __table_args__ = (
        Index("ix_leagues_group_flags", "group_id", "is_deleted", "is_active"),
    )

    id = Column(String(50), primary_key=True, default=generate_league_id)
    telegram_id = Column(String(100), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), index=True, nullable=True)
    name = Column(String(255), nullable=False)
    floor = Column(Integer, default=10, nullable=False)
    start_shamsi = Column(String(10), nullable=True)
    current_day = Column(Integer, default=1, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    is_finished = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    archive_enabled = Column(Boolean, default=True, nullable=False)
    cycle_number = Column(Integer, default=1, nullable=False)

    # سیستم جریمه اختصاصی هر لیگ (مبالغ به تومان)
    fines_enabled = Column(Boolean, default=False, nullable=False)
    fine_absent_amount = Column(Integer, default=0, nullable=False)
    fine_late_amount = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class LeagueFineManager(Base):
    """مسئولین جریمه هر لیگ (چند نفر مجاز است؛ بر اساس telegram_id شخص)"""

    __tablename__ = "league_fine_managers"
    __table_args__ = (
        Index("ix_lfm_league_tg", "league_id", "telegram_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    league_id = Column(
        String(50), ForeignKey("leagues.id", ondelete="CASCADE"), index=True, nullable=False
    )
    telegram_id = Column(String(100), index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class FineRecord(Base):
    """دفتر جریمه‌ها: یک رکورد برای هر غیبت یا عدم‌اعلام (مبلغ در لحظه ثبت ثابت می‌ماند)"""

    __tablename__ = "fine_records"
    __table_args__ = (
        Index("ix_fine_league_user", "league_id", "user_id"),
        Index("ix_fine_user_cycle_kind", "user_id", "cycle_id", "kind", "league_day"),
        Index(
            "ux_fine_record_key",
            "league_id",
            "user_id",
            "cycle_id",
            "kind",
            "league_day",
            unique=True,
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    league_id = Column(
        String(50), ForeignKey("leagues.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id = Column(String(100), nullable=False, index=True)
    cycle_id = Column(Integer, nullable=True, index=True)
    kind = Column(String(10), nullable=False)  # absent | late
    league_day = Column(Integer, nullable=False)
    amount = Column(Integer, default=0, nullable=False)
    is_waived = Column(Boolean, default=False, nullable=False)
    is_frozen = Column(Boolean, default=False, nullable=False)
    waived_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class FinePayment(Base):
    """پرداخت‌های جریمه (کامل یا جزئی) که توسط مسئول جریمه ثبت می‌شود"""

    __tablename__ = "fine_payments"
    __table_args__ = (
        Index("ix_finepay_league_user", "league_id", "user_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    league_id = Column(
        String(50), ForeignKey("leagues.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id = Column(String(100), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    recorded_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Cycle(Base):
    """مدل چله‌های ۴۰ روزه هر لیگ"""

    __tablename__ = "cycles"
    __table_args__ = (
        Index("ix_cycles_league_status", "league_id", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    league_id = Column(
        String(50), ForeignKey("leagues.id", ondelete="CASCADE"), index=True, nullable=False
    )
    cycle_number = Column(Integer, nullable=False, default=1)
    start_shamsi = Column(String(10), nullable=False)
    end_shamsi = Column(String(10), nullable=True)
    current_day = Column(Integer, default=1, nullable=False)
    status = Column(String(20), default="active", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime, nullable=True)


class ActivityLog(Base):
    """مدل لاگ‌های ثبت مطالعه روزانه کاربران"""

    __tablename__ = "activity_logs"
    __table_args__ = (
        Index("ix_actlog_user_league_date", "user_id", "league_id", "log_date"),
        Index("ix_actlog_league_cycle_day", "league_id", "cycle_id", "league_day"),
        Index("ix_actlog_league_date", "league_id", "log_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        String(100), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    league_id = Column(String(50), index=True, nullable=True)
    cycle_id = Column(
        Integer, ForeignKey("cycles.id", ondelete="SET NULL"), index=True, nullable=True
    )
    cycle_number = Column(Integer, index=True, nullable=True)
    league_day = Column(Integer, nullable=True)

    minutes = Column(Integer, nullable=False)
    pages = Column(Integer, default=0, nullable=False)
    points_earned = Column(Float, default=0.0, nullable=False)
    half_coupon_used = Column(Integer, default=0, nullable=False)
    one_min_coupon_used = Column(Integer, default=0, nullable=False)

    log_date = Column(String(10), nullable=False, index=True)
    log_hour = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CycleResult(Base):
    """مدل ذخیره کارنامه نهایی هر کاربر در پایان هر چله ۴۰ روزه"""

    __tablename__ = "cycle_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cycle_id = Column(
        Integer, ForeignKey("cycles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id = Column(String(100), index=True, nullable=False)
    user_name = Column(String(255), nullable=False)
    final_rank = Column(Integer, nullable=False)
    points = Column(Float, default=0.0, nullable=False)
    total_minutes = Column(Integer, default=0, nullable=False)
    total_pages = Column(Integer, default=0, nullable=False)
    streak = Column(Integer, default=0, nullable=False)
    no_study_days = Column(Integer, default=0, nullable=False)
    absent_days_list = Column(String(500), default="", nullable=False)
    late_days_list = Column(String(500), default="", nullable=False)
    half_coupons_used = Column(Integer, default=0, nullable=False)
    one_min_coupons_used = Column(Integer, default=0, nullable=False)
    half_coupons_remaining = Column(Integer, default=0, nullable=False)
    one_min_coupons_remaining = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SystemState(Base):
    """مدل نگهداری وضعیت‌های سیستمی و پروفایل فعال هر کاربر"""

    __tablename__ = "system_state"

    key = Column(String(100), primary_key=True)
    value = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class GroupMessage(Base):
    """مدل پیام‌های سفارشی هر مجموعه"""

    __tablename__ = "group_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(
        Integer, ForeignKey("groups.id", ondelete="CASCADE"), index=True, nullable=False
    )
    msg_key = Column(String(50), nullable=False, index=True)
    custom_text = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class GroupTerm(Base):
    """مدل اصطلاحات سفارشی واژه‌نامه هر مجموعه"""

    __tablename__ = "group_terms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(
        Integer, ForeignKey("groups.id", ondelete="CASCADE"), index=True, nullable=False
    )
    term_key = Column(String(50), nullable=False, index=True)
    custom_term = Column(String(100), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))