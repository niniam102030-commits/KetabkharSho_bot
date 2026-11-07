"""
هندلرهای سیستم جریمه لیگ‌ها:
- مشاهده جریمه‌ها (همه اعضا)
- ثبت پرداخت و بخشودگی (مسئول جریمه)
- مدیریت جریمه لیگ (ادمین مجموعه / مسئول جریمه)

قالب callback_data (همگی کمتر از ۶۴ بایت):
  fv:{lid}                  لیست جریمه‌ها
  fp:{lid}:{page}           لیست بدهکاران (مسئول)
  fd:{lid}:{uid}            جزئیات بدهکار
  fs:{lid}:{uid}            درخواست تسویه کامل (تایید)
  fc:{lid}:{uid}            تایید تسویه کامل
  fe:{lid}:{uid}            ثبت مبلغ دلخواه
  fw:{lid}:{uid}            لیست جریمه‌ها برای بخشودگی
  ft:{lid}:{rid}            بخشودن/بازگردانی یک جریمه
  fa:m:{lid}                منوی مدیریت جریمه لیگ
  fa:t:{lid}                فعال/غیرفعال‌سازی (ادمین)
  fa:am:{lid}:{a|l}         تنظیم مبلغ غیبت/عدم‌اعلام
  fa:mg:{lid}               مدیریت مسئولین (ادمین)
  fa:pk:{lid}:{page}:{e}    انتخاب مسئول از اعضا
  fa:ps:{lid}:{tg}:{e}      انتخاب نهایی مسئول
  fa:rm:{lid}:{tg}          حذف مسئول
  fa:x:{lid}                لغو ورودی متنی و بازگشت
"""
import asyncio
import logging
from typing import Any, List, Optional, Tuple

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

import fine_service
from fine_service import format_toman, parse_amount, KIND_LABELS
from database import (
    get_db,
    get_active_user,
    is_user_admin,
    get_or_create_active_cycle,
)
from models import User, League, Cycle, Group, GroupAdmin, FineRecord, FinePayment
from services import escape_md
from keyboards import VIEW_FINES_TEXT, PAY_FINES_TEXT
from handlers import (
    safe_send,
    safe_answer,
    send_text_chunks,
    dispatch_outbox,
    BroadcastThrottle,
    build_user_main_menu,
)

logger = logging.getLogger(__name__)

fine_router = Router(name="fine_router")

PAGE_SIZE = 8


class FineStates(StatesGroup):
    waiting_payment_amount = State()
    waiting_amount_setting = State()


# ---------------------------------------------------------------------------
# ابزارهای کمکی
# ---------------------------------------------------------------------------

def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)


async def _edit(callback: CallbackQuery, text: str, kb: Optional[InlineKeyboardMarkup] = None) -> None:
    """ویرایش پیام شیشه‌ای؛ در صورت خطا ارسال پیام جدید"""
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        return
    except Exception as exc:
        if "not modified" in str(exc).lower():
            return
    try:
        await callback.message.edit_text(text, reply_markup=kb)
        return
    except Exception as exc:
        if "not modified" in str(exc).lower():
            return
    await safe_send(callback.bot, callback.message.chat.id, text, reply_markup=kb)


def _nav_kb(rows: List[List[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _get_league(db, lid: str) -> Optional[League]:
    return db.query(League).filter(League.id == lid, League.is_deleted == False).first()


def _is_member(db, tg: str, lid: str) -> bool:
    return (
        db.query(User.id)
        .filter(User.telegram_id == tg, User.league_id == lid, User.is_active == True)
        .first()
        is not None
    )


def _cycle_numbers(db, league_id: str) -> dict:
    return {c.id: c.cycle_number for c in db.query(Cycle).filter(Cycle.league_id == league_id).all()}


def _get_ledger_user(db, lid: str, uid: str) -> Optional[User]:
    """کاربر فعال لیگ، یا کاربر حذف‌شده/منتقل‌شده‌ای که در دفتر جریمه این لیگ سابقه دارد"""
    u = db.query(User).filter(User.id == uid).first()
    if not u:
        return None
    if u.league_id == lid and u.is_active:
        return u
    has_record = (
        db.query(FineRecord.id)
        .filter(FineRecord.league_id == lid, FineRecord.user_id == uid)
        .first()
    )
    if has_record:
        return u
    has_payment = (
        db.query(FinePayment.id)
        .filter(FinePayment.league_id == lid, FinePayment.user_id == uid)
        .first()
    )
    return u if has_payment else None


def _amounts_line(lg: League) -> str:
    return (
        f"• جریمه غیبت: *{format_toman(lg.fine_absent_amount)}*\n"
        f"• جریمه عدم اعلام: *{format_toman(lg.fine_late_amount)}*"
    )


def _build_fines_text(db, lg: League, viewer_tg: str) -> str:
    """متن لیست بدهکاران با جمع کل در انتها (برای همه اعضا)"""
    fine_service.sync_league_fines(db, lg)
    debtors = fine_service.get_debtors(db, lg, include_inactive=False)
    lines = [f"💰 *جریمه‌های لیگ {escape_md(lg.name)}*", "", _amounts_line(lg), "━━━━━━━━━━━━━━━"]
    if not debtors:
        lines.append("🎉 هیچ جریمهٔ پرداخت‌نشده‌ای وجود ندارد.")
    else:
        for i, d in enumerate(debtors, 1):
            u = d["user"]
            mark = " 👈" if str(u.telegram_id) == str(viewer_tg) else ""
            lines.append(f"{i}. {escape_md(u.get_display_name())} — {format_toman(d['owed'])}{mark}")
    lines.append("━━━━━━━━━━━━━━━")
    lines.append(f"📌 *جمع جریمه‌های پرداخت‌نشده:* {format_toman(fine_service.total_owed(debtors))}")
    return "\n".join(lines)


def _fines_view_kb(db, lg: League, viewer_tg: str) -> Optional[InlineKeyboardMarkup]:
    if fine_service.is_fine_manager(db, lg.id, viewer_tg):
        return _nav_kb(
            [
                [_btn("💳 ثبت پرداخت", f"fp:{lg.id}:0")],
                [_btn("⚙️ تنظیم مبالغ", f"fa:m:{lg.id}")],
            ]
        )
    return None


# ---------------------------------------------------------------------------
# مشاهده جریمه‌ها (همه اعضا)
# ---------------------------------------------------------------------------

def _view_fines_sync(tg: str) -> Tuple[Optional[str], Optional[str], Any]:
    with get_db() as db:
        user = get_active_user(db, tg)
        if not user or not user.is_active or not user.league_id:
            return "⚠️ شما هنوز عضو هیچ لیگی نیستید.", None, None
        lg = _get_league(db, user.league_id)
        if not lg or not lg.fines_enabled:
            return "ℹ️ سیستم جریمه برای لیگ شما فعال نیست.", None, None
        return None, _build_fines_text(db, lg, tg), _fines_view_kb(db, lg, tg)


@fine_router.message(F.text == VIEW_FINES_TEXT)
async def handle_view_fines(message: Message, state: FSMContext) -> None:
    await state.clear()
    tg = str(message.from_user.id)
    err, text, kb = await asyncio.to_thread(_view_fines_sync, tg)
    if err:
        await safe_answer(message, err)
        return
    await send_text_chunks(message.bot, message.chat.id, text, reply_markup=kb)


@fine_router.callback_query(F.data.startswith("fv:"))
async def cb_view_fines(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    tg = str(callback.from_user.id)
    lid = callback.data.split(":", 1)[1]

    def _work():
        with get_db() as db:
            lg = _get_league(db, lid)
            if not lg or not lg.fines_enabled:
                return None, None
            if not (
                _is_member(db, tg, lid)
                or fine_service.is_fine_manager(db, lid, tg)
                or is_user_admin(db, tg, lg.group_id)
            ):
                return None, None
            return _build_fines_text(db, lg, tg), _fines_view_kb(db, lg, tg)

    text, kb = await asyncio.to_thread(_work)
    await callback.answer()
    if not text:
        await safe_send(callback.bot, callback.message.chat.id, "⚠️ دسترسی یا سیستم جریمه فعال نیست.")
        return
    await send_text_chunks(callback.bot, callback.message.chat.id, text, reply_markup=kb)


# ---------------------------------------------------------------------------
# منوی پرداخت (مسئول جریمه)
# ---------------------------------------------------------------------------

def _guard_manager(db, tg: str, lid: str) -> Optional[League]:
    """لیگ را فقط در صورت فعال بودن جریمه و مسئول بودن tg برمی‌گرداند"""
    lg = _get_league(db, lid)
    if not lg or not lg.fines_enabled:
        return None
    if not fine_service.is_fine_manager(db, lid, tg):
        return None
    return lg


def _debtors_screen(db, lg: League, page: int) -> Tuple[str, InlineKeyboardMarkup]:
    fine_service.sync_league_fines(db, lg)
    debtors = fine_service.get_debtors(db, lg, include_inactive=True)
    total = fine_service.total_owed(debtors)
    pages = max(1, (len(debtors) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(max(0, page), pages - 1)
    chunk = debtors[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
    rows: List[List[InlineKeyboardButton]] = []
    for d in chunk:
        u = d["user"]
        inactive_mark = "" if d.get("active", True) else " (خارج‌شده)"
        rows.append(
            [
                _btn(
                    f"👤 {u.get_display_name()}{inactive_mark} — {format_toman(d['owed'])}",
                    f"fd:{lg.id}:{u.id}",
                )
            ]
        )
    nav: List[InlineKeyboardButton] = []
    if page > 0:
        nav.append(_btn("◀️ قبلی", f"fp:{lg.id}:{page - 1}"))
    if page < pages - 1:
        nav.append(_btn("بعدی ▶️", f"fp:{lg.id}:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([_btn("⚙️ تنظیم مبالغ", f"fa:m:{lg.id}")])
    rows.append([_btn("🔙 بازگشت به لیست لیگ‌ها", "fl:list")])
    if not debtors:
        text = f"💳 *پرداخت جریمه — {escape_md(lg.name)}*\n\n🎉 هیچ بدهکاری وجود ندارد."
    else:
        text = (
            f"💳 *پرداخت جریمه — {escape_md(lg.name)}*\n\n"
            f"برای ثبت پرداخت روی نام شخص بزنید:\n"
            f"📌 جمع بدهی‌ها: *{format_toman(total)}* (صفحه {page + 1} از {pages})"
        )
    return text, _nav_kb(rows)


def _managed_leagues_picker(db, tg: str) -> Tuple[Optional[str], Optional[str], Optional[InlineKeyboardMarkup]]:
    """لیست شیشه‌ای لیگ‌هایی که کاربر مسئول جریمه آنهاست"""
    leagues = fine_service.get_managed_leagues(db, tg)
    if not leagues:
        return "⚠️ شما مسئول جریمه هیچ لیگی نیستید.", None, None
    rows: List[List[InlineKeyboardButton]] = []
    for lg in leagues:
        fine_service.sync_league_fines(db, lg)
        debtors = fine_service.get_debtors(db, lg, include_inactive=True)
        total = fine_service.total_owed(debtors)
        debtors_count = len(debtors)
        badge = f" — {debtors_count} بدهکار ({format_toman(total)})" if debtors_count else " — بدون بدهکار"
        rows.append([_btn(f"🏆 {lg.name}{badge}", f"fp:{lg.id}:0")])
    text = (
        "💳 *پرداخت و مدیریت جریمه‌ها*\n\n"
        "لیست لیگ‌هایی که شما مسئول جریمه آنها هستید:\n"
        "جهت مشاهده اسامی بدهکاران و ثبت پرداخت، لیگ مورد نظر را انتخاب کنید:"
    )
    return None, text, _nav_kb(rows)


@fine_router.message(F.text.in_([PAY_FINES_TEXT, "💳 پرداخت جریمه‌ها", "پرداخت جریمه", "پرداخت جریمه‌ها"]))
async def handle_pay_fines_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    tg = str(message.from_user.id)

    def _work():
        with get_db() as db:
            return _managed_leagues_picker(db, tg)

    err, text, kb = await asyncio.to_thread(_work)
    if err:
        await safe_answer(message, err)
        return
    await safe_answer(message, text, reply_markup=kb)


@fine_router.callback_query(F.data == "fl:list")
async def cb_managed_leagues_list(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    tg = str(callback.from_user.id)

    def _work():
        with get_db() as db:
            return _managed_leagues_picker(db, tg)

    err, text, kb = await asyncio.to_thread(_work)
    await callback.answer()
    if err:
        await _edit(callback, err)
        return
    await _edit(callback, text, kb)


@fine_router.callback_query(F.data.startswith("fp:"))
async def cb_debtors_list(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    tg = str(callback.from_user.id)
    parts = callback.data.split(":")
    lid = parts[1]
    page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

    def _work():
        with get_db() as db:
            lg = _guard_manager(db, tg, lid)
            if not lg:
                return None
            return _debtors_screen(db, lg, page)

    res = await asyncio.to_thread(_work)
    if not res:
        await callback.answer("⛔️ دسترسی ندارید.", show_alert=True)
        return
    await callback.answer()
    await _edit(callback, res[0], res[1])


def _detail_screen(db, lg: League, uid: str) -> Optional[Tuple[str, InlineKeyboardMarkup]]:
    u = _get_ledger_user(db, lg.id, uid)
    if not u:
        return None
    bal = fine_service.get_user_balance(db, lg.id, uid)
    kinds = fine_service.count_active_fine_kinds(db, lg.id, uid)
    text = (
        f"👤 *{escape_md(u.get_display_name())}* — لیگ {escape_md(lg.name)}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🚫 غیبت‌ها: {kinds.get('absent', 0)} | ⏰ عدم اعلام: {kinds.get('late', 0)}\n"
        f"💰 کل جریمه: {format_toman(bal['fines'])}\n"
        f"✅ پرداخت‌شده: {format_toman(bal['paid'])}\n"
        f"📌 *مانده بدهی: {format_toman(bal['owed'])}*"
    )
    rows: List[List[InlineKeyboardButton]] = []
    if bal["owed"] > 0:
        rows.append([_btn(f"✅ تسویه کامل ({format_toman(bal['owed'])})", f"fs:{lg.id}:{uid}")])
        rows.append([_btn("✏️ ثبت مبلغ پرداختی", f"fe:{lg.id}:{uid}")])
    rows.append([_btn("🗂 جریمه‌ها / حذف", f"fw:{lg.id}:{uid}")])
    rows.append([_btn("🔙 بازگشت به لیست", f"fp:{lg.id}:0")])
    return text, _nav_kb(rows)


@fine_router.callback_query(F.data.startswith("fd:"))
async def cb_debtor_detail(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    tg = str(callback.from_user.id)
    _, lid, uid = callback.data.split(":", 2)

    def _work():
        with get_db() as db:
            lg = _guard_manager(db, tg, lid)
            if not lg:
                return None
            return _detail_screen(db, lg, uid)

    res = await asyncio.to_thread(_work)
    if not res:
        await callback.answer("⛔️ دسترسی ندارید یا کاربر یافت نشد.", show_alert=True)
        return
    await callback.answer()
    await _edit(callback, res[0], res[1])


@fine_router.callback_query(F.data.startswith("fs:"))
async def cb_settle_ask(callback: CallbackQuery) -> None:
    tg = str(callback.from_user.id)
    _, lid, uid = callback.data.split(":", 2)

    def _work():
        with get_db() as db:
            lg = _guard_manager(db, tg, lid)
            if not lg:
                return None
            u = _get_ledger_user(db, lid, uid)
            if not u:
                return None
            return u.get_display_name(), fine_service.get_user_balance(db, lid, uid)["owed"]

    res = await asyncio.to_thread(_work)
    if not res or res[1] <= 0:
        await callback.answer("⚠️ بدهی‌ای برای تسویه وجود ندارد.", show_alert=True)
        return
    await callback.answer()
    kb = _nav_kb(
        [
            [_btn("✅ بله، تسویه شد", f"fc:{lid}:{uid}")],
            [_btn("🔙 انصراف", f"fd:{lid}:{uid}")],
        ]
    )
    await _edit(
        callback,
        f"❓ تسویه کامل *{escape_md(res[0])}* به مبلغ *{format_toman(res[1])}* تایید می‌شود؟",
        kb,
    )


async def _notify_payment(bot, tg_target: str, lg_name: str, applied: int, owed_after: int) -> None:
    msg = (
        f"✅ پرداخت *{format_toman(applied)}* از جریمه‌های شما در لیگ «{escape_md(lg_name)}» ثبت شد.\n"
        + (f"📌 مانده بدهی: {format_toman(owed_after)}" if owed_after > 0 else "🎉 جریمه‌های شما کاملاً تسویه شد.")
    )
    await safe_send(bot, tg_target, msg)


@fine_router.callback_query(F.data.startswith("fc:"))
async def cb_settle_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    tg = str(callback.from_user.id)
    _, lid, uid = callback.data.split(":", 2)

    def _work():
        with get_db() as db:
            lg = _guard_manager(db, tg, lid)
            if not lg:
                return None
            u = _get_ledger_user(db, lid, uid)
            if not u:
                return None
            owed = fine_service.get_user_balance(db, lid, uid)["owed"]
            applied = fine_service.record_payment(db, lid, uid, owed, tg) if owed > 0 else 0
            screen = _debtors_screen(db, lg, 0)
            return applied, str(u.telegram_id), lg.name, screen

    res = await asyncio.to_thread(_work)
    if not res:
        await callback.answer("⛔️ دسترسی ندارید.", show_alert=True)
        return
    applied, target, lg_name, screen = res
    if applied <= 0:
        await callback.answer("⚠️ بدهی‌ای وجود نداشت.", show_alert=True)
    else:
        await callback.answer("✅ تسویه ثبت شد.")
        await _notify_payment(callback.bot, target, lg_name, applied, 0)
    await _edit(callback, screen[0], screen[1])


@fine_router.callback_query(F.data.startswith("fe:"))
async def cb_custom_amount_ask(callback: CallbackQuery, state: FSMContext) -> None:
    tg = str(callback.from_user.id)
    _, lid, uid = callback.data.split(":", 2)

    def _work():
        with get_db() as db:
            lg = _guard_manager(db, tg, lid)
            if not lg:
                return None
            u = _get_ledger_user(db, lid, uid)
            if not u:
                return None
            return u.get_display_name(), fine_service.get_user_balance(db, lid, uid)["owed"]

    res = await asyncio.to_thread(_work)
    if not res or res[1] <= 0:
        await callback.answer("⚠️ بدهی‌ای وجود ندارد.", show_alert=True)
        return
    await callback.answer()
    await state.set_state(FineStates.waiting_payment_amount)
    await state.update_data(fine_lid=lid, fine_uid=uid)
    await _edit(
        callback,
        f"✏️ مبلغ پرداختی *{escape_md(res[0])}* را به تومان وارد کنید (حداکثر {format_toman(res[1])}):",
        _nav_kb([[_btn("❌ لغو", f"fd:{lid}:{uid}")]]),
    )


@fine_router.message(StateFilter(FineStates.waiting_payment_amount))
async def process_payment_amount(message: Message, state: FSMContext) -> None:
    tg = str(message.from_user.id)
    data = await state.get_data()
    lid, uid = data.get("fine_lid"), data.get("fine_uid")
    amount = parse_amount(message.text or "")
    if not lid or not uid:
        await state.clear()
        await safe_answer(message, "⚠️ عملیات منقضی شد. دوباره از منوی پرداخت اقدام کنید.")
        return
    if amount is None or amount <= 0:
        await safe_answer(message, "❌ لطفاً فقط یک عدد صحیح مثبت (به تومان) وارد کنید:")
        return

    def _work():
        with get_db() as db:
            lg = _guard_manager(db, tg, lid)
            if not lg:
                return ("denied",)
            u = _get_ledger_user(db, lid, uid)
            if not u:
                return ("denied",)
            owed = fine_service.get_user_balance(db, lid, uid)["owed"]
            if amount > owed:
                return ("over", owed)
            applied = fine_service.record_payment(db, lid, uid, amount, tg)
            owed_after = fine_service.get_user_balance(db, lid, uid)["owed"]
            detail = _detail_screen(db, lg, uid)
            return ("ok", applied, str(u.telegram_id), lg.name, owed_after, detail)

    res = await asyncio.to_thread(_work)
    if res[0] == "denied":
        await state.clear()
        await safe_answer(message, "⛔️ دسترسی ندارید.")
        return
    if res[0] == "over":
        await safe_answer(message, f"❌ مبلغ بیشتر از بدهی است (حداکثر {format_toman(res[1])}). دوباره وارد کنید:")
        return
    await state.clear()
    _, applied, target, lg_name, owed_after, detail = res
    await _notify_payment(message.bot, target, lg_name, applied, owed_after)
    await safe_answer(message, f"✅ پرداخت {format_toman(applied)} ثبت شد.")
    if detail:
        await safe_answer(message, detail[0], reply_markup=detail[1])


# ---------------------------------------------------------------------------
# بخشودگی / حذف جریمه‌ها
# ---------------------------------------------------------------------------

def _waive_screen(db, lg: League, uid: str) -> Tuple[str, InlineKeyboardMarkup]:
    recs = fine_service.get_user_fine_records(db, lg.id, uid)[:15]
    cyc = _cycle_numbers(db, lg.id)
    rows: List[List[InlineKeyboardButton]] = []
    for r in recs:
        label = f"چله {cyc.get(r.cycle_id, '؟')} | {KIND_LABELS.get(r.kind, r.kind)} روز {r.league_day} | {format_toman(r.amount)}"
        prefix = "↩️ بازگردانی: " if r.is_waived else "🗑 حذف: "
        rows.append([_btn(prefix + label, f"ft:{lg.id}:{r.id}")])
    rows.append([_btn("🔙 بازگشت", f"fd:{lg.id}:{uid}")])
    text = (
        "🗂 *جریمه‌های ثبت‌شده* (۱۵ مورد آخر)\n"
        "با زدن هر مورد، جریمه حذف (بخشوده) یا بازگردانده می‌شود."
        if recs
        else "🗂 هیچ جریمه‌ای ثبت نشده است."
    )
    return text, _nav_kb(rows)


@fine_router.callback_query(F.data.startswith("fw:"))
async def cb_waive_list(callback: CallbackQuery) -> None:
    tg = str(callback.from_user.id)
    _, lid, uid = callback.data.split(":", 2)

    def _work():
        with get_db() as db:
            lg = _guard_manager(db, tg, lid)
            return _waive_screen(db, lg, uid) if lg else None

    res = await asyncio.to_thread(_work)
    if not res:
        await callback.answer("⛔️ دسترسی ندارید.", show_alert=True)
        return
    await callback.answer()
    await _edit(callback, res[0], res[1])


@fine_router.callback_query(F.data.startswith("ft:"))
async def cb_waive_toggle(callback: CallbackQuery) -> None:
    tg = str(callback.from_user.id)
    _, lid, rid = callback.data.split(":", 2)

    def _work():
        with get_db() as db:
            lg = _guard_manager(db, tg, lid)
            if not lg or not rid.isdigit():
                return None
            rec = fine_service.toggle_waive(db, int(rid), lid, tg)
            if not rec:
                return None
            return rec.is_waived, _waive_screen(db, lg, rec.user_id)

    res = await asyncio.to_thread(_work)
    if not res:
        await callback.answer("⛔️ دسترسی ندارید یا رکورد یافت نشد.", show_alert=True)
        return
    await callback.answer("🗑 حذف شد." if res[0] else "↩️ بازگردانده شد.")
    await _edit(callback, res[1][0], res[1][1])


# ---------------------------------------------------------------------------
# اطلاع‌رسانی و بازسازی فوری کیبورد اعضا / مسئولین
# ---------------------------------------------------------------------------

def _build_refresh_outbox_sync(lid: str, text: str, extra_tgs: Optional[List[str]] = None,
                               skip_tgs: Optional[set] = None) -> List[Tuple[str, str, Any]]:
    """پیام + کیبورد جدید منوی اصلی برای تمام اعضای فعال لیگ (و شناسه‌های اضافه)"""
    skip = skip_tgs or set()
    with get_db() as db:
        tgs = [
            str(r[0])
            for r in db.query(User.telegram_id)
            .filter(User.league_id == lid, User.is_active == True)
            .distinct()
            .all()
        ]
        for t in extra_tgs or []:
            if str(t) not in tgs:
                tgs.append(str(t))
        outbox: List[Tuple[str, str, Any]] = []
        for tg in tgs:
            if tg in skip:
                continue
            try:
                kb = build_user_main_menu(db, tg)
            except Exception as exc:
                logger.warning(f"خطا در ساخت منوی {tg}: {exc}")
                continue
            outbox.append((tg, text, kb))
        return outbox


async def _refresh_league_keyboards(bot, lid: str, text: str, extra_tgs=None, skip_tgs=None) -> None:
    outbox = await asyncio.to_thread(_build_refresh_outbox_sync, lid, text, extra_tgs, skip_tgs)
    if outbox:
        await dispatch_outbox(bot, outbox, throttle=BroadcastThrottle())


async def _announce_new_manager(bot, lid: str, lg_name: str, manager_tg: str) -> None:
    """پیام تبریک/اعلام مسئولیت با دو دکمه شیشه‌ای + بازسازی فوری کیبورد مسئول"""
    kb = _nav_kb(
        [
            [_btn("📋 لیست جریمه‌ها", f"fv:{lid}")],
            [_btn("💳 پرداخت جریمه", f"fp:{lid}:0")],
        ]
    )
    await safe_send(
        bot,
        manager_tg,
        f"🎖 شما به عنوان *مسئول جریمه* لیگ «{escape_md(lg_name)}» انتخاب شدید.\n\n"
        "از این پس می‌توانید پرداخت‌ها را ثبت کنید، جریمه‌ها را حذف کنید و مبالغ را تنظیم نمایید.",
        reply_markup=kb,
    )

    def _kb():
        with get_db() as db:
            return build_user_main_menu(db, manager_tg)

    menu = await asyncio.to_thread(_kb)
    await safe_send(
        bot, manager_tg,
        "🔄 منوی شما به‌روز شد؛ گزینه‌های «مشاهده جریمه‌ها» و «پرداخت جریمه» اضافه شدند.",
        reply_markup=menu,
    )


# ---------------------------------------------------------------------------
# منوی مدیریت جریمه لیگ (ادمین مجموعه / مسئول جریمه)
# ---------------------------------------------------------------------------

def _roles(db, tg: str, lg: League) -> Tuple[bool, bool]:
    is_adm = is_user_admin(db, tg, lg.group_id)
    is_mgr = bool(lg.fines_enabled) and fine_service.is_fine_manager(db, lg.id, tg)
    return is_adm, is_mgr


def _manager_names(db, lid: str) -> List[Tuple[str, str]]:
    out = []
    for mtg in fine_service.get_manager_ids(db, lid):
        u = (
            db.query(User)
            .filter(User.telegram_id == mtg, User.league_id == lid, User.is_active == True)
            .first()
        ) or db.query(User).filter(User.telegram_id == mtg).first()
        if u:
            disp = u.get_display_name()
        elif is_user_admin(db, mtg):
            disp = f"ادمین ({mtg})"
        else:
            disp = f"کاربر {mtg}"
        out.append((mtg, disp))
    return out


def _menu_screen(db, lg: League, is_adm: bool) -> Tuple[str, InlineKeyboardMarkup]:
    managers = _manager_names(db, lg.id)
    status = "✅ فعال" if lg.fines_enabled else "⛔️ غیرفعال"
    mgr_txt = "، ".join(escape_md(n) for _, n in managers) if managers else "—"
    text = (
        f"💰 *مدیریت جریمه — {escape_md(lg.name)}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"وضعیت: {status}\n"
        f"{_amounts_line(lg)}\n"
        f"👥 مسئولین جریمه: {mgr_txt}"
    )
    rows: List[List[InlineKeyboardButton]] = []
    if is_adm:
        rows.append(
            [_btn("⛔️ غیرفعال‌سازی جریمه" if lg.fines_enabled else "✅ فعال‌سازی جریمه", f"fa:t:{lg.id}")]
        )
    if lg.fines_enabled or is_adm:
        rows.append(
            [
                _btn("🚫 مبلغ غیبت", f"fa:am:{lg.id}:a"),
                _btn("⏰ مبلغ عدم اعلام", f"fa:am:{lg.id}:l"),
            ]
        )
    if is_adm:
        rows.append([_btn("👥 مسئولین جریمه", f"fa:mg:{lg.id}")])
    if lg.fines_enabled:
        rows.append([_btn("📋 لیست جریمه‌ها", f"fv:{lg.id}"), _btn("💳 پرداخت", f"fp:{lg.id}:0")])
    return text, _nav_kb(rows)


def _auth_menu(db, tg: str, lid: str, need_admin: bool = False):
    lg = _get_league(db, lid)
    if not lg:
        return None, False, False
    is_adm, is_mgr = _roles(db, tg, lg)
    if need_admin and not is_adm:
        return None, is_adm, is_mgr
    if not (is_adm or is_mgr):
        return None, is_adm, is_mgr
    return lg, is_adm, is_mgr


@fine_router.callback_query(F.data.startswith("fa:m:"))
async def cb_fine_admin_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await _show_fine_menu(callback, state, callback.data.split(":", 2)[2])


async def _show_fine_menu(callback: CallbackQuery, state: FSMContext, lid: str) -> None:
    await state.clear()
    tg = str(callback.from_user.id)

    def _work():
        with get_db() as db:
            lg, is_adm, _ = _auth_menu(db, tg, lid)
            return _menu_screen(db, lg, is_adm) if lg else None

    res = await asyncio.to_thread(_work)
    if not res:
        await callback.answer("⛔️ دسترسی ندارید.", show_alert=True)
        return
    await callback.answer()
    await _edit(callback, res[0], res[1])


@fine_router.callback_query(F.data.startswith("fa:x:"))
async def cb_fine_cancel_input(callback: CallbackQuery, state: FSMContext) -> None:
    await _show_fine_menu(callback, state, callback.data.split(":", 2)[2])


def _picker_screen(
    db, lg: League, page: int, enabling: str, admin_tg: Optional[str] = None
) -> Tuple[str, InlineKeyboardMarkup]:
    managers = set(fine_service.get_manager_ids(db, lg.id))
    users = (
        db.query(User)
        .filter(User.league_id == lg.id, User.is_active == True)
        .order_by(User.name.asc())
        .all()
    )
    seen, cands = set(), []
    for u in users:
        t = str(u.telegram_id)
        if t in managers or t in seen:
            continue
        seen.add(t)
        cands.append(u)
    pages = max(1, (len(cands) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(max(0, page), pages - 1)
    rows: List[List[InlineKeyboardButton]] = []

    # دکمه‌های ویژه انتساب ادمین به عنوان مسئول جریمه
    if admin_tg and str(admin_tg) not in managers:
        rows.append([_btn("⭐️ تعیین خودم به عنوان مسئول این لیگ", f"fa:ps:{lg.id}:{admin_tg}:{enabling}")])
        grp_leagues = (
            db.query(League)
            .filter(League.group_id == lg.group_id, League.is_deleted == False)
            .all()
        )
        if len(grp_leagues) > 1:
            rows.append([_btn("🏢 تعیین خودم برای تمام لیگ‌های این مجموعه", f"fa:sgm:{lg.id}:{enabling}")])

    for u in cands[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]:
        rows.append([_btn(f"👤 {u.get_display_name()}", f"fa:ps:{lg.id}:{u.telegram_id}:{enabling}")])

    nav: List[InlineKeyboardButton] = []
    if page > 0:
        nav.append(_btn("◀️ قبلی", f"fa:pk:{lg.id}:{page - 1}:{enabling}"))
    if page < pages - 1:
        nav.append(_btn("بعدی ▶️", f"fa:pk:{lg.id}:{page + 1}:{enabling}"))
    if nav:
        rows.append(nav)
    rows.append([_btn("🔙 انصراف", f"fa:m:{lg.id}")])
    head = "برای فعال‌سازی جریمه، ابتدا *مسئول جریمه* را انتخاب کنید:" if enabling == "1" \
        else "یک نفر را به عنوان *مسئول جریمه* انتخاب کنید:"
    if not cands and (not admin_tg or str(admin_tg) in managers):
        head = "⚠️ عضو دیگری برای انتخاب وجود ندارد."
    return f"👥 {head}\n(صفحه {page + 1} از {pages})", _nav_kb(rows)


@fine_router.callback_query(F.data.startswith("fa:t:"))
async def cb_toggle_fines(callback: CallbackQuery, state: FSMContext) -> None:
    tg = str(callback.from_user.id)
    lid = callback.data.split(":", 2)[2]

    def _work():
        with get_db() as db:
            lg, is_adm, _ = _auth_menu(db, tg, lid, need_admin=True)
            if not lg:
                return None
            if lg.fines_enabled:
                lg.fines_enabled = False
                db.commit()
                return ("disabled", lg.name, _menu_screen(db, lg, True))
            if not fine_service.get_manager_ids(db, lid):
                return ("pick", lg.name, _picker_screen(db, lg, 0, "1", admin_tg=tg))
            lg.fines_enabled = True
            db.commit()
            fine_service.sync_league_fines(db, lg)
            return ("enabled", lg.name, _menu_screen(db, lg, True), fine_service.get_manager_ids(db, lid))

    res = await asyncio.to_thread(_work)
    if not res:
        await callback.answer("⛔️ فقط ادمین مجموعه دسترسی دارد.", show_alert=True)
        return
    await callback.answer()
    kind, lg_name, screen = res[0], res[1], res[2]
    await _edit(callback, screen[0], screen[1])
    if kind == "disabled":
        await _refresh_league_keyboards(
            callback.bot, lid,
            f"ℹ️ سیستم جریمه لیگ «{escape_md(lg_name)}» غیرفعال شد.",
        )
    elif kind == "enabled":
        await _refresh_league_keyboards(
            callback.bot, lid,
            f"💰 سیستم جریمه لیگ «{escape_md(lg_name)}» فعال شد. از دکمه «مشاهده جریمه‌ها» می‌توانید وضعیت را ببینید.",
            skip_tgs=set(res[3]),
        )
        for mtg in res[3]:
            await _announce_new_manager(callback.bot, lid, lg_name, mtg)


@fine_router.callback_query(F.data.startswith("fa:pk:"))
async def cb_pick_manager(callback: CallbackQuery) -> None:
    tg = str(callback.from_user.id)
    parts = callback.data.split(":")
    lid = parts[2]
    page = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
    enabling = parts[4] if len(parts) > 4 else "0"

    def _work():
        with get_db() as db:
            lg, _, _ = _auth_menu(db, tg, lid, need_admin=True)
            return _picker_screen(db, lg, page, enabling, admin_tg=tg) if lg else None

    res = await asyncio.to_thread(_work)
    if not res:
        await callback.answer("⛔️ دسترسی ندارید.", show_alert=True)
        return
    await callback.answer()
    await _edit(callback, res[0], res[1])


@fine_router.callback_query(F.data.startswith("fa:ps:"))
async def cb_select_manager(callback: CallbackQuery) -> None:
    tg = str(callback.from_user.id)
    parts = callback.data.split(":")
    lid, mtg = parts[2], parts[3]
    enabling = parts[4] if len(parts) > 4 else "0"

    def _work():
        with get_db() as db:
            lg, _, _ = _auth_menu(db, tg, lid, need_admin=True)
            if not lg:
                return None
            is_adm_cand = is_user_admin(db, mtg, lg.group_id)
            if not (_is_member(db, mtg, lid) or is_adm_cand):
                return None
            added = fine_service.add_manager(db, lid, mtg)
            newly_enabled = False
            if enabling == "1" and not lg.fines_enabled:
                lg.fines_enabled = True
                db.commit()
                newly_enabled = True
            fine_service.sync_league_fines(db, lg)
            return added, newly_enabled, lg.name, _menu_screen(db, lg, True), fine_service.get_manager_ids(db, lid)

    res = await asyncio.to_thread(_work)
    if not res:
        await callback.answer("⛔️ دسترسی ندارید یا شخص مجاز نیست.", show_alert=True)
        return
    added, newly_enabled, lg_name, screen, all_mgrs = res
    await callback.answer("✅ مسئول جریمه ثبت شد." if added else "ℹ️ قبلاً مسئول بوده است.")
    await _edit(callback, screen[0], screen[1])
    if newly_enabled:
        await _refresh_league_keyboards(
            callback.bot, lid,
            f"💰 سیستم جریمه لیگ «{escape_md(lg_name)}» فعال شد. از دکمه «مشاهده جریمه‌ها» می‌توانید وضعیت را ببینید.",
            skip_tgs=set(all_mgrs),
        )
        for m in all_mgrs:
            await _announce_new_manager(callback.bot, lid, lg_name, m)
    elif added:
        await _announce_new_manager(callback.bot, lid, lg_name, mtg)


@fine_router.callback_query(F.data.startswith("fa:sgm:"))
async def cb_set_group_manager(callback: CallbackQuery) -> None:
    tg = str(callback.from_user.id)
    parts = callback.data.split(":")
    lid = parts[2]
    enabling = parts[3] if len(parts) > 3 else "0"

    def _work():
        with get_db() as db:
            lg, _, _ = _auth_menu(db, tg, lid, need_admin=True)
            if not lg:
                return None
            auto_enable = (enabling == "1")
            count = fine_service.set_group_fine_manager(db, lg.group_id, tg, auto_enable=auto_enable)
            if enabling == "1" and not lg.fines_enabled:
                lg.fines_enabled = True
                db.commit()
            fine_service.sync_league_fines(db, lg)
            grp = db.query(Group).filter(Group.id == lg.group_id).first()
            grp_name = grp.name if grp else ""
            return count, grp_name, _menu_screen(db, lg, True)

    res = await asyncio.to_thread(_work)
    if not res:
        await callback.answer("⛔️ دسترسی ندارید.", show_alert=True)
        return
    count, grp_name, screen = res
    await callback.answer(
        f"✅ شما به عنوان مسئول جریمه تمام لیگ‌های مجموعه «{grp_name}» تعیین شدید.",
        show_alert=True,
    )
    await _edit(callback, screen[0], screen[1])
    await _announce_new_manager(callback.bot, lid, grp_name, tg)


@fine_router.callback_query(F.data.startswith("fa:mg:"))
async def cb_managers_screen(callback: CallbackQuery) -> None:
    await _show_managers(callback, callback.data.split(":", 2)[2])


async def _show_managers(callback: CallbackQuery, lid: str, answered: bool = False) -> None:
    tg = str(callback.from_user.id)

    def _work():
        with get_db() as db:
            lg, _, _ = _auth_menu(db, tg, lid, need_admin=True)
            if not lg:
                return None
            names = _manager_names(db, lid)
            rows = [[_btn(f"❌ حذف {n}", f"fa:rm:{lid}:{t}")] for t, n in names]
            mgr_ids = set(fine_service.get_manager_ids(db, lid))
            if tg not in mgr_ids:
                rows.append([_btn("⭐️ تعیین خودم به عنوان مسئول این لیگ", f"fa:ps:{lid}:{tg}:0")])

            grp_leagues = (
                db.query(League)
                .filter(League.group_id == lg.group_id, League.is_deleted == False)
                .all()
            )
            if len(grp_leagues) > 1:
                rows.append([_btn("🏢 تعیین خودم برای تمام لیگ‌های این مجموعه", f"fa:sgm:{lid}:0")])

            rows.append([_btn("➕ افزودن مسئول از اعضای لیگ", f"fa:pk:{lid}:0:0")])
            rows.append([_btn("🔙 بازگشت", f"fa:m:{lid}")])
            body = "\n".join(f"• {escape_md(n)}" for _, n in names) or "—"
            return f"👥 *مسئولین جریمه — {escape_md(lg.name)}*\n\n{body}", _nav_kb(rows)

    res = await asyncio.to_thread(_work)
    if not res:
        if not answered:
            await callback.answer("⛔️ دسترسی ندارید.", show_alert=True)
        return
    if not answered:
        await callback.answer()
    await _edit(callback, res[0], res[1])


@fine_router.callback_query(F.data.startswith("fa:rm:"))
async def cb_remove_manager(callback: CallbackQuery) -> None:
    tg = str(callback.from_user.id)
    parts = callback.data.split(":")
    lid, mtg = parts[2], parts[3]

    def _work():
        with get_db() as db:
            lg, _, _ = _auth_menu(db, tg, lid, need_admin=True)
            if not lg:
                return None
            mgrs = fine_service.get_manager_ids(db, lid)
            if lg.fines_enabled and len(mgrs) <= 1 and mtg in mgrs:
                return ("last",)
            fine_service.remove_manager(db, lid, mtg)
            return ("ok", lg.name)

    res = await asyncio.to_thread(_work)
    if not res:
        await callback.answer("⛔️ دسترسی ندارید.", show_alert=True)
        return
    if res[0] == "last":
        await callback.answer(
            "⚠️ جریمه فعال است و حداقل یک مسئول لازم است. ابتدا مسئول جدید اضافه یا جریمه را غیرفعال کنید.",
            show_alert=True,
        )
        return
    await callback.answer("✅ مسئول حذف شد.")
    await _show_managers(callback, lid, answered=True)
    await _refresh_league_keyboards(
        callback.bot, "-none-",
        f"ℹ️ شما دیگر مسئول جریمه لیگ «{escape_md(res[1])}» نیستید.",
        extra_tgs=[mtg],
    )


# ---------------------------------------------------------------------------
# تنظیم مبالغ جریمه
# ---------------------------------------------------------------------------

@fine_router.callback_query(F.data.startswith("fa:am:"))
async def cb_amount_ask(callback: CallbackQuery, state: FSMContext) -> None:
    tg = str(callback.from_user.id)
    parts = callback.data.split(":")
    lid, which = parts[2], parts[3]
    if which not in ("a", "l"):
        await callback.answer()
        return

    def _work():
        with get_db() as db:
            lg, _, _ = _auth_menu(db, tg, lid)
            if not lg:
                return None
            cur = lg.fine_absent_amount if which == "a" else lg.fine_late_amount
            return lg.name, int(cur or 0)

    res = await asyncio.to_thread(_work)
    if not res:
        await callback.answer("⛔️ دسترسی ندارید.", show_alert=True)
        return
    await callback.answer()
    await state.set_state(FineStates.waiting_amount_setting)
    await state.update_data(fine_lid=lid, fine_which=which)
    label = "غیبت" if which == "a" else "عدم اعلام"
    await _edit(
        callback,
        f"✏️ مبلغ جدید جریمه *{label}* لیگ «{escape_md(res[0])}» را به تومان وارد کنید.\n"
        f"مقدار فعلی: {format_toman(res[1])}\n"
        "(۰ یعنی بدون جریمه. جریمه‌های قبلی با مبلغ قدیمی باقی می‌مانند.)",
        _nav_kb([[_btn("❌ لغو", f"fa:x:{lid}")]]),
    )


@fine_router.message(StateFilter(FineStates.waiting_amount_setting))
async def process_amount_setting(message: Message, state: FSMContext) -> None:
    tg = str(message.from_user.id)
    data = await state.get_data()
    lid, which = data.get("fine_lid"), data.get("fine_which")
    amount = parse_amount(message.text or "")
    if amount is None:
        await safe_answer(message, "❌ لطفاً فقط یک عدد صحیح (به تومان) وارد کنید:")
        return

    def _work():
        with get_db() as db:
            lg, is_adm, _ = _auth_menu(db, tg, lid or "")
            if not lg:
                return None
            # ثبت جریمه‌های موجود با مبالغ قدیمی پیش از تغییر مبلغ
            fine_service.sync_league_fines(db, lg)
            if which == "a":
                lg.fine_absent_amount = amount
            else:
                lg.fine_late_amount = amount
            db.commit()
            # جریمه‌های جدید (روزهای ثبت‌نشده) با مبلغ جدید ساخته می‌شوند
            fine_service.sync_league_fines(db, lg)
            return _menu_screen(db, lg, is_adm)

    res = await asyncio.to_thread(_work)
    await state.clear()
    if not res:
        await safe_answer(message, "⛔️ دسترسی ندارید.")
        return
    await safe_answer(message, "✅ مبلغ جریمه ذخیره شد.")
    await safe_answer(message, res[0], reply_markup=res[1])
