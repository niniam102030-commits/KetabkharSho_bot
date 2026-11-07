#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت تست سرتاسری خودکار (Automated E2E Test Suite) پروژه «کتابخوارشو»
شامل شبیه‌سازی کامل ۱۰ سناریوی اصلی با دیتابیس موقت SQLite و MockBot
"""

import os
import sys
import tempfile
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# تنظیم متغیرهای محیطی پیش از ایمپورت ماژول‌های پروژه
TEMP_DB_DIR = tempfile.mkdtemp(prefix="ketabkharsho_e2e_")
TEMP_DB_PATH = os.path.join(TEMP_DB_DIR, "test_ketabkharsho.db")

os.environ["BOT_TOKEN"] = "123456789:AAH_TEST_TOKEN_KETABKHARSHO"
os.environ["API_URL"] = "https://tapi.bale.ai"
os.environ["ADMIN_IDS"] = "900001,900002"
os.environ["DATABASE_URL"] = f"sqlite:///{TEMP_DB_PATH}"
os.environ["DEFAULT_FLOOR"] = "20"
os.environ["LEAGUE_DURATION"] = "40"
os.environ["DEFAULT_HALF_COUPONS"] = "5"
os.environ["DEFAULT_ONE_MIN_COUPONS"] = "1"

from openpyxl import load_workbook
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from config import Config, settings
from database import (
    init_db,
    get_db,
    get_active_user,
    get_user_profiles,
    get_or_create_active_cycle,
    is_user_admin,
)
from models import (
    Group,
    GroupAdmin,
    League,
    Cycle,
    User,
    ActivityLog,
    CycleResult,
)
from services import DateService, ScoringService, ReportService, AbsenceService
from message_service import MessageService
from admin_handlers import (
    admin_router,
    AdminStates,
    cmd_create_group,
    process_cg_name,
    process_cg_password,
    cb_select_group_for_password,
    process_pg_new_password,
    cb_select_group_for_name,
    process_ng_new_name,
    cb_make_user_group_admin,
    cb_confirm_remove_group_admin,
    cmd_global_stats,
    cmd_add_league,
    cb_select_group_for_new_league,
    process_al_league_name,
    process_al_league_floor,
    cb_league_edit_floor,
    process_league_new_floor,
    cb_league_edit_cycle,
    process_league_new_cycle,
    cb_league_edit_date,
    process_league_new_date,
    cb_em_edit_term,
    process_em_new_term,
    cb_em_edit_msg,
    process_em_new_msg,
    cb_execute_user_add_second_league,
    cb_user_edit_name,
    process_user_new_name,
    cmd_broadcast,
    cb_broadcast_target_all,
    cb_broadcast_target_group,
    cb_broadcast_target_league,
    process_broadcast_text,
    cb_broadcast_confirm_send,
)
from handlers import (
    user_router,
    StudyStates,
    cmd_start,
    start_registration_or_new_group,
    process_group_password,
    process_register_first_name,
    process_register_last_name,
    cb_join_league,
    handle_log_study_today,
    handle_edit_study_today,
    handle_append_study_today,
    handle_log_study_yesterday,
    process_study_minutes,
    process_study_pages,
    handle_league_leaderboard,
    handle_user_profile,
    cb_switch_profile,
    midnight_job,
    send_daily_admin_reports,
    send_daily_user_reports,
    send_study_reminders,
)
from weekly_report import send_weekly_reports


# ===========================================================================
# کلاس‌های شبیه‌ساز (MockBot, MockMessage, MockCallbackQuery)
# ===========================================================================
class MockUser:
    def __init__(self, user_id: int | str, first_name: str = "کاربر", last_name: str = "تست"):
        self.id = int(user_id)
        self.first_name = first_name
        self.last_name = last_name
        self.full_name = f"{first_name} {last_name}".strip()


class MockChat:
    def __init__(self, chat_id: int | str):
        self.id = int(chat_id)


class MockBot:
    def __init__(self):
        self.id = 999999
        self.sent_messages: List[Dict[str, Any]] = []
        self.sent_documents: List[Dict[str, Any]] = []
        self.edited_messages: List[Dict[str, Any]] = []

    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        reply_markup=None,
        parse_mode: Optional[str] = None,
        **kwargs,
    ):
        entry = {
            "chat_id": str(chat_id),
            "text": text,
            "reply_markup": reply_markup,
            "parse_mode": parse_mode,
        }
        self.sent_messages.append(entry)
        return MockMessage(self, chat_id, text=text)

    async def send_document(
        self,
        chat_id: int | str,
        document: Any,
        caption: Optional[str] = None,
        **kwargs,
    ):
        file_path = getattr(document, "path", None)
        exists = bool(file_path and os.path.exists(file_path))
        size = os.path.getsize(file_path) if exists else 0
        entry = {
            "chat_id": str(chat_id),
            "file_path": str(file_path),
            "exists_at_send": exists,
            "size": size,
            "caption": caption or "",
        }
        self.sent_documents.append(entry)
        return entry


class MockMessage:
    def __init__(self, bot: MockBot, user_id: int | str, text: str = ""):
        self.bot = bot
        self.from_user = MockUser(user_id)
        self.chat = MockChat(user_id)
        self.text = text

    async def answer(self, text: str, reply_markup=None, parse_mode: Optional[str] = None, **kwargs):
        return await self.bot.send_message(
            chat_id=self.chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )

    async def edit_text(self, text: str, reply_markup=None, parse_mode: Optional[str] = None, **kwargs):
        entry = {
            "chat_id": str(self.chat.id),
            "text": text,
            "reply_markup": reply_markup,
            "parse_mode": parse_mode,
        }
        self.bot.edited_messages.append(entry)
        return self


class MockCallbackQuery:
    def __init__(self, bot: MockBot, user_id: int | str, data: str):
        self.bot = bot
        self.from_user = MockUser(user_id)
        self.message = MockMessage(bot, user_id, text="")
        self.data = data
        self.answered = False

    async def answer(self, text: Optional[str] = None, show_alert: bool = False, **kwargs):
        self.answered = True


def make_fsm(storage: MemoryStorage, bot_id: int, user_id: int | str) -> FSMContext:
    key = StorageKey(bot_id=bot_id, chat_id=int(user_id), user_id=int(user_id))
    return FSMContext(storage=storage, key=key)


# ===========================================================================
# اجرای ۱۰ سناریوی تست سرتاسری (E2E)
# ===========================================================================
async def run_all_tests() -> None:
    bot = MockBot()
    storage = MemoryStorage()

    SUPER_ADMIN_ID = 900001
    GROUP_ADMIN_ID = 800001
    USER_1_ID = 700001
    EARLY_USER_ID = 700002

    # -----------------------------------------------------------------------
    # سناریو ۱: راه‌اندازی اولیه (init_db)، ساخت گروه پیش‌فرض ۱ با رمز 1234 و ثبت سوپرادمین‌ها
    # -----------------------------------------------------------------------
    # اعتبارسنجی تطابق متغیرهای محیطی با کلاس تنظیمات (BALE_API_URL, CYCLE_DAYS, DEFAULT_LEAGUE_FLOOR, REPORTS_DIR)
    old_env = os.environ.copy()
    try:
        os.environ["BALE_API_URL"] = "https://custom-bale.example.com"
        os.environ.pop("API_URL", None)
        os.environ["CYCLE_DAYS"] = "50"
        os.environ.pop("LEAGUE_DURATION", None)
        os.environ["DEFAULT_LEAGUE_FLOOR"] = "25"
        os.environ.pop("DEFAULT_FLOOR", None)
        os.environ["REPORTS_DIR"] = "./custom_reports"

        custom_cfg = Config()
        assert custom_cfg.API_URL == "https://custom-bale.example.com"
        assert custom_cfg.BALE_API_URL == "https://custom-bale.example.com"
        assert custom_cfg.LEAGUE_DURATION == 50
        assert custom_cfg.CYCLE_DAYS == 50
        assert custom_cfg.DEFAULT_FLOOR == 25
        assert custom_cfg.DEFAULT_LEAGUE_FLOOR == 25
        assert custom_cfg.REPORTS_DIR == "./custom_reports"
    finally:
        os.environ.clear()
        os.environ.update(old_env)
        if os.path.exists("./custom_reports"):
            try:
                os.rmdir("./custom_reports")
            except OSError:
                pass

    init_db()
    with get_db() as db:
        g1 = db.query(Group).filter(Group.id == 1).first()
        assert g1 is not None and g1.password == "1234", "گروه ۱ با رمز 1234 ساخته نشد"
        sa_rows = db.query(GroupAdmin).filter(GroupAdmin.group_id == 1).all()
        sa_ids = {r.user_id for r in sa_rows}
        assert "900001" in sa_ids and "900002" in sa_ids, "سوپرادمین‌ها در گروه ۱ ثبت نشدند"
    print("✅ [PASS] Scenario 1: init_db, default group 1 (pwd 1234), and superadmins verified.")

    # -----------------------------------------------------------------------
    # سناریو ۱.۵: تست ارسال خودکار پیام استارتاپ/فعال‌سازی به ادمین‌ها
    # -----------------------------------------------------------------------
    from handlers import send_startup_notification
    before_startup_count = len(bot.sent_messages)
    sent_count = await send_startup_notification(bot)
    assert sent_count >= 2, f"پیام فعال‌سازی باید حداقل به ۲ ادمین ارسال شود، ولی برای {sent_count} ارسال شد"
    startup_msgs = bot.sent_messages[before_startup_count:]
    startup_recipients = {str(m["chat_id"]) for m in startup_msgs}
    assert "900001" in startup_recipients and "900002" in startup_recipients
    sample_notif = startup_msgs[0]["text"]
    assert "فعال شد" in sample_notif
    assert DateService.today_shamsi() in sample_notif
    assert DateService.now_iran_time_str()[:5] in sample_notif
    print("✅ [PASS] Scenario 1.5: Startup notification to admins with Shamsi date & Iran time verified.")

    # تست دستور /test_startup توسط ادمین
    from admin_handlers import cmd_test_startup_notification
    before_test_cmd = len(bot.sent_messages)
    await cmd_test_startup_notification(MockMessage(bot, SUPER_ADMIN_ID, "/test_startup"))
    assert len(bot.sent_messages) > before_test_cmd
    print("✅ [PASS] Scenario 1.6: /test_startup admin command verified.")

    # -----------------------------------------------------------------------
    # سناریو ۲: تست دستورات سوپرادمین (cg, رد رمز تکراری 1234, رمز 5678, pg, ng, ag, rg, gs)
    # -----------------------------------------------------------------------
    sa_fsm = make_fsm(storage, bot.id, SUPER_ADMIN_ID)
    await cmd_create_group(MockMessage(bot, SUPER_ADMIN_ID, "cg"), sa_fsm)
    assert await sa_fsm.get_state() == AdminStates.cg_waiting_name

    # تست عدم تداخل حروف دوحرفی ادمین (مثلاً "al") هنگامی که ادمین در استیت وارد کردن نام مجموعه است
    await process_cg_name(MockMessage(bot, SUPER_ADMIN_ID, "مجموعه فرهیختگان"), sa_fsm)
    assert await sa_fsm.get_state() == AdminStates.cg_waiting_password

    # تست رد شدن رمز کوتاه (کمتر از ۶ رقم)
    await process_cg_password(MockMessage(bot, SUPER_ADMIN_ID, "1234"), sa_fsm)
    assert await sa_fsm.get_state() == AdminStates.cg_waiting_password
    assert "۶" in bot.sent_messages[-1]["text"]

    # ثبت رمز معتبر ۶ رقمی
    await process_cg_password(MockMessage(bot, SUPER_ADMIN_ID, "567890"), sa_fsm)
    assert await sa_fsm.get_state() is None

    with get_db() as db:
        g2 = db.query(Group).filter(Group.id == 2).first()
        assert g2 is not None and g2.password == "567890" and g2.name == "مجموعه فرهیختگان"

    # تغییر رمز با pg به 9876 و برگشت به 5678
    await cb_select_group_for_password(MockCallbackQuery(bot, SUPER_ADMIN_ID, "adm_pwgrp_2"), sa_fsm)
    await process_pg_new_password(MockMessage(bot, SUPER_ADMIN_ID, "987654"), sa_fsm)
    with get_db() as db:
        assert db.query(Group).filter(Group.id == 2).first().password == "987654"
    await cb_select_group_for_password(MockCallbackQuery(bot, SUPER_ADMIN_ID, "adm_pwgrp_2"), sa_fsm)
    await process_pg_new_password(MockMessage(bot, SUPER_ADMIN_ID, "567890"), sa_fsm)

    # تغییر نام با ng
    await cb_select_group_for_name(MockCallbackQuery(bot, SUPER_ADMIN_ID, "adm_nggrp_2"), sa_fsm)
    await process_ng_new_name(MockMessage(bot, SUPER_ADMIN_ID, "باشگاه اندیشه"), sa_fsm)
    with get_db() as db:
        assert db.query(Group).filter(Group.id == 2).first().name == "باشگاه اندیشه"

    # افزودن ادمین با ag و حذف با rg
    await cb_make_user_group_admin(MockCallbackQuery(bot, SUPER_ADMIN_ID, f"adm_mkadm_{GROUP_ADMIN_ID}_1"))
    with get_db() as db:
        assert is_user_admin(db, GROUP_ADMIN_ID, 1) is True
    await cb_confirm_remove_group_admin(MockCallbackQuery(bot, SUPER_ADMIN_ID, f"adm_rmad_1_{GROUP_ADMIN_ID}"))
    with get_db() as db:
        assert is_user_admin(db, GROUP_ADMIN_ID, 1) is False
    # ثبت مجدد ادمین مجموعه ۱ برای سناریوی ۳
    await cb_make_user_group_admin(MockCallbackQuery(bot, SUPER_ADMIN_ID, f"adm_mkadm_{GROUP_ADMIN_ID}_1"))

    # آمار کلان gs
    await cmd_global_stats(MockMessage(bot, SUPER_ADMIN_ID, "gs"))
    assert "آمار کلان" in bot.sent_messages[-1]["text"]
    print("✅ [PASS] Scenario 2: Superadmin commands (cg, unique password, pg, ng, ag, rg, gs) verified.")

    # -----------------------------------------------------------------------
    # سناریو ۳: دستورات ادمین مجموعه (ساخت ۲ لیگ با al، ویرایش با el، شخصی‌سازی واژه‌نامه و پیام با em)
    # -----------------------------------------------------------------------
    ga_fsm = make_fsm(storage, bot.id, GROUP_ADMIN_ID)
    # ساخت لیگ ۱ در مجموعه ۱
    await cmd_add_league(MockMessage(bot, GROUP_ADMIN_ID, "al"), ga_fsm)
    assert await ga_fsm.get_state() == AdminStates.al_waiting_name
    await process_al_league_name(MockMessage(bot, GROUP_ADMIN_ID, "لیگ ستارگان"), ga_fsm)
    await process_al_league_floor(MockMessage(bot, GROUP_ADMIN_ID, "20"), ga_fsm)

    # ساخت لیگ ۲ در مجموعه ۱
    await cmd_add_league(MockMessage(bot, GROUP_ADMIN_ID, "al"), ga_fsm)
    await process_al_league_name(MockMessage(bot, GROUP_ADMIN_ID, "لیگ نخبگان"), ga_fsm)
    await process_al_league_floor(MockMessage(bot, GROUP_ADMIN_ID, "30"), ga_fsm)

    with get_db() as db:
        leagues_g1 = db.query(League).filter(League.group_id == 1).order_by(League.created_at.asc()).all()
        assert len(leagues_g1) == 2
        lg1_id, lg2_id = leagues_g1[0].id, leagues_g1[1].id

    # ویرایش کف مطالعه، شماره چله و تاریخ شروع شمسی لیگ ۱ (به ۴ روز قبل تا روز جاری = ۵ شود)
    await cb_league_edit_floor(MockCallbackQuery(bot, GROUP_ADMIN_ID, f"leagedit_floor_{lg1_id}"), ga_fsm)
    await process_league_new_floor(MockMessage(bot, GROUP_ADMIN_ID, "20"), ga_fsm)

    await cb_league_edit_cycle(MockCallbackQuery(bot, GROUP_ADMIN_ID, f"leagedit_cycle_{lg1_id}"), ga_fsm)
    await process_league_new_cycle(MockMessage(bot, GROUP_ADMIN_ID, "2"), ga_fsm)

    four_days_ago_shamsi = DateService.date_to_shamsi(DateService.today_date() - timedelta(days=4))
    await cb_league_edit_date(MockCallbackQuery(bot, GROUP_ADMIN_ID, f"leagedit_date_{lg1_id}"), ga_fsm)
    await process_league_new_date(MockMessage(bot, GROUP_ADMIN_ID, four_days_ago_shamsi), ga_fsm)

    with get_db() as db:
        lg1 = db.query(League).filter(League.id == lg1_id).first()
        assert lg1.floor == 20 and lg1.cycle_number == 2 and lg1.current_day == 5

    # شخصی‌سازی واژه‌نامه (میثاق -> عهد) و پیام خوش‌آمدگویی با em
    await cb_em_edit_term(MockCallbackQuery(bot, GROUP_ADMIN_ID, "em_edterm_1_meesaq"), ga_fsm)
    await process_em_new_term(MockMessage(bot, GROUP_ADMIN_ID, "عهد"), ga_fsm)

    await cb_em_edit_msg(MockCallbackQuery(bot, GROUP_ADMIN_ID, "em_edmsg_1_study_logged"), ga_fsm)
    await process_em_new_msg(MockMessage(bot, GROUP_ADMIN_ID, "📝 *ثبت مطالعه انجام شد!* (میثاق رعایت شد)"), ga_fsm)

    with get_db() as db:
        assert MessageService.get_term(db, 1, "meesaq") == "عهد"
        assert "عهد" in MessageService.get_message(db, 1, "study_logged")
    print("✅ [PASS] Scenario 3: Group admin commands (al, el floor/cycle/date, em terms & messages) verified.")

    # -----------------------------------------------------------------------
    # سناریو ۴: ثبت‌نام کاربر در مجموعه ۱، انتخاب لیگ ۱ و دریافت امتیاز هدیه همگام‌سازی (5 - 1) * 10 = 40
    # -----------------------------------------------------------------------
    u1_fsm = make_fsm(storage, bot.id, USER_1_ID)
    await start_registration_or_new_group(MockMessage(bot, USER_1_ID, "🚀 شروع ثبت نام"), u1_fsm)
    await process_group_password(MockMessage(bot, USER_1_ID, "۱۲۳۴"), u1_fsm)
    await process_register_first_name(MockMessage(bot, USER_1_ID, "علی"), u1_fsm)
    await process_register_last_name(MockMessage(bot, USER_1_ID, "محمدی"), u1_fsm)

    await cb_join_league(MockCallbackQuery(bot, USER_1_ID, f"join_{lg1_id}"), u1_fsm)
    with get_db() as db:
        u1 = get_active_user(db, USER_1_ID)
        assert u1 is not None and u1.id == str(USER_1_ID)
        assert u1.league_id == lg1_id
        assert u1.points == 40.0, f"امتیاز هدیه نادرست است: {u1.points}"
    print("✅ [PASS] Scenario 4: User registration, league selection, and sync gift points (40.0) verified.")

    # -----------------------------------------------------------------------
    # سناریو ۵ و ۶: تست ۴ حالت امتیازدهی، ویرایش مطالعه (edit)، افزودن زمان (append) و خروج با دکمه‌های منو
    # -----------------------------------------------------------------------
    # الف) تست خروج از استیت waiting_for_minutes با زدن دکمه «🏆 جدول لیگ» بدون دریافت خطای عدد
    await handle_log_study_today(MockMessage(bot, USER_1_ID, "📝 ثبت مطالعه امروز"), u1_fsm)
    assert await u1_fsm.get_state() == StudyStates.waiting_for_minutes
    await process_study_minutes(MockMessage(bot, USER_1_ID, "🏆 جدول لیگ"), u1_fsm)
    assert await u1_fsm.get_state() is None
    assert "جدول آنلاین" in bot.sent_messages[-1]["text"]

    # ب) حالت ۱: رسیدن کامل به میثاق (۲۰ دقیقه -> ۱۰ امتیاز، بدون مصرف سهمیه)
    await handle_log_study_today(MockMessage(bot, USER_1_ID, "📝 ثبت مطالعه امروز"), u1_fsm)
    await process_study_minutes(MockMessage(bot, USER_1_ID, "20"), u1_fsm)
    await process_study_pages(MockMessage(bot, USER_1_ID, "15"), u1_fsm)
    with get_db() as db:
        u1 = get_active_user(db, USER_1_ID)
        assert u1.points == 50.0 and u1.half_coupons == 5 and u1.one_min_coupons == 1

    # ج) حالت ۲ (از طریق ویرایش مطالعه امروز edit): نصف میثاق (۱۰ دقیقه -> ۱۰ امتیاز با مصرف ۱ سهمیه نصف میثاق)
    await handle_edit_study_today(MockMessage(bot, USER_1_ID, "🔄 ویرایش مطالعه امروز"), u1_fsm)
    await process_study_minutes(MockMessage(bot, USER_1_ID, "10"), u1_fsm)
    await process_study_pages(MockMessage(bot, USER_1_ID, "8"), u1_fsm)
    with get_db() as db:
        u1 = get_active_user(db, USER_1_ID)
        assert u1.points == 50.0 and u1.today_minutes == 10 and u1.half_coupons == 4 and u1.one_min_coupons == 1

    # د) تست افزودن زمان به ثبت امروز (append): افزودن ۱۰ دقیقه دیگر (مجموع ۲۰ دقیقه -> بازگشت سهمیه نصف میثاق به ۵!)
    await handle_append_study_today(MockMessage(bot, USER_1_ID, "➕ افزودن زمان به ثبت امروز"), u1_fsm)
    await process_study_minutes(MockMessage(bot, USER_1_ID, "10"), u1_fsm)
    await process_study_pages(MockMessage(bot, USER_1_ID, "7"), u1_fsm)
    with get_db() as db:
        u1 = get_active_user(db, USER_1_ID)
        assert u1.points == 50.0 and u1.today_minutes == 20 and u1.today_pages == 15
        assert u1.half_coupons == 5 and u1.one_min_coupons == 1

    # هـ) حالت ۳: ۱ دقیقه با مصرف سهمیه طلایی پس از اتمام سهمیه‌های نصف میثاق
    with get_db() as db:
        u1 = get_active_user(db, USER_1_ID)
        u1.half_coupons = 0
        u1.today_half_used = 0
        db.commit()
    await handle_edit_study_today(MockMessage(bot, USER_1_ID, "🔄 ویرایش مطالعه امروز"), u1_fsm)
    await process_study_minutes(MockMessage(bot, USER_1_ID, "2"), u1_fsm)
    await process_study_pages(MockMessage(bot, USER_1_ID, "2"), u1_fsm)
    with get_db() as db:
        u1 = get_active_user(db, USER_1_ID)
        assert u1.points == 50.0 and u1.one_min_coupons == 0 and u1.today_one_min_used == 1

    # و) حالت ۴: امتیاز تناسبی پس از اتمام تمام سهمیه‌ها (۵ دقیقه از ۲۰ دقیقه = ۲.۵ امتیاز)
    with get_db() as db:
        u1 = get_active_user(db, USER_1_ID)
        u1.today_one_min_used = 0
        u1.one_min_coupons = 0
        u1.half_coupons = 0
        db.commit()
    await handle_edit_study_today(MockMessage(bot, USER_1_ID, "🔄 ویرایش مطالعه امروز"), u1_fsm)
    await process_study_minutes(MockMessage(bot, USER_1_ID, "5"), u1_fsm)
    await process_study_pages(MockMessage(bot, USER_1_ID, "3"), u1_fsm)
    with get_db() as db:
        u1 = get_active_user(db, USER_1_ID)
        assert u1.points == 42.5 and u1.today_points == 2.5
    print("✅ [PASS] Scenario 5 & 6: All 4 scoring modes, edit/append coupon refund, and menu interruption verified.")

    # -----------------------------------------------------------------------
    # سناریو ۷: جاب نیمه‌شب (midnight_job)، ثبت غیبت، ثبت مطالعه دیروز (late)، حذف از absent و بازسازی streak
    # -----------------------------------------------------------------------
    with get_db() as db:
        u1 = get_active_user(db, USER_1_ID)
        # تنظیم تاریخ عضویت به ۳ روز قبل و حذف لاگ دیروز تا جاب نیمه‌شب برای دیروز (روز ۴ چله) غیبت ثبت کند
        u1.created_at = datetime.utcnow() - timedelta(days=3)
        db.commit()

    await midnight_job(bot, force=True)
    with get_db() as db:
        u1 = get_active_user(db, USER_1_ID)
        assert "4" in AbsenceService.parse_days_list(u1.absent_days_list) or 4 in AbsenceService.parse_days_list(u1.absent_days_list)
        assert u1.no_study_days >= 1

    # ثبت مطالعه دیروز با کسر ۵۰٪ امتیاز (۲۰ دقیقه -> ۱۰ امتیاز / ۲ = ۵ امتیاز)
    await handle_log_study_yesterday(MockMessage(bot, USER_1_ID, "⏳ ثبت مطالعه دیروز (با کسر ۵۰٪ امتیاز)"), u1_fsm)
    assert await u1_fsm.get_state() == StudyStates.waiting_for_minutes
    await process_study_minutes(MockMessage(bot, USER_1_ID, "20"), u1_fsm)
    await process_study_pages(MockMessage(bot, USER_1_ID, "12"), u1_fsm)

    with get_db() as db:
        u1 = get_active_user(db, USER_1_ID)
        assert 4 not in AbsenceService.parse_days_list(u1.absent_days_list), "روز ۴ از لیست غیبت حذف نشد"
        assert 4 in AbsenceService.parse_days_list(u1.late_days_list), "روز ۴ به لیست تاخیر اضافه نشد"
        assert u1.streak >= 2, f"زنجیره پس از ثبت دیروز بازسازی نشد: {u1.streak}"
    print("✅ [PASS] Scenario 7: midnight_job absence recording, late study logging, and streak reconstruction verified.")

    # -----------------------------------------------------------------------
    # سناریو ۸: چندپروفایلی (عضویت در لیگ دوم، switchprof_، و تجمیع یادآوری شبانه برای هر دو لیگ)
    # -----------------------------------------------------------------------
    await cb_execute_user_add_second_league(
        MockCallbackQuery(bot, GROUP_ADMIN_ID, f"adm_doaddl_{lg2_id}_{USER_1_ID}")
    )
    with get_db() as db:
        profs = get_user_profiles(db, USER_1_ID, only_active=True)
        assert len(profs) == 2, "پروفایل دوم ساخته نشد"
        prof2_id = [p.id for p in profs if p.id != str(USER_1_ID)][0]

    # تغییر پروفایل فعال به پروفایل اول
    await cb_switch_profile(MockCallbackQuery(bot, USER_1_ID, f"switchprof_{USER_1_ID}"), u1_fsm)
    with get_db() as db:
        assert get_active_user(db, USER_1_ID).id == str(USER_1_ID)

    # تست تغییر نام کاربر توسط ادمین و یکپارچگی نام در تمام پروفایل‌های موازی کاربر
    ga_fsm = make_fsm(storage, bot.id, GROUP_ADMIN_ID)
    await cb_user_edit_name(MockCallbackQuery(bot, GROUP_ADMIN_ID, f"adm_editname_{USER_1_ID}"), ga_fsm)
    await process_user_new_name(MockMessage(bot, GROUP_ADMIN_ID, "سید علی حسینی"), ga_fsm)
    with get_db() as db:
        profs = get_user_profiles(db, USER_1_ID, only_active=True)
        assert len(profs) == 2
        for p in profs:
            assert p.name == "سید علی حسینی", f"نام پروفایل {p.id} یکپارچه نشد: {p.name}"
            assert p.first_name == "سید"
            assert p.last_name == "علی حسینی"

    # تست ثبت‌نام مجدد کاربر با نام جدید و یکپارچگی نام در تمام پروفایل‌های موازی کاربر
    await start_registration_or_new_group(MockMessage(bot, USER_1_ID, "🚀 شروع ثبت نام"), u1_fsm)
    await process_group_password(MockMessage(bot, USER_1_ID, "۱۲۳۴"), u1_fsm)
    await process_register_first_name(MockMessage(bot, USER_1_ID, "مهدی"), u1_fsm)
    await process_register_last_name(MockMessage(bot, USER_1_ID, "کرمی"), u1_fsm)
    with get_db() as db:
        profs = get_user_profiles(db, USER_1_ID, only_active=True)
        assert len(profs) == 2
        for p in profs:
            assert p.name == "مهدی کرمی", f"نام پروفایل {p.id} در ثبت‌نام مجدد یکپارچه نشد: {p.name}"
            assert p.first_name == "مهدی"
            assert p.last_name == "کرمی"

    # تست اصلاح امتیاز هدیه همگام‌سازی کاربر با تغییر تاریخ شروع لیگ توسط ادمین
    with get_db() as db:
        u1_rec = db.query(User).filter(User.id == str(USER_1_ID)).first()
        pts_before = u1_rec.points  # 47.5 (عضویت در ۳ روز قبل: ۱۰ هدیه + ۳۷.۵ مطالعه)

    # الف) جلو بردن تاریخ شروع لیگ ۱ به ۲ روز قبل (عضویت کاربر در ۳ روز قبل قبل از شروع لیگ می‌افتد -> روز ۱ -> هدیه از ۱۰ به ۰ کاهش می‌یابد: ۳۷.۵)
    two_days_ago_shamsi = DateService.date_to_shamsi(DateService.today_date() - timedelta(days=2))
    await cb_league_edit_date(MockCallbackQuery(bot, GROUP_ADMIN_ID, f"leagedit_date_{lg1_id}"), ga_fsm)
    await process_league_new_date(MockMessage(bot, GROUP_ADMIN_ID, two_days_ago_shamsi), ga_fsm)
    with get_db() as db:
        u1_rec = db.query(User).filter(User.id == str(USER_1_ID)).first()
        assert u1_rec.points == pts_before - 10.0, f"امتیاز هدیه پس از جلو بردن تاریخ اصلاح نشد: {u1_rec.points}"

    # ب) عقب بردن تاریخ شروع لیگ ۱ به ۵ روز قبل (عضویت در ۳ روز قبل -> روز ۳ لیگ -> هدیه ۲۰: امتیاز = ۳۷.۵ + ۲۰ = ۵۷.۵)
    five_days_ago_shamsi = DateService.date_to_shamsi(DateService.today_date() - timedelta(days=5))
    await cb_league_edit_date(MockCallbackQuery(bot, GROUP_ADMIN_ID, f"leagedit_date_{lg1_id}"), ga_fsm)
    await process_league_new_date(MockMessage(bot, GROUP_ADMIN_ID, five_days_ago_shamsi), ga_fsm)
    with get_db() as db:
        u1_rec = db.query(User).filter(User.id == str(USER_1_ID)).first()
        assert u1_rec.points == pts_before + 10.0, f"امتیاز هدیه پس از عقب بردن تاریخ اصلاح نشد: {u1_rec.points}"

    # ج) بازگرداندن تاریخ شروع لیگ ۱ به ۴ روز قبل (روز جاری = ۵، روز عضویت = ۲ -> هدیه ۱۰، بازگشت به ۴۷.۵)
    await cb_league_edit_date(MockCallbackQuery(bot, GROUP_ADMIN_ID, f"leagedit_date_{lg1_id}"), ga_fsm)
    await process_league_new_date(MockMessage(bot, GROUP_ADMIN_ID, four_days_ago_shamsi), ga_fsm)
    with get_db() as db:
        u1_rec = db.query(User).filter(User.id == str(USER_1_ID)).first()
        assert u1_rec.points == pts_before, f"امتیاز هدیه پس از بازگرداندن تاریخ بازنشانی نشد: {u1_rec.points}"

    # صفر کردن ثبت امروز هر دو پروفایل برای تست تجمیع یادآوری شبانه
    with get_db() as db:
        for p in get_user_profiles(db, USER_1_ID, only_active=True):
            p.last_log_date = None
            p.today_minutes = 0
        db.commit()

    before_msg_count = len(bot.sent_messages)
    await send_study_reminders(bot, force=True)
    new_msgs = [m for m in bot.sent_messages[before_msg_count:] if m["chat_id"] == str(USER_1_ID)]
    assert len(new_msgs) == 1, "یادآوری شبانه باید در یک پیام واحد تجمیع شود"
    assert "لیگ ستارگان" in new_msgs[0]["text"] and "لیگ نخبگان" in new_msgs[0]["text"]
    print("✅ [PASS] Scenario 8: Multi-profile creation, profile switching, and aggregated night reminders verified.")

    # -----------------------------------------------------------------------
    # سناریو ۸.۵: ارسال پیام همگانی (Broadcast) توسط ادمین و تفکیک دسترسی سوپرادمین
    # -----------------------------------------------------------------------
    # ۱. عدم دسترسی ادمین معمولی به ارسال سراسری (کل سیستم)
    await cb_broadcast_target_all(MockCallbackQuery(bot, GROUP_ADMIN_ID, "admbc_target_all"), ga_fsm)
    assert await ga_fsm.get_state() is None

    # ۲. ارسال پیام همگانی توسط ادمین مجموعه به کل اعضای مجموعه ۱
    await cb_broadcast_target_group(MockCallbackQuery(bot, GROUP_ADMIN_ID, "admbc_tgt_grp_1"), ga_fsm)
    assert await ga_fsm.get_state() == AdminStates.bc_waiting_text
    await process_broadcast_text(MockMessage(bot, GROUP_ADMIN_ID, "📢 اطلاعیه مهم برای تمام اعضای مجموعه ۱"), ga_fsm)
    bc_before = len(bot.sent_messages)
    await cb_broadcast_confirm_send(MockCallbackQuery(bot, GROUP_ADMIN_ID, "admbc_confirm_send"), ga_fsm)
    bc_msgs = [m for m in bot.sent_messages[bc_before:] if m["chat_id"] == str(USER_1_ID)]
    assert len(bc_msgs) >= 1 and "📢 اطلاعیه مهم برای تمام اعضای مجموعه ۱" in bc_msgs[0]["text"]

    # ۳. ارسال پیام همگانی توسط ادمین به یک لیگ خاص (لیگ ۱)
    await cb_broadcast_target_league(MockCallbackQuery(bot, GROUP_ADMIN_ID, f"admbc_tgt_lg_{lg1_id}"), ga_fsm)
    await process_broadcast_text(MockMessage(bot, GROUP_ADMIN_ID, "🏆 پیام انگیزشی اعضای لیگ ستارگان"), ga_fsm)
    bc_before = len(bot.sent_messages)
    await cb_broadcast_confirm_send(MockCallbackQuery(bot, GROUP_ADMIN_ID, "admbc_confirm_send"), ga_fsm)
    bc_msgs = [m for m in bot.sent_messages[bc_before:] if m["chat_id"] == str(USER_1_ID)]
    assert len(bc_msgs) >= 1 and "🏆 پیام انگیزشی اعضای لیگ ستارگان" in bc_msgs[0]["text"]

    # ۴. ارسال پیام سراسری به کل کاربران سیستم توسط سوپرادمین
    sa_fsm = make_fsm(storage, bot.id, SUPER_ADMIN_ID)
    await cb_broadcast_target_all(MockCallbackQuery(bot, SUPER_ADMIN_ID, "admbc_target_all"), sa_fsm)
    assert await sa_fsm.get_state() == AdminStates.bc_waiting_text
    await process_broadcast_text(MockMessage(bot, SUPER_ADMIN_ID, "🌍 پیام سراسری سوپرادمین برای کل کاربران"), sa_fsm)
    bc_before = len(bot.sent_messages)
    await cb_broadcast_confirm_send(MockCallbackQuery(bot, SUPER_ADMIN_ID, "admbc_confirm_send"), sa_fsm)
    bc_msgs = [m for m in bot.sent_messages[bc_before:] if m["chat_id"] == str(USER_1_ID)]
    assert len(bc_msgs) >= 1 and "🌍 پیام سراسری سوپرادمین برای کل کاربران" in bc_msgs[0]["text"]
    print("✅ [PASS] Scenario 8.5: Broadcast flow with strict superadmin vs group admin permissions verified.")

    # -----------------------------------------------------------------------
    # سناریو ۹: تست تولید هر ۳ نوع فایل اکسل و اعتبارسنجی با openpyxl
    # -----------------------------------------------------------------------
    with get_db() as db:
        users_orm = db.query(User).filter(User.league_id == lg1_id).all()
        p1 = ReportService.generate_excel("لیگ ستارگان", users_orm, cycle_number=2, current_day=5, league_floor=20)
        p2 = ReportService.generate_excel(
            "لیگ دیکشنری",
            [{"name": "کاربر تستی", "points": 85.5, "minutes": 120, "pages": 60, "no_study": 1}],
            cycle_number=1,
            current_day=10,
            league_floor=20,
        )
        p3 = ReportService.generate_weekly_excel("لیگ ستارگان", users_orm, cycle_number=2, current_day=5, league_floor=20)
        p4 = ReportService.generate_cycle_history_excel(db, group_ids=[1])

    for excel_file in (p1, p2, p3, p4):
        assert os.path.exists(excel_file), f"فایل اکسل تولید نشد: {excel_file}"
        wb = load_workbook(excel_file)
        assert len(wb.sheetnames) >= 1
        ws = wb.active
        assert ws.sheet_view.rightToLeft is True
        wb.close()
        os.remove(excel_file)
    print("✅ [PASS] Scenario 9: All 3 Excel generators (User ORM, dict, weekly, multi-sheet history) verified.")

    # -----------------------------------------------------------------------
    # سناریو ۱۰: تست کامل پایان چله ۴۰ روزه در روز ۴۱ام به همراه کاربر سحرخیز قبل از ساعت ۸ صبح
    # -----------------------------------------------------------------------
    day_41_start_shamsi = DateService.date_to_shamsi(DateService.today_date() - timedelta(days=40))
    with get_db() as db:
        lg1 = db.query(League).filter(League.id == lg1_id).first()
        cyc1 = get_or_create_active_cycle(db, lg1)
        lg1.start_shamsi = day_41_start_shamsi
        cyc1.start_shamsi = day_41_start_shamsi
        lg1.cycle_number = 2
        cyc1.cycle_number = 2

        # ایجاد یک کاربر سحرخیز در لیگ ۱ که در چله قدیم ۱۰۰ امتیاز داشته و صبح روز ۴۱ام ۳۰ دقیقه مطالعه ثبت می‌کند
        early_user = User(
            id=str(EARLY_USER_ID),
            telegram_id=str(EARLY_USER_ID),
            group_id=1,
            name="سحرخیز کتابخوان",
            first_name="سحرخیز",
            last_name="کتابخوان",
            league_id=lg1_id,
            points=100.0,
            total_minutes=400,
            total_pages=200,
            streak=5,
            no_study_days=0,
            half_coupons=4,
            one_min_coupons=1,
            is_active=True,
        )
        db.add(early_user)

        # پاکسازی لاگ مطالعه امروز برای u1 تا به عنوان کاربر عادی بدون مطالعه صبحگاهی در سناریو ۱۰ بررسی شود
        db.query(ActivityLog).filter(
            ActivityLog.user_id == str(USER_1_ID),
            ActivityLog.log_date == DateService.today_str(),
        ).delete()
        u1_rec = db.query(User).filter(User.id == str(USER_1_ID)).first()
        u1_rec.today_minutes = 0
        u1_rec.today_pages = 0
        u1_rec.today_points = 0.0
        u1_rec.last_log_date = None
        db.commit()

    # ثبت مطالعه صبحگاهی توسط کاربر سحرخیز در روز ۴۱ قبل از ساعت ۸ صبح
    early_fsm = make_fsm(storage, bot.id, EARLY_USER_ID)
    await handle_log_study_today(MockMessage(bot, EARLY_USER_ID, "📝 ثبت مطالعه امروز"), early_fsm)
    await process_study_minutes(MockMessage(bot, EARLY_USER_ID, "30"), early_fsm)
    await process_study_pages(MockMessage(bot, EARLY_USER_ID, "25"), early_fsm)

    # اجرای جاب ساعت ۸ صبح روز ۴۱ام
    await send_daily_user_reports(bot, force=True)

    with get_db() as db:
        lg1 = db.query(League).filter(League.id == lg1_id).first()
        assert lg1.cycle_number == 3 and lg1.current_day == 1, "چله جدید از روز ۱ آغاز نشد"

        # بررسی اینکه فقط یک چله active برای لیگ وجود دارد
        active_cycles = db.query(Cycle).filter(Cycle.league_id == lg1_id, Cycle.status == "active").all()
        assert len(active_cycles) == 1 and active_cycles[0].cycle_number == 3, "تعداد چله‌های فعال نادرست است"

        # بررسی کارنامه ذخیره شده چله ۲ برای کاربر سحرخیز (باید بدون ۳۰ دقیقه صبح امروز یعنی ۱۰۰ امتیاز و ۴۰۰ دقیقه باشد)
        finished_cyc = db.query(Cycle).filter(Cycle.league_id == lg1_id, Cycle.cycle_number == 2).first()
        assert finished_cyc is not None and finished_cyc.status == "finished"
        early_res = (
            db.query(CycleResult)
            .filter(CycleResult.cycle_id == finished_cyc.id, CycleResult.user_id == str(EARLY_USER_ID))
            .first()
        )
        assert early_res is not None
        assert early_res.points == 100.0 and early_res.total_minutes == 400, (
            f"آمار چله قدیم سحرخیز به درستی تفکیک نشد: points={early_res.points}, mins={early_res.total_minutes}"
        )

        # بررسی انتقال مطالعه صبحگاهی سحرخیز به روز ۱ چله ۳
        eu_after = db.query(User).filter(User.id == str(EARLY_USER_ID)).first()
        assert eu_after.points == 10.0 and eu_after.total_minutes == 30 and eu_after.today_minutes == 30
        assert eu_after.streak == 1

        # بررسی صفر شدن آمار و زنجیره کاربر عادی برای چله ۳
        u1_after = db.query(User).filter(User.id == str(USER_1_ID)).first()
        assert u1_after.points == 0.0 and u1_after.total_minutes == 0 and u1_after.streak == 0

    print("✅ [PASS] Scenario 10: 40-day cycle rollover on Day 41 and early-riser log migration verified.")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    finally:
        # پاکسازی خودکار دیتابیس و دایرکتوری موقت تست
        from database import engine
        try:
            engine.dispose()
        except Exception:
            pass
        if os.path.exists(TEMP_DB_DIR):
            try:
                import shutil
                shutil.rmtree(TEMP_DB_DIR, ignore_errors=True)
            except Exception:
                pass
