import os
import time
import asyncio
import logging
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from typing import Any, List, Optional, Dict, Tuple

from aiogram import Router, F, Bot
from aiogram.exceptions import (
    TelegramRetryAfter,
    TelegramBadRequest,
    TelegramForbiddenError,
)
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardRemove,
    FSInputFile,
)
from sqlalchemy import func
from sqlalchemy.orm import Session, load_only

from config import settings
from database import (
    get_db,
    get_active_user,
    set_active_user_id,
    get_user_profiles,
    generate_new_profile_id,
    get_or_create_active_cycle,
    is_user_admin,
    get_system_state,
    set_system_state,
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
from message_service import MessageService
from keyboards import (
    get_start_menu,
    get_main_menu,
    get_study_edit_menu,
    get_league_selection,
    get_cancel_league_confirm,
    get_profile_switch_keyboard,
    get_cancel_or_back_keyboard,
)

logger = logging.getLogger(__name__)

user_router = Router(name="user_router")


class StudyStates(StatesGroup):
    """استیت‌های ثبت‌نام و ثبت مطالعه کاربران"""

    waiting_for_group_password = State()
    register_name = State()
    register_last_name = State()
    waiting_for_minutes = State()
    waiting_for_pages = State()


# کلمات رزرو شده که نباید به عنوان نام کوچک یا نام خانوادگی پذیرفته شوند
RESERVED_MENU_TEXTS = {
    "/start",
    "/admin",
    "/history",
    "/join_group",
    "/cancel_my_league",
    "🚀 شروع ثبت نام",
    "📝 ثبت مطالعه امروز",
    "🏆 جدول لیگ",
    "⏳ ثبت مطالعه دیروز (با کسر ۵۰٪ امتیاز)",
    "👤 حساب کاربری و سهمیه ها",
    "راهنما",
    "🔄 تغییر لیگ فعال",
    "⚙️ منوی مدیریت ادمین",
    "🔄 ویرایش مطالعه امروز",
    "➕ افزودن زمان به ثبت امروز",
    "🔙 بازگشت",
}


# ===========================================================================
# توابع کمکی ارسال پیام، قفل همزمانی کاربران و بررسی شرایط ثبت با تاخیر
# ===========================================================================
_user_locks: Dict[str, asyncio.Lock] = {}

PWD_MAX_FAILS_PER_USER = 5
PWD_USER_LOCK_SECONDS = 600
PWD_GLOBAL_MAX_FAILS_PER_HOUR = 100
PWD_GLOBAL_LOCK_SECONDS = 3600


def _state_int(db: Session, key: str, default: int = 0) -> int:
    try:
        return int(get_system_state(db, key, str(default)) or default)
    except ValueError:
        return default


def _pwd_is_locked(db: Session, tg_key: str) -> bool:
    """بررسی قفل پایدار تلاش رمز: هم برای همین کاربر و هم قفل سراسری"""
    now = int(time.time())
    if now < _state_int(db, f"pwd_lock_{tg_key}"):
        return True
    return False


def _pwd_register_failure(db: Session, tg_key: str) -> str:
    """ثبت یک تلاش ناموفق. خروجی: 'ok' یا 'user_locked' یا 'global_locked'"""
    now = int(time.time())

    # شمارنده سراسری (پنجره ۱ ساعته)
    g_start = _state_int(db, "pwd_global_start")
    g_count = _state_int(db, "pwd_global_count")
    if g_start == 0 or now - g_start > 3600:
        g_start, g_count = now, 0
    g_count += 1
    set_system_state(db, "pwd_global_start", str(g_start))
    set_system_state(db, "pwd_global_count", str(g_count))
    if g_count >= PWD_GLOBAL_MAX_FAILS_PER_HOUR:
        # فقط هشدار لاگ؛ قفل سراسری حذف شد تا یک مهاجم نتواند ثبت‌نام همه را مسدود کند
        set_system_state(db, "pwd_global_count", "0")
        logger.warning(
            "Suspicious activity: too many failed group-password attempts in the last hour."
        )

    # شمارنده اختصاصی کاربر
    fails = _state_int(db, f"pwd_fail_{tg_key}") + 1
    if fails >= PWD_MAX_FAILS_PER_USER:
        set_system_state(db, f"pwd_fail_{tg_key}", "0")
        set_system_state(db, f"pwd_lock_{tg_key}", str(now + PWD_USER_LOCK_SECONDS))
        return "user_locked"
    set_system_state(db, f"pwd_fail_{tg_key}", str(fails))
    return "ok"


def _get_user_lock(user_key: str | int) -> asyncio.Lock:
    """دریافت قفل اختصاصی هر کاربر جهت جلوگیری از شرایط رقابتی (Race Condition)"""
    key = str(user_key).strip()
    lock = _user_locks.get(key)
    if lock is None:
        if len(_user_locks) > 5000:
            for stale_key in [k for k, lk in _user_locks.items() if not lk.locked()]:
                _user_locks.pop(stale_key, None)
        lock = asyncio.Lock()
        _user_locks[key] = lock
    return lock


async def safe_send(
    bot: Bot,
    chat_id: int | str,
    text: str,
    reply_markup=None,
    parse_mode: Optional[str] = "Markdown",
) -> Optional[Message]:
    """ارسال ایمن پیام با مدیریت خطای FloodWait و خطای احتمالی Markdown"""
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
            logger.debug(f"خطا پس از انتظار FloodWait در ارسال به {chat_id}: {retry_exc}")
            return None
    except TelegramForbiddenError:
        logger.debug(f"کاربر {chat_id} ربات را بلاک کرده یا چت در دسترس نیست.")
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
            logger.debug(f"عدم امکان ارسال پیام بدون فرمت به {chat_id}: {exc}")
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
            logger.debug(f"عدم امکان ارسال پیام به {chat_id}: {exc}")
            return None


async def safe_answer(
    message: Message,
    text: str,
    reply_markup=None,
    parse_mode: Optional[str] = "Markdown",
) -> Optional[Message]:
    """پاسخ ایمن به پیام کاربر با مدیریت FloodWait و خطای احتمالی Markdown"""
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
            logger.debug(f"خطا پس از انتظار FloodWait در پاسخ به پیام: {retry_exc}")
            return None
    except TelegramBadRequest:
        try:
            return await message.answer(
                text=text, reply_markup=reply_markup, parse_mode=None
            )
        except Exception as exc:
            logger.debug(f"عدم امکان پاسخ بدون فرمت به پیام: {exc}")
            return None
    except Exception:
        try:
            return await message.answer(
                text=text, reply_markup=reply_markup, parse_mode=None
            )
        except Exception as exc:
            logger.debug(f"عدم امکان پاسخ به پیام: {exc}")
            return None


class BroadcastThrottle:
    """
    کنترل نرخ ارسال انبوه (Staggered Sending):
    بین هر پیام msg_delay ثانیه و پس از هر batch_size پیام batch_pause ثانیه توقف می‌کند
    تا نرخ ارسال حدود ۲۰ تا ۳۰ پیام در ثانیه بماند.
    """

    def __init__(
        self,
        batch_size: Optional[int] = None,
        msg_delay: Optional[float] = None,
        batch_pause: Optional[float] = None,
    ) -> None:
        self.batch_size = max(
            1, int(batch_size if batch_size is not None else settings.BROADCAST_BATCH_SIZE)
        )
        self.msg_delay = max(
            0.0, float(msg_delay if msg_delay is not None else settings.BROADCAST_MSG_DELAY)
        )
        self.batch_pause = max(
            0.0, float(batch_pause if batch_pause is not None else settings.BROADCAST_BATCH_PAUSE)
        )
        self._count = 0

    async def tick(self) -> None:
        """فراخوانی پس از هر ارسال؛ تاخیر کنترل‌شده بین پیام‌ها و دسته‌ها"""
        self._count += 1
        if self.msg_delay > 0:
            await asyncio.sleep(self.msg_delay)
        if self.batch_pause > 0 and self._count % self.batch_size == 0:
            await asyncio.sleep(self.batch_pause)


async def safe_send_document(
    bot: Bot,
    chat_id: int | str,
    file_path: str,
    caption: Optional[str] = None,
    throttle: Optional[BroadcastThrottle] = None,
) -> bool:
    """ارسال ایمن سند با یک بار تلاش مجدد پس از TelegramRetryAfter؛ هرگز استثنا پرتاب نمی‌کند"""
    ok = False
    for _attempt in range(2):
        try:
            await bot.send_document(
                chat_id=chat_id,
                document=FSInputFile(file_path),
                caption=caption,
            )
            ok = True
            break
        except TelegramRetryAfter as exc:
            await asyncio.sleep(min(exc.retry_after, 30))
            continue
        except TelegramForbiddenError:
            break
        except Exception as exc:
            logger.warning(f"عدم امکان ارسال سند به {chat_id}: {exc}")
            break
    if throttle is not None:
        await throttle.tick()
    return ok


async def dispatch_outbox(
    bot: Bot,
    outbox: List[Tuple[str, str, Any]],
    throttle: Optional[BroadcastThrottle] = None,
) -> int:
    """
    ارسال پلکانی لیستی از (chat_id, text, reply_markup).
    خطای هر پیام فقط همان پیام را رد می‌کند و حلقه ادامه می‌یابد. خروجی: تعداد ارسال موفق.
    """
    throttle = throttle or BroadcastThrottle()
    sent = 0
    for chat_id, text, markup in outbox:
        try:
            res = await safe_send(bot, chat_id, text, reply_markup=markup)
            if res:
                sent += 1
        except Exception as exc:
            logger.warning(f"خطای پیش‌بینی‌نشده در ارسال به {chat_id}: {exc}")
        await throttle.tick()
    return sent


async def send_text_chunks(
    bot: Bot,
    chat_id: int | str,
    full_text: str,
    max_len: int = 3500,
    reply_markup=None,
    throttle: Optional[BroadcastThrottle] = None,
) -> None:
    """تقسیم خط‌به‌خط متن‌های طولانی (بیش از ۳۵۰۰ کاراکتر) و ارسال متوالی آن‌ها (با throttle اختیاری)"""
    if len(full_text) <= max_len:
        await safe_send(bot, chat_id, full_text, reply_markup=reply_markup)
        if throttle is not None:
            await throttle.tick()
        return

    lines: List[str] = []
    for raw_line in full_text.splitlines():
        if len(raw_line) <= max_len:
            lines.append(raw_line)
        else:
            lines.extend(
                raw_line[i : i + max_len] for i in range(0, len(raw_line), max_len)
            )
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1
        if current_len + line_len > max_len and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_len = line_len
        else:
            current_chunk.append(line)
            current_len += line_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    for idx, ch in enumerate(chunks):
        kb = reply_markup if idx == len(chunks) - 1 else None
        await safe_send(bot, chat_id, ch, reply_markup=kb)
        if throttle is not None:
            await throttle.tick()
def user_can_log_late(db: Session, user: Optional[User]) -> bool:
    """
    بررسی شرط فعال بودن دکمه «ثبت مطالعه دیروز (با کسر ۵۰٪ امتیاز)»:
    ۱. کاربر در لیگ فعال عضو باشد.
    ۲. روز جاری چله بزرگتر از ۱ باشد.
    ۳. تاریخ عضویت کاربر قبل از امروز باشد.
    ۴. برای تاریخ دیروز (yesterday_str) یا روزِ دیروز چله هیچ رکوردی در ActivityLog نداشته باشد.
    """
    if not user or not user.is_active or not user.league_id:
        return False

    league = (
        db.query(League)
        .filter(
            League.id == user.league_id,
            League.is_deleted == False,
            League.is_active == True,
        )
        .first()
    )
    if not league:
        return False

    cycle = get_or_create_active_cycle(db, league)
    raw_current_day = DateService.calculate_raw_league_day(
        cycle.start_shamsi or league.start_shamsi
    )
    yesterday_day = raw_current_day - 1
    if yesterday_day < 1 or yesterday_day > settings.LEAGUE_DURATION:
        return False

    yesterday_str = DateService.yesterday_str()

    if not DateService.user_joined_before_today(user):
        return False

    existing_log = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.user_id == user.id,
            ActivityLog.league_id == league.id,
            (ActivityLog.cycle_id == cycle.id)
            | (
                (ActivityLog.cycle_id == None)
                & (ActivityLog.cycle_number == league.cycle_number)
            ),
            (ActivityLog.log_date == yesterday_str)
            | (ActivityLog.league_day == yesterday_day),
            ActivityLog.minutes > 0,
        )
        .first()
    )
    return existing_log is None


def build_user_main_menu(db: Session, telegram_id: str | int, active_user: Optional[User] = None):
    """ساخت کیبورد منوی اصلی متناسب با وضعیت فعلی کاربر"""
    tg_id = str(telegram_id).strip()
    if active_user is None:
        active_user = get_active_user(db, tg_id)
    profiles = get_user_profiles(db, tg_id, only_active=True)
    is_adm = is_user_admin(db, tg_id)
    can_late = user_can_log_late(db, active_user) if active_user else False
    return get_main_menu(
        is_admin=is_adm,
        has_multiple_profiles=(len(profiles) > 1),
        can_log_late=can_late,
    )


def format_league_leaderboard(
    db: Session, league: League, exclude_user_ids: Optional[set] = None
) -> str:
    """
    ساخت متن جدول آنلاین لیگ مطابق فرمت استاندارد:
    👑 *جدول آنلاین لیگ: {league.name}* 🌸
    🏆 چله {cycle.cycle_number} | روز {current_day} از 40
    """
    cycle = get_or_create_active_cycle(db, league)
    current_day = DateService.calculate_league_day(
        cycle.start_shamsi or league.start_shamsi
    )
    users = (
        db.query(User)
        .filter(User.league_id == league.id, User.is_active == True)
        .all()
    )
    if exclude_user_ids:
        users = [u for u in users if u.id not in exclude_user_ids]
    ranked = ScoringService.rank_users(users, league.floor)

    header = (
        f"👑 *جدول آنلاین لیگ: {escape_md(league.name)}* 🌸\n"
        f"🏆 چله {cycle.cycle_number} | روز {current_day} از {settings.LEAGUE_DURATION}\n\n"
        f" رتبه | نام | امتیاز | غیبت | عدم اعلام\n"
        f"-------------------------------------------------------"
    )
    lines = [header]

    if not ranked:
        lines.append("📭 هنوز عضوی در این لیگ ثبت‌نام نکرده است.")
    else:
        for rank, u in ranked:
            if rank == 1:
                medal = "🥇"
            elif rank == 2:
                medal = "🥈"
            elif rank == 3:
                medal = "🥉"
            else:
                medal = f"🔹 {rank}"

            disp_name = escape_md(u.get_display_name())
            pts = round(float(u.points or 0.0), 1)
            abs_cnt = int(u.no_study_days or 0)
            late_cnt = len(AbsenceService.parse_days_list(u.late_days_list))
            lines.append(
                f"{medal} | {disp_name} | 🏆 {pts} | ❌ {abs_cnt} ⚠️ {late_cnt}"
            )

    raw_text = "\n".join(lines)
    return MessageService.apply_terms(db, league.group_id, raw_text)


# ===========================================================================
# ۶.۱. دستور /start، ثبت‌نام و عضویت در مجموعه جدید (/join_group)
# ===========================================================================
@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    tg_id = str(message.from_user.id)

    with get_db() as db:
        user = get_active_user(db, tg_id)
        if not user or not user.is_active:
            welcome_txt = MessageService.get_message(db, 1, "welcome")
            await safe_answer(message, welcome_txt, reply_markup=get_start_menu())
            return

        # اگر کاربر ثبت‌نام کرده اما هنوز لیگی انتخاب نکرده است
        if not user.league_id:
            leagues = (
                db.query(League)
                .filter(
                    League.group_id == user.group_id,
                    League.is_deleted == False,
                    League.is_active == True,
                )
                .all()
            )
            if leagues:
                joined_ids = {
                    p.league_id
                    for p in get_user_profiles(db, tg_id, only_active=True)
                    if p.league_id
                }
                available = [l for l in leagues if l.id not in joined_ids]
                if available:
                    prompt_txt = MessageService.apply_terms(
                        db, user.group_id, "🏆 لطفاً لیگ مدنظرتان را انتخاب کنید:"
                    )
                    await safe_answer(
                        message,
                        prompt_txt,
                        reply_markup=get_league_selection(
                            available, exclude_league_ids=joined_ids
                        ),
                    )
                else:
                    await safe_answer(
                        message,
                        "شما در حال حاضر در تمامی لیگ‌های فعال این مجموعه عضو هستید.",
                        reply_markup=build_user_main_menu(db, tg_id, user),
                    )
                return

        kb = build_user_main_menu(db, tg_id, user)
        league = (
            db.query(League).filter(League.id == user.league_id).first()
            if user.league_id
            else None
        )
        l_name = f" (لیگ فعال: *{escape_md(league.name)}*)" if league else ""
        welcome_back = MessageService.apply_terms(
            db,
            user.group_id,
            f"🌸 سلام *{escape_md(user.name)}* عزیز، خوش آمدید!{l_name}\n"
            "💡 برای عضویت در مجموعه جدید می‌توانید از دستور `/join_group` استفاده کنید.",
        )

    await safe_answer(message, welcome_back, reply_markup=kb)


@user_router.message(F.text == "🚀 شروع ثبت نام")
@user_router.message(Command("join_group"))
async def start_registration_or_new_group(message: Message, state: FSMContext) -> None:
    await state.clear()
    with get_db() as db:
        enter_pwd_txt = MessageService.get_message(db, 1, "enter_pwd")

    await state.set_state(StudyStates.waiting_for_group_password)
    await safe_answer(
        message,
        enter_pwd_txt,
        reply_markup=get_cancel_or_back_keyboard(show_back=False),
    )


@user_router.callback_query(F.data == "join_new_group_prompt")
async def cb_join_new_group_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    with get_db() as db:
        enter_pwd_txt = MessageService.get_message(db, 1, "enter_pwd")

    await state.set_state(StudyStates.waiting_for_group_password)
    await safe_send(
        callback.bot,
        callback.message.chat.id,
        enter_pwd_txt,
        reply_markup=get_cancel_or_back_keyboard(show_back=False),
    )
    await callback.answer()


@user_router.message(StudyStates.waiting_for_group_password)
async def process_group_password(message: Message, state: FSMContext) -> None:
    tg_key = str(message.from_user.id)
    with get_db() as db_chk:
        locked = _pwd_is_locked(db_chk, tg_key)
    if locked:
        await safe_answer(
            message,
            "⛔️ به دلیل تلاشهای ناموفق زیاد، موقتاً امکان وارد کردن رمز وجود ندارد. چند دقیقه دیگر تلاش کنید.",
        )
        return
    if (message.text or "").strip() in RESERVED_MENU_TEXTS:
        await safe_answer(
            message,
            "🔑 لطفاً رمز ورود مجموعه را وارد کنید یا با «❌ لغو عملیات» خارج شوید.",
        )
        return
    raw_pwd = DateService.normalize_digits(message.text or "")
    with get_db() as db:
        grp = (
            db.query(Group)
            .filter(Group.password == raw_pwd, Group.is_deleted == False)
            .first()
        )
        if not grp:
            verdict = _pwd_register_failure(db, tg_key)
            if verdict != "ok":
                await state.clear()
                await safe_answer(
                    message,
                    "⛔️ تعداد تلاشهای ناموفق زیاد بود. چند دقیقه دیگر دوباره تلاش کنید.",
                    reply_markup=get_start_menu(),
                )
                return
            await safe_answer(
                message,
                "❌ رمز عبور اشتباه است.\n\n"
                "💡 *راهنمایی*: رمز ورود، یک عدد اختصاصی است که باید آن را از مدیرِ مجموعه خود دریافت کرده باشید.\n\n"
                "لطفاً رمز را مجدداً وارد کنید:",
            )
            return
        group_id = grp.id

    with get_db() as db_ok:
        set_system_state(db_ok, f"pwd_fail_{message.from_user.id}", "0")
    await state.update_data(reg_group_id=group_id)
    await state.set_state(StudyStates.register_name)
    await safe_answer(message, "لطفاً فقط نام (کوچک) خود را وارد کنید:")


@user_router.message(StudyStates.register_name)
async def process_register_first_name(message: Message, state: FSMContext) -> None:
    first_name = (message.text or "").strip()
    if (
        len(first_name) < 2
        or first_name.startswith("/")
        or first_name in RESERVED_MENU_TEXTS
        or first_name.isdigit()
    ):
        await safe_answer(
            message,
            "❌ نام وارد شده معتبر نیست. لطفاً فقط نام (کوچک) خود را به صورت صحیح (حداقل ۲ حرف) وارد کنید:",
        )
        return

    await state.update_data(reg_first_name=first_name)
    await state.set_state(StudyStates.register_last_name)
    await safe_answer(message, "لطفاً نام خانوادگی خود را وارد کنید:")


@user_router.message(StudyStates.register_last_name)
async def process_register_last_name(message: Message, state: FSMContext) -> None:
    last_name = (message.text or "").strip()
    if (
        len(last_name) < 2
        or last_name.startswith("/")
        or last_name in RESERVED_MENU_TEXTS
        or last_name.isdigit()
    ):
        await safe_answer(
            message,
            "❌ نام خانوادگی وارد شده معتبر نیست. لطفاً نام خانوادگی خود را به صورت صحیح وارد کنید:",
        )
        return

    data = await state.get_data()
    group_id = int(data.get("reg_group_id", 1))
    first_name = data.get("reg_first_name", "").strip()
    full_name = f"{first_name} {last_name}".strip()
    tg_id = str(message.from_user.id)

    with get_db() as db:
        # دریافت کلیه پروفایل‌های کاربر و به‌روزرسانی هماهنگ نام در تمام لیگ‌ها و مجموعه‌ها
        all_user_profiles = (
            db.query(User)
            .filter(User.telegram_id == tg_id)
            .order_by(User.created_at.asc())
            .all()
        )
        for prof in all_user_profiles:
            prof.name = full_name
            prof.first_name = first_name
            prof.last_name = last_name

        # بررسی اینکه آیا کاربر از قبل در این مجموعه پروفایل دارد
        existing_profile = next(
            (p for p in all_user_profiles if p.group_id == group_id),
            None,
        )
        if existing_profile and not existing_profile.league_id:
            existing_profile.is_active = True
            profile_id = existing_profile.id
        elif existing_profile and existing_profile.league_id:
            profile_id = existing_profile.id
        else:
            new_prof_id = generate_new_profile_id(db, tg_id, group_id=group_id)
            new_user = User(
                id=new_prof_id,
                telegram_id=tg_id,
                group_id=group_id,
                name=full_name,
                first_name=first_name,
                last_name=last_name,
                points=0.0,
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
            db.add(new_user)
            profile_id = new_prof_id

        db.commit()
        set_active_user_id(db, tg_id, profile_id)

        leagues = (
            db.query(League)
            .filter(
                League.group_id == group_id,
                League.is_deleted == False,
                League.is_active == True,
            )
            .order_by(League.id.asc())
            .all()
        )
        joined_league_ids = {
            p.league_id
            for p in get_user_profiles(db, tg_id, only_active=True)
            if p.league_id
        }
        available_leagues = [l for l in leagues if l.id not in joined_league_ids]
        kb_leagues = (
            get_league_selection(available_leagues, exclude_league_ids=joined_league_ids)
            if available_leagues
            else None
        )
        choose_league_msg = MessageService.apply_terms(
            db, group_id, "🏆 لطفاً لیگ مدنظرتان را انتخاب کنید:"
        )
        if leagues and not available_leagues:
            no_league_msg = MessageService.apply_terms(
                db,
                group_id,
                "شما در حال حاضر در تمامی لیگ‌های فعال این مجموعه عضو هستید.",
            )
        else:
            no_league_msg = MessageService.apply_terms(
                db,
                group_id,
                "⚠️ در حال حاضر هیچ لیگ فعالی در این مجموعه تعریف نشده است. لطفاً منتظر ایجاد لیگ توسط مدیر بمانید.",
            )
        main_kb = build_user_main_menu(db, tg_id)

    await state.clear()
    await safe_answer(message, f"✅ نام شما ثبت شد: «{escape_md(full_name)}»")

    if kb_leagues:
        await safe_answer(message, choose_league_msg, reply_markup=kb_leagues)
    else:
        await safe_answer(message, no_league_msg, reply_markup=main_kb)


# ===========================================================================
# ۶.۲. پیوستن به لیگ (join_{league_id})
# ===========================================================================
@user_router.callback_query(F.data.startswith("join_"))
async def cb_join_league(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data == "join_new_group_prompt":
        return
    async with _get_user_lock(str(callback.from_user.id)):
        await _cb_join_league_impl(callback, state)


async def _cb_join_league_impl(callback: CallbackQuery, state: FSMContext) -> None:
    league_id = callback.data.replace("join_", "")
    tg_id = str(callback.from_user.id)

    with get_db() as db:
        league = (
            db.query(League)
            .filter(
                League.id == league_id,
                League.is_deleted == False,
                League.is_active == True,
            )
            .first()
        )
        if not league:
            await callback.answer("این لیگ دیگر فعال نیست.", show_alert=True)
            return

        # ۱. اگر کاربر از قبل پروفایل فعالی در همین لیگ دارد، پروفایل فعال او به آن تغییر می‌یابد
        existing_in_league = (
            db.query(User)
            .filter(
                User.telegram_id == tg_id,
                User.league_id == league.id,
                User.is_active == True,
            )
            .first()
        )
        if existing_in_league:
            set_active_user_id(db, tg_id, existing_in_league.id)
            main_kb = build_user_main_menu(db, tg_id, existing_in_league)
            msg_txt = MessageService.apply_terms(
                db,
                league.group_id,
                f"🎉 شما به لیگ «{escape_md(league.name)}» منتقل شدید.\n"
                f"به جمع ما خوش آمدید {escape_md(existing_in_league.name)}! 🌸",
            )
            await safe_send(
                callback.bot, callback.message.chat.id, msg_txt, reply_markup=main_kb
            )
            await callback.answer()
            return

        # ۲. محاسبه روز جاری چله و امتیاز هدیه همگام‌سازی
        cycle = get_or_create_active_cycle(db, league)
        current_day = DateService.calculate_league_day(
            cycle.start_shamsi or league.start_shamsi
        )
        gift_points = (current_day - 1) * 10

        active_user = get_active_user(db, tg_id)
        if active_user and not active_user.league_id:
            target_user = active_user
            target_user.group_id = league.group_id
            target_user.league_id = league.id
            target_user.points = float(gift_points)
            target_user.total_minutes = 0
            target_user.total_pages = 0
            target_user.streak = 0
            target_user.no_study_days = 0
            target_user.absent_days_list = ""
            target_user.late_days_list = ""
            target_user.half_coupons = settings.DEFAULT_HALF_COUPONS
            target_user.one_min_coupons = settings.DEFAULT_ONE_MIN_COUPONS
            target_user.user_floor = None
            target_user.last_log_date = None
            target_user.today_minutes = 0
            target_user.today_pages = 0
            target_user.today_points = 0.0
            target_user.today_half_used = 0
            target_user.today_one_min_used = 0
            target_user.is_active = True
            target_user.created_at = datetime.now(timezone.utc)
            db.query(ActivityLog).filter(
                ActivityLog.user_id == target_user.id,
                ActivityLog.league_id == league.id,
                (ActivityLog.cycle_id == cycle.id)
                | (
                    (ActivityLog.cycle_id == None)
                    & (ActivityLog.cycle_number == league.cycle_number)
                ),
            ).delete(synchronize_session=False)
            db.commit()
        else:
            # ساخت پروفایل جدید برای عضویت در لیگ جدید
            existing_any = db.query(User).filter(User.telegram_id == tg_id).first()
            base_name = active_user.name if active_user else (existing_any.name if existing_any else (callback.from_user.full_name or "کاربر"))
            base_fn = active_user.first_name if active_user else (existing_any.first_name if existing_any else (callback.from_user.first_name or ""))
            base_ln = active_user.last_name if active_user else (existing_any.last_name if existing_any else (callback.from_user.last_name or ""))
            new_prof_id = generate_new_profile_id(
                db, tg_id, group_id=league.group_id, league_id=league.id
            )
            target_user = User(
                id=new_prof_id,
                telegram_id=tg_id,
                group_id=league.group_id,
                name=base_name,
                first_name=base_fn,
                last_name=base_ln,
                league_id=league.id,
                points=float(gift_points),
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
            db.add(target_user)
            db.commit()
            db.refresh(target_user)

        set_active_user_id(db, tg_id, target_user.id)
        main_kb = build_user_main_menu(db, tg_id, target_user)

        join_text = f"🎉 شما به لیگ «{escape_md(league.name)}» پیوستید."
        if gift_points > 0:
            join_text += f"\n✨ امتیاز هدیه همگام‌سازی شما با روز {current_day} لیگ: {gift_points} امتیاز!"

        welcome_user_text = f"به جمع ما خوش آمدید {escape_md(target_user.name)}! 🌸"

        join_text = MessageService.apply_terms(db, league.group_id, join_text)
        welcome_user_text = MessageService.apply_terms(db, league.group_id, welcome_user_text)

        admin_notif = (
            f"🆕 *عضو جدید ثبت نام کرد!*\n\n"
            f"👤 نام: {escape_md(target_user.name)}\n"
            f"🏆 لیگ: {escape_md(league.name)}\n"
            f"📍 روز لیگ: {current_day}\n"
            f"🎁 امتیاز هدیه: {gift_points}\n"
            f"🆔 آیدی: `{tg_id}`"
        )

    await state.clear()
    await safe_send(callback.bot, callback.message.chat.id, join_text)
    await safe_send(
        callback.bot,
        callback.message.chat.id,
        welcome_user_text,
        reply_markup=main_kb,
    )

    # اطلاع‌رسانی به مدیران ارشد (ADMIN_IDS)
    for adm_id in settings.ADMIN_IDS:
        await safe_send(callback.bot, adm_id, admin_notif)

    await callback.answer()


# ===========================================================================
# ۶.۴. ثبت مطالعه امروز، ویرایش، افزودن زمان، و ثبت مطالعه دیروز
# ===========================================================================
@user_router.message(F.text == "🔙 بازگشت")
async def handle_back_to_main_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    tg_id = str(message.from_user.id)
    with get_db() as db:
        user = get_active_user(db, tg_id)
        if not user or not user.is_active:
            await safe_answer(
                message,
                MessageService.get_message(db, 1, "welcome"),
                reply_markup=get_start_menu(),
            )
            return
        kb = build_user_main_menu(db, tg_id, user)
        txt = MessageService.apply_terms(db, user.group_id, "🏠 بازگشت به منوی اصلی:")

    await safe_answer(message, txt, reply_markup=kb)


@user_router.message(F.text == "📝 ثبت مطالعه امروز")
async def handle_log_study_today(message: Message, state: FSMContext) -> None:
    await state.clear()
    tg_id = str(message.from_user.id)
    today_str = DateService.today_str()

    with get_db() as db:
        user = get_active_user(db, tg_id)
        if not user or not user.is_active:
            await safe_answer(
                message,
                MessageService.get_message(db, 1, "welcome"),
                reply_markup=get_start_menu(),
            )
            return
        if not user.league_id:
            leagues = (
                db.query(League)
                .filter(
                    League.group_id == user.group_id,
                    League.is_deleted == False,
                    League.is_active == True,
                )
                .all()
            )
            joined_ids = {
                p.league_id
                for p in get_user_profiles(db, tg_id, only_active=True)
                if p.league_id
            }
            available = [l for l in leagues if l.id not in joined_ids]
            if not available:
                await safe_answer(
                    message,
                    "شما در حال حاضر در تمامی لیگ‌های فعال این مجموعه عضو هستید.",
                    reply_markup=build_user_main_menu(db, tg_id, user),
                )
                return
            await safe_answer(
                message,
                MessageService.apply_terms(
                    db, user.group_id, "🏆 لطفاً ابتدا لیگ مدنظرتان را انتخاب کنید:"
                ),
                reply_markup=get_league_selection(
                    available, exclude_league_ids=joined_ids
                ),
            )
            return

        league = db.query(League).filter(League.id == user.league_id).first()
        if not league or league.is_deleted or not league.is_active:
            await safe_answer(message, MessageService.apply_terms(db, user.group_id, "⚠️ لیگ فعلی شما فعال نیست."))
            return

        profiles = get_user_profiles(db, tg_id, only_active=True)
        league_text = (
            f" (در لیگ «{escape_md(league.name)}»)" if len(profiles) > 1 else ""
        )
        effective_floor = user.get_effective_floor(league.floor)

        # بررسی اینکه آیا امروز قبلاً مطالعه ثبت کرده است
        already_logged_today = (
            user.last_log_date == today_str and int(user.today_minutes or 0) > 0
        )
        if already_logged_today:
            can_late = user_can_log_late(db, user)
            msg_txt = (
                f"📊 {escape_md(user.name)} عزیز!\n\n"
                f"شما امروز{league_text} {user.today_minutes} دقیقه ثبت کرده‌اید.\n"
                f"چه اقدامی مدنظر دارید؟"
            )
            msg_txt = MessageService.apply_terms(db, user.group_id, msg_txt)
            await safe_answer(message, msg_txt, reply_markup=get_study_edit_menu(can_log_late=can_late))
            return

        prompt_txt = (
            f"⏱ {escape_md(user.name)} عزیز!\n\n"
            f"امروز{league_text} چند دقیقه مطالعه کردید؟\n"
            f"(میثاق شما: {effective_floor} دقیقه)\n\n"
            f"لطفاً فقط عدد بفرستید:"
        )
        prompt_txt = MessageService.apply_terms(db, user.group_id, prompt_txt)
        user_id = user.id

    await state.update_data(
        study_mode="fresh", study_user_id=user_id, study_init_date=today_str
    )
    await state.set_state(StudyStates.waiting_for_minutes)
    await safe_answer(
        message,
        prompt_txt,
        reply_markup=get_cancel_or_back_keyboard(show_back=False),
    )


@user_router.message(F.text == "🔄 ویرایش مطالعه امروز")
async def handle_edit_study_today(message: Message, state: FSMContext) -> None:
    await state.clear()
    tg_id = str(message.from_user.id)
    today_str = DateService.today_str()
    with get_db() as db:
        user = get_active_user(db, tg_id)
        if not user or not user.is_active or not user.league_id:
            return
        league = db.query(League).filter(League.id == user.league_id).first()
        if not league or league.is_deleted or not league.is_active:
            await safe_answer(
                message,
                MessageService.apply_terms(db, user.group_id, "⚠️ لیگ فعلی شما فعال نیست."),
            )
            return
        if user.last_log_date != today_str or int(user.today_minutes or 0) <= 0:
            # اگر کاربر هنوز امروز ثبتی ندارد (مثلاً از منوی شب قبل کلیک کرده)، به ثبت عادی هدایت شود
            await handle_log_study_today(message, state)
            return
        eff_floor = user.get_effective_floor(league.floor if league else 10)
        prompt_txt = (
            f"🔄 *ویرایش ثبت امروز*\n\n"
            f"⏱ {escape_md(user.name)} عزیز، کل زمان مطالعه امروز شما چند دقیقه بوده است؟\n"
            f"(این عدد جایگزین {user.today_minutes} دقیقه قبلی می‌شود | میثاق شما: {eff_floor} دقیقه)\n\n"
            f"لطفاً فقط عدد بفرستید:"
        )
        prompt_txt = MessageService.apply_terms(db, user.group_id, prompt_txt)
        user_id = user.id

    await state.update_data(
        study_mode="edit", study_user_id=user_id, study_init_date=today_str
    )
    await state.set_state(StudyStates.waiting_for_minutes)
    await safe_answer(
        message,
        prompt_txt,
        reply_markup=get_cancel_or_back_keyboard(show_back=False),
    )


@user_router.message(F.text == "➕ افزودن زمان به ثبت امروز")
async def handle_append_study_today(message: Message, state: FSMContext) -> None:
    await state.clear()
    tg_id = str(message.from_user.id)
    today_str = DateService.today_str()
    with get_db() as db:
        user = get_active_user(db, tg_id)
        if not user or not user.is_active or not user.league_id:
            return
        league = db.query(League).filter(League.id == user.league_id).first()
        if not league or league.is_deleted or not league.is_active:
            await safe_answer(
                message,
                MessageService.apply_terms(db, user.group_id, "⚠️ لیگ فعلی شما فعال نیست."),
            )
            return
        if user.last_log_date != today_str or int(user.today_minutes or 0) <= 0:
            await handle_log_study_today(message, state)
            return
        prompt_txt = (
            f"➕ *افزودن زمان به ثبت امروز*\n\n"
            f"⏱ {escape_md(user.name)} عزیز، چند دقیقه دیگر مطالعه کردید تا به {user.today_minutes} دقیقه قبلی امروز اضافه شود؟\n\n"
            f"لطفاً فقط عدد بفرستید:"
        )
        prompt_txt = MessageService.apply_terms(db, user.group_id, prompt_txt)
        user_id = user.id

    await state.update_data(
        study_mode="append", study_user_id=user_id, study_init_date=today_str
    )
    await state.set_state(StudyStates.waiting_for_minutes)
    await safe_answer(
        message,
        prompt_txt,
        reply_markup=get_cancel_or_back_keyboard(show_back=False),
    )


@user_router.message(F.text == "⏳ ثبت مطالعه دیروز (با کسر ۵۰٪ امتیاز)")
async def handle_log_study_yesterday(message: Message, state: FSMContext) -> None:
    await state.clear()
    tg_id = str(message.from_user.id)
    today_str = DateService.today_str()

    with get_db() as db:
        user = get_active_user(db, tg_id)
        if not user or not user_can_log_late(db, user):
            kb = build_user_main_menu(db, tg_id, user)
            err_txt = MessageService.apply_terms(
                db,
                user.group_id if user else 1,
                "⚠️ امکان ثبت مطالعه دیروز برای شما فعال نیست (قبلاً ثبت کرده‌اید یا روز اول چله است).",
            )
            await safe_answer(
                message,
                err_txt,
                reply_markup=kb,
            )
            return

        league = db.query(League).filter(League.id == user.league_id).first()
        profiles = get_user_profiles(db, tg_id, only_active=True)
        league_text = (
            f" (در لیگ «{escape_md(league.name)}»)"
            if (league and len(profiles) > 1)
            else ""
        )
        effective_floor = user.get_effective_floor(league.floor if league else 10)
        prompt_txt = (
            f"⏳ {escape_md(user.name)} عزیز!\n\n"
            f"شما در حال ثبت مطالعه برای *دیروز*{league_text} هستید.\n"
            f"(میثاق شما: {effective_floor} دقیقه - امتیاز این ثبت نصف محاسبه می‌شود)\n\n"
            f"دیروز چند دقیقه مطالعه کردید؟\n\n"
            f"لطفاً فقط عدد بفرستید:"
        )
        prompt_txt = MessageService.apply_terms(db, user.group_id, prompt_txt)
        user_id = user.id

    await state.update_data(
        study_mode="late", study_user_id=user_id, study_init_date=today_str
    )
    await state.set_state(StudyStates.waiting_for_minutes)
    await safe_answer(
        message,
        prompt_txt,
        reply_markup=get_cancel_or_back_keyboard(show_back=False),
    )


async def _dispatch_menu_interruption(message: Message, state: FSMContext, text_val: str) -> bool:
    """بررسی اینکه آیا کاربر در وسط استیت ثبت مطالعه یکی از دکمه‌های منوی اصلی یا دستورات را زده است"""
    if text_val == "📝 ثبت مطالعه امروز":
        await handle_log_study_today(message, state)
        return True
    if text_val == "⏳ ثبت مطالعه دیروز (با کسر ۵۰٪ امتیاز)":
        await handle_log_study_yesterday(message, state)
        return True
    if text_val == "🏆 جدول لیگ":
        await handle_league_leaderboard(message, state)
        return True
    if text_val == "👤 حساب کاربری و سهمیه ها":
        await handle_user_profile(message, state)
        return True
    if text_val in ("راهنما", "/help"):
        await handle_rules_help(message, state)
        return True
    if text_val == "🔄 تغییر لیگ فعال":
        await handle_switch_active_league_menu(message, state)
        return True
    if text_val in ("/history", "history"):
        await state.clear()
        await handle_cycle_history(message)
        return True
    if text_val == "/cancel_my_league":
        await state.clear()
        await cmd_cancel_my_league(message)
        return True
    if text_val == "🔙 بازگشت":
        await handle_back_to_main_menu(message, state)
        return True
    return False


@user_router.message(StudyStates.waiting_for_minutes)
async def process_study_minutes(message: Message, state: FSMContext) -> None:
    txt_clean = (message.text or "").strip()
    if await _dispatch_menu_interruption(message, state, txt_clean):
        return
    raw_mins = DateService.normalize_digits(txt_clean)
    if not raw_mins.isdigit() or not (1 <= int(raw_mins) <= 1440):
        await safe_answer(
            message,
            "❌ لطفاً زمان مطالعه را به صورت یک عدد صحیح بین 1 تا 1440 (دقیقه) وارد کنید:",
        )
        return

    minutes = int(raw_mins)
    data = await state.get_data()
    study_uid = data.get("study_user_id")
    tg_id = str(message.from_user.id)

    with get_db() as db:
        user = (
            db.query(User).filter(User.id == study_uid).first()
            if study_uid
            else get_active_user(db, tg_id)
        )
        user_display = escape_md(user.name) if user else "کاربر"

    await state.update_data(study_minutes=minutes)
    await state.set_state(StudyStates.waiting_for_pages)
    await safe_answer(
        message, f"📄 حالا {user_display} عزیز بفرمایید چند صفحه خواندید؟"
    )


@user_router.message(StudyStates.waiting_for_pages)
async def process_study_pages(message: Message, state: FSMContext) -> None:
    txt_clean = (message.text or "").strip()
    if await _dispatch_menu_interruption(message, state, txt_clean):
        return
    raw_pages = DateService.normalize_digits(txt_clean)
    if not raw_pages.isdigit() or not (0 <= int(raw_pages) <= 5000):
        await safe_answer(
            message,
            "❌ لطفاً تعداد صفحات را به صورت یک عدد صحیح بین 0 تا 5000 وارد کنید:",
        )
        return

    pages = int(raw_pages)
    tg_id = str(message.from_user.id)

    async with _get_user_lock(tg_id):
        current_state = await state.get_state()
        if current_state != StudyStates.waiting_for_pages.state:
            return

        data = await state.get_data()
        mode = data.get("study_mode", "fresh")
        input_minutes = int(data.get("study_minutes", 0))
        study_uid = data.get("study_user_id")
        init_date = data.get("study_init_date")

        now_ir = DateService.now_iran()
        today_str = DateService.today_str()
        yesterday_str = DateService.yesterday_str()

        # اگر کاربر قبل از نیمه‌شب دکمه ثبت را زده و پس از نیمه‌شب عدد صفحات را ارسال کرده است
        if init_date and init_date != today_str:
            await state.clear()
            with get_db() as db:
                u_curr = get_active_user(db, tg_id)
                kb = build_user_main_menu(db, tg_id, u_curr)
            await safe_answer(
                message,
                "⚠️ به دلیل عبور از نیمه‌شب و تغییر روز، عملیات قبلی لغو شد. لطفاً مجدداً گزینه موردنظر را از منوی اصلی انتخاب کنید.",
                reply_markup=kb,
            )
            return

        with get_db() as db:
            user = (
                db.query(User).filter(User.id == study_uid).first()
                if study_uid
                else get_active_user(db, tg_id)
            )
            if not user or not user.is_active or not user.league_id:
                await state.clear()
                await safe_answer(
                    message,
                    "❌ اطلاعات کاربری یا لیگ یافت نشد.",
                    reply_markup=build_user_main_menu(db, tg_id),
                )
                return

            league = db.query(League).filter(League.id == user.league_id).first()
            if not league or league.is_deleted or not league.is_active:
                await state.clear()
                await safe_answer(
                    message,
                    "❌ لیگ یافت نشد یا غیرفعال شده است.",
                    reply_markup=build_user_main_menu(db, tg_id, user),
                )
                return

            cycle = get_or_create_active_cycle(db, league)
            raw_current_day = DateService.calculate_raw_league_day(
                cycle.start_shamsi or league.start_shamsi
            )
            current_day = DateService.calculate_league_day(
                cycle.start_shamsi or league.start_shamsi
            )
            effective_floor = user.get_effective_floor(league.floor)

            if mode == "late":
                # بررسی مجدد مجاز بودن ثبت دیروز جهت جلوگیری از ثبت تکراری یا عبور از نیمه‌شب
                if not user_can_log_late(db, user):
                    kb = build_user_main_menu(db, tg_id, user)
                    err_msg = MessageService.apply_terms(
                        db,
                        user.group_id,
                        "⚠️ مطالعه دیروز قبلاً ثبت شده یا مهلت ثبت آن به پایان رسیده است.",
                    )
                    await state.clear()
                    await safe_answer(message, err_msg, reply_markup=kb)
                    return

                # ثبت با تاخیر برای دیروز (محاسبه از raw_current_day جهت پشتیبانی دقیق از روز ۴۰ در بامداد روز ۴۱)
                target_date_str = yesterday_str
                target_league_day = max(
                    1, min(settings.LEAGUE_DURATION, raw_current_day - 1)
                )

                pts, half_used, one_used, status_msg = ScoringService.calculate_points(
                    minutes=input_minutes,
                    floor=effective_floor,
                    half_coupons=user.half_coupons,
                    one_min_coupons=user.one_min_coupons,
                )
                pts = float(
                    (Decimal(str(pts)) / Decimal(2)).quantize(
                        Decimal("0.1"), rounding=ROUND_HALF_UP
                    )
                )
                status_msg += f"\n⏳ (به دلیل ثبت با تاخیر، ۵۰٪ امتیاز محاسبه شد: {pts} امتیاز)"

                user.points = round(float(user.points or 0.0) + pts, 1)
                user.total_minutes = int(user.total_minutes or 0) + input_minutes
                user.total_pages = int(user.total_pages or 0) + pages
                user.half_coupons = max(0, int(user.half_coupons or 0) - half_used)
                user.one_min_coupons = max(0, int(user.one_min_coupons or 0) - one_used)

                # افزودن روز دیروز به late_days_list و حذف از absent_days_list
                late_days = AbsenceService.parse_days_list(user.late_days_list)
                if target_league_day not in late_days:
                    late_days.append(target_league_day)
                user.late_days_list = AbsenceService.format_days_list(late_days)

                absent_days = AbsenceService.parse_days_list(user.absent_days_list)
                if target_league_day in absent_days:
                    absent_days.remove(target_league_day)
                user.absent_days_list = AbsenceService.format_days_list(absent_days)
                user.no_study_days = len(absent_days)

                log_entry = ActivityLog(
                    user_id=user.id,
                    league_id=league.id,
                    cycle_id=cycle.id,
                    cycle_number=league.cycle_number,
                    league_day=target_league_day,
                    minutes=input_minutes,
                    pages=pages,
                    points_earned=pts,
                    half_coupon_used=half_used,
                    one_min_coupon_used=one_used,
                    log_date=target_date_str,
                    log_hour=now_ir.hour,
                )
                db.add(log_entry)
                db.commit()

                # بازسازی شکاف‌های تاریخی و زنجیره استمرار بر اساس لاگ‌های روزهای قبل و امروز
                AbsenceService.reconcile_historical_gaps(db, user=user, league=league)
                AbsenceService.reconcile_streaks(db, user=user, league=league)
                db.refresh(user)

                cum_minutes = input_minutes
                cum_pages = pages
                day_label = "دیروز"
                header_msg = MessageService.get_message(db, user.group_id, "late_logged")

            else:
                # ثبت امروز: حالت‌های fresh، edit یا append
                if user.last_log_date != today_str:
                    user.today_minutes = 0
                    user.today_pages = 0
                    user.today_points = 0.0
                    user.today_half_used = 0
                    user.today_one_min_used = 0

                # در حالت edit یا append ابتدا مقادیر ثبت‌شده قبلی امروز را برمی‌گردانیم (با رعایت سقف مجاز سهمیه‌ها)
                if user.last_log_date == today_str and (
                    user.today_minutes > 0 or user.today_points > 0
                ):
                    user.points = max(
                        0.0, round(float(user.points or 0.0) - float(user.today_points or 0.0), 1)
                    )
                    user.total_minutes = max(
                        0, int(user.total_minutes or 0) - int(user.today_minutes or 0)
                    )
                    user.total_pages = max(
                        0, int(user.total_pages or 0) - int(user.today_pages or 0)
                    )
                    user.half_coupons = min(
                        settings.DEFAULT_HALF_COUPONS,
                        max(0, int(user.half_coupons or 0) + int(user.today_half_used or 0)),
                    )
                    user.one_min_coupons = min(
                        settings.DEFAULT_ONE_MIN_COUPONS,
                        max(0, int(user.one_min_coupons or 0) + int(user.today_one_min_used or 0)),
                    )

                if mode == "append" and user.last_log_date == today_str:
                    cum_minutes = int(user.today_minutes or 0) + input_minutes
                    cum_pages = int(user.today_pages or 0) + pages
                else:
                    cum_minutes = input_minutes
                    cum_pages = pages

                pts, half_used, one_used, status_msg = ScoringService.calculate_points(
                    minutes=cum_minutes,
                    floor=effective_floor,
                    half_coupons=user.half_coupons,
                    one_min_coupons=user.one_min_coupons,
                )

                user.points = round(float(user.points or 0.0) + pts, 1)
                user.total_minutes = int(user.total_minutes or 0) + cum_minutes
                user.total_pages = int(user.total_pages or 0) + cum_pages
                user.half_coupons = max(0, int(user.half_coupons or 0) - half_used)
                user.one_min_coupons = max(0, int(user.one_min_coupons or 0) - one_used)

                user.last_log_date = today_str
                user.today_minutes = cum_minutes
                user.today_pages = cum_pages
                user.today_points = pts
                user.today_half_used = half_used
                user.today_one_min_used = one_used

                existing_today_log = (
                    db.query(ActivityLog)
                    .filter(
                        ActivityLog.user_id == user.id,
                        ActivityLog.league_id == league.id,
                        ActivityLog.log_date == today_str,
                    )
                    .first()
                )
                log_day_to_record = (
                    raw_current_day
                    if raw_current_day > settings.LEAGUE_DURATION
                    else current_day
                )
                if existing_today_log:
                    existing_today_log.minutes = cum_minutes
                    existing_today_log.pages = cum_pages
                    existing_today_log.points_earned = pts
                    existing_today_log.half_coupon_used = half_used
                    existing_today_log.one_min_coupon_used = one_used
                    existing_today_log.league_day = log_day_to_record
                    existing_today_log.cycle_id = cycle.id
                    existing_today_log.cycle_number = league.cycle_number
                    existing_today_log.log_hour = now_ir.hour
                else:
                    db.add(
                        ActivityLog(
                            user_id=user.id,
                            league_id=league.id,
                            cycle_id=cycle.id,
                            cycle_number=league.cycle_number,
                            league_day=log_day_to_record,
                            minutes=cum_minutes,
                            pages=cum_pages,
                            points_earned=pts,
                            half_coupon_used=half_used,
                            one_min_coupon_used=one_used,
                            log_date=today_str,
                            log_hour=now_ir.hour,
                        )
                    )
                db.commit()

                AbsenceService.reconcile_historical_gaps(db, user=user, league=league)
                AbsenceService.reconcile_streaks(db, user=user, league=league)
                db.refresh(user)

                day_label = "امروز"
                header_msg = MessageService.get_message(db, user.group_id, "study_logged")

            # محاسبه رتبه کاربر و روزهای باقیمانده چله
            all_league_users = (
                db.query(User)
                .filter(User.league_id == league.id, User.is_active == True)
                .all()
            )
            my_rank = ScoringService.get_user_rank(user, all_league_users, league.floor)
            days_left = max(0, settings.LEAGUE_DURATION - current_day)
            league_title = f"لیگ «{escape_md(league.name)}»"

            card_body = (
                f"{header_msg}\n\n"
                f"⏱ زمان {day_label}: {cum_minutes} دقیقه\n"
                f"📄 صفحات {day_label}: {cum_pages} صفحه\n"
                f"🏆 چله {cycle.cycle_number} | روز {current_day} از {settings.LEAGUE_DURATION}\n"
                f"🔥 زنجیره شما: {user.streak} روز\n"
                f"🏆 رتبه شما در {league_title}: {my_rank}\n"
                f"⏳ روزهای مانده تا پایان چله: {days_left} روز\n\n"
                f"{status_msg}"
            )
            final_text = MessageService.apply_terms(db, user.group_id, card_body)
            main_kb = build_user_main_menu(db, tg_id, user)

        await state.clear()
        await safe_answer(message, final_text, reply_markup=main_kb)


# ===========================================================================
# ۶.۵. جدول لیگ، حساب کاربری، راهنما، تغییر لیگ فعال، تاریخچه و انصراف
# ===========================================================================
def _fetch_user_leaderboard_sync(tg_id: str) -> Tuple[Optional[str], Optional[str], Any]:
    with get_db() as db:
        user = get_active_user(db, tg_id)
        if not user or not user.is_active or not user.league_id:
            err = MessageService.apply_terms(
                db, user.group_id if user else 1, "⚠️ شما هنوز عضو هیچ لیگی نیستید."
            )
            return err, None, None
        league = db.query(League).filter(League.id == user.league_id).first()
        if not league:
            err = MessageService.apply_terms(
                db, user.group_id if user else 1, "⚠️ لیگ شما یافت نشد."
            )
            return err, None, None
        table_text = format_league_leaderboard(db, league)
        kb = build_user_main_menu(db, tg_id, user)
        return None, table_text, kb


@user_router.message(F.text == "🏆 جدول لیگ")
async def handle_league_leaderboard(message: Message, state: FSMContext) -> None:
    await state.clear()
    tg_id = str(message.from_user.id)
    err_text, table_text, kb = await asyncio.to_thread(
        _fetch_user_leaderboard_sync, tg_id
    )
    if err_text:
        await safe_answer(message, err_text)
        return
    await send_text_chunks(message.bot, message.chat.id, table_text, reply_markup=kb)


def _fetch_user_profile_sync(tg_id: str) -> Tuple[Optional[str], Optional[str], Any]:
    with get_db() as db:
        user = get_active_user(db, tg_id)
        if not user or not user.is_active or not user.league_id:
            err = MessageService.apply_terms(
                db, user.group_id if user else 1, "⚠️ شما هنوز عضو هیچ لیگی نیستید."
            )
            return err, None, None
        league = db.query(League).filter(League.id == user.league_id).first()
        if not league:
            err = MessageService.apply_terms(
                db, user.group_id if user else 1, "⚠️ لیگ شما یافت نشد."
            )
            return err, None, None

        cycle = get_or_create_active_cycle(db, league)
        current_day = DateService.calculate_league_day(
            cycle.start_shamsi or league.start_shamsi
        )
        days_left = max(0, settings.LEAGUE_DURATION - current_day)
        effective_floor = user.get_effective_floor(league.floor)

        all_users = (
            db.query(User)
            .filter(User.league_id == league.id, User.is_active == True)
            .all()
        )
        my_rank = ScoringService.get_user_rank(user, all_users, league.floor)

        absent_days_text = user.absent_days_list if user.absent_days_list else "ندارد"
        late_days_text = user.late_days_list if user.late_days_list else "ندارد"

        profile_text = (
            f"👤 *شناسنامه مطالعه شما در لیگ {escape_md(league.name)}*:\n"
            f"🏆 *چله {cycle.cycle_number} | روز {current_day} از {settings.LEAGUE_DURATION}*\n\n"
            f"🌸 *نام*: {escape_md(user.name)}\n"
            f"🏆 *رتبه شما*: {my_rank}\n"
            f"⏱ *میثاق روزانه شما*: {effective_floor} دقیقه\n"
            f"⭐️ *امتیاز کل*: {round(float(user.points or 0.0), 1)} امتیاز\n"
            f"⏱ *زمان کل مطالعه*: {user.total_minutes} دقیقه\n"
            f"📄 *صفحات کل*: {user.total_pages} صفحه\n"
            f"🔥 *زنجیره استمرار*: {user.streak} روز\n"
            f"❌ *تعداد غیبت*: {user.no_study_days} روز (روزهای: {absent_days_text})\n"
            f"⚠️ *ثبت‌های دیرهنگام*: روزهای: {late_days_text}\n"
            f"⏳ *روزهای مانده به پایان چله*: {days_left} روز\n\n"
            f"🎫 فرصت‌ها و سهمیه‌های باقیمانده این دوره:\n"
            f"🔹 سهمیه نصف میثاق: {user.half_coupons} از {settings.DEFAULT_HALF_COUPONS} روز\n"
            f"🔸 سهمیه طلایی ۱ دقیقه‌ای: {user.one_min_coupons} از {settings.DEFAULT_ONE_MIN_COUPONS} روز\n\n"
            f"🔔 برای خاموش/روشنکردن یادآوری شبانه، دستور /reminder را بفرستید.\n"
            f"⚠️ جهت انصراف، دستور /cancel_my_league را بفرستید."
        )
        profile_text = MessageService.apply_terms(db, user.group_id, profile_text)
        kb = build_user_main_menu(db, tg_id, user)
        return None, profile_text, kb


@user_router.message(F.text == "👤 حساب کاربری و سهمیه ها")
async def handle_user_profile(message: Message, state: FSMContext) -> None:
    await state.clear()
    tg_id = str(message.from_user.id)
    err_text, profile_text, kb = await asyncio.to_thread(_fetch_user_profile_sync, tg_id)
    if err_text:
        await safe_answer(message, err_text)
        return
    await safe_answer(message, profile_text, reply_markup=kb)


@user_router.message(F.text == "راهنما")
@user_router.message(Command("help"))
async def handle_rules_help(message: Message, state: FSMContext) -> None:
    await state.clear()
    tg_id = str(message.from_user.id)
    with get_db() as db:
        user = get_active_user(db, tg_id)
        grp_id = user.group_id if user else 1
        help_txt = MessageService.get_message(db, grp_id, "rules_help")
        kb = build_user_main_menu(db, tg_id, user) if (user and user.is_active) else get_start_menu()

    await safe_answer(message, help_txt, reply_markup=kb)


@user_router.message(F.text == "🔄 تغییر لیگ فعال")
async def handle_switch_active_league_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    tg_id = str(message.from_user.id)
    with get_db() as db:
        profiles = get_user_profiles(db, tg_id, only_active=True)
        active_user = get_active_user(db, tg_id)
        active_id = active_user.id if active_user else ""

        prof_tuples: List[Tuple[User, str]] = []
        for p in profiles:
            lg = (
                db.query(League).filter(League.id == p.league_id).first()
                if p.league_id
                else None
            )
            l_name = lg.name if lg else "بدون لیگ"
            prof_tuples.append((p, l_name))

        kb = get_profile_switch_keyboard(prof_tuples, active_id)
        grp_id = active_user.group_id if active_user else 1
        prompt = MessageService.apply_terms(
            db, grp_id, "🔄 لطفاً لیگ (پروفایل) فعال موردنظر خود را انتخاب کنید:"
        )

    await safe_answer(message, prompt, reply_markup=kb)


@user_router.callback_query(F.data.startswith("switchprof_"))
async def cb_switch_profile(callback: CallbackQuery, state: FSMContext) -> None:
    target_prof_id = callback.data.replace("switchprof_", "")
    tg_id = str(callback.from_user.id)

    with get_db() as db:
        prof = (
            db.query(User)
            .filter(
                User.id == target_prof_id,
                User.telegram_id == tg_id,
                User.is_active == True,
            )
            .first()
        )
        if not prof:
            await callback.answer("پروفایل یافت نشد.", show_alert=True)
            return

        set_active_user_id(db, tg_id, prof.id)
        lg = (
            db.query(League).filter(League.id == prof.league_id).first()
            if prof.league_id
            else None
        )
        l_name = lg.name if lg else "بدون لیگ"
        main_kb = build_user_main_menu(db, tg_id, prof)
        msg_txt = MessageService.apply_terms(
            db,
            prof.group_id,
            f"✅ لیگ فعال شما به «{escape_md(l_name)}» تغییر یافت.",
        )

    await state.clear()
    await safe_send(callback.bot, callback.message.chat.id, msg_txt, reply_markup=main_kb)
    await callback.answer("لیگ فعال تغییر کرد.")


@user_router.message(Command("history"))
@user_router.message(StateFilter(None), F.text.func(lambda t: t and t.strip().lower() == "history"))
async def handle_cycle_history(message: Message) -> None:
    tg_id = str(message.from_user.id)
    with get_db() as db:
        profiles = get_user_profiles(db, tg_id, only_active=False)
        prof_ids = [p.id for p in profiles] or [tg_id]
        results = (
            db.query(CycleResult)
            .filter(CycleResult.user_id.in_(prof_ids))
            .order_by(CycleResult.id.desc())
            .all()
        )
        if not results:
            await safe_answer(
                message, "📭 هنوز هیچ چله پایان‌یافته‌ای در کارنامه شما ثبت نشده است."
            )
            return

        lines = ["📜 *تاریخچه کارنامه چله‌های پایان‌یافته شما:*\n"]
        for r in results:
            cyc = db.query(Cycle).filter(Cycle.id == r.cycle_id).first()
            lg = (
                db.query(League).filter(League.id == cyc.league_id).first()
                if cyc
                else None
            )
            l_name = escape_md(lg.name) if lg else "لیگ"
            c_num = cyc.cycle_number if cyc else 1
            lines.append(
                f"🏆 *{l_name} - چله {c_num}*\n"
                f"🥇 رتبه نهایی: *{r.final_rank}* | ⭐️ امتیاز: *{round(float(r.points or 0.0), 1)}*\n"
                f"⏱ زمان کل: *{r.total_minutes}* دقیقه | 📄 صفحات: *{r.total_pages}*\n"
                f"❌ غیبت: *{r.no_study_days}* روز | 🔥 زنجیره: *{r.streak}* روز\n"
                f"───────────────────"
            )
        active_u = get_active_user(db, tg_id)
        grp_id = active_u.group_id if active_u else 1
        text = MessageService.apply_terms(db, grp_id, "\n".join(lines))

    await send_text_chunks(message.bot, message.chat.id, text)


@user_router.message(Command("cancel_my_league"))
async def cmd_cancel_my_league(message: Message) -> None:
    tg_id = str(message.from_user.id)
    with get_db() as db:
        user = get_active_user(db, tg_id)
        if not user or not user.league_id:
            await safe_answer(message, "⚠️ شما در حال حاضر عضو هیچ لیگی نیستید.")
            return
        lg = db.query(League).filter(League.id == user.league_id).first()
        l_name = escape_md(lg.name) if lg else "فعلی"
        prompt = MessageService.apply_terms(
            db,
            user.group_id,
            f"⚠️ آیا مطمئن هستید که می‌خواهید از لیگ «{l_name}» انصراف دهید؟\n"
            "با انصراف، پروفایل شما در این لیگ غیرفعال خواهد شد.",
        )

    await safe_answer(message, prompt, reply_markup=get_cancel_league_confirm())


@user_router.message(Command("reminder"))
async def cmd_toggle_reminder(message: Message, state: FSMContext) -> None:
    await state.clear()
    tg_id = str(message.from_user.id)
    with get_db() as db:
        profiles = get_user_profiles(db, tg_id, only_active=True)
        if not profiles:
            await safe_answer(
                message, "⚠️ ابتدا باید ثبتنام کنید.", reply_markup=get_start_menu()
            )
            return
        new_value = not all(bool(p.reminder_enabled) for p in profiles)
        for p in profiles:
            p.reminder_enabled = new_value
        db.commit()
        kb = build_user_main_menu(db, tg_id)

    if new_value:
        txt = "🔔 یادآوری شبانه روشن شد. برای خاموشکردن دوباره /reminder را بفرستید."
    else:
        txt = "🔕 یادآوری شبانه خاموش شد. برای روشنکردن دوباره /reminder را بفرستید."
    await safe_answer(message, txt, reply_markup=kb)


@user_router.callback_query(F.data == "confirm_cancel_league")
async def cb_confirm_cancel_league(callback: CallbackQuery, state: FSMContext) -> None:
    tg_id = str(callback.from_user.id)
    with get_db() as db:
        user = get_active_user(db, tg_id)
        if not user:
            await callback.answer("کاربر یافت نشد.", show_alert=True)
            return

        user.league_id = None
        user.is_active = False
        db.commit()

        remaining = get_user_profiles(db, tg_id, only_active=True)
        if remaining:
            set_active_user_id(db, tg_id, remaining[0].id)
            kb = build_user_main_menu(db, tg_id, remaining[0])
            msg = "✅ انصراف شما ثبت شد و به پروفایل دیگرتان منتقل شدید."
        else:
            kb = get_start_menu()
            msg = "✅ انصراف شما از لیگ با موفقیت ثبت شد. هر زمان مایل بودید می‌توانید مجدداً ثبت‌نام کنید."

    await state.clear()
    await safe_send(callback.bot, callback.message.chat.id, msg, reply_markup=kb)
    await callback.answer("انصراف ثبت شد.")


# ===========================================================================
# ۸. جاب‌های زمان‌بندی‌شده روزانه (00:00, 01:00, 08:00, 22:00)
# ===========================================================================

def _midnight_job_sync(today_str: str, yesterday_str: str, force: bool) -> bool:
    """اجرای همگام عملیات دیتابیس و پاکسازی فایل‌های موقت در ترد مجزا"""
    ReportService.cleanup_old_reports(max_age_hours=24)

    with get_db() as db:
        last_run = get_system_state(db, "last_daily_job_date")
        if last_run == today_str and not force:
            return False

        missing_dates = AbsenceService.get_missing_dates(last_run, yesterday_str)
        AbsenceService.process_absences_for_dates(db, missing_dates)
        AbsenceService.reconcile_historical_gaps(db)
        AbsenceService.reconcile_streaks(db)

        # صفر کردن مقادیر today_* برای کاربرانی که هنوز در تاریخ جدید لاگی ثبت نکرده‌اند
        active_users = db.query(User).filter(User.is_active == True).all()
        for u in active_users:
            if u.last_log_date != today_str:
                u.today_minutes = 0
                u.today_pages = 0
                u.today_points = 0.0
                u.today_half_used = 0
                u.today_one_min_used = 0

        # به‌روزرسانی current_day لیگ‌ها و چله‌های فعال
        active_leagues = (
            db.query(League)
            .filter(League.is_deleted == False, League.is_active == True)
            .all()
        )
        for lg in active_leagues:
            cyc = get_or_create_active_cycle(db, lg)
            new_day = DateService.calculate_league_day(
                cyc.start_shamsi or lg.start_shamsi
            )
            lg.current_day = new_day
            cyc.current_day = new_day

        set_system_state(db, "last_daily_job_date", today_str)
        db.commit()
    return True


async def midnight_job(bot: Bot, force: bool = False) -> None:
    """
    ۱. جاب ساعت 00:00 نیمه‌شب:
    - بدون ارسال هیچ پیامی به کاربران.
    - پاکسازی خودکار فایل‌های اکسل موقت قدیمی‌تر از ۲۴ ساعت در پوشه reports/.
    - ثبت غیبت روز قبل و روزهای جاافتاده احتمالی در ترد جداگانه بدون بلاک کردن Event Loop.
    """
    today_str = DateService.today_str()
    yesterday_str = DateService.yesterday_str()
    executed = await asyncio.to_thread(
        _midnight_job_sync, today_str, yesterday_str, force
    )
    if executed:
        logger.info(
            f"جاب نیمه‌شب (midnight_job) برای تاریخ {today_str} با موفقیت اجرا شد."
        )


def _get_all_admin_recipients_sync() -> set[str]:
    with get_db() as db:
        admin_recipients: set[str] = {
            str(sa).strip() for sa in settings.ADMIN_IDS if str(sa).strip()
        }
        group_admins = db.query(GroupAdmin).all()
        for ga in group_admins:
            if ga.user_id and str(ga.user_id).strip():
                admin_recipients.add(str(ga.user_id).strip())
    return admin_recipients


async def send_startup_notification(bot: Bot) -> int:
    """
    ارسال پیام فعال‌شدن ربات به همراه تاریخ شمسی و ساعت دقیق به وقت ایران برای ادمین‌ها.
    این پیام در زمان اجرای ربات برای تمامی مدیران ارشد (ADMIN_IDS) و مدیران مجموعه‌ها ارسال می‌شود.
    خروجی: تعداد ادمین‌هایی که پیام با موفقیت به آن‌ها ارسال شده است.
    """
    time_str = DateService.now_iran_time_str()
    full_date_shamsi = DateService.today_shamsi_full()

    startup_text = (
        "🟢 *ربات «کتابخوارشو» با موفقیت فعال شد!*\n\n"
        f"📅 *تاریخ فعال‌سازی (شمسی):* `{full_date_shamsi}`\n"
        f"⏰ *ساعت دقیق (به وقت ایران):* `{time_str}`\n\n"
        "✨ وضعیت سیستم: آنلاین و آماده دریافت پیام‌ها"
    )

    admin_recipients = await asyncio.to_thread(_get_all_admin_recipients_sync)

    sent_count = 0
    for admin_id in admin_recipients:
        try:
            res = await safe_send(bot, admin_id, startup_text)
            if res:
                sent_count += 1
        except Exception as exc:
            logger.warning(f"عدم امکان ارسال پیام فعال‌سازی به ادمین {admin_id}: {exc}")

    logger.info(
        f"پیام فعال‌سازی ربات (ساعت {time_str} - تاریخ {full_date_shamsi}) برای {sent_count} نفر از {len(admin_recipients)} ادمین ارسال شد."
    )
    return sent_count


def _init_daily_admin_reports_sync(today_str: str, force: bool) -> Optional[List[str]]:
    with get_db() as db:
        last_run = get_system_state(db, "last_daily_admin_report_date")
        if last_run == today_str and not force:
            return None

        league_ids = [
            r[0]
            for r in db.query(League.id)
            .filter(
                League.is_deleted == False,
                League.is_active == True,
                League.archive_enabled == True,
            )
            .order_by(League.id.asc())
            .all()
        ]
        set_system_state(db, "last_daily_admin_report_date", today_str)
        return league_ids


def _build_single_admin_report_sync(
    league_id: str,
) -> Optional[Tuple[str, List[str]]]:
    with get_db() as db:
        lg = db.get(League, league_id)
        if not lg or lg.is_deleted or not lg.is_active or not lg.archive_enabled:
            return None
        cyc = get_or_create_active_cycle(db, lg)
        curr_day = DateService.calculate_league_day(
            cyc.start_shamsi or lg.start_shamsi
        )
        archived_day = max(1, curr_day - 1)
        table_txt = format_league_leaderboard(db, lg)
        report_text = (
            f"📊 *آرشیو چله {cyc.cycle_number} روز {archived_day} لیگ: {escape_md(lg.name)}*\n\n"
            f"{table_txt}"
        )
        report_text = MessageService.apply_terms(db, lg.group_id, report_text)

        group_admins = (
            db.query(GroupAdmin.user_id)
            .filter(GroupAdmin.group_id == lg.group_id)
            .all()
        )
        rcpt_set = {str(a[0]) for a in group_admins}
        for sa in settings.ADMIN_IDS:
            rcpt_set.add(str(sa))
        if settings.ARCHIVE_CHANNEL:
            rcpt_set.add(settings.ARCHIVE_CHANNEL)
        return report_text, sorted(rcpt_set)


async def send_daily_admin_reports(bot: Bot, force: bool = False) -> None:
    """
    ۲. جاب ساعت 01:00 بامداد:
    ارسال گزارش متنی رتبه‌بندی روز گذشته به صورت پلکانی و لیگ به لیگ،
    با اجرای کوئری‌ها در ترد جداگانه و کنترل نرخ ارسال.
    """
    today_str = DateService.today_str()
    league_ids = await asyncio.to_thread(
        _init_daily_admin_reports_sync, today_str, force
    )
    if not league_ids:
        return

    throttle = BroadcastThrottle()
    for league_id in league_ids:
        try:
            built = await asyncio.to_thread(_build_single_admin_report_sync, league_id)
            if not built:
                continue
            report_text, recipients = built
        except Exception as exc:
            logger.error(f"خطا در ساخت گزارش آرشیو لیگ {league_id}: {exc}", exc_info=True)
            continue

        for rcpt in recipients:
            try:
                await send_text_chunks(bot, rcpt, report_text, throttle=throttle)
            except Exception as exc:
                logger.warning(f"خطا در ارسال گزارش آرشیو به {rcpt}: {exc}")


def _complete_and_rollover_cycle(
    db: Session, league: League, active_cycle: Cycle
) -> Dict[str, Any]:
    """
    فرآیند کامل پایان چله ۴۰ روزه در ساعت ۸ صبح روز ۴۱ام:
    ۱. تفکیک مطالعات صبحگاهی سحرخیزان در روز ۴۱ام.
    ۲. ثبت رکوردهای CycleResult و بستن چله فعلی.
    ۳. ساخت چله جدید (cycle_number + 1) از روز ۱ با تاریخ شمسی امروز.
    ۴. بازنشانی آمار دوره کاربران و سهمیه‌ها و انتقال مطالعات صبحگاهی سحرخیزان به روز ۱ چله جدید.
    خروجی: دیکشنری اطلاعات کارنامه نهایی جهت ارسال امن و پلکانی در خارج از نشست دیتابیس.
    """
    today_str = DateService.today_str()
    today_shamsi = DateService.today_shamsi()

    users = (
        db.query(User)
        .filter(User.league_id == league.id, User.is_active == True)
        .all()
    )

    # ۱. شناسایی و جداسازی لاگ‌های صبحگاهی امروز با یک کوئری سریع
    today_logs_map: Dict[str, ActivityLog] = {}
    for t_log in (
        db.query(ActivityLog)
        .filter(
            ActivityLog.league_id == league.id,
            ActivityLog.log_date == today_str,
        )
        .order_by(ActivityLog.id.asc())
        .all()
    ):
        today_logs_map.setdefault(t_log.user_id, t_log)

    early_morning_logs: Dict[str, ActivityLog] = {}
    for u in users:
        today_log = today_logs_map.get(u.id)
        if today_log:
            early_morning_logs[u.id] = today_log
            u.points = max(
                0.0, round(float(u.points or 0.0) - float(today_log.points_earned or 0.0), 1)
            )
            u.total_minutes = max(
                0, int(u.total_minutes or 0) - int(today_log.minutes or 0)
            )
            u.total_pages = max(
                0, int(u.total_pages or 0) - int(today_log.pages or 0)
            )
            u.half_coupons = min(
                settings.DEFAULT_HALF_COUPONS,
                int(u.half_coupons or 0) + int(today_log.half_coupon_used or 0),
            )
            u.one_min_coupons = min(
                settings.DEFAULT_ONE_MIN_COUPONS,
                int(u.one_min_coupons or 0) + int(today_log.one_min_coupon_used or 0),
            )
    db.commit()

    # بازسازی دقیق زنجیره و غیبت‌های ۴۰ روزه چله قدیم (بدون احتساب لاگ روز ۴۱)
    AbsenceService.reconcile_historical_gaps(db, league=league)
    AbsenceService.reconcile_streaks(db, league=league)

    # ۲. آماده‌سازی جدول نهایی و اکسل نهایی چله قدیم
    old_cycle_number = active_cycle.cycle_number
    league_name_snapshot = league.name
    group_id_snapshot = league.group_id
    league_floor_snapshot = league.floor
    final_table_text = format_league_leaderboard(db, league)
    users_snapshot = [
        ReportService._extract_row_dict(u, league_floor=league_floor_snapshot)
        for u in users
    ]
    final_excel_path = ReportService.generate_excel(
        league_name=league_name_snapshot,
        users_data=users_snapshot,
        cycle_number=old_cycle_number,
        current_day=settings.LEAGUE_DURATION,
        league_floor=league_floor_snapshot,
    )
    cycle_finished_msg = MessageService.get_message(
        db, group_id_snapshot, "cycle_finished"
    )

    # ۳. رتبه‌بندی نهایی، ذخیره در CycleResult و بستن چله قدیم
    ranked_final = ScoringService.rank_users(users, league.floor)
    for final_rank, u in ranked_final:
        half_rem = int(u.half_coupons or 0)
        one_rem = int(u.one_min_coupons or 0)
        db.add(
            CycleResult(
                cycle_id=active_cycle.id,
                user_id=u.id,
                user_name=u.name,
                final_rank=final_rank,
                points=round(float(u.points or 0.0), 1),
                total_minutes=int(u.total_minutes or 0),
                total_pages=int(u.total_pages or 0),
                streak=int(u.streak or 0),
                no_study_days=int(u.no_study_days or 0),
                absent_days_list=u.absent_days_list or "",
                late_days_list=u.late_days_list or "",
                half_coupons_used=max(0, settings.DEFAULT_HALF_COUPONS - half_rem),
                one_min_coupons_used=max(0, settings.DEFAULT_ONE_MIN_COUPONS - one_rem),
                half_coupons_remaining=half_rem,
                one_min_coupons_remaining=one_rem,
            )
        )

    active_cycle.status = "finished"
    active_cycle.end_shamsi = DateService.date_to_shamsi(DateService.yesterday_date())
    active_cycle.current_day = settings.LEAGUE_DURATION
    active_cycle.finished_at = datetime.now(timezone.utc)
    db.commit()

    # ۴. ساخت چله جدید (cycle_number + 1) از روز ۱
    new_cycle_num = int(league.cycle_number or 1) + 1
    league.cycle_number = new_cycle_num
    league.start_shamsi = today_shamsi
    league.current_day = 1

    new_cycle = Cycle(
        league_id=league.id,
        cycle_number=new_cycle_num,
        start_shamsi=today_shamsi,
        current_day=1,
        status="active",
    )
    db.add(new_cycle)
    db.commit()
    db.refresh(new_cycle)

    # ۵. صفر کردن آمار دوره کاربران و انتقال مطالعات صبحگاهی سحرخیزان به روز ۱ چله جدید
    for u in users:
        early_log = early_morning_logs.get(u.id)
        u.points = 0.0
        u.total_minutes = 0
        u.total_pages = 0
        u.no_study_days = 0
        u.absent_days_list = ""
        u.late_days_list = ""
        u.half_coupons = settings.DEFAULT_HALF_COUPONS
        u.one_min_coupons = settings.DEFAULT_ONE_MIN_COUPONS

        if early_log:
            eff_fl = u.get_effective_floor(league.floor)
            pts, h_used, o_used, _ = ScoringService.calculate_points(
                early_log.minutes, eff_fl, u.half_coupons, u.one_min_coupons
            )
            u.points = pts
            u.total_minutes = early_log.minutes
            u.total_pages = early_log.pages
            u.half_coupons -= h_used
            u.one_min_coupons -= o_used
            u.last_log_date = today_str
            u.today_minutes = early_log.minutes
            u.today_pages = early_log.pages
            u.today_points = pts
            u.today_half_used = h_used
            u.today_one_min_used = o_used
            u.streak = 1

            early_log.cycle_id = new_cycle.id
            early_log.cycle_number = new_cycle_num
            early_log.league_day = 1
            early_log.points_earned = pts
            early_log.half_coupon_used = h_used
            early_log.one_min_coupon_used = o_used
        else:
            u.streak = 0
            u.last_log_date = None
            u.today_minutes = 0
            u.today_pages = 0
            u.today_points = 0.0
            u.today_half_used = 0
            u.today_one_min_used = 0

    db.commit()

    for u in users:
        set_system_state(db, f"streak_offset_{u.id}", "0", commit=False)
    db.commit()

    # آماده‌سازی گیرندگان؛ ارسال واقعی خارج از نشست دیتابیس و به صورت پلکانی انجام می‌شود
    group_admins = (
        db.query(GroupAdmin.user_id).filter(GroupAdmin.group_id == league.group_id).all()
    )
    admin_recipients = {str(a[0]) for a in group_admins} | {
        str(sa) for sa in settings.ADMIN_IDS
    }
    user_recipients = {str(u.telegram_id or u.id) for u in users}
    all_recipients = admin_recipients | user_recipients

    final_caption = MessageService.apply_terms(
        db,
        league.group_id,
        f"🏆 کارنامه نهایی چله {old_cycle_number} لیگ «{league_name_snapshot}»",
    )
    return {
        "recipients": sorted(all_recipients),
        "cycle_finished_msg": cycle_finished_msg,
        "final_table_text": final_table_text,
        "excel_path": final_excel_path,
        "caption": final_caption,
    }


async def _dispatch_cycle_rollover(bot: Bot, payload: Dict[str, Any]) -> None:
    """ارسال پلکانی پیام پایان چله، جدول نهایی و اکسل؛ حذف فایل اکسل در هر حالت"""
    throttle = BroadcastThrottle()
    excel_path = payload["excel_path"]
    try:
        for rcpt in payload["recipients"]:
            try:
                await safe_send(bot, rcpt, payload["cycle_finished_msg"])
                await throttle.tick()
                await send_text_chunks(
                    bot, rcpt, payload["final_table_text"], throttle=throttle
                )
                await safe_send_document(
                    bot, rcpt, excel_path, caption=payload["caption"], throttle=throttle
                )
            except Exception as exc:
                logger.warning(f"خطا در ارسال کارنامه پایان چله به {rcpt}: {exc}")
    finally:
        if os.path.exists(excel_path):
            try:
                os.remove(excel_path)
            except OSError:
                pass


_daily_user_reports_lock = asyncio.Lock()


async def send_daily_user_reports(bot: Bot, force: bool = False) -> None:
    """قفل سراسری: جلوگیری از اجرای همزمان و رولاور دوباره چله"""
    async with _daily_user_reports_lock:
        await _send_daily_user_reports_impl(bot, force=force)

def _build_morning_cards(
    db: Session,
    lg: League,
    cyc: Cycle,
    current_day: int,
    yesterday_str: str,
    force: bool,
    admin_ids: set,
    profile_counts: Dict[str, int],
) -> List[Tuple[str, str, Any]]:
    """
    ساخت کارنامه‌های صبحگاهی یک لیگ (همگام، بدون هیچ I/O شبکه‌ای).
    کاربران با Keyset Pagination خوانده می‌شوند و فقط رشته‌های نهایی در حافظه می‌مانند.
    """
    yesterday_day = max(1, current_day - 1)
    terms = MessageService.get_terms(db, lg.group_id)

    # رتبه‌بندی با ستون‌های حداقلی (فقط فیلدهای مورد نیاز کلید مرتب‌سازی)
    ranking_users = (
        db.query(User)
        .options(
            load_only(User.id, User.points, User.user_floor, User.total_minutes)
        )
        .filter(User.league_id == lg.id, User.is_active == True)
        .all()
    )
    rank_map = {u.id: rnk for rnk, u in ScoringService.rank_users(ranking_users, lg.floor)}
    del ranking_users
    db.expunge_all()

    # لاگ‌های دیروز کل لیگ با یک کوئری (به جای یک کوئری برای هر کاربر)
    y_logs: Dict[str, Tuple[int, float]] = {}
    log_query = db.query(
        ActivityLog.user_id, ActivityLog.minutes, ActivityLog.points_earned
    ).filter(
        ActivityLog.league_id == lg.id,
        (ActivityLog.cycle_id == cyc.id) | (ActivityLog.cycle_number == lg.cycle_number),
        (ActivityLog.log_date == yesterday_str) | (ActivityLog.league_day == yesterday_day),
        ActivityLog.minutes > 0,
    )
    for uid, mins, pts in log_query.yield_per(1000):
        y_logs.setdefault(uid, (mins, pts))

    outbox: List[Tuple[str, str, Any]] = []
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

        for u in chunk:
            joined_before = DateService.user_joined_before_today(u)
            if not joined_before and not force:
                continue

            y_info = y_logs.get(u.id)
            late_days = AbsenceService.parse_days_list(u.late_days_list)
            if y_info:
                y_minutes, y_points = y_info
                if yesterday_day in late_days:
                    y_status = f"⚠️ ثبت با تاخیر ({y_minutes} دقیقه | {y_points} امتیاز)"
                else:
                    y_status = f"✅ ثبت موفق ({y_minutes} دقیقه | {y_points} امتیاز)"
                hint_line = "✨ خداقوت! امروز هم مطالعه خود را به موقع ثبت کنید."
            else:
                y_status = "❌ عدم ثبت (غیبت)"
                hint_line = (
                    "💡 *راهنمایی:* اگر دیروز مطالعه داشته‌اید اما فراموش کردید ثبت کنید، "
                    "همین امروز می‌توانید از دکمه «⏳ ثبت مطالعه دیروز (با کسر ۵۰٪ امتیاز)» در منوی اصلی استفاده کنید تا غیبت دیروز شما حذف شود."
                )

            u_rank = rank_map.get(u.id, 1)
            report_card = (
                f"☀️ *کارنامه صبحگاهی باشگاه کتابخوارشو*\n"
                f"🏆 لیگ: *{escape_md(lg.name)}* (چله {cyc.cycle_number} | روز {current_day} از {settings.LEAGUE_DURATION})\n"
                f"───────────────────\n"
                f"👤 نام: *{escape_md(u.name)}*\n"
                f"📌 وضعیت دیروز (روز {yesterday_day}): {y_status}\n"
                f"🏅 رتبه فعلی شما: *{u_rank}*\n"
                f"⭐️ امتیاز کل: *{round(float(u.points or 0.0), 1)}*\n"
                f"🔥 زنجیره استمرار: *{u.streak}* روز\n"
                f"❌ تعداد غیبت دوره: *{u.no_study_days}* روز\n\n"
                f"{hint_line}"
            )
            report_card = MessageService.apply_terms(
                db, lg.group_id, report_card, terms=terms
            )
            tg_target = str(u.telegram_id or u.id)
            can_late = (not y_info) and current_day > 1 and joined_before
            kb = get_main_menu(
                is_admin=(tg_target in admin_ids),
                has_multiple_profiles=(profile_counts.get(tg_target, 1) > 1),
                can_log_late=can_late,
            )
            outbox.append((tg_target, report_card, kb))

        db.expunge_all()

    return outbox


def _init_morning_reports_sync(
    today_str: str, force: bool
) -> Optional[Tuple[List[str], set, Dict[str, int]]]:
    with get_db() as db:
        last_run = get_system_state(db, "last_daily_user_report_date")
        if last_run == today_str and not force:
            return None

        league_ids = [
            r[0]
            for r in db.query(League.id)
            .filter(League.is_deleted == False, League.is_active == True)
            .order_by(League.id.asc())
            .all()
        ]
        admin_ids = {str(a).strip() for a in settings.ADMIN_IDS if str(a).strip()}
        admin_ids |= {
            str(r[0]).strip()
            for r in db.query(GroupAdmin.user_id).all()
            if r[0]
        }
        profile_counts: Dict[str, int] = {
            str(tg): int(cnt)
            for tg, cnt in db.query(User.telegram_id, func.count(User.id))
            .filter(User.is_active == True)
            .group_by(User.telegram_id)
            .all()
        }
        set_system_state(db, "last_daily_user_report_date", today_str)
        return league_ids, admin_ids, profile_counts


def _check_league_morning_mode_sync(league_id: str) -> Tuple[Optional[str], int]:
    """بررسی سریع وضعیت روز لیگ در ترد جداگانه: ('skip' | 'rollover' | 'cards', current_day)"""
    with get_db() as db:
        lg = db.get(League, league_id)
        if not lg or lg.is_deleted or not lg.is_active:
            return "skip", 0
        cyc = get_or_create_active_cycle(db, lg)
        raw_current_day = DateService.calculate_raw_league_day(
            cyc.start_shamsi or lg.start_shamsi
        )
        if raw_current_day > settings.LEAGUE_DURATION:
            return "rollover", raw_current_day
        return "cards", min(raw_current_day, settings.LEAGUE_DURATION)


def _build_league_morning_cards_sync(
    league_id: str,
    current_day: int,
    yesterday_str: str,
    force: bool,
    admin_ids: set,
    profile_counts: Dict[str, int],
) -> List[Tuple[str, str, Any]]:
    with get_db() as db:
        lg = db.get(League, league_id)
        if not lg or lg.is_deleted or not lg.is_active:
            return []
        cyc = get_or_create_active_cycle(db, lg)
        return _build_morning_cards(
            db,
            lg,
            cyc,
            current_day,
            yesterday_str,
            force,
            admin_ids,
            profile_counts,
        )


def _rollover_league_cycle_sync(league_id: str) -> Optional[Dict[str, Any]]:
    """اجرای کامل فرآیند پایان چله ۴۰ روزه و تولید اکسل در ترد مجزا بدون مسدودسازی Event Loop"""
    with get_db() as db:
        lg = db.get(League, league_id)
        if not lg or lg.is_deleted or not lg.is_active:
            return None
        cyc = get_or_create_active_cycle(db, lg)
        return _complete_and_rollover_cycle(db, lg, cyc)


async def _send_daily_user_reports_impl(bot: Bot, force: bool = False) -> None:
    """
    ۴. جاب ساعت 08:00 صبح:
    - بررسی پایان چله ۴۰ روزه (raw_current_day > settings.LEAGUE_DURATION).
    - آماده‌سازی کارنامه‌ها در ترد پس‌زمینه (asyncio.to_thread) و ارسال پلکانی بدون اشغال Event Loop.
    """
    today_str = DateService.today_str()
    yesterday_str = DateService.yesterday_str()

    init_data = await asyncio.to_thread(_init_morning_reports_sync, today_str, force)
    if not init_data:
        return
    league_ids, admin_ids, profile_counts = init_data

    throttle = BroadcastThrottle()
    for league_id in league_ids:
        outbox: List[Tuple[str, str, Any]] = []
        rollover_payload: Optional[Dict[str, Any]] = None
        try:
            mode, current_day = await asyncio.to_thread(
                _check_league_morning_mode_sync, league_id
            )
            if mode == "skip":
                continue
            if mode == "rollover":
                rollover_payload = await asyncio.to_thread(
                    _rollover_league_cycle_sync, league_id
                )
            elif current_day > 1 or force:
                outbox = await asyncio.to_thread(
                    _build_league_morning_cards_sync,
                    league_id,
                    current_day,
                    yesterday_str,
                    force,
                    admin_ids,
                    profile_counts,
                )
        except Exception as exc:
            logger.error(f"خطا در پردازش گزارش صبحگاهی لیگ {league_id}: {exc}", exc_info=True)
            continue

        if rollover_payload:
            await _dispatch_cycle_rollover(bot, rollover_payload)
        if outbox:
            await dispatch_outbox(bot, outbox, throttle)
        del outbox


def _build_study_reminders_outbox_sync(
    today_str: str, force: bool
) -> List[Tuple[str, str, Any]]:
    """استخراج لیست کاربران ثبت‌نکرده و ساخت پیام‌های یادآوری در ترد مجزا"""
    outbox: List[Tuple[str, str, Any]] = []

    with get_db() as db:
        last_run = get_system_state(db, "last_reminder_date")
        if last_run == today_str and not force:
            return []

        league_map: Dict[str, Tuple[str, int, Optional[int]]] = {
            r[0]: (r[1], r[2], r[3])
            for r in db.query(League.id, League.name, League.floor, League.group_id)
            .filter(League.is_deleted == False, League.is_active == True)
            .all()
        }

        terms_cache: Dict[Optional[int], Dict[str, str]] = {}
        base_cache: Dict[Optional[int], str] = {}

        def _terms(gid: Optional[int]) -> Dict[str, str]:
            if gid not in terms_cache:
                terms_cache[gid] = MessageService.get_terms(db, gid)
            return terms_cache[gid]

        def _base(gid: Optional[int]) -> str:
            if gid not in base_cache:
                base_cache[gid] = MessageService.get_message(db, gid, "reminder_night")
            return base_cache[gid]

        unlogged_by_tg: Dict[str, List[Tuple[int, str, Optional[int]]]] = {}
        chunk_size = max(50, int(settings.DB_CHUNK_SIZE))
        last_id = ""
        while True:
            chunk = (
                db.query(User)
                .options(
                    load_only(
                        User.id,
                        User.telegram_id,
                        User.league_id,
                        User.user_floor,
                        User.last_log_date,
                        User.today_minutes,
                    )
                )
                .filter(
                    User.is_active == True,
                    User.reminder_enabled == True,
                    User.league_id.isnot(None),
                    User.id > last_id,
                )
                .order_by(User.id.asc())
                .limit(chunk_size)
                .all()
            )
            if not chunk:
                break
            last_id = chunk[-1].id

            for u in chunk:
                if u.last_log_date == today_str and int(u.today_minutes or 0) > 0:
                    continue
                lg_info = league_map.get(u.league_id)
                if not lg_info:
                    continue
                lg_name, lg_floor, lg_group = lg_info
                tg_id = str(u.telegram_id or u.id)
                unlogged_by_tg.setdefault(tg_id, []).append(
                    (u.get_effective_floor(lg_floor), lg_name, lg_group)
                )
            db.expunge_all()

        for tg_id, prof_list in unlogged_by_tg.items():
            first_floor, first_name, first_group = prof_list[0]
            base_reminder = _base(first_group)
            if len(prof_list) == 1:
                extra = f"\n\n🏆 لیگ: *{escape_md(first_name)}* (میثاق: {first_floor} دقیقه)"
                extra = MessageService.apply_terms(
                    db, first_group, extra, terms=_terms(first_group)
                )
                full_msg = base_reminder + extra
            else:
                league_lines = ["\n\n📌 *لیگ‌های ثبت‌نشده امروز شما:*"]
                for eff_fl, lg_name, lg_group in prof_list:
                    line = f"🔸 لیگ *{escape_md(lg_name)}* (میثاق: {eff_fl} دقیقه)"
                    league_lines.append(
                        MessageService.apply_terms(
                            db, lg_group, line, terms=_terms(lg_group)
                        )
                    )
                full_msg = base_reminder + "\n".join(league_lines)

            outbox.append((tg_id, full_msg, None))

        set_system_state(db, "last_reminder_date", today_str)

    return outbox


async def send_study_reminders(bot: Bot, force: bool = False) -> None:
    """
    ۵. جاب ساعت 22:00 شب:
    آماده‌سازی لیست یادآوری در ترد پس‌زمینه (asyncio.to_thread) و ارسال پلکانی
    جهت جلوگیری از مسدود شدن Event Loop و Time-out پیام‌رسان بله.
    """
    today_str = DateService.today_str()
    outbox = await asyncio.to_thread(
        _build_study_reminders_outbox_sync, today_str, force
    )
    if outbox:
        await dispatch_outbox(bot, outbox, BroadcastThrottle())
