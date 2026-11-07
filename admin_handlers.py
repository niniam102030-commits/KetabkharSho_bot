import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
)
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import settings
from database import (
    get_db,
    get_admin_group_ids,
    is_user_admin,
    is_group_password_unique,
    get_or_create_active_cycle,
    generate_new_profile_id,
    set_active_user_id,
    set_system_state,
    get_active_user,
)
from models import (
    Group,
    GroupAdmin,
    User,
    League,
    Cycle,
    ActivityLog,
    CycleResult,
)
from services import (
    DateService,
    ScoringService,
    ReportService,
    AbsenceService,
    escape_md,
)
from message_service import (
    MessageService,
    DEFAULT_TERMS,
    TERM_LABELS,
    DEFAULT_MESSAGES,
    MESSAGE_LABELS,
)
from keyboards import (
    get_admin_main_inline_menu,
    get_inline_cancel_keyboard,
    CANCEL_TEXTS,
)

logger = logging.getLogger(__name__)

admin_router = Router(name="admin_router")


class AdminStates(StatesGroup):
    """استیت‌های ماشین وضعیت پنل مدیریت (سوپرادمین و ادمین مجموعه)"""

    # مدیریت مجموعه‌ها
    cg_waiting_name = State()
    cg_waiting_password = State()
    pg_waiting_password = State()
    ng_waiting_name = State()

    # ایجاد و ویرایش لیگ
    al_waiting_name = State()
    al_waiting_floor = State()
    leagedit_waiting_floor = State()
    leagedit_waiting_cycle = State()
    leagedit_waiting_date = State()

    # ویرایش کاربر
    usr_waiting_name = State()
    usr_waiting_points = State()
    usr_waiting_streak = State()
    usr_waiting_minutes = State()
    usr_waiting_pages = State()
    usr_waiting_no_study = State()
    usr_waiting_late = State()
    usr_waiting_floor = State()

    # ویرایش واژه‌نامه و پیام‌های مجموعه (em)
    em_waiting_term_value = State()
    em_waiting_msg_value = State()


# ===========================================================================
# توابع کمکی ارسال ایمن پیام و ساخت پنل‌های مدیریتی
# ===========================================================================
async def safe_send_message(
    bot: Bot,
    chat_id: int | str,
    text: str,
    reply_markup=None,
    parse_mode: Optional[str] = "Markdown",
) -> Optional[Message]:
    """ارسال ایمن پیام با مدیریت FloodWait و قابلیت Fallback بدون parse_mode در صورت خطای فرمت"""
    try:
        return await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    except TelegramRetryAfter as exc:
        await asyncio.sleep(min(exc.retry_after, 30))
        try:
            return await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
        except Exception as retry_exc:
            logger.warning(f"خطا پس از انتظار FloodWait در ارسال به {chat_id}: {retry_exc}")
            return None
    except TelegramBadRequest:
        try:
            return await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=None,
            )
        except Exception as exc:
            logger.warning(f"خطا در ارسال پیام بدون فرمت به {chat_id}: {exc}")
            return None
    except Exception:
        try:
            return await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=None,
            )
        except Exception as exc:
            logger.warning(f"خطا در ارسال پیام به {chat_id}: {exc}")
            return None


async def safe_reply(
    message: Message,
    text: str,
    reply_markup=None,
    parse_mode: Optional[str] = "Markdown",
) -> Optional[Message]:
    """پاسخ ایمن به پیام کاربر/ادمین با مدیریت FloodWait و خطای Markdown"""
    try:
        return await message.answer(
            text=text, reply_markup=reply_markup, parse_mode=parse_mode
        )
    except TelegramRetryAfter as exc:
        await asyncio.sleep(min(exc.retry_after, 30))
        try:
            return await message.answer(
                text=text, reply_markup=reply_markup, parse_mode=parse_mode
            )
        except Exception as retry_exc:
            logger.warning(f"خطا پس از انتظار FloodWait در پاسخ به پیام: {retry_exc}")
            return None
    except TelegramBadRequest:
        try:
            return await message.answer(
                text=text, reply_markup=reply_markup, parse_mode=None
            )
        except Exception as exc:
            logger.warning(f"خطا در پاسخ بدون فرمت به پیام: {exc}")
            return None
    except Exception:
        try:
            return await message.answer(
                text=text, reply_markup=reply_markup, parse_mode=None
            )
        except Exception as exc:
            logger.warning(f"خطا در پاسخ به پیام: {exc}")
            return None


def _build_admin_help_text(is_super: bool) -> str:
    """ساخت متن راهنمای دستورات متنی ادمین بر اساس سطح دسترسی"""
    lines = ["⚙️ *پنل مدیریت کتابخوارشو*\n"]
    if is_super:
        lines.extend(
            [
                "👑 *دستورات ویژه مدیر ارشد (بدون اسلش):*",
                "🔹 `cg` : ایجاد مجموعه جدید",
                "🔹 `vg` : مشاهده مجموعه‌ها و رمزها",
                "🔹 `pg` : تغییر رمز ورود مجموعه",
                "🔹 `ng` : تغییر نام مجموعه",
                "🔹 `ag` یا `aa` : افزودن ادمین به مجموعه",
                "🔹 `rg` : حذف ادمین از مجموعه",
                "🔹 `gs` : مشاهده آمار کلان کل سیستم\n",
            ]
        )
    else:
        lines.extend(
            [
                "🔑 *دستورات مجموعه شما (بدون اسلش):*",
                "🔹 `vg` : مشاهده مجموعه‌ها و رمز ورود",
                "🔹 `pg` : تغییر رمز ورود مجموعه",
                "🔹 `ng` : تغییر نام مجموعه\n",
            ]
        )

    lines.extend(
        [
            "📋 *دستورات مدیریت لیگ‌ها و کاربران (بدون اسلش):*",
            "🔸 `al` : افزودن لیگ جدید",
            "🔸 `el` یا `dl` : ویرایش و حذف لیگ‌ها",
            "🔸 `us` یا `eu` : مدیریت کاربران و پروفایل‌ها",
            "🔸 `st` : آمار کلی مجموعه",
            "🔸 `ex` : دریافت خروجی اکسل لیگ‌های فعال",
            "🔸 `sr` : دریافت اکسل آرشیو تاریخچه چله‌ها",
            "🔸 `em` : مدیریت لحن، واژه‌نامه و پیام‌های مجموعه\n",
            "🧪 برای مشاهده دستورات تست سیستمی، `/test_help` را ارسال کنید.",
        ]
    )
    return "\n".join(lines)


def _get_league_edit_keyboard(league_id: str) -> InlineKeyboardMarkup:
    """کیبورد شیشه‌ای تنظیمات و حذف لیگ (بند ۷.۳ - el و dl)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏱ ویرایش زمان میثاق",
                    callback_data=f"leagedit_floor_{league_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏆 شماره چله",
                    callback_data=f"leagedit_cycle_{league_id}",
                ),
                InlineKeyboardButton(
                    text="📅 تاریخ شروع",
                    callback_data=f"leagedit_date_{league_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗑 حذف لیگ",
                    callback_data=f"adm_deleteleague_{league_id}",
                )
            ],
        ]
    )


def _get_user_past_days(db: Session, u: User) -> set[int]:
    """روزهای گذشتهٔ چلهٔ فعال کاربر (۱ تا دیروز؛ در بامداد روز ۴۱ شامل روز ۴۰ هم میشود)"""
    if not u.league_id:
        return set()
    lg = db.query(League).filter(League.id == u.league_id).first()
    if not lg:
        return set()
    cyc = get_or_create_active_cycle(db, lg)
    raw_day = DateService.calculate_raw_league_day(cyc.start_shamsi or lg.start_shamsi)
    return set(range(1, min(settings.LEAGUE_DURATION, raw_day - 1) + 1))


def _get_user_manage_keyboard(user_id: str) -> InlineKeyboardMarkup:
    """کیبورد شیشه‌ای ۷ ردیفه مدیریت کاربر (بند ۷.۳ - us و eu)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ تغییر نام", callback_data=f"adm_editname_{user_id}"
                ),
                InlineKeyboardButton(
                    text="🔄 تغییر لیگ", callback_data=f"adm_moveleague_{user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="➕ افزودن کاربر به لیگ دیگر",
                    callback_data=f"adm_addleague_{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⭐️ امتیاز", callback_data=f"adm_edit_points_{user_id}"
                ),
                InlineKeyboardButton(
                    text="🔥 زنجیره", callback_data=f"adm_edit_streak_{user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⏱ زمان کل", callback_data=f"adm_edit_minutes_{user_id}"
                ),
                InlineKeyboardButton(
                    text="📄 صفحات کل", callback_data=f"adm_edit_pages_{user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ تعداد غیبت", callback_data=f"adm_edit_no_study_{user_id}"
                ),
                InlineKeyboardButton(
                    text="⚠️ عدم اعلام", callback_data=f"adm_edit_late_{user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⏱ میثاق اختصاصی", callback_data=f"adm_userfloor_{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 حذف کاربر", callback_data=f"adm_delete_{user_id}"
                )
            ],
        ]
    )


def _format_user_admin_card(db: Session, user: User) -> str:
    """ساخت متن اطلاعات کامل کاربر برای پنل مدیریت ادمین"""
    league = (
        db.query(League).filter(League.id == user.league_id).first()
        if user.league_id
        else None
    )
    group = (
        db.query(Group).filter(Group.id == user.group_id).first()
        if user.group_id
        else None
    )
    league_name = escape_md(league.name) if league else "بدون لیگ"
    group_name = escape_md(group.name) if group else "نامشخص"
    league_floor = league.floor if league else settings.DEFAULT_FLOOR
    eff_floor = user.get_effective_floor(league_floor)
    custom_floor_txt = f"{user.user_floor} دقیقه" if user.user_floor else f"پیش‌فرض لیگ ({league_floor} دقیقه)"
    absent_txt = user.absent_days_list if user.absent_days_list else "-"
    late_txt = user.late_days_list if user.late_days_list else "-"
    late_count = len(AbsenceService.parse_days_list(user.late_days_list))

    return (
        f"👤 *مدیریت کاربر:* {escape_md(user.name)}\n"
        f"🆔 کد پروفایل: `{user.id}` | آیدی: `{user.telegram_id}`\n"
        f"🏢 مجموعه: *{group_name}*\n"
        f"🏆 لیگ: *{league_name}*\n"
        f"───────────────────\n"
        f"⭐️ امتیاز کل: *{round(float(user.points or 0.0), 1)}*\n"
        f"⏱ زمان کل: *{user.total_minutes}* دقیقه\n"
        f"📄 صفحات کل: *{user.total_pages}* صفحه\n"
        f"🔥 زنجیره استمرار: *{user.streak}* روز\n"
        f"❌ تعداد غیبت: *{user.no_study_days}* روز (روزها: `{absent_txt}`)\n"
        f"⚠️ عدم اعلام به موقع (تاخیر): *{late_count}* بار (روزها: `{late_txt}`)\n"
        f"⏱ میثاق موثر: *{eff_floor}* دقیقه ({custom_floor_txt})\n"
        f"🎫 سهمیه‌های مانده: نصف میثاق *{user.half_coupons}* | طلایی *{user.one_min_coupons}*"
    )


def _get_em_main_keyboard(group_id: int) -> InlineKeyboardMarkup:
    """کیبورد شیشه‌ای ۳ دکمه‌ای مدیریت لحن و پیام‌های مجموعه (em)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚙️ تنظیم اصطلاحات اختصاصی (کف، چله، سهمیه...)",
                    callback_data=f"em_terms_{group_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 ویرایش پیام‌های ارسالی به اعضا",
                    callback_data=f"em_msgs_{group_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ خروج از تنظیمات",
                    callback_data="adm_cancel",
                )
            ],
        ]
    )


def _get_em_terms_keyboard(db: Session, group_id: int) -> InlineKeyboardMarkup:
    """کیبورد ویرایش و بازنشانی ۵ اصطلاح مجموعه"""
    current_terms = MessageService.get_terms(db, group_id)
    rows: List[List[InlineKeyboardButton]] = []
    for t_key, t_label in TERM_LABELS.items():
        val = current_terms.get(t_key, DEFAULT_TERMS[t_key])
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"✏️ {t_label}: «{val}»",
                    callback_data=f"em_edterm_{group_id}_{t_key}",
                ),
                InlineKeyboardButton(
                    text="🔄 پیش‌فرض",
                    callback_data=f"em_rstterm_{group_id}_{t_key}",
                ),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="🔙 بازگشت", callback_data=f"em_grp_{group_id}"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _get_em_msgs_keyboard(group_id: int) -> InlineKeyboardMarkup:
    """کیبورد ویرایش و بازنشانی ۷ پیام مجموعه"""
    rows: List[List[InlineKeyboardButton]] = []
    for m_key, m_label in MESSAGE_LABELS.items():
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"✏️ {m_label}",
                    callback_data=f"em_edmsg_{group_id}_{m_key}",
                ),
                InlineKeyboardButton(
                    text="🔄 پیش‌فرض",
                    callback_data=f"em_rstmsg_{group_id}_{m_key}",
                ),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="🔙 بازگشت", callback_data=f"em_grp_{group_id}"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ===========================================================================
# هندلر عمومی لغو (Global FSM Cancel) و بازگشت به مرحله قبل
# توجه: این هندلرها باید قبل از هندلرهای استیتدار ثبت شوند و admin_router در main.py اول include میشود.
# ===========================================================================
async def _cancel_flow(
    bot: Bot, chat_id: int | str, tg_id: str, state: FSMContext, was_admin_flow: bool
) -> None:
    """پاکسازی ایمن FSM و بازگشت به منوی مناسب (بدون باقی ماندن داده نیمه‌کاره)"""
    from database import get_active_user
    from handlers import build_user_main_menu
    from keyboards import get_start_menu

    await state.clear()
    with get_db() as db:
        user = get_active_user(db, tg_id)
        has_profile = bool(user and user.is_active)
        is_adm = is_user_admin(db, tg_id)
        if has_profile:
            kb = build_user_main_menu(db, tg_id, user)
        elif is_adm:
            kb = build_user_main_menu(db, tg_id, None)
        else:
            kb = get_start_menu()

    await safe_send_message(
        bot,
        chat_id,
        "✅ عملیات لغو شد و اطلاعات نیمه‌کاره پاک گردید.\n🏠 بازگشت به منوی اصلی.",
        reply_markup=kb,
        parse_mode=None,
    )
    if was_admin_flow and is_adm:
        await safe_send_message(
            bot,
            chat_id,
            _build_admin_help_text(settings.is_super_admin(tg_id)),
            reply_markup=get_admin_main_inline_menu(),
        )


@admin_router.message(F.text.func(lambda t: bool(t) and t.strip() in CANCEL_TEXTS))
@admin_router.message(Command("cancel"))
async def global_cancel_message(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    was_admin = bool(current and current.startswith("AdminStates:"))
    await _cancel_flow(
        message.bot, message.chat.id, str(message.from_user.id), state, was_admin
    )


@admin_router.callback_query(F.data == "fsm_cancel")
async def global_cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    current = await state.get_state()
    was_admin = bool(current and current.startswith("AdminStates:"))
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await _cancel_flow(
        callback.bot,
        callback.message.chat.id,
        str(callback.from_user.id),
        state,
        was_admin,
    )
    await callback.answer("لغو شد.")


@admin_router.callback_query(F.data == "fsm_back")
async def global_back_callback(callback: CallbackQuery, state: FSMContext) -> None:
    current = await state.get_state()
    chat_id = callback.message.chat.id
    if current == AdminStates.cg_waiting_password.state:
        await state.set_state(AdminStates.cg_waiting_name)
        await safe_send_message(
            callback.bot,
            chat_id,
            "🏢 لطفاً *نام مجموعه جدید* را وارد کنید:",
            reply_markup=get_inline_cancel_keyboard(),
        )
    elif current == AdminStates.al_waiting_floor.state:
        await state.set_state(AdminStates.al_waiting_name)
        await safe_send_message(
            callback.bot,
            chat_id,
            "➕ لطفاً *نام لیگ جدید* را وارد کنید:",
            reply_markup=get_inline_cancel_keyboard(),
        )
    else:
        await callback.answer(
            "مرحله قبلی وجود ندارد؛ از «❌ لغو عملیات» استفاده کنید.", show_alert=True
        )
        return
    await callback.answer()


# ===========================================================================
# ۷.۱. منوی مدیریت ادمین
# ===========================================================================
@admin_router.message(F.text == "⚙️ منوی مدیریت ادمین")
@admin_router.message(Command("admin"))
async def show_admin_panel(message: Message, state: FSMContext) -> None:
    user_id = str(message.from_user.id)
    with get_db() as db:
        if not is_user_admin(db, user_id):
            await safe_reply(message, "⛔️ شما دسترسی به پنل مدیریت ندارید.")
            return
        is_super = settings.is_super_admin(user_id)

    await state.clear()
    text = _build_admin_help_text(is_super)
    await safe_reply(message, text, reply_markup=get_admin_main_inline_menu())


@admin_router.callback_query(F.data == "adm_cancel")
async def cb_admin_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    try:
        await callback.message.edit_text("✅ عملیات مدیریت بسته شد.")
    except Exception:
        await safe_send_message(callback.bot, callback.message.chat.id, "✅ عملیات مدیریت بسته شد.")
    await callback.answer()


# ===========================================================================
# ۷.۲. دستورات متنی مدیر ارشد و مدیران مجموعه (cg, vg, pg, ng, ag, aa, rg, gs)
# ===========================================================================

# --- دستور cg (ایجاد مجموعه جدید - ویژه سوپرادمین) ---
@admin_router.message(StateFilter(None), F.text.func(lambda t: t and t.strip().lower() == "cg"))
async def cmd_create_group(message: Message, state: FSMContext) -> None:
    user_id = str(message.from_user.id)
    if not settings.is_super_admin(user_id):
        await safe_reply(message, "⛔️ این دستور فقط مخصوص مدیر ارشد است.")
        return

    await state.clear()
    await state.set_state(AdminStates.cg_waiting_name)
    await safe_reply(
        message,
        "🏢 لطفاً *نام مجموعه جدید* را وارد کنید:",
        reply_markup=get_inline_cancel_keyboard(),
    )


@admin_router.message(AdminStates.cg_waiting_name)
async def process_cg_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await safe_reply(message, "❌ نام مجموعه باید حداقل ۲ کاراکتر باشد. مجدداً وارد کنید:")
        return

    await state.update_data(cg_name=name)
    await state.set_state(AdminStates.cg_waiting_password)
    await safe_reply(
        message,
        f"🔑 نام مجموعه: *{escape_md(name)}*\n\n"
        "حالا *رمز ورود مجموعه* (یک عدد ۶ تا ۸ رقمی یکتا) را وارد کنید:",
        reply_markup=get_inline_cancel_keyboard(show_back=True),
    )


@admin_router.message(AdminStates.cg_waiting_password)
async def process_cg_password(message: Message, state: FSMContext) -> None:
    pwd = DateService.normalize_digits(message.text or "")
    if not (pwd.isdigit() and 6 <= len(pwd) <= 8):
        await safe_reply(
            message,
            "❌ رمز ورود باید فقط شامل اعداد و بین ۶ تا ۸ رقم باشد. لطفاً مجدداً وارد کنید:",
        )
        return

    with get_db() as db:
        if not is_group_password_unique(db, pwd):
            await safe_reply(
                message,
                "❌ این رمز از قبل برای مجموعه دیگری استفاده شده است. لطفاً رمز متفاوت دیگری وارد کنید:",
            )
            return

        data = await state.get_data()
        group_name = data.get("cg_name", "مجموعه جدید")
        new_group = Group(name=group_name, password=pwd, is_deleted=False)
        db.add(new_group)
        db.commit()
        db.refresh(new_group)
        g_id = new_group.id

    await state.clear()
    await safe_reply(
        message,
        f"✅ *مجموعه جدید با موفقیت ساخته شد!*\n\n"
        f"🆔 آیدی مجموعه: `{g_id}`\n"
        f"🏷 نام مجموعه: *{escape_md(group_name)}*\n"
        f"🔑 رمز ورود: `{pwd}`",
    )


# --- دستور vg (مشاهده مجموعه‌ها و رمزها) ---
@admin_router.message(StateFilter(None), F.text.func(lambda t: t and t.strip().lower() == "vg"))
async def cmd_view_groups(message: Message, state: FSMContext) -> None:
    user_id = str(message.from_user.id)
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
        group_ids = get_admin_group_ids(db, user_id)
        groups = (
            db.query(Group)
            .filter(Group.id.in_(group_ids), Group.is_deleted == False)
            .order_by(Group.id.asc())
            .all()
        )
        if not groups:
            await safe_reply(message, "📭 هیچ مجموعه‌ای یافت نشد.")
            return

        lines = ["🏢 *لیست مجموعه‌ها و رمزهای ورود:*\n"]
        for g in groups:
            lines.append(f"🆔 ID: {g.id} | 🏷 {escape_md(g.name)} | 🔑 رمز: `{g.password}`")

    await state.clear()
    await safe_reply(message, "\n".join(lines))


# --- دستور pg (تغییر رمز ورود مجموعه) ---
@admin_router.message(StateFilter(None), F.text.func(lambda t: t and t.strip().lower() == "pg"))
async def cmd_change_group_password(message: Message, state: FSMContext) -> None:
    user_id = str(message.from_user.id)
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
        group_ids = get_admin_group_ids(db, user_id)
        groups = (
            db.query(Group)
            .filter(Group.id.in_(group_ids), Group.is_deleted == False)
            .order_by(Group.id.asc())
            .all()
        )
        if not groups:
            await safe_reply(message, "📭 هیچ مجموعه‌ای تحت مدیریت شما یافت نشد.")
            return

        await state.clear()
        if len(groups) == 1 and not settings.is_super_admin(user_id):
            g = groups[0]
            await state.update_data(pg_group_id=g.id)
            await state.set_state(AdminStates.pg_waiting_password)
            await safe_reply(
                message,
                f"🔑 تغییر رمز مجموعه *{escape_md(g.name)}* (رمز فعلی: `{g.password}`)\n\n"
                "لطفاً رمز جدید (عدد ۶ تا ۸ رقمی) را وارد کنید:",
                reply_markup=get_inline_cancel_keyboard(),
            )
            return

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"🏢 {g.name} (رمز: {g.password})",
                        callback_data=f"adm_pwgrp_{g.id}",
                    )
                ]
                for g in groups
            ]
        )
        await safe_reply(message, "🔑 مجموعه موردنظر برای تغییر رمز را انتخاب کنید:", reply_markup=kb)


@admin_router.callback_query(F.data.startswith("adm_pwgrp_"))
async def cb_select_group_for_password(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = str(callback.from_user.id)
    group_id = int(callback.data.replace("adm_pwgrp_", ""))
    with get_db() as db:
        if not is_user_admin(db, user_id, group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        grp = db.query(Group).filter(Group.id == group_id, Group.is_deleted == False).first()
        if not grp:
            await callback.answer("مجموعه یافت نشد.", show_alert=True)
            return
        g_name, g_pwd = grp.name, grp.password

    await state.update_data(pg_group_id=group_id)
    await state.set_state(AdminStates.pg_waiting_password)
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        f"🔑 تغییر رمز مجموعه *{escape_md(g_name)}* (رمز فعلی: `{g_pwd}`)\n\n"
        "لطفاً رمز جدید (عدد ۶ تا ۸ رقمی) را وارد کنید:",
        reply_markup=get_inline_cancel_keyboard(),
    )
    await callback.answer()


@admin_router.message(AdminStates.pg_waiting_password)
async def process_pg_new_password(message: Message, state: FSMContext) -> None:
    pwd = DateService.normalize_digits(message.text or "")
    if not (pwd.isdigit() and 6 <= len(pwd) <= 8):
        await safe_reply(
            message,
            "❌ رمز ورود باید فقط شامل اعداد و بین ۶ تا ۸ رقم باشد. لطفاً مجدداً وارد کنید:",
        )
        return

    data = await state.get_data()
    group_id = int(data.get("pg_group_id", 0))

    with get_db() as db:
        if not is_group_password_unique(db, pwd, exclude_group_id=group_id):
            await safe_reply(
                message,
                "❌ این رمز از قبل برای مجموعه دیگری استفاده شده است. لطفاً رمز متفاوت دیگری وارد کنید:",
            )
            return

        grp = db.query(Group).filter(Group.id == group_id).first()
        if not grp:
            await state.clear()
            await safe_reply(message, "❌ مجموعه یافت نشد.")
            return

        grp.password = pwd
        db.commit()
        g_name = grp.name

    await state.clear()
    await safe_reply(
        message,
        f"✅ رمز ورود مجموعه *{escape_md(g_name)}* با موفقیت به `{pwd}` تغییر یافت.",
    )


# --- دستور ng (تغییر نام مجموعه) ---
@admin_router.message(StateFilter(None), F.text.func(lambda t: t and t.strip().lower() == "ng"))
async def cmd_change_group_name(message: Message, state: FSMContext) -> None:
    user_id = str(message.from_user.id)
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
        group_ids = get_admin_group_ids(db, user_id)
        groups = (
            db.query(Group)
            .filter(Group.id.in_(group_ids), Group.is_deleted == False)
            .order_by(Group.id.asc())
            .all()
        )
        if not groups:
            await safe_reply(message, "📭 هیچ مجموعه‌ای یافت نشد.")
            return

        await state.clear()
        if len(groups) == 1 and not settings.is_super_admin(user_id):
            g = groups[0]
            await state.update_data(ng_group_id=g.id)
            await state.set_state(AdminStates.ng_waiting_name)
            await safe_reply(
                message,
                f"🏷 تغییر نام مجموعه *{escape_md(g.name)}*\nلطفاً نام جدید مجموعه را وارد کنید:",
                reply_markup=get_inline_cancel_keyboard(),
            )
            return

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"🏢 {g.name}",
                        callback_data=f"adm_nggrp_{g.id}",
                    )
                ]
                for g in groups
            ]
        )
        await safe_reply(message, "🏷 مجموعه موردنظر برای تغییر نام را انتخاب کنید:", reply_markup=kb)


@admin_router.callback_query(F.data.startswith("adm_nggrp_"))
async def cb_select_group_for_name(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = str(callback.from_user.id)
    group_id = int(callback.data.replace("adm_nggrp_", ""))
    with get_db() as db:
        if not is_user_admin(db, user_id, group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        grp = db.query(Group).filter(Group.id == group_id, Group.is_deleted == False).first()
        if not grp:
            await callback.answer("مجموعه یافت نشد.", show_alert=True)
            return
        g_name = grp.name

    await state.update_data(ng_group_id=group_id)
    await state.set_state(AdminStates.ng_waiting_name)
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        f"🏷 تغییر نام مجموعه *{escape_md(g_name)}*\nلطفاً نام جدید مجموعه را وارد کنید:",
        reply_markup=get_inline_cancel_keyboard(),
    )
    await callback.answer()


@admin_router.message(AdminStates.ng_waiting_name)
async def process_ng_new_name(message: Message, state: FSMContext) -> None:
    new_name = (message.text or "").strip()
    if len(new_name) < 2:
        await safe_reply(message, "❌ نام مجموعه باید حداقل ۲ کاراکتر باشد. مجدداً وارد کنید:")
        return

    data = await state.get_data()
    group_id = int(data.get("ng_group_id", 0))
    with get_db() as db:
        grp = db.query(Group).filter(Group.id == group_id).first()
        if not grp:
            await state.clear()
            await safe_reply(message, "❌ مجموعه یافت نشد.")
            return
        old_name = grp.name
        grp.name = new_name
        db.commit()

    await state.clear()
    await safe_reply(
        message,
        f"✅ نام مجموعه از «{escape_md(old_name)}» به *{escape_md(new_name)}* تغییر یافت.",
    )


# --- دستورات ag و aa (افزودن ادمین به مجموعه - ویژه سوپرادمین) ---
@admin_router.message(StateFilter(None), F.text.func(lambda t: t and t.strip().lower() in ("ag", "aa")))
async def cmd_add_group_admin(message: Message, state: FSMContext) -> None:
    user_id = str(message.from_user.id)
    if not settings.is_super_admin(user_id):
        await safe_reply(message, "⛔️ این دستور فقط مخصوص مدیر ارشد است.")
        return

    await state.clear()
    with get_db() as db:
        groups = db.query(Group).filter(Group.is_deleted == False).order_by(Group.id.asc()).all()
        if not groups:
            await safe_reply(message, "📭 هیچ مجموعه‌ای یافت نشد.")
            return

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"🏢 {g.name} (ID: {g.id})",
                        callback_data=f"adm_aggrp_{g.id}",
                    )
                ]
                for g in groups
            ]
        )
    await safe_reply(
        message,
        "👤 لطفاً مجموعه‌ای که می‌خواهید برای آن ادمین تعیین کنید را انتخاب نمایید:",
        reply_markup=kb,
    )


@admin_router.callback_query(F.data.startswith("adm_aggrp_"))
async def cb_select_group_for_add_admin(callback: CallbackQuery) -> None:
    user_id = str(callback.from_user.id)
    if not settings.is_super_admin(user_id):
        await callback.answer("عدم دسترسی", show_alert=True)
        return

    group_id = int(callback.data.replace("adm_aggrp_", ""))
    with get_db() as db:
        grp = db.query(Group).filter(Group.id == group_id).first()
        if not grp:
            await callback.answer("مجموعه یافت نشد.", show_alert=True)
            return

        users = (
            db.query(User)
            .filter(User.group_id == group_id, User.is_active == True)
            .order_by(User.name.asc())
            .all()
        )
        # یکتاسازی بر اساس telegram_id
        unique_users: Dict[str, User] = {}
        for u in users:
            tg_id = u.telegram_id or u.id
            if tg_id not in unique_users:
                unique_users[tg_id] = u

        if not unique_users:
            await safe_send_message(
                callback.bot,
                callback.message.chat.id,
                f"📭 هیچ کاربری در مجموعه *{escape_md(grp.name)}* عضو نیست.",
            )
            await callback.answer()
            return

        user_list = list(unique_users.values())
        # ارسال در دسته‌های ۵۰ تایی
        for i in range(0, len(user_list), 50):
            batch = user_list[i : i + 50]
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"👤 {u.name} ({u.telegram_id})",
                            callback_data=f"adm_mkadm_{u.telegram_id}_{group_id}",
                        )
                    ]
                    for u in batch
                ]
            )
            await safe_send_message(
                callback.bot,
                callback.message.chat.id,
                f"👥 انتخاب ادمین برای مجموعه *{escape_md(grp.name)}* (بخش {i // 50 + 1}):",
                reply_markup=kb,
            )

    await callback.answer()


@admin_router.callback_query(F.data.startswith("adm_mkadm_"))
async def cb_make_user_group_admin(callback: CallbackQuery) -> None:
    user_id = str(callback.from_user.id)
    if not settings.is_super_admin(user_id):
        await callback.answer("عدم دسترسی", show_alert=True)
        return

    payload = callback.data.replace("adm_mkadm_", "")
    target_tg_id, grp_id_str = payload.rsplit("_", 1)
    group_id = int(grp_id_str)

    with get_db() as db:
        grp = db.query(Group).filter(Group.id == group_id).first()
        if not grp:
            await callback.answer("مجموعه یافت نشد.", show_alert=True)
            return

        exists = (
            db.query(GroupAdmin)
            .filter(GroupAdmin.group_id == group_id, GroupAdmin.user_id == target_tg_id)
            .first()
        )
        if not exists:
            db.add(GroupAdmin(group_id=group_id, user_id=target_tg_id))
            db.commit()

        target_user = db.query(User).filter(User.telegram_id == target_tg_id).first()
        target_name = target_user.name if target_user else target_tg_id
        grp_name = grp.name

    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        f"✅ کاربر *{escape_md(target_name)}* (`{target_tg_id}`) به عنوان مدیر مجموعه *{escape_md(grp_name)}* ثبت شد.",
    )
    # ارسال پیام تبریک به ادمین جدید
    await safe_send_message(
        callback.bot,
        target_tg_id,
        f"🎉 *تبریک!*\n\nشما به عنوان مدیر مجموعه *{escape_md(grp_name)}* منصوب شدید.\n"
        "اکنون می‌توانید با ارسال `/start` از دکمه «⚙️ منوی مدیریت ادمین» استفاده نمایید.",
    )
    await callback.answer("ادمین اضافه شد.")


# --- دستور rg (حذف ادمین از مجموعه - ویژه سوپرادمین) ---
@admin_router.message(StateFilter(None), F.text.func(lambda t: t and t.strip().lower() == "rg"))
async def cmd_remove_group_admin(message: Message, state: FSMContext) -> None:
    user_id = str(message.from_user.id)
    if not settings.is_super_admin(user_id):
        await safe_reply(message, "⛔️ این دستور فقط مخصوص مدیر ارشد است.")
        return

    await state.clear()
    with get_db() as db:
        groups = db.query(Group).filter(Group.is_deleted == False).order_by(Group.id.asc()).all()
        if not groups:
            await safe_reply(message, "📭 هیچ مجموعه‌ای یافت نشد.")
            return

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"🏢 {g.name} (ID: {g.id})",
                        callback_data=f"adm_rggrp_{g.id}",
                    )
                ]
                for g in groups
            ]
        )
    await safe_reply(
        message,
        "🏢 مجموعه موردنظر برای مشاهده و عزل ادمین‌ها را انتخاب کنید:",
        reply_markup=kb,
    )


@admin_router.callback_query(F.data.startswith("adm_rggrp_"))
async def cb_select_group_for_remove_admin(callback: CallbackQuery) -> None:
    user_id = str(callback.from_user.id)
    if not settings.is_super_admin(user_id):
        await callback.answer("عدم دسترسی", show_alert=True)
        return

    group_id = int(callback.data.replace("adm_rggrp_", ""))
    with get_db() as db:
        grp = db.query(Group).filter(Group.id == group_id).first()
        if not grp:
            await callback.answer("مجموعه یافت نشد.", show_alert=True)
            return

        admins = db.query(GroupAdmin).filter(GroupAdmin.group_id == group_id).all()
        if not admins:
            await safe_send_message(
                callback.bot,
                callback.message.chat.id,
                f"📭 هیچ ادمینی برای مجموعه *{escape_md(grp.name)}* ثبت نشده است.",
            )
            await callback.answer()
            return

        buttons: List[List[InlineKeyboardButton]] = []
        for a in admins:
            u = db.query(User).filter(User.telegram_id == a.user_id).first()
            admin_name = u.name if u else "ادمین"
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"❌ عزل {admin_name} | {a.user_id}",
                        callback_data=f"adm_rmad_{group_id}_{a.user_id}",
                    )
                ]
            )

        await safe_send_message(
            callback.bot,
            callback.message.chat.id,
            f"👥 لیست ادمین‌های مجموعه *{escape_md(grp.name)}* (برای عزل کلیک کنید):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("adm_rmad_"))
async def cb_confirm_remove_group_admin(callback: CallbackQuery) -> None:
    user_id = str(callback.from_user.id)
    if not settings.is_super_admin(user_id):
        await callback.answer("عدم دسترسی", show_alert=True)
        return

    payload = callback.data.replace("adm_rmad_", "")
    grp_id_str, target_uid = payload.split("_", 1)
    group_id = int(grp_id_str)

    with get_db() as db:
        db.query(GroupAdmin).filter(
            GroupAdmin.group_id == group_id, GroupAdmin.user_id == target_uid
        ).delete()
        db.commit()

    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        f"✅ دسترسی ادمین `{target_uid}` از مجموعه `{group_id}` حذف شد.",
    )
    await callback.answer("حذف شد.")


# --- دستور gs (مشاهده آمار کلان سیستم - ویژه سوپرادمین) ---
@admin_router.message(StateFilter(None), F.text.func(lambda t: t and t.strip().lower() == "gs"))
async def cmd_global_stats(message: Message) -> None:
    user_id = str(message.from_user.id)
    if not settings.is_super_admin(user_id):
        await safe_reply(message, "⛔️ این دستور فقط مخصوص مدیر ارشد است.")
        return

    today_str = DateService.today_str()
    with get_db() as db:
        total_profiles = db.query(User).filter(User.is_active == True).count()
        total_groups = db.query(Group).filter(Group.is_deleted == False).count()
        total_leagues = (
            db.query(League)
            .filter(League.is_deleted == False, League.is_active == True)
            .count()
        )
        total_mins = (
            db.query(func.sum(User.total_minutes))
            .filter(User.is_active == True)
            .scalar()
            or 0
        )
        total_pages = (
            db.query(func.sum(User.total_pages))
            .filter(User.is_active == True)
            .scalar()
            or 0
        )
        avg_mins = round(total_mins / total_profiles, 1) if total_profiles > 0 else 0.0
        today_logs = (
            db.query(ActivityLog).filter(ActivityLog.log_date == today_str).count()
        )
        finished_cycles = (
            db.query(Cycle).filter(Cycle.status == "finished").count()
        )

    text = (
        "🌐 *آمار کلان کل سیستم کتابخوارشو*\n"
        "───────────────────\n"
        f"🏢 مجموعه‌های فعال: *{total_groups}*\n"
        f"🏆 لیگ‌های فعال: *{total_leagues}*\n"
        f"👥 کل پروفایل‌های فعال: *{total_profiles}*\n"
        f"⏱ مجموع کل زمان مطالعه: *{total_mins:,}* دقیقه\n"
        f"📄 مجموع کل صفحات: *{total_pages:,}* صفحه\n"
        f"📊 میانگین مطالعه هر کاربر: *{avg_mins}* دقیقه\n"
        f"📝 مطالعات ثبت‌شده امروز: *{today_logs}*\n"
        f"🏁 کل چله‌های تکمیل‌شده: *{finished_cycles}*"
    )
    await safe_reply(message, text)


# ===========================================================================
# ۷.۳. دستورات مدیریت مجموعه و لیگ‌ها (al, el, dl, us, eu, st, ex, sr, em)
# ===========================================================================

# --- مشاهده جداول لیگ‌ها از پنل شیشه‌ای ---
@admin_router.callback_query(F.data == "adm_viewleagues_select")
async def cb_view_leagues_select(callback: CallbackQuery) -> None:
    user_id = str(callback.from_user.id)
    with get_db() as db:
        if not is_user_admin(db, user_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        group_ids = get_admin_group_ids(db, user_id)
        leagues = (
            db.query(League)
            .filter(
                League.group_id.in_(group_ids),
                League.is_deleted == False,
                League.is_active == True,
            )
            .order_by(League.id.asc())
            .all()
        )
        if not leagues:
            await safe_send_message(callback.bot, callback.message.chat.id, "📭 هیچ لیگ فعالی یافت نشد.")
            await callback.answer()
            return

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"🏆 {l.name} (چله {l.cycle_number})",
                        callback_data=f"adm_viewleague_{l.id}",
                    )
                ]
                for l in leagues
            ]
        )
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        "📊 لیگ موردنظر برای مشاهده جدول آنلاین را انتخاب کنید:",
        reply_markup=kb,
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("adm_viewleague_"))
async def cb_view_single_league_table(callback: CallbackQuery) -> None:
    user_id = str(callback.from_user.id)
    league_id = callback.data.replace("adm_viewleague_", "")
    from handlers import format_league_leaderboard, send_text_chunks

    with get_db() as db:
        league = db.query(League).filter(League.id == league_id, League.is_deleted == False).first()
        if not league or not is_user_admin(db, user_id, league.group_id):
            await callback.answer("لیگ یافت نشد یا دسترسی ندارید.", show_alert=True)
            return
        table_text = format_league_leaderboard(db, league)

    await send_text_chunks(callback.bot, callback.message.chat.id, table_text)
    await callback.answer()


# --- دستور al و دکمه شیشه‌ای adm_menu_newleague (افزودن لیگ جدید) ---
async def _start_add_league_flow(bot: Bot, chat_id: int | str, user_id: str, state: FSMContext) -> None:
    with get_db() as db:
        if not is_user_admin(db, user_id):
            await safe_send_message(bot, chat_id, "⛔️ عدم دسترسی.")
            return
        group_ids = get_admin_group_ids(db, user_id)
        groups = (
            db.query(Group)
            .filter(Group.id.in_(group_ids), Group.is_deleted == False)
            .order_by(Group.id.asc())
            .all()
        )
        if not groups:
            await safe_send_message(bot, chat_id, "📭 هیچ مجموعه‌ای برای ساخت لیگ یافت نشد.")
            return

        await state.clear()
        if len(groups) == 1:
            g = groups[0]
            await state.update_data(al_group_id=g.id)
            await state.set_state(AdminStates.al_waiting_name)
            await safe_send_message(
                bot,
                chat_id,
                f"➕ ساخت لیگ جدید در مجموعه *{escape_md(g.name)}*\n\n"
                "لطفاً *نام لیگ جدید* را وارد کنید:",
                reply_markup=get_inline_cancel_keyboard(),
            )
            return

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"🏢 {g.name}",
                        callback_data=f"adm_algrp_{g.id}",
                    )
                ]
                for g in groups
            ]
        )
        await safe_send_message(
            bot,
            chat_id,
            "🏢 لطفاً مجموعه‌ای که می‌خواهید لیگ جدید در آن ساخته شود را انتخاب کنید:",
            reply_markup=kb,
        )


@admin_router.message(StateFilter(None), F.text.func(lambda t: t and t.strip().lower() == "al"))
async def cmd_add_league(message: Message, state: FSMContext) -> None:
    await _start_add_league_flow(message.bot, message.chat.id, str(message.from_user.id), state)


@admin_router.callback_query(F.data == "adm_menu_newleague")
async def cb_menu_new_league(callback: CallbackQuery, state: FSMContext) -> None:
    await _start_add_league_flow(
        callback.bot, callback.message.chat.id, str(callback.from_user.id), state
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("adm_algrp_"))
async def cb_select_group_for_new_league(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = str(callback.from_user.id)
    group_id = int(callback.data.replace("adm_algrp_", ""))
    with get_db() as db:
        if not is_user_admin(db, user_id, group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        grp = db.query(Group).filter(Group.id == group_id, Group.is_deleted == False).first()
        if not grp:
            await callback.answer("مجموعه یافت نشد.", show_alert=True)
            return
        g_name = grp.name

    await state.update_data(al_group_id=group_id)
    await state.set_state(AdminStates.al_waiting_name)
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        f"➕ ساخت لیگ جدید در مجموعه *{escape_md(g_name)}*\n\n"
        "لطفاً *نام لیگ جدید* را وارد کنید:",
        reply_markup=get_inline_cancel_keyboard(),
    )
    await callback.answer()


@admin_router.message(AdminStates.al_waiting_name)
async def process_al_league_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await safe_reply(message, "❌ نام لیگ باید حداقل ۲ کاراکتر باشد. مجدداً وارد کنید:")
        return

    await state.update_data(al_name=name)
    await state.set_state(AdminStates.al_waiting_floor)
    await safe_reply(
        message,
        f"⏱ نام لیگ: *{escape_md(name)}*\n\n"
        "حالا *کف مطالعه روزانه (میثاق)* را به دقیقه وارد کنید (فقط عدد، مثلاً `15`):",
        reply_markup=get_inline_cancel_keyboard(show_back=True),
    )


@admin_router.message(AdminStates.al_waiting_floor)
async def process_al_league_floor(message: Message, state: FSMContext) -> None:
    raw_floor = DateService.normalize_digits(message.text or "")
    if not raw_floor.isdigit() or not (1 <= int(raw_floor) <= 1440):
        await safe_reply(message, "❌ لطفاً یک عدد صحیح بین 1 تا 1440 وارد کنید:")
        return

    floor_val = int(raw_floor)
    data = await state.get_data()
    group_id = int(data.get("al_group_id", 1))
    league_name = data.get("al_name", "لیگ کتابخوانی")
    today_shamsi = DateService.today_shamsi()

    with get_db() as db:
        new_league = League(
            group_id=group_id,
            name=league_name,
            floor=floor_val,
            start_shamsi=today_shamsi,
            current_day=1,
            is_active=True,
            is_finished=False,
            is_deleted=False,
            archive_enabled=True,
            cycle_number=1,
        )
        db.add(new_league)
        db.commit()
        db.refresh(new_league)

        get_or_create_active_cycle(db, new_league, default_start_shamsi=today_shamsi)
        l_id = new_league.id

    await state.clear()
    await safe_reply(
        message,
        f"✅ *لیگ جدید با موفقیت ایجاد شد!*\n\n"
        f"🆔 کد لیگ: `{l_id}`\n"
        f"🏆 نام لیگ: *{escape_md(league_name)}*\n"
        f"⏱ میثاق روزانه: *{floor_val}* دقیقه\n"
        f"📅 تاریخ شروع چله ۱: `{today_shamsi}`",
    )


# --- دستورات el و dl و دکمه شیشه‌ای adm_menu_leagues (ویرایش و حذف لیگ‌ها) ---
async def _send_leagues_management_list(bot: Bot, chat_id: int | str, user_id: str) -> None:
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
        group_ids = get_admin_group_ids(db, user_id)
        leagues = (
            db.query(League)
            .filter(
                League.group_id.in_(group_ids),
                League.is_deleted == False,
                League.is_active == True,
            )
            .order_by(League.id.asc())
            .all()
        )
        if not leagues:
            await safe_send_message(bot, chat_id, "📭 هیچ لیگ فعالی یافت نشد.")
            return

        for lg in leagues:
            cyc = get_or_create_active_cycle(db, lg)
            curr_day = DateService.calculate_league_day(cyc.start_shamsi or lg.start_shamsi)
            members_count = (
                db.query(User)
                .filter(User.league_id == lg.id, User.is_active == True)
                .count()
            )
            grp = db.query(Group).filter(Group.id == lg.group_id).first()
            grp_name = grp.name if grp else "پیش‌فرض"

            text = (
                f"🏆 *لیگ: {escape_md(lg.name)}* (`{lg.id}`)\n"
                f"🏢 مجموعه: {escape_md(grp_name)}\n"
                f"⏱ میثاق روزانه: *{lg.floor}* دقیقه\n"
                f"🔄 شماره چله فعلی: *{lg.cycle_number}*\n"
                f"📅 تاریخ شروع چله: `{cyc.start_shamsi or lg.start_shamsi}` (روز *{curr_day}* از {settings.LEAGUE_DURATION})\n"
                f"👥 تعداد اعضا: *{members_count}* نفر"
            )
            await safe_send_message(
                bot, chat_id, text, reply_markup=_get_league_edit_keyboard(lg.id)
            )


@admin_router.message(StateFilter(None), F.text.func(lambda t: t and t.strip().lower() in ("el", "dl")))
async def cmd_edit_or_delete_leagues(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _send_leagues_management_list(message.bot, message.chat.id, str(message.from_user.id))


@admin_router.callback_query(F.data == "adm_menu_leagues")
async def cb_menu_leagues(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _send_leagues_management_list(
        callback.bot, callback.message.chat.id, str(callback.from_user.id)
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("leagedit_floor_"))
async def cb_league_edit_floor(callback: CallbackQuery, state: FSMContext) -> None:
    league_id = callback.data.replace("leagedit_floor_", "")
    user_id = str(callback.from_user.id)
    with get_db() as db:
        lg = db.query(League).filter(League.id == league_id, League.is_deleted == False).first()
        if not lg or not is_user_admin(db, user_id, lg.group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        l_name, l_floor = lg.name, lg.floor

    await state.update_data(edit_league_id=league_id)
    await state.set_state(AdminStates.leagedit_waiting_floor)
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        f"⏱ ویرایش میثاق لیگ *{escape_md(l_name)}* (فعلی: {l_floor} دقیقه)\n"
        "لطفاً زمان میثاق جدید را به دقیقه وارد کنید:",
        reply_markup=get_inline_cancel_keyboard(),
    )
    await callback.answer()


@admin_router.message(AdminStates.leagedit_waiting_floor)
async def process_league_new_floor(message: Message, state: FSMContext) -> None:
    raw = DateService.normalize_digits(message.text or "")
    if not raw.isdigit() or not (1 <= int(raw) <= 1440):
        await safe_reply(message, "❌ لطفاً عددی صحیح بین 1 تا 1440 وارد کنید:")
        return

    new_floor = int(raw)
    data = await state.get_data()
    league_id = data.get("edit_league_id")

    with get_db() as db:
        lg = db.query(League).filter(League.id == league_id).first()
        if not lg:
            await state.clear()
            await safe_reply(message, "❌ لیگ یافت نشد.")
            return
        lg.floor = new_floor
        db.commit()
        l_name = lg.name

    await state.clear()
    await safe_reply(
        message,
        f"✅ میثاق روزانه لیگ *{escape_md(l_name)}* به *{new_floor}* دقیقه تغییر یافت.",
    )


@admin_router.callback_query(F.data.startswith("leagedit_cycle_"))
async def cb_league_edit_cycle(callback: CallbackQuery, state: FSMContext) -> None:
    league_id = callback.data.replace("leagedit_cycle_", "")
    user_id = str(callback.from_user.id)
    with get_db() as db:
        lg = db.query(League).filter(League.id == league_id, League.is_deleted == False).first()
        if not lg or not is_user_admin(db, user_id, lg.group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        l_name, l_cyc = lg.name, lg.cycle_number

    await state.update_data(edit_league_id=league_id)
    await state.set_state(AdminStates.leagedit_waiting_cycle)
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        f"🏆 ویرایش شماره چله لیگ *{escape_md(l_name)}* (فعلی: چله {l_cyc})\n"
        "لطفاً شماره چله جدید را وارد کنید (فقط عدد):",
        reply_markup=get_inline_cancel_keyboard(),
    )
    await callback.answer()


@admin_router.message(AdminStates.leagedit_waiting_cycle)
async def process_league_new_cycle(message: Message, state: FSMContext) -> None:
    raw = DateService.normalize_digits(message.text or "")
    if not raw.isdigit() or int(raw) < 1:
        await safe_reply(message, "❌ لطفاً یک عدد صحیح بزرگتر یا مساوی 1 وارد کنید:")
        return

    new_cyc_num = int(raw)
    data = await state.get_data()
    league_id = data.get("edit_league_id")

    with get_db() as db:
        lg = db.query(League).filter(League.id == league_id).first()
        if not lg:
            await state.clear()
            await safe_reply(message, "❌ لیگ یافت نشد.")
            return
        lg.cycle_number = new_cyc_num
        active_cycle = get_or_create_active_cycle(db, lg)
        active_cycle.cycle_number = new_cyc_num
        db.commit()
        l_name = lg.name

    await state.clear()
    await safe_reply(
        message,
        f"✅ شماره چله لیگ *{escape_md(l_name)}* به *{new_cyc_num}* تغییر یافت.",
    )


@admin_router.callback_query(F.data.startswith("leagedit_date_"))
async def cb_league_edit_date(callback: CallbackQuery, state: FSMContext) -> None:
    league_id = callback.data.replace("leagedit_date_", "")
    user_id = str(callback.from_user.id)
    with get_db() as db:
        lg = db.query(League).filter(League.id == league_id, League.is_deleted == False).first()
        if not lg or not is_user_admin(db, user_id, lg.group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        cyc = get_or_create_active_cycle(db, lg)
        l_name = lg.name
        cur_date = cyc.start_shamsi or lg.start_shamsi

    await state.update_data(edit_league_id=league_id)
    await state.set_state(AdminStates.leagedit_waiting_date)
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        f"📅 ویرایش تاریخ شروع چله لیگ *{escape_md(l_name)}* (فعلی: `{cur_date}`)\n"
        "لطفاً تاریخ شروع شمسی جدید را با فرمت `1405/07/01` وارد کنید:",
        reply_markup=get_inline_cancel_keyboard(),
    )
    await callback.answer()


@admin_router.message(AdminStates.leagedit_waiting_date)
async def process_league_new_date(message: Message, state: FSMContext) -> None:
    norm_shamsi = DateService.normalize_shamsi(message.text or "")
    if not norm_shamsi:
        await safe_reply(
            message,
            "❌ فرمت تاریخ شمسی نامعتبر است. لطفاً با فرمت استاندارد مثل `1405/07/01` وارد کنید:",
        )
        return

    data = await state.get_data()
    league_id = data.get("edit_league_id")

    with get_db() as db:
        lg = db.query(League).filter(League.id == league_id).first()
        if not lg:
            await state.clear()
            await safe_reply(message, "❌ لیگ یافت نشد.")
            return
        new_day = DateService.calculate_league_day(norm_shamsi)
        lg.start_shamsi = norm_shamsi
        lg.current_day = new_day
        active_cycle = get_or_create_active_cycle(db, lg)
        active_cycle.start_shamsi = norm_shamsi
        active_cycle.current_day = new_day

        start_d = DateService.shamsi_to_date(norm_shamsi)
        if start_d:
            cycle_logs = (
                db.query(ActivityLog)
                .filter(
                    ActivityLog.league_id == lg.id,
                    (ActivityLog.cycle_id == active_cycle.id)
                    | (ActivityLog.cycle_number == lg.cycle_number),
                )
                .all()
            )
            for c_log in cycle_logs:
                if c_log.log_date:
                    try:
                        ld = datetime.strptime(c_log.log_date[:10], "%Y-%m-%d").date()
                        calc_day = (ld - start_d).days + 1
                        if calc_day >= 1:
                            c_log.league_day = calc_day
                    except ValueError:
                        pass

        db.commit()
        AbsenceService.reconcile_historical_gaps(db, league=lg)
        AbsenceService.reconcile_streaks(db, league=lg)
        l_name = lg.name

    await state.clear()
    await safe_reply(
        message,
        f"✅ تاریخ شروع لیگ *{escape_md(l_name)}* به `{norm_shamsi}` تغییر یافت (روز جاری: *{new_day}*).",
    )


@admin_router.callback_query(F.data.startswith("adm_deleteleague_"))
async def cb_delete_league_prompt(callback: CallbackQuery) -> None:
    league_id = callback.data.replace("adm_deleteleague_", "")
    user_id = str(callback.from_user.id)
    with get_db() as db:
        lg = db.query(League).filter(League.id == league_id, League.is_deleted == False).first()
        if not lg or not is_user_admin(db, user_id, lg.group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        l_name = lg.name

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ بله، لیگ حذف شود",
                    callback_data=f"adm_confirmleague_{league_id}",
                ),
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="adm_canceldeleteleague",
                ),
            ]
        ]
    )
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        f"⚠️ آیا از حذف کامل لیگ *{escape_md(l_name)}* اطمینان دارید؟",
        reply_markup=kb,
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("adm_confirmleague_"))
async def cb_confirm_delete_league(callback: CallbackQuery) -> None:
    league_id = callback.data.replace("adm_confirmleague_", "")
    user_id = str(callback.from_user.id)
    with get_db() as db:
        lg = db.query(League).filter(League.id == league_id).first()
        if not lg or not is_user_admin(db, user_id, lg.group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        l_name = lg.name
        lg.is_deleted = True
        lg.is_active = False
        # آزادسازی لیگ کاربران عضو این لیگ
        db.query(User).filter(User.league_id == league_id).update(
            {User.league_id: None}, synchronize_session=False
        )
        db.commit()

    try:
        await callback.message.edit_text(f"🗑 لیگ *{escape_md(l_name)}* با موفقیت حذف شد.", parse_mode="Markdown")
    except Exception:
        await safe_send_message(callback.bot, callback.message.chat.id, f"🗑 لیگ {l_name} حذف شد.")
    await callback.answer("حذف شد.")


@admin_router.callback_query(F.data == "adm_canceldeleteleague")
async def cb_cancel_delete_league(callback: CallbackQuery) -> None:
    try:
        await callback.message.edit_text("✅ عملیات حذف لیگ لغو شد.")
    except Exception:
        pass
    await callback.answer("لغو شد.")


# --- دستورات us و eu و دکمه شیشه‌ای adm_menu_users (مدیریت کاربران و پروفایل‌ها) ---
async def _send_users_by_league(bot: Bot, chat_id: int | str, user_id: str) -> None:
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
        group_ids = get_admin_group_ids(db, user_id)
        leagues = (
            db.query(League)
            .filter(
                League.group_id.in_(group_ids),
                League.is_deleted == False,
                League.is_active == True,
            )
            .order_by(League.id.asc())
            .all()
        )

        any_sent = False
        for lg in leagues:
            users = (
                db.query(User)
                .filter(User.league_id == lg.id, User.is_active == True)
                .order_by(User.points.desc(), User.total_minutes.desc())
                .all()
            )
            if not users:
                continue
            any_sent = True
            for i in range(0, len(users), 50):
                batch = users[i : i + 50]
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=f"👤 {u.name}",
                                callback_data=f"adm_manage_{u.id}",
                            )
                        ]
                        for u in batch
                    ]
                )
                part_txt = f" (بخش {i // 50 + 1})" if len(users) > 50 else ""
                await safe_send_message(
                    bot,
                    chat_id,
                    f"👥 *کاربران لیگ {escape_md(lg.name)}{part_txt}:*\n"
                    "برای مدیریت هر کاربر روی نام او کلیک کنید:",
                    reply_markup=kb,
                )

        # کاربرانی که در مجموعه هستند اما هنوز لیگی ندارند
        unassigned_users = (
            db.query(User)
            .filter(
                User.group_id.in_(group_ids),
                User.is_active == True,
                (User.league_id == None) | (User.league_id == ""),
            )
            .all()
        )
        if unassigned_users:
            any_sent = True
            for i in range(0, len(unassigned_users), 50):
                batch = unassigned_users[i : i + 50]
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=f"👤 {u.name}",
                                callback_data=f"adm_manage_{u.id}",
                            )
                        ]
                        for u in batch
                    ]
                )
                await safe_send_message(
                    bot,
                    chat_id,
                    "👥 *کاربران بدون لیگ:*",
                    reply_markup=kb,
                )

        if not any_sent:
            await safe_send_message(bot, chat_id, "📭 هیچ کاربر فعالی در مجموعه‌های شما یافت نشد.")


@admin_router.message(StateFilter(None), F.text.func(lambda t: t and t.strip().lower() in ("us", "eu")))
async def cmd_manage_users_list(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _send_users_by_league(message.bot, message.chat.id, str(message.from_user.id))


@admin_router.callback_query(F.data == "adm_menu_users")
async def cb_menu_users_list(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _send_users_by_league(
        callback.bot, callback.message.chat.id, str(callback.from_user.id)
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("adm_manage_"))
async def cb_open_user_manage_panel(callback: CallbackQuery, state: FSMContext) -> None:
    target_uid = callback.data.replace("adm_manage_", "")
    admin_id = str(callback.from_user.id)

    with get_db() as db:
        u = db.query(User).filter(User.id == target_uid).first()
        if not u:
            await callback.answer("کاربر یافت نشد.", show_alert=True)
            return
        if not is_user_admin(db, admin_id, u.group_id):
            await callback.answer("عدم دسترسی به این کاربر", show_alert=True)
            return
        card_text = _format_user_admin_card(db, u)

    await state.clear()
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        card_text,
        reply_markup=_get_user_manage_keyboard(target_uid),
    )
    await callback.answer()


# --- ویرایش فیلدهای کاربر در پنل مدیریت ---
@admin_router.callback_query(F.data.startswith("adm_editname_"))
async def cb_user_edit_name(callback: CallbackQuery, state: FSMContext) -> None:
    target_uid = callback.data.replace("adm_editname_", "")
    await state.update_data(target_user_id=target_uid)
    await state.set_state(AdminStates.usr_waiting_name)
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        "✏️ لطفاً *نام و نام خانوادگی جدید* کاربر را وارد کنید:",
        reply_markup=get_inline_cancel_keyboard(),
    )
    await callback.answer()


@admin_router.message(AdminStates.usr_waiting_name)
async def process_user_new_name(message: Message, state: FSMContext) -> None:
    new_name = (message.text or "").strip()
    if len(new_name) < 2:
        await safe_reply(message, "❌ نام باید حداقل ۲ کاراکتر باشد. مجدداً وارد کنید:")
        return

    parts = new_name.split(maxsplit=1)
    first_n = parts[0]
    last_n = parts[1] if len(parts) > 1 else ""

    data = await state.get_data()
    target_uid = data.get("target_user_id")

    with get_db() as db:
        u = db.query(User).filter(User.id == target_uid).first()
        if not u:
            await state.clear()
            await safe_reply(message, "❌ کاربر یافت نشد.")
            return
        u.name = new_name
        u.first_name = first_n
        u.last_name = last_n
        db.commit()
        card = _format_user_admin_card(db, u)

    await state.clear()
    await safe_reply(message, f"✅ نام کاربر به‌روزرسانی شد.\n\n{card}", reply_markup=_get_user_manage_keyboard(target_uid))


def _get_profile_league_ids(db: Session, telegram_id: str | int) -> set[str]:
    """مجموعه شناسه لیگ‌هایی که این شخص در آنها پروفایل فعال دارد"""
    rows = (
        db.query(User.league_id)
        .filter(
            User.telegram_id == str(telegram_id).strip(),
            User.is_active == True,
            User.league_id.isnot(None),
        )
        .all()
    )
    return {r[0] for r in rows if r[0]}


def _get_admin_profile_lock(profile_id: str) -> asyncio.Lock:
    """قفل اختصاصی شخص (بر اساس telegram_id) مشترک با هندلرهای کاربر"""
    from handlers import _get_user_lock

    with get_db() as db:
        row = db.query(User.telegram_id).filter(User.id == profile_id).first()
    tg = row[0] if row and row[0] else profile_id
    return _get_user_lock(tg)


@admin_router.callback_query(F.data.startswith("adm_moveleague_"))
async def cb_user_move_league(callback: CallbackQuery) -> None:
    target_uid = callback.data.replace("adm_moveleague_", "")
    admin_id = str(callback.from_user.id)
    kb: Optional[InlineKeyboardMarkup] = None

    with get_db() as db:
        u = db.query(User).filter(User.id == target_uid).first()
        if not u or not is_user_admin(db, admin_id, u.group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        group_ids = get_admin_group_ids(db, admin_id)
        all_leagues = (
            db.query(League)
            .filter(
                League.group_id.in_(group_ids),
                League.is_deleted == False,
                League.is_active == True,
            )
            .all()
        )
        excluded = _get_profile_league_ids(db, u.telegram_id or u.id)
        if u.league_id:
            excluded.add(u.league_id)
        leagues = [l for l in all_leagues if l.id not in excluded]
        if leagues:
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"🏆 {l.name} (کف: {l.floor} دقیقه)",
                            callback_data=f"adm_domove_{l.id}_{u.id}",
                        )
                    ]
                    for l in leagues
                ]
            )
        u_name = u.name

    if kb is None:
        await safe_send_message(
            callback.bot,
            callback.message.chat.id,
            "هیچ لیگ دیگری برای انتقال این کاربر در دسترس نیست.",
        )
        await callback.answer()
        return

    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        f"🔄 انتقال پروفایل *{escape_md(u_name)}* به کدام لیگ انجام شود؟",
        reply_markup=kb,
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("adm_domove_"))
async def cb_execute_user_move_league(callback: CallbackQuery) -> None:
    from handlers import build_user_main_menu

    payload = callback.data.replace("adm_domove_", "")
    new_league_id, target_uid = payload.split("_", 1)
    admin_id = str(callback.from_user.id)

    async with _get_admin_profile_lock(target_uid):
        warn_text: Optional[str] = None
        with get_db() as db:
            u = db.query(User).filter(User.id == target_uid).first()
            lg = (
                db.query(League)
                .filter(
                    League.id == new_league_id,
                    League.is_deleted == False,
                    League.is_active == True,
                )
                .first()
            )
            if not u or not u.is_active or not lg:
                await callback.answer(
                    "کاربر یافت نشد یا لیگ مقصد غیرفعال/حذف شده است.", show_alert=True
                )
                return
            if not is_user_admin(db, admin_id, lg.group_id) or not is_user_admin(
                db, admin_id, u.group_id
            ):
                await callback.answer("عدم دسترسی", show_alert=True)
                return

            tg_id = u.telegram_id or u.id
            if u.league_id == lg.id:
                warn_text = "⚠️ کاربر هم‌اکنون در همین لیگ عضو است."
            elif _get_profile_league_ids(db, tg_id) & {lg.id}:
                warn_text = (
                    f"⚠️ کاربر *{escape_md(u.name)}* از قبل یک پروفایل فعال دیگر "
                    f"در لیگ *{escape_md(lg.name)}* دارد."
                )

            if warn_text is None:
                old_league = (
                    db.query(League).filter(League.id == u.league_id).first()
                    if u.league_id
                    else None
                )
                old_l_name = old_league.name if old_league else "بدون لیگ"

                cyc = get_or_create_active_cycle(db, lg)
                current_day = DateService.calculate_league_day(
                    cyc.start_shamsi or lg.start_shamsi
                )
                gift_points = float(max(0, (current_day - 1) * 10))

                # ریست کامل آمار دوره؛ لاگ‌های قبلی متعلق به لیگ/چله قبلی باقی می‌مانند
                u.league_id = lg.id
                u.group_id = lg.group_id
                u.points = gift_points
                u.total_minutes = 0
                u.total_pages = 0
                u.streak = 0
                u.no_study_days = 0
                u.absent_days_list = ""
                u.late_days_list = ""
                u.half_coupons = settings.DEFAULT_HALF_COUPONS
                u.one_min_coupons = settings.DEFAULT_ONE_MIN_COUPONS
                if u.user_floor is not None and u.user_floor < lg.floor:
                    u.user_floor = None
                u.last_log_date = None
                u.today_minutes = 0
                u.today_pages = 0
                u.today_points = 0.0
                u.today_half_used = 0
                u.today_one_min_used = 0
                u.created_at = datetime.now(timezone.utc)
                db.query(ActivityLog).filter(
                    ActivityLog.user_id == u.id,
                    ActivityLog.league_id == lg.id,
                    (ActivityLog.cycle_id == cyc.id)
                    | (
                        (ActivityLog.cycle_id == None)
                        & (ActivityLog.cycle_number == lg.cycle_number)
                    ),
                ).delete(synchronize_session=False)
                db.commit()

                set_system_state(db, f"streak_offset_{u.id}", "0")

                active_now = get_active_user(db, tg_id)
                if active_now and active_now.id == u.id:
                    set_active_user_id(db, tg_id, u.id)

                eff_floor = u.get_effective_floor(lg.floor)
                l_name = lg.name
                u_name = u.name
                user_msg = MessageService.apply_terms(
                    db,
                    lg.group_id,
                    f"🔄 شما توسط مدیر از لیگ «{escape_md(old_l_name)}» به لیگ «{escape_md(l_name)}» منتقل شدید.\n"
                    f"🏆 چله {cyc.cycle_number} | روز {current_day} از {settings.LEAGUE_DURATION}\n"
                    f"✨ امتیاز هدیه همگام‌سازی: {gift_points}\n"
                    f"⏱ میثاق شما در این لیگ: {eff_floor} دقیقه\n"
                    f"🌸 به لیگ جدید خوش آمدید!",
                )
                user_kb = build_user_main_menu(db, tg_id, u)

        if warn_text is not None:
            await safe_send_message(callback.bot, callback.message.chat.id, warn_text)
            await callback.answer()
            return

    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        f"✅ کاربر *{escape_md(u_name)}* به لیگ *{escape_md(l_name)}* منتقل شد (امتیاز هدیه همگام‌سازی: *{gift_points}*).",
    )
    await safe_send_message(callback.bot, tg_id, user_msg, reply_markup=user_kb)
    await callback.answer("منتقل شد.")


@admin_router.callback_query(F.data.startswith("adm_addleague_"))
async def cb_user_add_second_league(callback: CallbackQuery) -> None:
    target_uid = callback.data.replace("adm_addleague_", "")
    admin_id = str(callback.from_user.id)
    kb: Optional[InlineKeyboardMarkup] = None

    with get_db() as db:
        u = db.query(User).filter(User.id == target_uid).first()
        if not u or not is_user_admin(db, admin_id, u.group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        group_ids = get_admin_group_ids(db, admin_id)
        all_leagues = (
            db.query(League)
            .filter(
                League.group_id.in_(group_ids),
                League.is_deleted == False,
                League.is_active == True,
            )
            .all()
        )
        excluded = _get_profile_league_ids(db, u.telegram_id or u.id)
        leagues = [l for l in all_leagues if l.id not in excluded]
        if leagues:
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"➕ {l.name} (کف: {l.floor} دقیقه)",
                            callback_data=f"adm_doaddl_{l.id}_{u.id}",
                        )
                    ]
                    for l in leagues
                ]
            )
        u_name = u.name

    if kb is None:
        await safe_send_message(
            callback.bot,
            callback.message.chat.id,
            f"کاربر *{escape_md(u_name)}* در حال حاضر در تمامی لیگ‌های فعال عضو است.",
        )
        await callback.answer()
        return

    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        f"➕ افزودن پروفایل جدید برای *{escape_md(u_name)}* در کدام لیگ انجام شود؟",
        reply_markup=kb,
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("adm_doaddl_"))
async def cb_execute_user_add_second_league(callback: CallbackQuery) -> None:
    source_uid = callback.data.replace("adm_doaddl_", "").split("_", 1)[1]
    async with _get_admin_profile_lock(source_uid):
        await _execute_user_add_second_league_impl(callback)


async def _execute_user_add_second_league_impl(callback: CallbackQuery) -> None:
    payload = callback.data.replace("adm_doaddl_", "")
    target_league_id, source_uid = payload.split("_", 1)
    admin_id = str(callback.from_user.id)

    with get_db() as db:
        src_user = db.query(User).filter(User.id == source_uid).first()
        lg = (
            db.query(League)
            .filter(
                League.id == target_league_id,
                League.is_deleted == False,
                League.is_active == True,
            )
            .first()
        )
        if not src_user or not lg or not is_user_admin(db, admin_id, lg.group_id):
            await callback.answer("کاربر یا لیگ یافت نشد.", show_alert=True)
            return

        tg_id = src_user.telegram_id or src_user.id
        # بررسی عدم عضویت تکراری در همین لیگ
        existing_in_league = (
            db.query(User)
            .filter(
                User.telegram_id == tg_id,
                User.league_id == lg.id,
                User.is_active == True,
            )
            .first()
        )
        if existing_in_league:
            await safe_send_message(
                callback.bot,
                callback.message.chat.id,
                f"⚠️ کاربر *{escape_md(src_user.name)}* از قبل در لیگ *{escape_md(lg.name)}* عضو است.",
            )
            await callback.answer()
            return

        cyc = get_or_create_active_cycle(db, lg)
        current_day = DateService.calculate_league_day(cyc.start_shamsi or lg.start_shamsi)
        gift_points = float(max(0, (current_day - 1) * 10))
        new_prof_id = generate_new_profile_id(db, tg_id, group_id=lg.group_id, league_id=lg.id)

        new_profile = User(
            id=new_prof_id,
            telegram_id=tg_id,
            group_id=lg.group_id,
            name=src_user.name,
            first_name=src_user.first_name,
            last_name=src_user.last_name,
            league_id=lg.id,
            points=gift_points,
            total_minutes=0,
            total_pages=0,
            streak=0,
            no_study_days=0,
            absent_days_list="",
            late_days_list="",
            half_coupons=settings.DEFAULT_HALF_COUPONS,
            one_min_coupons=settings.DEFAULT_ONE_MIN_COUPONS,
            is_active=True,
        )
        db.add(new_profile)
        db.commit()
        set_active_user_id(db, tg_id, new_prof_id)
        u_name = src_user.name
        l_name = lg.name

    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        f"✅ پروفایل جدید برای *{escape_md(u_name)}* در لیگ *{escape_md(l_name)}* ساخته شد (امتیاز هدیه همگام‌سازی: *{gift_points}*).",
    )
    await safe_send_message(
        callback.bot,
        tg_id,
        f"🎉 شما توسط مدیر به لیگ «{escape_md(l_name)}» نیز اضافه شدید!\n"
        f"✨ امتیاز هدیه همگام‌سازی با روز {current_day} لیگ: {gift_points} امتیاز!\n"
        "می‌توانید از دکمه «🔄 تغییر لیگ فعال» در منوی اصلی برای جابجایی بین لیگ‌های خود استفاده کنید.",
    )
    await callback.answer("اضافه شد.")


@admin_router.callback_query(F.data.startswith("adm_edit_points_"))
async def cb_user_edit_points(callback: CallbackQuery, state: FSMContext) -> None:
    target_uid = callback.data.replace("adm_edit_points_", "")
    await state.update_data(target_user_id=target_uid)
    await state.set_state(AdminStates.usr_waiting_points)
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        "⭐️ لطفاً *امتیاز کل جدید* کاربر را وارد کنید (عدد):",
        reply_markup=get_inline_cancel_keyboard(),
    )
    await callback.answer()


@admin_router.message(AdminStates.usr_waiting_points)
async def process_user_new_points(message: Message, state: FSMContext) -> None:
    raw = DateService.normalize_digits(message.text or "")
    try:
        val = float(raw)
    except ValueError:
        await safe_reply(message, "❌ لطفاً یک عدد معتبر وارد کنید:")
        return

    data = await state.get_data()
    target_uid = data.get("target_user_id")
    with get_db() as db:
        u = db.query(User).filter(User.id == target_uid).first()
        if u:
            u.points = round(val, 1)
            db.commit()
            card = _format_user_admin_card(db, u)
        else:
            card = "کاربر یافت نشد."

    await state.clear()
    await safe_reply(message, f"✅ امتیاز کاربر تغییر یافت.\n\n{card}", reply_markup=_get_user_manage_keyboard(target_uid))


@admin_router.callback_query(F.data.startswith("adm_edit_streak_"))
async def cb_user_edit_streak(callback: CallbackQuery, state: FSMContext) -> None:
    target_uid = callback.data.replace("adm_edit_streak_", "")
    await state.update_data(target_user_id=target_uid)
    await state.set_state(AdminStates.usr_waiting_streak)
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        "🔥 لطفاً *زنجیره استمرار جدید* (تعداد روز) را وارد کنید:",
        reply_markup=get_inline_cancel_keyboard(),
    )
    await callback.answer()


@admin_router.message(AdminStates.usr_waiting_streak)
async def process_user_new_streak(message: Message, state: FSMContext) -> None:
    raw = DateService.normalize_digits(message.text or "")
    if not raw.isdigit():
        await safe_reply(message, "❌ لطفاً یک عدد صحیح غیرمنفی وارد کنید:")
        return

    data = await state.get_data()
    target_uid = data.get("target_user_id")
    with get_db() as db:
        u = db.query(User).filter(User.id == target_uid).first()
        if u:
            u.streak = int(raw)
            lg_s = (
                db.query(League).filter(League.id == u.league_id).first()
                if u.league_id
                else None
            )
            raw_streak = 0
            if lg_s:
                cyc_s = get_or_create_active_cycle(db, lg_s)
                raw_streak = AbsenceService._compute_raw_streak_from_logs(db, u, lg_s, cyc_s)
            set_system_state(db, f"streak_offset_{u.id}", str(int(raw) - raw_streak))
            db.commit()
            card = _format_user_admin_card(db, u)
        else:
            card = "کاربر یافت نشد."

    await state.clear()
    await safe_reply(message, f"✅ زنجیره استمرار کاربر تغییر یافت.\n\n{card}", reply_markup=_get_user_manage_keyboard(target_uid))


@admin_router.callback_query(F.data.startswith("adm_edit_minutes_"))
async def cb_user_edit_minutes(callback: CallbackQuery, state: FSMContext) -> None:
    target_uid = callback.data.replace("adm_edit_minutes_", "")
    await state.update_data(target_user_id=target_uid)
    await state.set_state(AdminStates.usr_waiting_minutes)
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        "⏱ لطفاً *مجموع زمان کل مطالعه جدید* (به دقیقه) را وارد کنید:",
        reply_markup=get_inline_cancel_keyboard(),
    )
    await callback.answer()


@admin_router.message(AdminStates.usr_waiting_minutes)
async def process_user_new_minutes(message: Message, state: FSMContext) -> None:
    raw = DateService.normalize_digits(message.text or "")
    if not raw.isdigit():
        await safe_reply(message, "❌ لطفاً یک عدد صحیح غیرمنفی وارد کنید:")
        return

    data = await state.get_data()
    target_uid = data.get("target_user_id")
    with get_db() as db:
        u = db.query(User).filter(User.id == target_uid).first()
        if u:
            u.total_minutes = int(raw)
            db.commit()
            card = _format_user_admin_card(db, u)
        else:
            card = "کاربر یافت نشد."

    await state.clear()
    await safe_reply(message, f"✅ زمان کل مطالعه تغییر یافت.\n\n{card}", reply_markup=_get_user_manage_keyboard(target_uid))


@admin_router.callback_query(F.data.startswith("adm_edit_pages_"))
async def cb_user_edit_pages(callback: CallbackQuery, state: FSMContext) -> None:
    target_uid = callback.data.replace("adm_edit_pages_", "")
    await state.update_data(target_user_id=target_uid)
    await state.set_state(AdminStates.usr_waiting_pages)
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        "📄 لطفاً *مجموع صفحات کل جدید* را وارد کنید:",
        reply_markup=get_inline_cancel_keyboard(),
    )
    await callback.answer()


@admin_router.message(AdminStates.usr_waiting_pages)
async def process_user_new_pages(message: Message, state: FSMContext) -> None:
    raw = DateService.normalize_digits(message.text or "")
    if not raw.isdigit():
        await safe_reply(message, "❌ لطفاً یک عدد صحیح غیرمنفی وارد کنید:")
        return

    data = await state.get_data()
    target_uid = data.get("target_user_id")
    with get_db() as db:
        u = db.query(User).filter(User.id == target_uid).first()
        if u:
            u.total_pages = int(raw)
            db.commit()
            card = _format_user_admin_card(db, u)
        else:
            card = "کاربر یافت نشد."

    await state.clear()
    await safe_reply(message, f"✅ صفحات کل کاربر تغییر یافت.\n\n{card}", reply_markup=_get_user_manage_keyboard(target_uid))


@admin_router.callback_query(F.data.startswith("adm_edit_no_study_"))
async def cb_user_edit_no_study(callback: CallbackQuery, state: FSMContext) -> None:
    target_uid = callback.data.replace("adm_edit_no_study_", "")
    await state.update_data(target_user_id=target_uid)
    await state.set_state(AdminStates.usr_waiting_no_study)
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        "❌ لطفاً *تعداد روزهای غیبت جدید* را وارد کنید (عدد):",
        reply_markup=get_inline_cancel_keyboard(),
    )
    await callback.answer()


@admin_router.message(AdminStates.usr_waiting_no_study)
async def process_user_new_no_study(message: Message, state: FSMContext) -> None:
    raw = DateService.normalize_digits(message.text or "")
    if not raw.isdigit():
        await safe_reply(message, "❌ لطفاً یک عدد صحیح غیرمنفی وارد کنید:")
        return

    new_count = int(raw)
    note = ""
    data = await state.get_data()
    target_uid = data.get("target_user_id")
    with get_db() as db:
        u = db.query(User).filter(User.id == target_uid).first()
        if u:
            logged_days = {
                int(r.league_day)
                for r in db.query(ActivityLog)
                .filter(
                    ActivityLog.user_id == u.id,
                    ActivityLog.league_id == u.league_id,
                    ActivityLog.minutes > 0,
                )
                .all()
                if r.league_day
            }
            past_days = _get_user_past_days(db, u)
            future_days = set(range(1, settings.LEAGUE_DURATION + 1)) - past_days
            allowed_days = past_days - logged_days
            eff_count = min(new_count, len(allowed_days))
            if eff_count < new_count:
                note = (
                    "\n⚠️ عدد واردشده بیشتر از تعداد روزهای گذشتهٔ بدون ثبت در این چله بود؛ "
                    f"مقدار روی {eff_count} تنظیم شد."
                )
            u.absent_days_list = AbsenceService.sync_days_list_with_count(
                u.absent_days_list,
                eff_count,
                max_day=settings.LEAGUE_DURATION,
                exclude_days=logged_days | future_days,
                preferred_days=sorted(allowed_days),
            )
            u.no_study_days = len(AbsenceService.parse_days_list(u.absent_days_list))
            db.commit()
            card = _format_user_admin_card(db, u)
        else:
            card = "کاربر یافت نشد."

    await state.clear()
    await safe_reply(message, f"✅ تعداد غیبت و لیست روزهای غیبت همگام‌سازی شد.{note}\n\n{card}", reply_markup=_get_user_manage_keyboard(target_uid))


@admin_router.callback_query(F.data.startswith("adm_edit_late_"))
async def cb_user_edit_late(callback: CallbackQuery, state: FSMContext) -> None:
    target_uid = callback.data.replace("adm_edit_late_", "")
    await state.update_data(target_user_id=target_uid)
    await state.set_state(AdminStates.usr_waiting_late)
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        "⚠️ لطفاً *تعداد روزهای ثبت با تاخیر (عدم اعلام به موقع)* را وارد کنید (عدد):",
        reply_markup=get_inline_cancel_keyboard(),
    )
    await callback.answer()


@admin_router.message(AdminStates.usr_waiting_late)
async def process_user_new_late(message: Message, state: FSMContext) -> None:
    raw = DateService.normalize_digits(message.text or "")
    if not raw.isdigit():
        await safe_reply(message, "❌ لطفاً یک عدد صحیح غیرمنفی وارد کنید:")
        return

    new_count = int(raw)
    note = ""
    data = await state.get_data()
    target_uid = data.get("target_user_id")
    with get_db() as db:
        u = db.query(User).filter(User.id == target_uid).first()
        if u:
            absent_days = set(AbsenceService.parse_days_list(u.absent_days_list))
            past_days_l = _get_user_past_days(db, u)
            future_days_l = set(range(1, settings.LEAGUE_DURATION + 1)) - past_days_l
            allowed_late = past_days_l - absent_days
            eff_late = min(new_count, len(allowed_late))
            if eff_late < new_count:
                note = (
                    "\n⚠️ عدد واردشده بیشتر از تعداد روزهای گذشتهٔ قابلثبت در این چله بود؛ "
                    f"مقدار روی {eff_late} تنظیم شد."
                )
            u.late_days_list = AbsenceService.sync_days_list_with_count(
                u.late_days_list,
                eff_late,
                max_day=settings.LEAGUE_DURATION,
                exclude_days=absent_days | future_days_l,
                preferred_days=sorted(allowed_late),
            )
            db.commit()
            card = _format_user_admin_card(db, u)
        else:
            card = "کاربر یافت نشد."

    await state.clear()
    await safe_reply(message, f"✅ تعداد ثبت‌های با تاخیر همگام‌سازی شد.{note}\n\n{card}", reply_markup=_get_user_manage_keyboard(target_uid))


@admin_router.callback_query(F.data.startswith("adm_userfloor_"))
async def cb_user_edit_floor(callback: CallbackQuery, state: FSMContext) -> None:
    target_uid = callback.data.replace("adm_userfloor_", "")
    await state.update_data(target_user_id=target_uid)
    await state.set_state(AdminStates.usr_waiting_floor)
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        "⏱ لطفاً *میثاق اختصاصی جدید کاربر* را به دقیقه وارد کنید (برای بازگشت به میثاق پیش‌فرض لیگ، عدد `0` را بفرستید):",
        reply_markup=get_inline_cancel_keyboard(),
    )
    await callback.answer()


@admin_router.message(AdminStates.usr_waiting_floor)
async def process_user_new_floor(message: Message, state: FSMContext) -> None:
    raw = DateService.normalize_digits(message.text or "")
    if not raw.isdigit() or int(raw) > 1440:
        await safe_reply(message, "❌ لطفاً عددی صحیح بین 0 تا 1440 وارد کنید:")
        return

    val = int(raw)
    data = await state.get_data()
    target_uid = data.get("target_user_id")
    with get_db() as db:
        u = db.query(User).filter(User.id == target_uid).first()
        if u:
            u.user_floor = val if val > 0 else None
            db.commit()
            card = _format_user_admin_card(db, u)
        else:
            card = "کاربر یافت نشد."

    await state.clear()
    await safe_reply(message, f"✅ میثاق اختصاصی کاربر تنظیم شد.\n\n{card}", reply_markup=_get_user_manage_keyboard(target_uid))


@admin_router.callback_query(F.data.startswith("adm_delete_"))
async def cb_user_delete(callback: CallbackQuery) -> None:
    target_uid = callback.data.replace("adm_delete_", "")
    admin_id = str(callback.from_user.id)
    with get_db() as db:
        u = db.query(User).filter(User.id == target_uid).first()
        if not u or not is_user_admin(db, admin_id, u.group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        u_name = u.name
        u.is_active = False
        u.league_id = None
        db.commit()

    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        f"🗑 کاربر *{escape_md(u_name)}* (`{target_uid}`) با موفقیت غیرفعال و از لیگ خارج شد.",
    )
    await callback.answer("حذف شد.")


# --- دستور st و دکمه شیشه‌ای adm_menu_stats (آمار کلی مجموعه) ---
async def _send_group_stats(bot: Bot, chat_id: int | str, user_id: str) -> None:
    today_str = DateService.today_str()
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
        group_ids = get_admin_group_ids(db, user_id)
        users = (
            db.query(User)
            .filter(User.group_id.in_(group_ids), User.is_active == True)
            .all()
        )
        total_users = len(users)
        active_today = sum(1 for u in users if u.last_log_date == today_str and u.today_minutes > 0)
        total_mins = sum(int(u.total_minutes or 0) for u in users)
        total_pages = sum(int(u.total_pages or 0) for u in users)
        avg_mins = round(total_mins / total_users, 1) if total_users > 0 else 0.0

        best_user: Optional[User] = None
        if users:
            best_user = max(
                users,
                key=lambda u: (float(u.points or 0.0), int(u.total_minutes or 0)),
            )

        best_txt = (
            f"{escape_md(best_user.name)} ({best_user.points} امتیاز | {best_user.total_minutes} دقیقه)"
            if best_user
            else "-"
        )

    text = (
        "📊 *آمار کلی مجموعه تحت مدیریت شما*\n"
        "───────────────────\n"
        f"👥 کل کاربران فعال: *{total_users}* نفر\n"
        f"✅ ثبت‌کنندگان مطالعه امروز: *{active_today}* نفر\n"
        f"⏱ مجموع زمان کل مطالعه: *{total_mins:,}* دقیقه\n"
        f"📄 مجموع صفحات کل: *{total_pages:,}* صفحه\n"
        f"📈 میانگین مطالعه هر نفر: *{avg_mins}* دقیقه\n"
        f"🥇 برترین کاربر فعلی: *{best_txt}*"
    )
    await safe_send_message(bot, chat_id, text)


@admin_router.message(StateFilter(None), F.text.func(lambda t: t and t.strip().lower() == "st"))
async def cmd_group_stats(message: Message) -> None:
    await _send_group_stats(message.bot, message.chat.id, str(message.from_user.id))


@admin_router.callback_query(F.data == "adm_menu_stats")
async def cb_menu_stats(callback: CallbackQuery) -> None:
    await _send_group_stats(callback.bot, callback.message.chat.id, str(callback.from_user.id))
    await callback.answer()


# --- توابع کمکی خروجی اکسل و هندلرهای ex / adm_menu_excel ---
def _collect_admin_league_ids_sync(user_id: str) -> Optional[List[str]]:
    """شناسه لیگ‌های فعال تحت مدیریت ادمین؛ None یعنی ادمین نیست (اجرا در ترد)"""
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return None
        group_ids = get_admin_group_ids(db, user_id)
        return [
            r[0]
            for r in db.query(League.id)
            .filter(
                League.group_id.in_(group_ids),
                League.is_deleted == False,
                League.is_active == True,
            )
            .order_by(League.id.asc())
            .all()
        ]


def _collect_league_export_sync(league_id: str) -> Optional[Dict[str, Any]]:
    """جمع‌آوری داده اکسل یک لیگ با خواندن دسته‌ای کاربران (اجرا در ترد با نشست مستقل)"""
    with get_db() as db:
        lg = db.get(League, league_id)
        if not lg or lg.is_deleted or not lg.is_active:
            return None
        cyc = get_or_create_active_cycle(db, lg)
        curr_day = DateService.calculate_league_day(cyc.start_shamsi or lg.start_shamsi)

        users_data: List[Dict[str, Any]] = []
        chunk_size = max(50, int(settings.DB_CHUNK_SIZE))
        last_id = ""
        while True:
            chunk = (
                db.query(User)
                .filter(
                    User.league_id == lg.id,
                    User.is_active == True,
                    User.id > last_id,
                )
                .order_by(User.id.asc())
                .limit(chunk_size)
                .all()
            )
            if not chunk:
                break
            last_id = chunk[-1].id
            users_data.extend(
                ReportService._extract_row_dict(u, league_floor=lg.floor) for u in chunk
            )
            db.expunge_all()

        return {
            "id": lg.id,
            "name": lg.name,
            "cycle_number": lg.cycle_number,
            "current_day": curr_day,
            "floor": lg.floor,
            "users_data": users_data,
        }


async def _send_active_leagues_excel(bot: Bot, chat_id: int | str, user_id: str) -> None:
    from handlers import safe_send_document

    league_ids = await asyncio.to_thread(_collect_admin_league_ids_sync, user_id)
    if league_ids is None:
        return
    if not league_ids:
        await safe_send_message(bot, chat_id, "📭 هیچ لیگ فعالی برای تولید اکسل یافت نشد.")
        return

    # هر بار فقط داده یک لیگ در حافظه است و پس از ارسال آزاد می‌شود
    for league_id in league_ids:
        task = await asyncio.to_thread(_collect_league_export_sync, league_id)
        if not task:
            continue

        file_path = ""
        try:
            file_path = await asyncio.to_thread(
                ReportService.generate_excel,
                league_name=task["name"],
                users_data=task["users_data"],
                cycle_number=task["cycle_number"],
                current_day=task["current_day"],
                league_floor=task["floor"],
            )
            task["users_data"] = []
            caption = f"📥 گزارش اکسل لیگ «{task['name']}»\n🏆 چله {task['cycle_number']} | روز {task['current_day']}"
            ok = await safe_send_document(
                bot,
                chat_id,
                file_path,
                caption=caption,
            )
            if not ok:
                logger.error(f"خطا در ارسال فایل اکسل لیگ {task['id']}")
                await safe_send_message(
                    bot,
                    chat_id,
                    f"❌ در ارسال فایل اکسل لیگ «{escape_md(task['name'])}» خطایی رخ داد.",
                )
        except Exception as exc:
            logger.error(f"خطا در تولید/ارسال اکسل لیگ {task['id']}: {exc}")
            await safe_send_message(
                bot,
                chat_id,
                f"❌ در تولید فایل اکسل لیگ «{escape_md(task['name'])}» خطایی رخ داد: {escape_md(str(exc))}",
            )
        finally:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass
            task = None

@admin_router.message(StateFilter(None), F.text.func(lambda t: t and t.strip().lower() == "ex"))
async def cmd_export_excel(message: Message) -> None:
    await _send_active_leagues_excel(message.bot, message.chat.id, str(message.from_user.id))


@admin_router.callback_query(F.data == "adm_menu_excel")
async def cb_menu_excel(callback: CallbackQuery) -> None:
    await _send_active_leagues_excel(
        callback.bot, callback.message.chat.id, str(callback.from_user.id)
    )
    await callback.answer()


def _build_cycle_history_excel_sync(group_ids: List[int]) -> str:
    """تولید همگام اکسل آرشیو تاریخچه چله‌ها در ترد جداگانه با نشست دیتابیس مستقل"""
    with get_db() as db:
        return ReportService.generate_cycle_history_excel(db, group_ids=group_ids)


# --- دستور sr (دریافت فایل اکسل آرشیو تاریخچه چله‌ها) ---
@admin_router.message(StateFilter(None), F.text.func(lambda t: t and t.strip().lower() == "sr"))
async def cmd_export_cycle_history_excel(message: Message) -> None:
    user_id = str(message.from_user.id)
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
        group_ids = get_admin_group_ids(db, user_id)

    file_path = await asyncio.to_thread(_build_cycle_history_excel_sync, group_ids)

    try:
        await message.bot.send_document(
            chat_id=message.chat.id,
            document=FSInputFile(file_path),
            caption="📚 فایل اکسل چندشیتی آرشیو تاریخچه چله‌های فعال و پایان‌یافته",
        )
    except Exception as exc:
        logger.error(f"خطا در ارسال اکسل تاریخچه چله‌ها: {exc}")
        await safe_reply(message, "❌ خطا در ارسال فایل اکسل آرشیو.")
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass


# --- دستور em (مدیریت لحن، واژه‌نامه و پیام‌های مجموعه) ---
@admin_router.message(StateFilter(None), F.text.func(lambda t: t and t.strip().lower() == "em"))
async def cmd_edit_messages_and_terms(message: Message, state: FSMContext) -> None:
    user_id = str(message.from_user.id)
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
        group_ids = get_admin_group_ids(db, user_id)
        groups = (
            db.query(Group)
            .filter(Group.id.in_(group_ids), Group.is_deleted == False)
            .order_by(Group.id.asc())
            .all()
        )
        if not groups:
            await safe_reply(message, "📭 هیچ مجموعه‌ای یافت نشد.")
            return

        await state.clear()
        if len(groups) == 1:
            g = groups[0]
            await safe_reply(
                message,
                f"🎨 *مدیریت لحن، واژه‌نامه و پیام‌های مجموعه {escape_md(g.name)}*\n"
                "لطفاً بخش موردنظر را انتخاب کنید:",
                reply_markup=_get_em_main_keyboard(g.id),
            )
            return

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"🏢 {g.name}",
                        callback_data=f"em_grp_{g.id}",
                    )
                ]
                for g in groups
            ]
        )
        await safe_reply(
            message,
            "🎨 لطفاً مجموعه موردنظر برای ویرایش واژه‌نامه و پیام‌ها را انتخاب کنید:",
            reply_markup=kb,
        )


@admin_router.callback_query(F.data.startswith("em_grp_"))
async def cb_em_select_group(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = str(callback.from_user.id)
    group_id = int(callback.data.replace("em_grp_", ""))
    with get_db() as db:
        if not is_user_admin(db, user_id, group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        grp = db.query(Group).filter(Group.id == group_id).first()
        g_name = grp.name if grp else str(group_id)

    await state.clear()
    text = (
        f"🎨 *مدیریت لحن، واژه‌نامه و پیام‌های مجموعه {escape_md(g_name)}*\n"
        "لطفاً بخش موردنظر را انتخاب کنید:"
    )
    try:
        await callback.message.edit_text(
            text, reply_markup=_get_em_main_keyboard(group_id), parse_mode="Markdown"
        )
    except Exception:
        await safe_send_message(
            callback.bot,
            callback.message.chat.id,
            text,
            reply_markup=_get_em_main_keyboard(group_id),
        )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("em_terms_"))
async def cb_em_terms_menu(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = str(callback.from_user.id)
    group_id = int(callback.data.replace("em_terms_", ""))
    with get_db() as db:
        if not is_user_admin(db, user_id, group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        kb = _get_em_terms_keyboard(db, group_id)

    await state.clear()
    text = (
        "⚙️ *تنظیم اصطلاحات اختصاصی مجموعه*\n\n"
        "برای تغییر هر اصطلاح روی دکمه ✏️ و برای بازگشت به عبارت پیش‌فرض روی 🔄 بزنید:"
    )
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        await safe_send_message(callback.bot, callback.message.chat.id, text, reply_markup=kb)
    await callback.answer()


@admin_router.callback_query(F.data.startswith("em_edterm_"))
async def cb_em_edit_term(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = str(callback.from_user.id)
    payload = callback.data.replace("em_edterm_", "")
    grp_str, term_key = payload.split("_", 1)
    group_id = int(grp_str)

    with get_db() as db:
        if not is_user_admin(db, user_id, group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        curr_val = MessageService.get_term(db, group_id, term_key)

    label = TERM_LABELS.get(term_key, term_key)
    await state.update_data(em_group_id=group_id, em_term_key=term_key)
    await state.set_state(AdminStates.em_waiting_term_value)
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        f"✏️ ویرایش اصطلاح *{escape_md(label)}*\n"
        f"مقدار فعلی: «{escape_md(curr_val)}»\n\n"
        "لطفاً معادل جدید موردنظر خود را ارسال کنید:",
        reply_markup=get_inline_cancel_keyboard(),
    )
    await callback.answer()


@admin_router.message(AdminStates.em_waiting_term_value)
async def process_em_new_term(message: Message, state: FSMContext) -> None:
    new_val = (message.text or "").strip()
    if not new_val or len(new_val) > 50:
        await safe_reply(message, "❌ عبارت وارد شده باید بین ۱ تا ۵۰ کاراکتر باشد. مجدداً وارد کنید:")
        return

    data = await state.get_data()
    group_id = int(data.get("em_group_id", 1))
    term_key = data.get("em_term_key", "meesaq")

    with get_db() as db:
        MessageService.set_term(db, group_id, term_key, new_val)
        kb = _get_em_terms_keyboard(db, group_id)

    await state.clear()
    await safe_reply(
        message,
        f"✅ اصطلاح *{escape_md(TERM_LABELS.get(term_key, term_key))}* به «{escape_md(new_val)}» تغییر یافت.",
        reply_markup=kb,
    )


@admin_router.callback_query(F.data.startswith("em_rstterm_"))
async def cb_em_reset_term(callback: CallbackQuery) -> None:
    user_id = str(callback.from_user.id)
    payload = callback.data.replace("em_rstterm_", "")
    grp_str, term_key = payload.split("_", 1)
    group_id = int(grp_str)

    with get_db() as db:
        if not is_user_admin(db, user_id, group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        MessageService.reset_term(db, group_id, term_key)
        kb = _get_em_terms_keyboard(db, group_id)

    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass
    await callback.answer("به مقدار پیش‌فرض بازنشانی شد.")


@admin_router.callback_query(F.data.startswith("em_msgs_"))
async def cb_em_msgs_menu(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = str(callback.from_user.id)
    group_id = int(callback.data.replace("em_msgs_", ""))
    with get_db() as db:
        if not is_user_admin(db, user_id, group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return

    await state.clear()
    text = (
        "💬 *ویرایش پیام‌های ارسالی به اعضای مجموعه*\n\n"
        "برای تغییر متن هر پیام روی ✏️ و برای بازنشانی به متن پیش‌فرض روی 🔄 کلیک کنید:"
    )
    kb = _get_em_msgs_keyboard(group_id)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        await safe_send_message(callback.bot, callback.message.chat.id, text, reply_markup=kb)
    await callback.answer()


@admin_router.callback_query(F.data.startswith("em_edmsg_"))
async def cb_em_edit_msg(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = str(callback.from_user.id)
    payload = callback.data.replace("em_edmsg_", "")
    grp_str, msg_key = payload.split("_", 1)
    group_id = int(grp_str)

    with get_db() as db:
        if not is_user_admin(db, user_id, group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        curr_msg = MessageService.get_message(db, group_id, msg_key, apply_group_terms=False)

    label = MESSAGE_LABELS.get(msg_key, msg_key)
    await state.update_data(em_group_id=group_id, em_msg_key=msg_key)
    await state.set_state(AdminStates.em_waiting_msg_value)
    await safe_send_message(
        callback.bot,
        callback.message.chat.id,
        f"✏️ ویرایش *{escape_md(label)}*\n\n"
        f"📌 متن فعلی:\n{curr_msg}\n\n"
        "لطفاً متن جدید را ارسال کنید:",
        reply_markup=get_inline_cancel_keyboard(),
        parse_mode=None,
    )
    await callback.answer()


@admin_router.message(AdminStates.em_waiting_msg_value)
async def process_em_new_msg(message: Message, state: FSMContext) -> None:
    new_text = (message.text or "").strip()
    if len(new_text) < 3:
        await safe_reply(message, "❌ متن پیام بسیار کوتاه است. لطفاً مجدداً وارد کنید:")
        return

    data = await state.get_data()
    group_id = int(data.get("em_group_id", 1))
    msg_key = data.get("em_msg_key", "welcome")

    with get_db() as db:
        MessageService.set_message(db, group_id, msg_key, new_text)

    await state.clear()
    await safe_reply(
        message,
        f"✅ متن «{MESSAGE_LABELS.get(msg_key, msg_key)}» با موفقیت ذخیره شد.",
        reply_markup=_get_em_msgs_keyboard(group_id),
    )


@admin_router.callback_query(F.data.startswith("em_rstmsg_"))
async def cb_em_reset_msg(callback: CallbackQuery) -> None:
    user_id = str(callback.from_user.id)
    payload = callback.data.replace("em_rstmsg_", "")
    grp_str, msg_key = payload.split("_", 1)
    group_id = int(grp_str)

    with get_db() as db:
        if not is_user_admin(db, user_id, group_id):
            await callback.answer("عدم دسترسی", show_alert=True)
            return
        MessageService.reset_message(db, group_id, msg_key)

    await callback.answer("پیام به حالت پیش‌فرض بازگردانی شد.", show_alert=True)


# ===========================================================================
# دستورات کمکی و تست ادمین (با اسلش)
# ===========================================================================
@admin_router.message(Command("leagues"))
async def cmd_slash_leagues(message: Message) -> None:
    user_id = str(message.from_user.id)
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
        group_ids = get_admin_group_ids(db, user_id)
        leagues = (
            db.query(League)
            .filter(League.group_id.in_(group_ids), League.is_deleted == False)
            .order_by(League.id.asc())
            .all()
        )
        if not leagues:
            await safe_reply(message, "📭 لیگی یافت نشد.")
            return
        lines = ["📋 *فهرست لیگ‌ها و وضعیت آرشیو:*\n"]
        for l in leagues:
            arch = "✅ فعال" if l.archive_enabled else "❌ غیرفعال"
            lines.append(
                f"🔹 `{l.id}` | *{escape_md(l.name)}* | چله {l.cycle_number} | کف: {l.floor} دقیقه | آرشیو: {arch}"
            )
    await safe_reply(message, "\n".join(lines))


@admin_router.message(Command("archive_exclude"))
async def cmd_archive_exclude(message: Message) -> None:
    user_id = str(message.from_user.id)
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await safe_reply(message, "⚠️ فرمت صحیح: `/archive_exclude <league_id>`")
        return
    league_id = parts[1].strip()
    with get_db() as db:
        lg = db.query(League).filter(League.id == league_id).first()
        if not lg or not is_user_admin(db, user_id, lg.group_id):
            await safe_reply(message, "❌ لیگ یافت نشد یا دسترسی ندارید.")
            return
        lg.archive_enabled = False
        db.commit()
        l_name = lg.name
    await safe_reply(message, f"🔕 ارسال آرشیو خودکار برای لیگ *{escape_md(l_name)}* (`{league_id}`) غیرفعال شد.")


@admin_router.message(Command("archive_include"))
async def cmd_archive_include(message: Message) -> None:
    user_id = str(message.from_user.id)
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await safe_reply(message, "⚠️ فرمت صحیح: `/archive_include <league_id>`")
        return
    league_id = parts[1].strip()
    with get_db() as db:
        lg = db.query(League).filter(League.id == league_id).first()
        if not lg or not is_user_admin(db, user_id, lg.group_id):
            await safe_reply(message, "❌ لیگ یافت نشد یا دسترسی ندارید.")
            return
        lg.archive_enabled = True
        db.commit()
        l_name = lg.name
    await safe_reply(message, f"🔔 ارسال آرشیو خودکار برای لیگ *{escape_md(l_name)}* (`{league_id}`) فعال شد.")


@admin_router.message(Command("datetest"))
async def cmd_datetest(message: Message) -> None:
    user_id = str(message.from_user.id)
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
    now_ir = DateService.now_iran()
    await safe_reply(
        message,
        f"🕒 *تست زمان و تاریخ سرور (ایران):*\n\n"
        f"📅 تاریخ شمسی امروز: `{DateService.today_shamsi()}`\n"
        f"📆 تاریخ میلادی امروز: `{DateService.today_str()}`\n"
        f"⏪ تاریخ میلادی دیروز: `{DateService.yesterday_str()}`\n"
        f"⏰ ساعت دقیق تهران: `{now_ir.strftime('%H:%M:%S')}`",
    )


@admin_router.message(Command("test_help"))
async def cmd_test_help(message: Message) -> None:
    user_id = str(message.from_user.id)
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
    text = (
        "🧪 *راهنمای دستورات تست و عیب‌یابی ادمین:*\n\n"
        "🔹 `/leagues` : نمایش کدها و وضعیت آرشیو لیگ‌ها\n"
        "🔹 `/datetest` : بررسی ساعت ایران و تقویم شمسی\n"
        "🔹 `/test_startup` : تست ارسال پیام فعال‌سازی (استارتاپ) به ادمین‌ها\n"
        "🔹 `/test_status` : وضعیت آخرین اجرای جاب‌های روزانه\n"
        "🔹 `/test_reminder` : اجرای دستی یادآوری شبانه (۲۲:۰۰)\n"
        "🔹 `/test_leaderboard` : ارسال جدول همه لیگ‌های فعال به شما\n"
        "🔹 `/test_archive` : اجرای دستی گزارش بامداد ادمین (۰۱:۰۰)\n"
        "🔹 `/test_report` : اجرای دستی گزارش هفتگی جمعه (۰۲:۰۰)\n"
        "🔹 `/test_daily` : اجرای دستی کارنامه صبحگاهی اعضا (۰۸:۰۰)\n"
        "🔹 `/test_all` : اجرای ترتیبی جاب‌های تست\n"
        "🔹 `/archive_exclude <id>` : حذف لیگ از گزارش آرشیو\n"
        "🔹 `/archive_include <id>` : افزودن لیگ به گزارش آرشیو"
    )
    await safe_reply(message, text)


@admin_router.message(Command("test_status"))
async def cmd_test_status(message: Message) -> None:
    user_id = str(message.from_user.id)
    from database import get_system_state

    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
        last_midnight = get_system_state(db, "last_daily_job_date", "اجرا نشده")
        last_admin_rep = get_system_state(db, "last_daily_admin_report_date", "اجرا نشده")
        last_user_rep = get_system_state(db, "last_daily_user_report_date", "اجرا نشده")
        last_rem = get_system_state(db, "last_reminder_date", "اجرا نشده")

    text = (
        "📊 *وضعیت اجرای جاب‌های زمان‌بندی‌شده:*\n\n"
        f"🌙 جاب نیمه‌شب (00:00): `{last_midnight}`\n"
        f"🕵️ گزارش بامداد ادمین (01:00): `{last_admin_rep}`\n"
        f"☀️ کارنامه صبحگاهی کاربران (08:00): `{last_user_rep}`\n"
        f"⏰ یادآوری شبانه (22:00): `{last_rem}`"
    )
    await safe_reply(message, text)


@admin_router.message(Command("test_reminder"))
async def cmd_test_reminder(message: Message) -> None:
    user_id = str(message.from_user.id)
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
    from handlers import send_study_reminders

    await safe_reply(message, "⏳ در حال اجرای دستی یادآوری شبانه...")
    await send_study_reminders(message.bot, force=True)
    await safe_reply(message, "✅ اجرای یادآوری شبانه به پایان رسید.")


@admin_router.message(Command("test_leaderboard"))
async def cmd_test_leaderboard(message: Message) -> None:
    user_id = str(message.from_user.id)
    from handlers import format_league_leaderboard, send_text_chunks

    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
        group_ids = get_admin_group_ids(db, user_id)
        leagues = (
            db.query(League)
            .filter(
                League.group_id.in_(group_ids),
                League.is_deleted == False,
                League.is_active == True,
            )
            .all()
        )
        tables = [format_league_leaderboard(db, lg) for lg in leagues]

    for tbl in tables:
        await send_text_chunks(message.bot, message.chat.id, tbl)


@admin_router.message(Command("test_archive"))
async def cmd_test_archive(message: Message) -> None:
    user_id = str(message.from_user.id)
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
    from handlers import send_daily_admin_reports

    await safe_reply(message, "⏳ در حال ارسال گزارش آرشیو روزانه ادمین‌ها...")
    await send_daily_admin_reports(message.bot, force=True)
    await safe_reply(message, "✅ گزارش آرشیو ادمین‌ها ارسال شد.")


@admin_router.message(Command("test_report"))
async def cmd_test_weekly_report(message: Message) -> None:
    user_id = str(message.from_user.id)
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
    from weekly_report import send_weekly_reports

    await safe_reply(message, "⏳ در حال تولید و ارسال گزارش هفتگی و اکسل...")
    await send_weekly_reports(message.bot, force=True)
    await safe_reply(message, "✅ گزارش هفتگی ارسال شد.")


@admin_router.message(Command("test_daily"))
async def cmd_test_daily_user_report(message: Message) -> None:
    user_id = str(message.from_user.id)
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
    from handlers import send_daily_user_reports

    await safe_reply(message, "⏳ در حال ارسال کارنامه صبحگاهی به کاربران...")
    await send_daily_user_reports(message.bot, force=True)
    await safe_reply(message, "✅ کارنامه صبحگاهی ارسال شد.")


@admin_router.message(Command("test_all"))
async def cmd_test_all_jobs(message: Message) -> None:
    user_id = str(message.from_user.id)
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
    from handlers import (
        midnight_job,
        send_daily_admin_reports,
        send_daily_user_reports,
        send_study_reminders,
    )
    from weekly_report import send_weekly_reports

    await safe_reply(message, "🚀 شروع اجرای ترتیبی تمام جاب‌های سیستم...")
    await midnight_job(message.bot, force=True)
    await send_daily_admin_reports(message.bot, force=True)
    await send_weekly_reports(message.bot, force=True)
    await send_daily_user_reports(message.bot, force=True)
    await send_study_reminders(message.bot, force=True)
    await safe_reply(message, "✅ تمام ۵ جاب اصلی با موفقیت اجرا شدند.")


@admin_router.message(Command("test_startup"))
async def cmd_test_startup_notification(message: Message) -> None:
    user_id = str(message.from_user.id)
    with get_db() as db:
        if not is_user_admin(db, user_id):
            return
    from handlers import send_startup_notification

    await safe_reply(message, "⏳ در حال ارسال پیام تست فعال‌سازی (استارتاپ) به ادمین‌ها...")
    count = await send_startup_notification(message.bot)
    await safe_reply(
        message,
        f"✅ پیام فعال‌سازی ربات با تاریخ شمسی و ساعت ایران برای {count} نفر از ادمین‌ها ارسال گردید.",
    )
