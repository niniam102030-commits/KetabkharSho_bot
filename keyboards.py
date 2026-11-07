from typing import Iterable, List, Optional, Set, Tuple
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from models import League, User


def get_start_menu() -> ReplyKeyboardMarkup:
    """۱. منوی شروع ثبت‌نام"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 شروع ثبت نام")],
        ],
        resize_keyboard=True,
    )


def get_main_menu(
    is_admin: bool = False,
    has_multiple_profiles: bool = False,
    can_log_late: bool = False,
) -> ReplyKeyboardMarkup:
    """۲. منوی اصلی کاربران (پویا بر اساس وضعیت ثبت با تاخیر، چندپروفایلی و دسترسی ادمین)"""
    rows: List[List[KeyboardButton]] = [
        [
            KeyboardButton(text="📝 ثبت مطالعه امروز"),
            KeyboardButton(text="🏆 جدول لیگ"),
        ]
    ]

    if can_log_late:
        rows.append([KeyboardButton(text="⏳ ثبت مطالعه دیروز (با کسر ۵۰٪ امتیاز)")])

    rows.append([KeyboardButton(text="👤 حساب کاربری و سهمیه ها")])
    rows.append([KeyboardButton(text="راهنما")])

    bottom_row: List[KeyboardButton] = []
    if has_multiple_profiles:
        bottom_row.append(KeyboardButton(text="🔄 تغییر لیگ فعال"))
    if is_admin:
        bottom_row.append(KeyboardButton(text="⚙️ منوی مدیریت ادمین"))

    if bottom_row:
        rows.append(bottom_row)

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def get_study_edit_menu(can_log_late: bool = False) -> ReplyKeyboardMarkup:
    """۳. منوی ویرایش مطالعه امروز (به همراه گزینه ثبت مطالعه دیروز در صورت واجد شرایط بودن)"""
    rows: List[List[KeyboardButton]] = [
        [KeyboardButton(text="🔄 ویرایش مطالعه امروز")],
        [KeyboardButton(text="➕ افزودن زمان به ثبت امروز")],
    ]
    if can_log_late:
        rows.append([KeyboardButton(text="⏳ ثبت مطالعه دیروز (با کسر ۵۰٪ امتیاز)")])
    rows.append([KeyboardButton(text="🔙 بازگشت")])
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
    )


def get_league_selection(
    leagues: Iterable[League],
    exclude_league_ids: Optional[Set[str]] = None,
) -> InlineKeyboardMarkup:
    """۴. دکمه‌های شیشه‌ای انتخاب لیگ هنگام ثبت‌نام یا جابجایی (با حذف لیگ‌های عضو فعلی)"""
    excluded = exclude_league_ids or set()
    inline_keyboard: List[List[InlineKeyboardButton]] = []
    for l in leagues:
        if l.id in excluded:
            continue
        inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{l.name} (کف: {l.floor} دقیقه)",
                    callback_data=f"join_{l.id}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def get_cancel_league_confirm() -> InlineKeyboardMarkup:
    """۵. تایید انصراف از لیگ"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ بله، انصراف می‌دهم",
                    callback_data="confirm_cancel_league",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ منصرف شدم",
                    callback_data="fsm_cancel",
                )
            ]
        ]
    )


def get_profile_switch_keyboard(
    profiles_with_league_names: List[Tuple[User, str]],
    active_user_id: str,
) -> InlineKeyboardMarkup:
    """کیبورد شیشه‌ای تغییر لیگ/پروفایل فعال به همراه دکمه عضویت در مجموعه جدید"""
    rows: List[List[InlineKeyboardButton]] = []
    for u, league_name in profiles_with_league_names:
        prefix = "✅ " if u.id == active_user_id else ""
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{prefix}لیگ: {league_name}",
                    callback_data=f"switchprof_{u.id}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="➕ عضویت در مجموعه یا لیگ جدید (با رمز مجموعه)",
                callback_data="join_new_group_prompt",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_main_inline_menu() -> InlineKeyboardMarkup:
    """کیبورد شیشه‌ای ۶ دکمه‌ای منوی مدیریت ادمین (بند ۷.۱)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 مشاهده جداول لیگ‌ها",
                    callback_data="adm_viewleagues_select",
                ),
                InlineKeyboardButton(
                    text="🔍 جستجوی کاربر",
                    callback_data="adm_menu_search_user",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👥 مدیریت کاربران",
                    callback_data="adm_menu_users",
                ),
                InlineKeyboardButton(
                    text="📋 مدیریت لیگ‌ها",
                    callback_data="adm_menu_leagues",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="➕ ایجاد لیگ جدید",
                    callback_data="adm_menu_newleague",
                ),
                InlineKeyboardButton(
                    text="📊 آمار کلی ربات",
                    callback_data="adm_menu_stats",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📢 ارسال پیام همگانی",
                    callback_data="adm_menu_broadcast",
                ),
                InlineKeyboardButton(
                    text="📥 دریافت خروجی اکسل",
                    callback_data="adm_menu_excel",
                ),
            ],
        ]
    )


# ---------------------------------------------------------------------------
# کیبوردها و ثابتهای لغو / بازگشت مرحله (FSM)
# ---------------------------------------------------------------------------
CANCEL_TEXT = "❌ لغو عملیات"
BACK_STEP_TEXT = "🔙 مرحله قبل"
CANCEL_TEXTS = {CANCEL_TEXT, "لغو", "/cancel"}


def get_cancel_or_back_keyboard(show_back: bool = True) -> ReplyKeyboardMarkup:
    """کیبورد معمولی مراحل دریافت ورودی: لغو عملیات و (در صورت نیاز) مرحله قبل"""
    row: List[KeyboardButton] = []
    if show_back:
        row.append(KeyboardButton(text=BACK_STEP_TEXT))
    row.append(KeyboardButton(text=CANCEL_TEXT))
    return ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)


def get_inline_cancel_keyboard(show_back: bool = False) -> InlineKeyboardMarkup:
    """کیبورد شیشه‌ای مراحل دریافت ورودی در پنل ادمین"""
    row: List[InlineKeyboardButton] = []
    if show_back:
        row.append(
            InlineKeyboardButton(text=BACK_STEP_TEXT, callback_data="fsm_back")
        )
    row.append(InlineKeyboardButton(text=CANCEL_TEXT, callback_data="fsm_cancel"))
    return InlineKeyboardMarkup(inline_keyboard=[row])