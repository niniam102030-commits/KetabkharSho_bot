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
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

# تنظیم متغیرهای محیطی پیش از ایمپورت ماژول‌های پروژه
TEMP_DB_DIR = tempfile.mkdtemp(prefix="ketabkharsho_e2e_")
TEMP_DB_PATH = os.path.join(TEMP_DB_DIR, "test_ketabkharsho.db")

os.environ["BOT_TOKEN"] = "123456789:AAH_TEST_TOKEN_KETABKHARSHO"
os.environ["API_URL"] = "https://tapi.bale.ai"
os.environ["ADMIN_IDS"] = "900001,900002"
os.environ["DATABASE_URL"] = f"sqlite:///{TEMP_DB_PATH}"
os.environ["BACKUP_DIR"] = os.path.join(TEMP_DB_DIR, "backups")
os.environ["REPORTS_DIR"] = os.path.join(TEMP_DB_DIR, "reports")
os.environ["LOG_FILE"] = os.path.join(TEMP_DB_DIR, "test.log")
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
    _midnight_job_sync,
    reset_league_members_for_new_start,
    cleanse_prestart_activity_and_scores,
    _build_study_reminders_outbox_sync,
    user_can_log_late,
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

    async def download(self, document: Any, destination: Any):
        file_path = getattr(document, "file_path", None) or getattr(document, "path", None)
        if file_path and os.path.exists(file_path):
            import shutil
            shutil.copyfile(file_path, str(destination))
        return destination

    async def get_file(self, file_id: str):
        class _FileInfo:
            def __init__(self, fid):
                self.file_path = fid
        return _FileInfo(file_id)

    async def download_file(self, file_path: str, destination: Any):
        if os.path.exists(file_path):
            import shutil
            shutil.copyfile(file_path, str(destination))
        return destination


class MockDocument:
    def __init__(self, file_path: str, file_name: str = "ketabkharsho.db", file_size: int = 1024, mime_type: str = "application/x-sqlite3"):
        self.file_id = file_path
        self.file_path = file_path
        self.file_name = file_name
        self.file_size = file_size
        self.mime_type = mime_type


class MockMessage:
    def __init__(self, bot: MockBot, user_id: int | str, text: str = "", document: Any = None):
        self.bot = bot
        self.from_user = MockUser(user_id)
        self.chat = MockChat(user_id)
        self.text = text
        self.document = document

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
        u1.created_at = datetime.now(timezone.utc) - timedelta(days=3)
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

    # -------------------------------------------------------------------------
    # Scenario 11: سیستم جریمه و تبدیل خودکار جریمه غیبت به عدم اعلام پس از ثبت دیرهنگام
    # -------------------------------------------------------------------------
    with get_db() as db:
        import fine_service
        from models import FineRecord

        # فعال‌سازی سیستم جریمه روی لیگ ۱ (چله پس از رولاور روی روز ۱ است؛ برای تست غیبت روز ۲ شروع را ۳ روز قبل قرار می‌دهیم)
        lg1 = db.query(League).filter(League.id == lg1_id).first()
        three_days_ago_shamsi = DateService.date_to_shamsi(DateService.today_date() - timedelta(days=3))
        lg1.start_shamsi = three_days_ago_shamsi
        lg1_cyc = get_or_create_active_cycle(db, lg1)
        lg1_cyc.start_shamsi = three_days_ago_shamsi
        lg1.fines_enabled = True
        lg1.fine_absent_amount = 10000  # ۱۰ هزار تومان غیبت
        lg1.fine_late_amount = 4000     # ۴ هزار تومان عدم اعلام
        fine_service.add_manager(db, lg1_id, SUPER_ADMIN_ID)
        assert fine_service.is_fine_manager(db, lg1_id, SUPER_ADMIN_ID)

        # تنظیم روز ۲ به عنوان غیبت برای کاربر ۱
        u1 = db.query(User).filter(User.id == str(USER_1_ID)).first()
        u1.absent_days_list = "2"
        u1.late_days_list = ""
        u1.no_study_days = 1
        db.commit()

        # همگام‌سازی جریمه‌ها (همانند اتفاقی که در جاب نیمه‌شب رخ می‌دهد)
        fine_service.sync_league_fines(db, lg1)

        # بررسی ایجاد جریمه غیبت ۱۰ هزار تومانی
        bal_before = fine_service.get_user_balance(db, lg1_id, u1.id)
        assert bal_before["fines"] == 10000 and bal_before["owed"] == 10000
        records = fine_service.get_user_fine_records(db, lg1_id, u1.id)
        assert len(records) == 1
        assert records[0].kind == "absent" and records[0].league_day == 2 and records[0].amount == 10000

        # شبیه‌سازی ثبت مطالعه دیروز (روز ۲) و تبدیل غیبت به اعلام دیرهنگام
        u1.absent_days_list = ""
        u1.late_days_list = "2"
        u1.no_study_days = 0
        db.commit()

        # همگام‌سازی مجدد جریمه‌ها (که در ثبت دیروز یا مشاهده پنل جریمه خودکار فراخوانی می‌شود)
        fine_service.sync_league_fines(db, lg1)

        # بررسی تبدیل جریمه غیبت به جریمه عدم اعلام ۴ هزار تومانی
        bal_after = fine_service.get_user_balance(db, lg1_id, u1.id)
        assert bal_after["fines"] == 4000 and bal_after["owed"] == 4000
        records_after = fine_service.get_user_fine_records(db, lg1_id, u1.id)
        assert len(records_after) == 1
        assert records_after[0].kind == "late" and records_after[0].league_day == 2 and records_after[0].amount == 4000

        # تسویه بدهی توسط مسئول
        paid_res = fine_service.record_payment(db, lg1_id, u1.id, 4000, SUPER_ADMIN_ID)
        assert paid_res == 4000
        bal_final = fine_service.get_user_balance(db, lg1_id, u1.id)
        assert bal_final["owed"] == 0

    print("✅ [PASS] Scenario 11: Fine system and automatic conversion of absence penalty to late penalty verified.")

    # -------------------------------------------------------------------------
    # Scenario 12: انتساب ادمین به عنوان مسئول جریمه گروه و نمایش شیشه‌ای لیگ‌ها در پرداخت
    # -------------------------------------------------------------------------
    with get_db() as db:
        from fine_handlers import _managed_leagues_picker, _debtors_screen

        # فعال‌سازی جریمه روی لیگ ۲ از گروه ۱
        lg2 = db.query(League).filter(League.id == lg2_id).first()
        lg2.fines_enabled = True
        lg2.fine_absent_amount = 8000
        lg2.fine_late_amount = 3000
        db.commit()

        # ادمین خودش را به عنوان مسئول جریمه تمام لیگ‌های گروه ۱ تعیین می‌کند
        assigned_count = fine_service.set_group_fine_manager(db, 1, GROUP_ADMIN_ID, auto_enable=False)
        assert assigned_count >= 1

        # بررسی اینکه ادمین اکنون مسئول چندین لیگ است
        admin_managed = fine_service.get_managed_leagues(db, GROUP_ADMIN_ID)
        assert len(admin_managed) >= 2
        managed_ids = [l.id for l in admin_managed]
        assert lg1_id in managed_ids and lg2_id in managed_ids

        # بررسی باز شدن منوی پرداخت جریمه: باید ابتدا لیست لیگ‌ها به صورت کلید شیشه‌ای بیاید
        err, text, kb = _managed_leagues_picker(db, str(GROUP_ADMIN_ID))
        assert err is None
        assert "لیست لیگ‌هایی که شما مسئول جریمه آنها هستید" in text
        # دکمه‌های شیشه‌ای باید شامل هر دو لیگ باشند
        button_callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert f"fp:{lg1_id}:0" in button_callbacks
        assert f"fp:{lg2_id}:0" in button_callbacks

        # انتخاب لیگ ۱: نمایش صفحه بدهکاران با دکمه بازگشت به لیست لیگ‌ها
        text_d, kb_d = _debtors_screen(db, lg1, 0)
        debtor_callbacks = [btn.callback_data for row in kb_d.inline_keyboard for btn in row]
        assert "fl:list" in debtor_callbacks

        # سناریوی ادمینی که در جدول User وجود ندارد:
        NON_USER_ADMIN_ID = "9988776655"
        db.add(GroupAdmin(group_id=1, user_id=NON_USER_ADMIN_ID))
        db.commit()
        fine_service.add_manager(db, lg1_id, NON_USER_ADMIN_ID)
        from fine_handlers import _manager_names, _menu_screen
        names = _manager_names(db, lg1_id)
        mgr_dict = dict(names)
        assert NON_USER_ADMIN_ID in mgr_dict
        assert "ادمین" in mgr_dict[NON_USER_ADMIN_ID]

        # بررسی باز شدن منوی مدیریت جریمه توسط ادمینی که کاربر نیست
        menu_text, menu_kb = _menu_screen(db, lg1, is_adm=True)
        assert "مدیریت جریمه" in menu_text

        # بررسی تابع get_all_manager_tg_ids
        all_mgr_ids = fine_service.get_all_manager_tg_ids(db)
        assert NON_USER_ADMIN_ID in all_mgr_ids
        assert str(GROUP_ADMIN_ID) in all_mgr_ids

    print("✅ [PASS] Scenario 12: Admin self-assignment to group fine management & inline league picker verified.")

    # -------------------------------------------------------------------------
    # Scenario 13: لیگ با تاریخ شروع در آینده (۵ روز بعد):
    # ۱. ثبت‌نام قبل از شروع لیگ: امتیاز هدیه صفر و امتیاز کاربر صفر.
    # ۲. مسدود بودن کامل ثبت مطالعه (امروز، ویرایش، افزودن، دیروز).
    # ۳. عدم ارسال یادآوری شبانه در دوران پیش‌ثبت‌نام.
    # ۴. صفر بودن قطعی امتیازات قبل از شروع و در لحظه شروع رسمی چله.
    # -------------------------------------------------------------------------
    with get_db() as db:
        future_date = DateService.today_date() + timedelta(days=5)
        future_shamsi = DateService.date_to_shamsi(future_date)

        # ساخت لیگ ۵ روز در آینده
        lg_future = League(
            group_id=1,
            name="لیگ آینده ۵ روز بعد",
            floor=15,
            start_shamsi=future_shamsi,
            current_day=0,
            is_active=True,
            cycle_number=1,
        )
        db.add(lg_future)
        db.commit()
        db.refresh(lg_future)
        cyc_future = get_or_create_active_cycle(db, lg_future, default_start_shamsi=future_shamsi)

        # بررسی متدهای سرویس تاریخ
        assert not DateService.league_has_started(future_shamsi)
        assert DateService.days_until_league_start(future_shamsi) == 5
        assert DateService.calculate_league_day(future_shamsi) == 0

        # کاربر جدید در دوره پیش‌ثبت‌نام ثبت‌نام می‌کند
        FUTURE_USER_TG = "8899001122"
        u_fut = User(
            id=FUTURE_USER_TG,
            telegram_id=FUTURE_USER_TG,
            group_id=1,
            name="کاربر پیش ثبت نام",
            league_id=lg_future.id,
            points=0.0,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(u_fut)
        db.commit()

        # ۱. امتیاز کاربر جدید حتماً باید صفر باشد
        assert u_fut.points == 0.0

        # ۲. بررسی عدم امکان ثبت مطالعه دیروز
        assert not user_can_log_late(db, u_fut)

        # ۳. بررسی یادآوری شبانه: کاربر نباید در اوت‌باکس یادآوری شبانه باشد
        rem_outbox = _build_study_reminders_outbox_sync(DateService.today_str(), force=True)
        rem_rcpts = [item[0] for item in rem_outbox]
        assert FUTURE_USER_TG not in rem_rcpts

        # ۴. شبیه‌سازی کاربری که قبل از شروع احیاناً امتیاز یا لاگی دارد
        u_fut.points = 25.0
        u_fut.total_minutes = 60
        u_fut.streak = 2
        fake_log = ActivityLog(
            user_id=u_fut.id,
            league_id=lg_future.id,
            cycle_id=cyc_future.id,
            minutes=60,
            points_earned=25.0,
            log_date=DateService.today_str(),
        )
        db.add(fake_log)
        db.commit()

        # صفر کردن در دوران پیش‌ثبت‌نام
        reset_league_members_for_new_start(db, lg_future, cyc_future)
        db.refresh(u_fut)
        assert u_fut.points == 0.0
        assert u_fut.total_minutes == 0
        assert u_fut.streak == 0
        remaining_logs = db.query(ActivityLog).filter(ActivityLog.league_id == lg_future.id).count()
        assert remaining_logs == 0

        # ۵. لحظه‌ی شروع لیگ (تغییر تاریخ به امروز): در جاب نیمه‌شب یا استارتاپ امتیاز همه صفر می‌شود
        today_shamsi = DateService.today_shamsi()
        lg_future.start_shamsi = today_shamsi
        cyc_future.start_shamsi = today_shamsi
        db.commit()

        # شبیه‌سازی امتیاز قبل از لحظه شروع
        u_fut.points = 10.0
        db.commit()

        _midnight_job_sync(DateService.today_str(), DateService.yesterday_str(), force=True)
        db.refresh(u_fut)
        assert u_fut.points == 0.0, "در لحظه شروع لیگ امتیاز کاربر صفر نشد"
        assert DateService.league_has_started(today_shamsi)

        # پس از شروع لیگ، کاربر در یادآوری شبانه قرار می‌گیرد
        rem_outbox_started = _build_study_reminders_outbox_sync(DateService.today_str(), force=True)
        started_rcpts = [item[0] for item in rem_outbox_started]
        assert FUTURE_USER_TG in started_rcpts

        # ۶. شبیه‌سازی دیپلوی سرور پس از شروع لیگ (مثلاً روز ۲ یا دیرتر) در حالتی که کاربر امتیاز قبل از شروع داشته است
        yesterday_date = DateService.yesterday_date()
        yesterday_shamsi = DateService.date_to_shamsi(yesterday_date)
        two_days_ago_str = (yesterday_date - timedelta(days=2)).strftime("%Y-%m-%d")
        yesterday_str = yesterday_date.strftime("%Y-%m-%d")

        lg_future.start_shamsi = yesterday_shamsi
        cyc_future.start_shamsi = yesterday_shamsi
        db.commit()

        # ثبت لاگ قبل از شروع (۲ روز قبل) با ۲۰ امتیاز + ثبت لاگ معتبر در روز ۱ (دیروز) با ۱۰ امتیاز
        db.add(ActivityLog(
            user_id=u_fut.id,
            league_id=lg_future.id,
            cycle_id=cyc_future.id,
            minutes=40,
            points_earned=20.0,
            log_date=two_days_ago_str,
        ))
        db.add(ActivityLog(
            user_id=u_fut.id,
            league_id=lg_future.id,
            cycle_id=cyc_future.id,
            minutes=20,
            points_earned=10.0,
            log_date=yesterday_str,
        ))
        u_fut.points = 30.0  # ۲۰ امتیاز قبل شروع + ۱۰ امتیاز دیروز
        u_fut.total_minutes = 60
        db.commit()

        # اجرای پالایش هوشمند (همانند اتفاقی که در استارتاپ بات رخ می‌دهد)
        cleanse_prestart_activity_and_scores(db, lg_future, cyc_future)
        db.refresh(u_fut)

        # ۲۰ امتیاز قبل از شروع باید کاملاً حذف شده باشد و فقط ۱۰ امتیاز دیروز باقی بماند
        assert u_fut.points == 10.0, f"امتیاز کاربر تصحیح نشد: {u_fut.points}"
        assert u_fut.total_minutes == 20
        # لاگ قبل از شروع باید حذف شده باشد
        pre_logs_count = db.query(ActivityLog).filter(
            ActivityLog.league_id == lg_future.id,
            ActivityLog.log_date == two_days_ago_str,
        ).count()
        assert pre_logs_count == 0
        valid_logs_count = db.query(ActivityLog).filter(
            ActivityLog.league_id == lg_future.id,
            ActivityLog.log_date == yesterday_str,
        ).count()
        assert valid_logs_count == 1

        # ۷. سناریوی چله‌های قبلی و لیگ‌های دیگر:
        # اطمینان از اینکه لاگ‌های مربوط به چله ۱ و لیگ‌های دیگر در صورت اجرای پالایش چله ۲ هرگز حذف نمی‌شوند
        past_cycle_log = ActivityLog(
            user_id=u_fut.id,
            league_id=lg_future.id,
            cycle_id=cyc_future.id,
            cycle_number=1,  # چله قبلی
            minutes=50,
            points_earned=25.0,
            log_date=two_days_ago_str,
        )
        db.add(past_cycle_log)

        # ساخت چله ۲
        cyc_future2 = Cycle(
            league_id=lg_future.id,
            cycle_number=2,
            start_shamsi=yesterday_shamsi,
            current_day=2,
            status="active",
        )
        lg_future.cycle_number = 2
        db.add(cyc_future2)
        db.commit()
        db.refresh(cyc_future2)

        # اجرای مجدد پالایش برای چله ۲
        cleanse_prestart_activity_and_scores(db, lg_future, cyc_future2)

        # لاگ چله ۱ نباید حذف شده باشد
        past_cycle_exists = db.query(ActivityLog).filter(
            ActivityLog.league_id == lg_future.id,
            ActivityLog.cycle_number == 1,
        ).first()
        assert past_cycle_exists is not None, "لاگ‌های چله قبلی به اشتباه حذف شدند!"

        # همچنین بررسی بازسازی و حفظ زنجیره استمرار کاربر
        db.refresh(u_fut)
        assert u_fut.streak >= 1, f"زنجیره استمرار کاربر برای روزهای معتبر حفظ نشد: {u_fut.streak}"

    print("✅ [PASS] Scenario 13: Future start date league (no reminders, blocked study logging, guaranteed score zeroing, past cycles preserved) verified.")

    # -------------------------------------------------------------------------
    # Scenario 14: قابلیت دریافت و پشتیبان‌گیری فایل خام دیتابیس (.db):
    # ۱. تابع هسته send_database_backup: ارسال اسنپ‌شات آنلاین به همراه آمار دقیق
    # ۲. دستور /backup: دسترسی مجاز فقط برای سوپرادمین‌ها و عدم دسترسی کاربر عادی
    # ۳. دکمه شیشه‌ای adm_menu_backup_db: ارسال فایل به ادمین
    # ۴. ارسال خودکار فایل دیتابیس به همراه گزارش‌های هفتگی اکسل جمعه‌ها
    # -------------------------------------------------------------------------
    from handlers import send_database_backup
    from admin_handlers import cmd_export_database, cb_menu_backup_db

    # ۱. تست مستقیم تابع هسته send_database_backup
    db_bot = MockBot()
    ok_backup = await send_database_backup(db_bot, [SUPER_ADMIN_ID], event_title="تست مستقیم بکاپ دیتابیس")
    assert ok_backup is True, "تهیه و ارسال اسنپ‌شات دیتابیس با شکست مواجه شد"
    assert len(db_bot.sent_documents) >= 1
    doc_entry = db_bot.sent_documents[-1]
    assert doc_entry["chat_id"] == str(SUPER_ADMIN_ID)
    assert doc_entry["file_path"].endswith(".db")
    assert doc_entry["exists_at_send"] is True
    assert doc_entry["size"] > 0
    assert "نسخه پشتیبان پایگاه داده" in doc_entry["caption"]
    assert "تست مستقیم بکاپ دیتابیس" in doc_entry["caption"]

    # ۲. تست دستور متنی /backup
    # ۲.۱. کاربر غیرسوپرادمین (رد دسترسی)
    non_sa_bot = MockBot()
    await cmd_export_database(MockMessage(non_sa_bot, "998877", "/backup"))
    assert any("دسترسی به دریافت فایل پایگاه داده فقط مخصوص مدیران ارشد" in m["text"] for m in non_sa_bot.sent_messages)
    assert len(non_sa_bot.sent_documents) == 0

    # ۲.۲. سوپرادمین (تایید و ارسال سند)
    sa_bot = MockBot()
    await cmd_export_database(MockMessage(sa_bot, SUPER_ADMIN_ID, "/backup"))
    assert any("در حال تهیه نسخه پشتیبان" in m["text"] for m in sa_bot.sent_messages)
    assert len(sa_bot.sent_documents) == 1
    assert sa_bot.sent_documents[0]["file_path"].endswith(".db")

    # ۳. تست کال‌بک کوئری adm_menu_backup_db
    cb_bot = MockBot()
    cb_query_sa = MockCallbackQuery(cb_bot, SUPER_ADMIN_ID, "adm_menu_backup_db")
    await cb_menu_backup_db(cb_query_sa)
    assert len(cb_bot.sent_documents) == 1
    assert cb_bot.sent_documents[0]["file_path"].endswith(".db")

    # ۴. تست ارسال خودکار به همراه گزارش‌های هفتگی جمعه (send_weekly_reports)
    weekly_bot = MockBot()
    await send_weekly_reports(weekly_bot, force=True)
    weekly_db_docs = [
        d for d in weekly_bot.sent_documents
        if d["file_path"].endswith(".db") and "گزارش هفتگی" in d["caption"]
    ]
    assert len(weekly_db_docs) >= 1, "فایل دیتابیس در کنار گزارش‌های هفتگی دوره‌ای ارسال نشد"

    print("✅ [PASS] Scenario 14: On-demand database download & periodic automated database backup verified.")

    # -------------------------------------------------------------------------
    # Scenario 15: قابلیت ارسال فایل دیتابیس توسط ادمین و اعمال آن:
    # ۱. اعتبارسنجی فایل دیتابیس ارسالی (validate_sqlite_file)
    # ۲. هندلر دریافت فایل سند دیتابیس (handle_admin_database_upload)
    # ۳. ادغام هوشمند (Smart Merge): افزودن مجموعه‌ها، رمزها، کاربران، مسئولین جریمه و لاگ‌ها
    # ۴. جایگزینی کامل دیتابیس (Replace Restore)
    # -------------------------------------------------------------------------
    from database import validate_sqlite_file, restore_database_merge, restore_database_replace
    from admin_handlers import (
        handle_admin_database_upload,
        cb_apply_db_merge,
        cb_apply_db_replace,
        cb_apply_db_cancel,
        _PENDING_DB_UPLOADS,
    )
    import sqlite3

    donor_db_path = os.path.join(TEMP_DB_DIR, "donor_test.db")
    d_conn = sqlite3.connect(donor_db_path)
    with d_conn:
        d_conn.execute("CREATE TABLE groups (id INTEGER PRIMARY KEY, name VARCHAR(255), password VARCHAR(8), is_deleted BOOLEAN, created_at DATETIME);")
        d_conn.execute("CREATE TABLE group_admins (id INTEGER PRIMARY KEY, group_id INTEGER, user_id VARCHAR(100), created_at DATETIME);")
        d_conn.execute("CREATE TABLE leagues (id VARCHAR(50) PRIMARY KEY, group_id INTEGER, name VARCHAR(255), floor INTEGER, start_shamsi VARCHAR(10), current_day INTEGER, is_deleted BOOLEAN, is_active BOOLEAN, cycle_number INTEGER, fines_enabled BOOLEAN, archive_enabled BOOLEAN);")
        d_conn.execute("CREATE TABLE league_fine_managers (id INTEGER PRIMARY KEY, league_id VARCHAR(50), user_id VARCHAR(100), created_at DATETIME);")
        d_conn.execute("CREATE TABLE cycles (id INTEGER PRIMARY KEY, league_id VARCHAR(50), cycle_number INTEGER, start_shamsi VARCHAR(10), end_shamsi VARCHAR(10), current_day INTEGER, status VARCHAR(20), created_at DATETIME, finished_at DATETIME);")
        d_conn.execute("CREATE TABLE users (id VARCHAR(100) PRIMARY KEY, telegram_id VARCHAR(100), group_id INTEGER, name VARCHAR(255), first_name VARCHAR(255), last_name VARCHAR(255), league_id VARCHAR(50), points FLOAT, total_minutes INTEGER, total_pages INTEGER, streak INTEGER, no_study_days INTEGER, absent_days_list TEXT, late_days_list TEXT, half_coupons INTEGER, one_min_coupons INTEGER, user_floor INTEGER, last_log_date VARCHAR(10), today_minutes INTEGER, today_pages INTEGER, today_points FLOAT, today_half_used INTEGER, today_one_min_used INTEGER, is_active BOOLEAN, created_at DATETIME);")
        d_conn.execute("CREATE TABLE activity_logs (id INTEGER PRIMARY KEY, user_id VARCHAR(100), league_id VARCHAR(50), cycle_id INTEGER, cycle_number INTEGER, league_day INTEGER, minutes INTEGER, pages INTEGER, points_earned FLOAT, half_coupon_used INTEGER, one_min_coupon_used INTEGER, log_date VARCHAR(10), log_hour INTEGER, created_at DATETIME);")
        d_conn.execute("CREATE TABLE fine_records (id INTEGER PRIMARY KEY, user_id VARCHAR(100), league_id VARCHAR(50), cycle_id INTEGER, league_day INTEGER, kind VARCHAR(20), amount INTEGER, status VARCHAR(20), created_at DATETIME);")
        d_conn.execute("CREATE TABLE fine_payments (id INTEGER PRIMARY KEY, user_id VARCHAR(100), league_id VARCHAR(50), amount INTEGER, receipt_photo_id VARCHAR(255), tracking_code VARCHAR(100), status VARCHAR(20), approved_by VARCHAR(100), created_at DATETIME, reviewed_at DATETIME);")
        d_conn.execute("CREATE TABLE cycle_results (id INTEGER PRIMARY KEY, cycle_id INTEGER, user_id VARCHAR(100), user_name VARCHAR(255), final_rank INTEGER, points FLOAT, total_minutes INTEGER, total_pages INTEGER, streak INTEGER, no_study_days INTEGER, absent_days_list TEXT, late_days_list TEXT, half_coupons_used INTEGER, one_min_coupons_used INTEGER, half_coupons_remaining INTEGER, one_min_coupons_remaining INTEGER, created_at DATETIME);")
        d_conn.execute("CREATE TABLE group_messages (id INTEGER PRIMARY KEY, group_id INTEGER, key VARCHAR(50), text TEXT, updated_at DATETIME);")
        d_conn.execute("CREATE TABLE group_terms (id INTEGER PRIMARY KEY, group_id INTEGER, key VARCHAR(50), value VARCHAR(255), updated_at DATETIME);")
        d_conn.execute("CREATE TABLE system_states (key VARCHAR(100) PRIMARY KEY, value TEXT);")

        d_conn.execute("INSERT INTO groups VALUES (99, 'مجموعه نخبگان', '9876', 0, CURRENT_TIMESTAMP);")
        d_conn.execute("INSERT INTO leagues VALUES ('donor_league_1', 99, 'لیگ پیشرفته نخبگان', 20, '1405/08/01', 5, 0, 1, 1, 1, 1);")
        d_conn.execute("INSERT INTO league_fine_managers VALUES (1, 'donor_league_1', 'fine_mgr_99', CURRENT_TIMESTAMP);")
        d_conn.execute("INSERT INTO users VALUES ('user_donor_99', 'tg_donor_99', 99, 'امیر نخبگانی', 'امیر', 'نخبگانی', 'donor_league_1', 150.0, 300, 120, 5, 0, '', '', 3, 3, 20, '2026-11-20', 40, 20, 15.0, 0, 0, 1, CURRENT_TIMESTAMP);")
        d_conn.execute("INSERT INTO activity_logs VALUES (1, 'user_donor_99', 'donor_league_1', 1, 1, 5, 40, 20, 15.0, 0, 0, '2026-11-20', 14, CURRENT_TIMESTAMP);")
        d_conn.execute("INSERT INTO fine_payments VALUES (1, 'user_donor_99', 'donor_league_1', 50000, 'rec_photo_99', 'TRK_99', 'approved', 'admin_tester', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);")
        d_conn.execute("INSERT INTO group_messages VALUES (1, 99, 'welcome', 'خوش آمدید به نخبگان', CURRENT_TIMESTAMP);")
        d_conn.execute("INSERT INTO group_terms VALUES (1, 99, 'league', 'لیگ حرفه‌ای', CURRENT_TIMESTAMP);")
        d_conn.execute("INSERT INTO system_states VALUES ('donor_test_key', 'donor_test_value');")
    d_conn.close()

    # ۱. تست اعتبارسنجی
    val_ok, _, stats = validate_sqlite_file(donor_db_path)
    assert val_ok is True
    assert stats["groups_count"] == 1
    assert stats["users_count"] == 1

    # ۲. تست هندلر دریافت سند توسط سوپرادمین
    upload_bot = MockBot()
    doc = MockDocument(donor_db_path, "ketabkharsho_backup_donor.db", os.path.getsize(donor_db_path))
    msg_upload = MockMessage(upload_bot, SUPER_ADMIN_ID, text="", document=doc)
    await handle_admin_database_upload(msg_upload)

    # بررسی ثبت درخواست در لیست انتظار و ارائه گزینه‌های شیشه‌ای
    assert len(_PENDING_DB_UPLOADS) >= 1
    token = list(_PENDING_DB_UPLOADS.keys())[-1]
    last_msg = upload_bot.sent_messages[-1]
    assert "فایل پایگاه داده با موفقیت دریافت و اعتبارسنجی شد" in last_msg["text"]

    # ۳. تست ادغام هوشمند (Smart Merge)
    cb_merge = MockCallbackQuery(upload_bot, SUPER_ADMIN_ID, f"apply_db_merge_{token}")
    await cb_apply_db_merge(cb_merge)

    # بررسی وجود اطلاعات در دیتابیس فعال:
    with get_db() as db:
        g99 = db.query(Group).filter(Group.id == 99).first()
        assert g99 is not None, "گروه جدید ادغام نشد"
        assert g99.password == "9876", "رمز مجموعه جدید حفظ نشد"

        l_donor = db.query(League).filter(League.id == "donor_league_1").first()
        assert l_donor is not None, "لیگ جدید ادغام نشد"

        u_donor = db.query(User).filter(User.id == "user_donor_99").first()
        assert u_donor is not None, "کاربر جدید ادغام نشد"
        assert u_donor.points >= 150.0, "امتیازات کاربر حفظ نشد"

        act_log = db.query(ActivityLog).filter(ActivityLog.user_id == "user_donor_99").first()
        assert act_log is not None, "لاگ مطالعه ادغام نشد"

        from models import FinePayment, GroupMessage, GroupTerm
        fp_merged = db.query(FinePayment).filter(FinePayment.user_id == "user_donor_99").first()
        assert fp_merged is not None, "رکورد پرداخت جریمه ادغام نشد"
        assert fp_merged.amount == 50000, "مبلغ پرداخت جریمه نادرست است"
        assert fp_merged.recorded_by == "admin_tester", "ثبت‌کننده پرداخت جریمه نادرست است"

        gm_merged = db.query(GroupMessage).filter(GroupMessage.group_id == 99, GroupMessage.msg_key == "welcome").first()
        assert gm_merged is not None, "پیام سفارشی گروه ادغام نشد"
        assert gm_merged.custom_text == "خوش آمدید به نخبگان", "متن پیام سفارشی نادرست است"

        gt_merged = db.query(GroupTerm).filter(GroupTerm.group_id == 99, GroupTerm.term_key == "league").first()
        assert gt_merged is not None, "اصطلاح سفارشی گروه ادغام نشد"
        assert gt_merged.custom_term == "لیگ حرفه‌ای", "مقدار اصطلاح سفارشی نادرست است"

        from database import get_system_state
        assert get_system_state(db, "donor_test_key") == "donor_test_value", "وضعیت سیستمی ادغام نشد"

        # اطمینان از دست‌نخورده ماندن دیتای قبلی (گروه شماره ۱ و کاربرانش)
        g1 = db.query(Group).filter(Group.id == 1).first()
        assert g1 is not None, "گروه قبلی در اثر ادغام حذف شد!"

    print("✅ [PASS] Scenario 15: Upload database, validation, smart merge & full restore verified.")

    # -------------------------------------------------------------------------
    # Scenario 16: فعال‌سازی دسترسی سوپرادمین با ارسال شناسه عددی یکی از ادمین‌های ریشه (ADMIN_IDS):
    # ۱. کاربر عادی ابتدا سوپرادمین نیست و عبارت قدیمی ali102030 دیگر معتبر نیست
    # ۲. ارسال شناسه عددی یکی از ادمین‌های ریشه (SUPER_ADMIN_ID)
    # ۳. ترفیع به سوپرادمین در حافظه، اطلاع‌رسانی به سایر سوپرادمین‌ها با دکمه عزل، و ثبت در system_states
    # ۴. پایداری دسترسی پس از فراخوانی مجدد init_db()
    # -------------------------------------------------------------------------
    from admin_handlers import cmd_claim_superadmin, _matches_superadmin_root_id
    from database import get_system_state

    TEST_PROMOTEE_ID = "5544332211"
    assert not settings.is_super_admin(TEST_PROMOTEE_ID)
    assert not _matches_superadmin_root_id("ali102030")
    assert not _matches_superadmin_root_id("Ali102030")
    assert not _matches_superadmin_root_id("999999999")
    assert _matches_superadmin_root_id(str(SUPER_ADMIN_ID))

    claim_bot = MockBot()
    claim_fsm = make_fsm(storage, claim_bot.id, TEST_PROMOTEE_ID)
    msg_claim = MockMessage(claim_bot, TEST_PROMOTEE_ID, text=str(SUPER_ADMIN_ID))
    await cmd_claim_superadmin(msg_claim, claim_fsm)

    # بررسی فعال شدن دسترسی و ارسال هشدار با دکمه عزل به سایر سوپرادمین‌ها
    assert settings.is_super_admin(TEST_PROMOTEE_ID)
    assert any("دسترسی مدیر ارشد (Superadmin) با موفقیت برای شما فعال شد" in m["text"] for m in claim_bot.sent_messages)
    assert any(
        str(m["chat_id"]) == str(SUPER_ADMIN_ID) and "هشدار امنیتی" in m["text"]
        for m in claim_bot.sent_messages
    ), "اعلان امنیتی به سایر سوپرادمین‌ها ارسال نشد!"

    # بررسی ثبت در دیتابیس
    with get_db() as db:
        val = get_system_state(db, f"superadmin_{TEST_PROMOTEE_ID}")
        assert val == "1"

    # شبیه‌سازی راه‌اندازی مجدد (init_db) و ماندگاری دسترسی
    settings.ADMIN_IDS = [SUPER_ADMIN_ID, "889977"]
    if hasattr(settings, "_extra_superadmins"):
        settings._extra_superadmins.clear()
    assert not settings.is_super_admin(TEST_PROMOTEE_ID)

    init_db()
    assert settings.is_super_admin(TEST_PROMOTEE_ID), "دسترسی سوپرادمین پس از ریستارت سرویس باقی نماند!"

    print("✅ [PASS] Scenario 16: Superadmin promotion via root ADMIN_IDS numeric ID (alert + persistence) verified.")

    # -------------------------------------------------------------------------
    # Scenario 17: عزل سوپرادمین جدید توسط سوپرادمین‌های قبلی با کلیدهای شیشه‌ای:
    # ۱. سوپرادمین اصلی لیست سوپرادمین‌ها را باز می‌کند
    # ۲. سوپرادمین اصلی درخواست عزل TEST_PROMOTEE_ID را ثبت می‌کند
    # ۳. تایید عزل، سلب دسترسی در حافظه و دیتابیس، و ارسال اعلان به کاربر
    # ۴. تضمین غیرقابل عزل بودن ادمین‌های ریشه (.env)
    # -------------------------------------------------------------------------
    from admin_handlers import (
        cb_menu_manage_superadmins,
        cb_revoke_sa_prompt,
        cb_revoke_sa_confirm,
    )
    from database import demote_super_admin

    # ۱. باز کردن منوی شیشه‌ای مدیریت سوپرادمین‌ها
    manage_bot = MockBot()
    cb_menu = MockCallbackQuery(manage_bot, SUPER_ADMIN_ID, "adm_menu_manage_superadmins")
    await cb_menu_manage_superadmins(cb_menu)
    last_msg = (manage_bot.edited_messages or manage_bot.sent_messages)[-1]
    assert "مدیریت مدیران ارشد ربات" in last_msg["text"]

    # ۲. مرحله تایید عزل برای TEST_PROMOTEE_ID
    prompt_bot = MockBot()
    cb_prompt = MockCallbackQuery(prompt_bot, SUPER_ADMIN_ID, f"revoke_sa_prompt_{TEST_PROMOTEE_ID}")
    await cb_revoke_sa_prompt(cb_prompt)
    prompt_msg = (prompt_bot.edited_messages or prompt_bot.sent_messages)[-1]
    assert "تایید عزل مدیر ارشد" in prompt_msg["text"]
    assert TEST_PROMOTEE_ID in prompt_msg["text"]

    # ۳. تایید قطعی عزل
    confirm_bot = MockBot()
    cb_confirm = MockCallbackQuery(confirm_bot, SUPER_ADMIN_ID, f"revoke_sa_confirm_{TEST_PROMOTEE_ID}")
    await cb_revoke_sa_confirm(cb_confirm)

    # بررسی سلب دسترسی در حافظه
    assert not settings.is_super_admin(TEST_PROMOTEE_ID), "سوپرادمین عزل‌شده هنوز در حافظه دسترسی دارد!"

    # بررسی حذف از دیتابیس
    with get_db() as db:
        val = get_system_state(db, f"superadmin_{TEST_PROMOTEE_ID}")
        assert val is None, "کلید سوپرادمین هنوز در system_state باقی مانده است!"
        ga = db.query(GroupAdmin).filter(GroupAdmin.group_id == 1, GroupAdmin.user_id == TEST_PROMOTEE_ID).first()
        assert ga is None, "کاربر عزل‌شده هنوز در group_admins گروه ۱ حضور دارد!"

    # بررسی ارسال پیام اعلان عزل به کاربر
    revoked_user_notif = [m for m in confirm_bot.sent_messages if m.get("chat_id") == TEST_PROMOTEE_ID]
    assert len(revoked_user_notif) >= 1, "پیام سلب دسترسی به کاربر ارسال نشد!"
    assert "لغو گردید" in revoked_user_notif[0]["text"]

    # ۴. بررسی عدم امکان عزل ادمین‌های ریشه (.env)
    demote_root_ok, _ = demote_super_admin(SUPER_ADMIN_ID)
    assert demote_root_ok is False, "ادمین ریشه نباید قابل عزل باشد!"
    assert settings.is_super_admin(SUPER_ADMIN_ID), "ادمین ریشه نباید دسترسی‌اش سلب شود!"

    print("✅ [PASS] Scenario 17: Superadmin revocation via inline buttons & root protection verified.")

    # -------------------------------------------------------------------------
    # Scenario 18: تست‌های رگرسیون ایمنی، همزمانی، ورودی یونیکد، پایداری کیبورد و ایزوله‌سازی چله
    # -------------------------------------------------------------------------
    # ۱. عدم کرش با ارقام بالانویس یونیکد («²») در تمام ورودی‌های عددی
    assert AbsenceService.parse_days_list("1,²,3") == [1, 3]
    u1_fsm_reg = make_fsm(storage, bot.id, USER_1_ID)
    await u1_fsm_reg.update_data(
        study_mode="fresh",
        study_user_id=str(USER_1_ID),
        study_init_date=DateService.today_str(),
    )
    await u1_fsm_reg.set_state(StudyStates.waiting_for_minutes)
    await process_study_minutes(MockMessage(bot, USER_1_ID, "²"), u1_fsm_reg)
    assert await u1_fsm_reg.get_state() == StudyStates.waiting_for_minutes
    await u1_fsm_reg.set_state(StudyStates.waiting_for_pages)
    await process_study_pages(MockMessage(bot, USER_1_ID, "²"), u1_fsm_reg)
    assert await u1_fsm_reg.get_state() == StudyStates.waiting_for_pages
    await u1_fsm_reg.clear()

    # ۲. اعتبارسنجی fallback متغیرهای محیطی خالی در Config (سازگاری با docker-compose)
    saved_env = os.environ.copy()
    try:
        os.environ["BALE_API_URL"] = ""
        os.environ["API_URL"] = ""
        os.environ["DEFAULT_LEAGUE_FLOOR"] = ""
        os.environ["DEFAULT_FLOOR"] = "25"
        os.environ["CYCLE_DAYS"] = ""
        os.environ["LEAGUE_DURATION"] = "35"
        cfg_empty = Config()
        assert cfg_empty.API_URL == "https://tapi.bale.ai"
        assert cfg_empty.DEFAULT_FLOOR == 25
        assert cfg_empty.LEAGUE_DURATION == 35
    finally:
        os.environ.clear()
        os.environ.update(saved_env)

    # ۳. جلوگیری از عضویت بین‌گروهی غیرمجاز توسط ادمین یک مجموعه دیگر
    CROSS_ADMIN_ID = "800099"
    with get_db() as db:
        db.add(GroupAdmin(group_id=2, user_id=CROSS_ADMIN_ID))
        lg_g2 = League(
            group_id=2,
            name="لیگ گروه ۲",
            floor=15,
            start_shamsi=DateService.today_shamsi(),
            is_active=True,
        )
        db.add(lg_g2)
        db.commit()
        db.refresh(lg_g2)
        lg_g2_id = lg_g2.id

    cross_bot = MockBot()
    await cb_execute_user_add_second_league(
        MockCallbackQuery(cross_bot, CROSS_ADMIN_ID, f"adm_doaddl_{lg_g2_id}:{USER_1_ID}")
    )
    with get_db() as db:
        cross_prof = (
            db.query(User)
            .filter(User.telegram_id == str(USER_1_ID), User.league_id == lg_g2_id)
            .first()
        )
        assert cross_prof is None, "ادمین گروه ۲ نباید بتواند کاربر گروه ۱ را بدون دسترسی عضو کند!"

    # ۴. محافظت در برابر انصراف تکراری/اشتباه از پروفایل دوم هنگام دابل‌کلیک confirm_cancel_league:{uid}
    from handlers import cb_confirm_cancel_league
    cancel_bot = MockBot()
    cancel_fsm = make_fsm(storage, cancel_bot.id, USER_1_ID)
    with get_db() as db:
        profs_before = get_user_profiles(db, USER_1_ID, only_active=True)
        assert len(profs_before) >= 2
        target_cancel_pid = profs_before[1].id
    await cb_confirm_cancel_league(
        MockCallbackQuery(cancel_bot, USER_1_ID, f"confirm_cancel_league:{target_cancel_pid}"),
        cancel_fsm,
    )
    # کلیک مجدد روی همان دکمه نباید پروفایل اول را غیرفعال کند
    await cb_confirm_cancel_league(
        MockCallbackQuery(cancel_bot, USER_1_ID, f"confirm_cancel_league:{target_cancel_pid}"),
        cancel_fsm,
    )
    with get_db() as db:
        profs_after = get_user_profiles(db, USER_1_ID, only_active=True)
        assert len(profs_after) == len(profs_before) - 1, "دابل‌کلیک انصراف نباید پروفایل دوم را حذف کند!"

    # ۵. عدم ارسال گزارش آرشیو بامداد در روز ۱ لیگ (وقتی force=False است)
    from handlers import _build_single_admin_report_sync
    day1_report = _build_single_admin_report_sync(lg_g2_id, force=False)
    assert day1_report is None, "آرشیو بامداد در روز ۱ چله نباید ارسال شود!"

    # ۶. اطمینان از عدم نگاشت cycle_id نامعتبر در restore_database_merge (سناریو ۱۵)
    with get_db() as db:
        merged_log = db.query(ActivityLog).filter(ActivityLog.user_id == "user_donor_99").first()
        assert merged_log is not None and merged_log.cycle_id is None, (
            f"لاگ ادغام‌شده بدون چله متناظر نباید به چله لیگ دیگری متصل شود: cycle_id={merged_log.cycle_id}"
        )

    # ۷. صفحه‌بندی فهرست بخشودگی جریمه برای بیش از ۱۰ رکورد
    from fine_handlers import _waive_screen
    from models import FineRecord
    with get_db() as db:
        lg1_obj = db.query(League).filter(League.id == lg1_id).first()
        cyc_cur = get_or_create_active_cycle(db, lg1_obj)
        for d_i in range(10, 23):
            db.add(
                FineRecord(
                    league_id=lg1_id,
                    user_id=str(USER_1_ID),
                    cycle_id=cyc_cur.id,
                    kind="absent",
                    league_day=d_i,
                    amount=5000,
                )
            )
        db.commit()
        w_txt0, w_kb0 = _waive_screen(db, lg1_obj, str(USER_1_ID), page=0)
        w_cbs0 = [b.callback_data for r in w_kb0.inline_keyboard for b in r]
        assert f"fw:{lg1_id}:{USER_1_ID}:1" in w_cbs0, "دکمه صفحه بعدی بخشودگی ساخته نشد"
        w_txt1, w_kb1 = _waive_screen(db, lg1_obj, str(USER_1_ID), page=1)
        w_cbs1 = [b.callback_data for r in w_kb1.inline_keyboard for b in r]
        assert f"fw:{lg1_id}:{USER_1_ID}:0" in w_cbs1, "دکمه صفحه قبلی بخشودگی ساخته نشد"

    print("✅ [PASS] Scenario 18: Regression suite (Unicode digits, env fallback, cross-group guard, double-cancel, Day-1 archive skip, merge cycle isolation, waive pagination) verified.")

    # -------------------------------------------------------------------------
    # Scenario 19: تست‌های تاییدشده (موارد ۳، ۴، ۵ و ۶)
    # -------------------------------------------------------------------------
    from admin_handlers import cb_execute_user_move_league
    from database import set_system_state, get_system_state, reload_superadmins_from_db

    # ۱. مورد ۳: جلوگیری از دریافت امتیاز هدیه روز ۴۰ برای عضویت در بامداد روز ۴۱ (پیش از رول‌اوور)
    day41_start = DateService.date_to_shamsi(
        DateService.today_date() - timedelta(days=settings.LEAGUE_DURATION)
    )
    assert DateService.calculate_raw_league_day(day41_start) == settings.LEAGUE_DURATION + 1

    with get_db() as db:
        lg_day41 = League(
            group_id=1,
            name="لیگ روز ۴۱",
            floor=10,
            start_shamsi=day41_start,
            is_active=True,
        )
        db.add(lg_day41)
        lg_donor_for_move = League(
            group_id=1,
            name="لیگ مبدا انتقال روز ۴۱",
            floor=10,
            start_shamsi=DateService.today_shamsi(),
            is_active=True,
        )
        db.add(lg_donor_for_move)
        db.flush()
        db.add(
            User(
                id="770102",
                telegram_id="770102",
                group_id=1,
                name="کاربر انتقال ۴۱",
                league_id=lg_donor_for_move.id,
                points=25.0,
                is_active=True,
            )
        )
        db.add(
            User(
                id="770103",
                telegram_id="770103",
                group_id=1,
                name="کاربر لیگ دوم ۴۱",
                league_id=lg_donor_for_move.id,
                points=10.0,
                is_active=True,
            )
        )
        db.commit()
        lg_day41_id = lg_day41.id

    d41_bot = MockBot()
    d41_join_fsm = make_fsm(storage, d41_bot.id, "770101")
    await cb_join_league(
        MockCallbackQuery(d41_bot, "770101", f"join_{lg_day41_id}"),
        d41_join_fsm,
    )
    await cb_execute_user_move_league(
        MockCallbackQuery(d41_bot, SUPER_ADMIN_ID, f"adm_domove_{lg_day41_id}:770102")
    )
    await cb_execute_user_add_second_league(
        MockCallbackQuery(d41_bot, SUPER_ADMIN_ID, f"adm_doaddl_{lg_day41_id}:770103")
    )

    with get_db() as db:
        u_d41_join = db.query(User).filter(User.telegram_id == "770101", User.league_id == lg_day41_id).first()
        u_d41_move = db.query(User).filter(User.telegram_id == "770102", User.league_id == lg_day41_id).first()
        u_d41_add = db.query(User).filter(User.telegram_id == "770103", User.league_id == lg_day41_id).first()
        assert u_d41_join is not None and u_d41_join.points == 0.0, f"عضویت در روز ۴۱ نباید امتیاز هدیه بدهد: {u_d41_join and u_d41_join.points}"
        assert u_d41_move is not None and u_d41_move.points == 0.0, f"انتقال به لیگ در روز ۴۱ نباید امتیاز هدیه بدهد: {u_d41_move and u_d41_move.points}"
        assert u_d41_add is not None and u_d41_add.points == 0.0, f"افزودن لیگ دوم در روز ۴۱ نباید امتیاز هدیه بدهد: {u_d41_add and u_d41_add.points}"

    u_join_msgs = [m["text"] for m in d41_bot.sent_messages if m["chat_id"] == "770101"]
    assert any("چله فعلی به پایان رسیده" in t for t in u_join_msgs), "پیام انتظار شروع چله جدید به کاربر روز ۴۱ ارسال نشد"

    # ۲. مورد ۴: اعلان ثبت‌نام عضو جدید به GroupAdminهای مجموعه + بدون تکرار برای سوپرادمین
    DEDICATED_G_ADMIN = "770011"
    with get_db() as db:
        if not db.query(GroupAdmin).filter(GroupAdmin.group_id == 2, GroupAdmin.user_id == DEDICATED_G_ADMIN).first():
            db.add(GroupAdmin(group_id=2, user_id=DEDICATED_G_ADMIN))
        if not db.query(GroupAdmin).filter(GroupAdmin.group_id == 2, GroupAdmin.user_id == str(SUPER_ADMIN_ID)).first():
            db.add(GroupAdmin(group_id=2, user_id=str(SUPER_ADMIN_ID)))
        db.commit()

    notif_bot = MockBot()
    notif_fsm = make_fsm(storage, notif_bot.id, "770201")
    await cb_join_league(
        MockCallbackQuery(notif_bot, "770201", f"join_{lg_g2_id}"),
        notif_fsm,
    )
    g2_adm_notifs = [
        m for m in notif_bot.sent_messages
        if m["chat_id"] == DEDICATED_G_ADMIN and "عضو جدید ثبت نام کرد" in m["text"]
    ]
    sa_notifs = [
        m for m in notif_bot.sent_messages
        if m["chat_id"] == str(SUPER_ADMIN_ID) and "عضو جدید ثبت نام کرد" in m["text"]
    ]
    assert len(g2_adm_notifs) == 1, f"اعلان ثبت‌نام به ادمین مجموعه ارسال نشد: {len(g2_adm_notifs)}"
    assert len(sa_notifs) == 1, f"اعلان ثبت‌نام نباید به سوپرادمین تکراری ارسال شود: {len(sa_notifs)}"

    # ۳. مورد ۵: پرسش استراتژی ادغام از سوپرادمین + اولویت دیتابیس زنده / اولویت فایل ارسالی + یکتایی رمز گروه + محافظت سوپرادمین
    with get_db() as db:
        set_system_state(db, "superadmin_5544332211", "1")
    reload_superadmins_from_db()
    with get_db() as db:
        g1_live = db.query(Group).filter(Group.id == 1).first()
        u1_live = db.query(User).filter(User.id == str(USER_1_ID)).first()
        live_g1_name = g1_live.name
        live_g1_pwd = g1_live.password
        live_u1_name = u1_live.name
        live_u1_points = u1_live.points
        assert get_system_state(db, "superadmin_5544332211") == "1"

    conflict_db_path = os.path.join(TEMP_DB_DIR, "conflict_donor.db")
    c_conn = sqlite3.connect(conflict_db_path)
    with c_conn:
        c_conn.execute("CREATE TABLE groups (id INTEGER PRIMARY KEY, name VARCHAR(255), password VARCHAR(8), is_deleted BOOLEAN, created_at DATETIME);")
        c_conn.execute("CREATE TABLE group_admins (id INTEGER PRIMARY KEY, group_id INTEGER, user_id VARCHAR(100), created_at DATETIME);")
        c_conn.execute("CREATE TABLE leagues (id VARCHAR(50) PRIMARY KEY, group_id INTEGER, name VARCHAR(255), floor INTEGER, start_shamsi VARCHAR(10), current_day INTEGER, is_deleted BOOLEAN, is_active BOOLEAN, cycle_number INTEGER, fines_enabled BOOLEAN, archive_enabled BOOLEAN);")
        c_conn.execute("CREATE TABLE users (id VARCHAR(100) PRIMARY KEY, telegram_id VARCHAR(100), group_id INTEGER, name VARCHAR(255), first_name VARCHAR(255), last_name VARCHAR(255), league_id VARCHAR(50), points FLOAT, total_minutes INTEGER, total_pages INTEGER, streak INTEGER, no_study_days INTEGER, absent_days_list TEXT, late_days_list TEXT, half_coupons INTEGER, one_min_coupons INTEGER, user_floor INTEGER, last_log_date VARCHAR(10), today_minutes INTEGER, today_pages INTEGER, today_points FLOAT, today_half_used INTEGER, today_one_min_used INTEGER, is_active BOOLEAN, created_at DATETIME);")
        c_conn.execute("CREATE TABLE activity_logs (id INTEGER PRIMARY KEY, user_id VARCHAR(100), league_id VARCHAR(50), cycle_id INTEGER, cycle_number INTEGER, league_day INTEGER, minutes INTEGER, pages INTEGER, points_earned FLOAT, half_coupon_used INTEGER, one_min_coupon_used INTEGER, log_date VARCHAR(10), log_hour INTEGER, created_at DATETIME);")
        c_conn.execute("CREATE TABLE fine_records (id INTEGER PRIMARY KEY, user_id VARCHAR(100), league_id VARCHAR(50), cycle_id INTEGER, league_day INTEGER, kind VARCHAR(20), amount INTEGER, status VARCHAR(20), created_at DATETIME);")
        c_conn.execute("CREATE TABLE system_state (key VARCHAR(100) PRIMARY KEY, value TEXT);")

        c_conn.execute("INSERT INTO groups VALUES (1, 'گروه یک آپلودی', '554433', 0, CURRENT_TIMESTAMP);")
        c_conn.execute("INSERT INTO groups VALUES (101, 'گروه جدید تکراری رمز', ?, 0, CURRENT_TIMESTAMP);", (live_g1_pwd,))
        c_conn.execute("INSERT INTO leagues VALUES (?, 1, 'لیگ تستی آپلودی', 15, '1405/08/01', 1, 0, 1, 1, 0, 1);", (lg1_id,))
        c_conn.execute("INSERT INTO users VALUES (?, ?, 1, 'کاربر یک آپلودی', 'کاربر', 'آپلودی', ?, 777.5, 100, 50, 2, 0, '', '', 5, 1, NULL, NULL, 0, 0, 0.0, 0, 0, 1, CURRENT_TIMESTAMP);", (str(USER_1_ID), str(USER_1_ID), lg1_id))
        c_conn.execute("INSERT INTO users VALUES ('user_merge_only_new', 'tg_merge_new', 101, 'عضو جدید ادغامی', 'عضو', 'جدید', ?, 55.0, 60, 20, 1, 0, '', '', 5, 1, NULL, NULL, 0, 0, 0.0, 0, 0, 1, CURRENT_TIMESTAMP);", (lg1_id,))
        c_conn.execute("INSERT INTO system_state VALUES ('superadmin_5544332211', '0');")
    c_conn.close()

    # ۳الف. ارسال فایل و بررسی نمایش هر دو گزینه ادغام + جایگزینی + انصراف
    merge_bot_live = MockBot()
    doc_live = MockDocument(conflict_db_path, "conflict_donor.db", os.path.getsize(conflict_db_path))
    await handle_admin_database_upload(MockMessage(merge_bot_live, SUPER_ADMIN_ID, text="", document=doc_live))
    tok_live = list(_PENDING_DB_UPLOADS.keys())[-1]
    prompt_kb = merge_bot_live.sent_messages[-1]["reply_markup"].inline_keyboard
    prompt_cbs = [btn.callback_data for row in prompt_kb for btn in row]
    assert f"apply_db_merge_live_{tok_live}" in prompt_cbs, "دکمه ادغام با اولویت دیتابیس زنده ساخته نشد"
    assert f"apply_db_merge_over_{tok_live}" in prompt_cbs, "دکمه ادغام با اولویت فایل ارسالی ساخته نشد"
    assert f"apply_db_replace_{tok_live}" in prompt_cbs, "دکمه جایگزینی کامل ساخته نشد"
    assert f"apply_db_cancel_{tok_live}" in prompt_cbs, "دکمه انصراف ساخته نشد"

    # ۳ب. اجرای ادغام با اولویت دیتابیس زنده (live_priority)
    await cb_apply_db_merge(MockCallbackQuery(merge_bot_live, SUPER_ADMIN_ID, f"apply_db_merge_live_{tok_live}"))
    assert any("تعارض رمز مجموعه" in m["text"] for m in merge_bot_live.sent_messages), "هشدار تعارض رمز مجموعه در گزارش ارسال نشد"

    with get_db() as db:
        g1_after_live = db.query(Group).filter(Group.id == 1).first()
        u1_after_live = db.query(User).filter(User.id == str(USER_1_ID)).first()
        u_new_after_live = db.query(User).filter(User.id == "user_merge_only_new").first()
        g101_after_live = db.query(Group).filter(Group.id == 101).first()
        assert g1_after_live.name == live_g1_name and g1_after_live.password == live_g1_pwd, "در حالت اولویت زنده نباید گروه موجود تغییر کند"
        assert u1_after_live.name == live_u1_name and u1_after_live.points == live_u1_points, "در حالت اولویت زنده نباید کاربر موجود تغییر کند"
        assert u_new_after_live is not None and u_new_after_live.points == 55.0, "رکورد جدید در حالت اولویت زنده ثبت نشد"
        assert g101_after_live is not None and g101_after_live.password != live_g1_pwd, "رمز تکراری برای مجموعه جدید تنظیم شد!"

    # ۳پ. ارسال مجدد فایل و اجرای ادغام با اولویت فایل ارسالی (uploaded_overwrite)
    merge_bot_over = MockBot()
    doc_over = MockDocument(conflict_db_path, "conflict_donor_over.db", os.path.getsize(conflict_db_path))
    await handle_admin_database_upload(MockMessage(merge_bot_over, SUPER_ADMIN_ID, text="", document=doc_over))
    tok_over = list(_PENDING_DB_UPLOADS.keys())[-1]
    await cb_apply_db_merge(MockCallbackQuery(merge_bot_over, SUPER_ADMIN_ID, f"apply_db_merge_over_{tok_over}"))

    with get_db() as db:
        g1_after_over = db.query(Group).filter(Group.id == 1).first()
        u1_after_over = db.query(User).filter(User.id == str(USER_1_ID)).first()
        assert g1_after_over.name == "گروه یک آپلودی", "در حالت اولویت فایل ارسالی باید گروه موجود بروزرسانی شود"
        assert u1_after_over.name == "کاربر یک آپلودی" and u1_after_over.points == 777.5, (
            f"در حالت اولویت فایل ارسالی باید کاربر موجود با مقادیر فایل بروزرسانی شود: name={u1_after_over.name}, points={u1_after_over.points}"
        )
        active_pwds = [g.password for g in db.query(Group).filter(Group.is_deleted == False).all()]
        assert len(active_pwds) == len(set(active_pwds)), f"رمزهای فعال تکراری شدند: {active_pwds}"
        assert get_system_state(db, "superadmin_5544332211") == "1", "سوپرادمین فعال نباید توسط فایل ارسالی عزل شود!"

    # ۴. مورد ۶: حذف Dockerfile تکراری و باقی ماندن Dockerfile ریشه
    assert not Path("docker/Dockerfile").exists(), "فایل تکراری docker/Dockerfile باید حذف شده باشد"
    assert Path("Dockerfile").exists(), "فایل اصلی Dockerfile باید حفظ شود"

    print("✅ [PASS] Scenario 19: Day-41 gift-point guard, GroupAdmin notifications, interactive DB merge priority & Docker cleanup verified.")

    # -----------------------------------------------------------------------
    # سناریو ۲۰: سهمیه‌های قابل‌تغییر لیگ (lq)، ویرایش مطالعه دیروز (ey)،
    #            اعلان مطالعه هم‌لیگی‌ها (pn / /peer_notify) و اختیاری بودن صفحات (op)
    # -----------------------------------------------------------------------
    from admin_handlers import (
        cmd_league_quotas,
        cb_league_quota_adjust,
        cb_league_quota_set_prompt,
        process_league_new_half_quota,
        cmd_toggle_edit_yesterday_menu,
        cb_toggle_edit_yesterday,
        cmd_toggle_peer_notify_menu,
        cb_toggle_peer_notify,
        cmd_toggle_optional_pages_menu,
        cb_toggle_optional_pages,
    )
    from handlers import (
        user_can_edit_yesterday,
        handle_edit_study_yesterday,
        cmd_toggle_peer_notify,
        _fetch_user_profile_sync,
    )
    from database import set_active_user_id
    from keyboards import EDIT_YESTERDAY_TEXT, SKIP_PAGES_TEXT

    s20_bot = MockBot()
    s20_admin_id = SUPER_ADMIN_ID
    s20_peer_a = "88001122"
    s20_peer_b = "88001133"
    s20_state = make_fsm(storage, s20_bot.id, s20_admin_id)

    with get_db() as db:
        g20 = Group(name="مجموعه تست ویژگی‌های جدید", password="987654", is_deleted=False)
        db.add(g20)
        db.commit()
        db.refresh(g20)
        g20_id = g20.id
        # پیش‌فرض هر سه قابلیت باید خاموش باشد
        assert g20.allow_edit_yesterday is False, "ویرایش دیروز به صورت پیش‌فرض باید غیرفعال باشد"
        assert g20.peer_notify_enabled is False, "اعلان هم‌لیگی به صورت پیش‌فرض باید غیرفعال باشد"
        assert g20.optional_pages is False, "اختیاری بودن صفحات به صورت پیش‌فرض باید غیرفعال باشد"

        start_sh20 = DateService.date_to_shamsi(DateService.today_date() - timedelta(days=3))
        lg20 = League(
            group_id=g20_id,
            name="لیگ تست ۲۰",
            floor=20,
            start_shamsi=start_sh20,
            current_day=4,
            is_active=True,
            is_deleted=False,
            cycle_number=1,
        )
        db.add(lg20)
        db.commit()
        db.refresh(lg20)
        lg20_id = lg20.id
        cyc20 = get_or_create_active_cycle(db, lg20, default_start_shamsi=start_sh20)

        u_a = User(
            id=s20_peer_a,
            telegram_id=s20_peer_a,
            group_id=g20_id,
            name="آرش کتابخوان",
            first_name="آرش",
            last_name="کتابخوان",
            league_id=lg20_id,
            points=10.0,
            total_minutes=20,
            total_pages=10,
            half_coupons=3,  # ۲ عدد مصرف کرده از ۵
            one_min_coupons=1,
            is_active=True,
            created_at=datetime.now(timezone.utc) - timedelta(days=3),
        )
        u_b = User(
            id=s20_peer_b,
            telegram_id=s20_peer_b,
            group_id=g20_id,
            name="بهرام مطالعه‌گر",
            first_name="بهرام",
            last_name="مطالعه‌گر",
            league_id=lg20_id,
            points=0.0,
            half_coupons=5,
            one_min_coupons=1,
            is_active=True,
            created_at=datetime.now(timezone.utc) - timedelta(days=3),
        )
        db.add_all([u_a, u_b])
        db.flush()
        # ثبت لاگ دیروز برای u_a (۲۰ دقیقه، ۱۰ امتیاز، بدون تاخیر)
        db.add(
            ActivityLog(
                user_id=s20_peer_a,
                league_id=lg20_id,
                cycle_id=cyc20.id,
                cycle_number=1,
                league_day=3,
                minutes=20,
                pages=10,
                points_earned=10.0,
                half_coupon_used=0,
                one_min_coupon_used=0,
                log_date=DateService.yesterday_str(),
                log_hour=14,
            )
        )
        db.commit()
        set_active_user_id(db, s20_peer_a, s20_peer_a)
        set_active_user_id(db, s20_peer_b, s20_peer_b)

    # ۱) تست lq: افزایش و کاهش سهمیه لیگ و همگام‌سازی سهمیه کاربران فعال
    await cmd_league_quotas(MockMessage(s20_bot, s20_admin_id, "lq"), s20_state)
    await cb_league_quota_adjust(MockCallbackQuery(s20_bot, s20_admin_id, f"lq_adj:half:{lg20_id}:+1"))
    await cb_league_quota_adjust(MockCallbackQuery(s20_bot, s20_admin_id, f"lq_adj:one:{lg20_id}:+1"))
    with get_db() as db:
        lg_chk = db.query(League).filter(League.id == lg20_id).first()
        ua_chk = db.query(User).filter(User.id == s20_peer_a).first()
        assert lg_chk.half_coupons_limit == 6, f"سقف نصف میثاق باید ۶ شود: {lg_chk.half_coupons_limit}"
        assert lg_chk.one_min_coupons_limit == 2, f"سقف طلایی باید ۲ شود: {lg_chk.one_min_coupons_limit}"
        assert ua_chk.half_coupons == 4, f"سهمیه باقیمانده کاربر باید +۱ شود (۴): {ua_chk.half_coupons}"
        assert ua_chk.one_min_coupons == 2, f"سهمیه طلایی کاربر باید ۲ شود: {ua_chk.one_min_coupons}"

    # تنظیم عدد دلخواه سهمیه نصف میثاق به 8 از طریق FSM
    await cb_league_quota_set_prompt(MockCallbackQuery(s20_bot, s20_admin_id, f"lq_set:half:{lg20_id}"), s20_state)
    await process_league_new_half_quota(MockMessage(s20_bot, s20_admin_id, "8"), s20_state)
    with get_db() as db:
        lg_chk = db.query(League).filter(League.id == lg20_id).first()
        ua_chk = db.query(User).filter(User.id == s20_peer_a).first()
        assert lg_chk.half_coupons_limit == 8 and ua_chk.half_coupons == 6
    _, prof_before_pn, _ = _fetch_user_profile_sync(s20_peer_a)
    assert "6 از 8 روز" in prof_before_pn and "2 از 2 روز" in prof_before_pn, "پروفایل باید سقف جدید سهمیه‌ها را نمایش دهد"
    assert "/peer_notify" not in prof_before_pn, "وقتی اعلان هم‌لیگی غیرفعال است نباید /peer_notify در پروفایل نمایش داده شود"

    # ۲) تست ey (ویرایش مطالعه دیروز)
    with get_db() as db:
        ua_chk = db.query(User).filter(User.id == s20_peer_a).first()
        assert user_can_edit_yesterday(db, ua_chk) is False, "وقتی ey غیرفعال است کاربر نباید بتواند دیروز را ویرایش کند"
    await cmd_toggle_edit_yesterday_menu(MockMessage(s20_bot, s20_admin_id, "ey"), s20_state)
    await cb_toggle_edit_yesterday(MockCallbackQuery(s20_bot, s20_admin_id, f"toggle_ey_{g20_id}"))
    with get_db() as db:
        ua_chk = db.query(User).filter(User.id == s20_peer_a).first()
        assert user_can_edit_yesterday(db, ua_chk) is True, "پس از فعالسازی ey کاربر باید بتواند دیروز را ویرایش کند"

    # ویرایش مطالعه دیروز u_a از ۲۰ دقیقه (۱۰ امتیاز) به ۱۰ دقیقه (نصف میثاق -> ۱۰ امتیاز کامل و مصرف ۱ سهمیه نصف)
    u_a_state = make_fsm(storage, s20_bot.id, s20_peer_a)
    await handle_edit_study_yesterday(MockMessage(s20_bot, s20_peer_a, EDIT_YESTERDAY_TEXT), u_a_state)
    await process_study_minutes(MockMessage(s20_bot, s20_peer_a, "10"), u_a_state)
    await process_study_pages(MockMessage(s20_bot, s20_peer_a, "5"), u_a_state)
    with get_db() as db:
        ua_chk = db.query(User).filter(User.id == s20_peer_a).first()
        y_log = db.query(ActivityLog).filter(ActivityLog.user_id == s20_peer_a, ActivityLog.log_date == DateService.yesterday_str()).first()
        assert ua_chk.points == 10.0 and ua_chk.total_minutes == 10 and ua_chk.total_pages == 5, (
            f"ویرایش مطالعه دیروز نادرست محاسبه شد: pts={ua_chk.points}, mins={ua_chk.total_minutes}, pages={ua_chk.total_pages}"
        )
        assert ua_chk.half_coupons == 5, f"باید ۱ سهمیه نصف میثاق مصرف شود (۵): {ua_chk.half_coupons}"
        assert y_log.minutes == 10 and y_log.pages == 5 and y_log.points_earned == 10.0

    # ۳) تست pn و /peer_notify (اعلان مطالعه هم‌لیگی‌ها) و op (اختیاری کردن صفحات)
    u_b_state = make_fsm(storage, s20_bot.id, s20_peer_b)
    await cmd_toggle_peer_notify(MockMessage(s20_bot, s20_peer_b, "/peer_notify"), u_b_state)
    with get_db() as db:
        ub_chk = db.query(User).filter(User.id == s20_peer_b).first()
        assert ub_chk.peer_notify_enabled is False, "تا قبل از فعالسازی ادمین، /peer_notify نباید روشن شود"

    await cmd_toggle_peer_notify_menu(MockMessage(s20_bot, s20_admin_id, "pn"), s20_state)
    await cb_toggle_peer_notify(MockCallbackQuery(s20_bot, s20_admin_id, f"toggle_pn_{g20_id}"))
    _, prof_after_pn, _ = _fetch_user_profile_sync(s20_peer_b)
    assert "/peer_notify" in prof_after_pn, "پس از فعالسازی ادمین، دستور /peer_notify باید در پروفایل دیده شود"

    # کاربر B اعلان هم‌لیگی را روشن می‌کند
    await cmd_toggle_peer_notify(MockMessage(s20_bot, s20_peer_b, "/peer_notify"), u_b_state)
    with get_db() as db:
        ub_chk = db.query(User).filter(User.id == s20_peer_b).first()
        assert ub_chk.peer_notify_enabled is True, "کاربر B باید اعلان هم‌لیگی را روشن کرده باشد"

    # ۴) فعالسازی op (اختیاری کردن تعداد صفحات)
    await cmd_toggle_optional_pages_menu(MockMessage(s20_bot, s20_admin_id, "op"), s20_state)
    await cb_toggle_optional_pages(MockCallbackQuery(s20_bot, s20_admin_id, f"toggle_op_{g20_id}"))

    # کاربر A امروز مطالعه ثبت می‌کند و تعداد صفحات را رد (skip) می‌کند -> باید هم امتیاز ثبت شود و هم پیام به B برود!
    notif_bot = MockBot()
    u_a_today_state = make_fsm(storage, notif_bot.id, s20_peer_a)
    await handle_log_study_today(MockMessage(notif_bot, s20_peer_a, "📝 ثبت مطالعه امروز"), u_a_today_state)
    await process_study_minutes(MockMessage(notif_bot, s20_peer_a, "25"), u_a_today_state)
    await process_study_pages(MockMessage(notif_bot, s20_peer_a, SKIP_PAGES_TEXT), u_a_today_state)
    # اجازه اجرای تسک پس‌زمینه ارسال اعلان به هم‌لیگی‌ها
    await asyncio.sleep(0.15)

    with get_db() as db:
        ua_chk = db.query(User).filter(User.id == s20_peer_a).first()
        assert ua_chk.today_minutes == 25 and ua_chk.today_pages == 0 and ua_chk.today_points == 10.0, (
            f"ثبت مطالعه با صفحات اختیاری نادرست بود: mins={ua_chk.today_minutes}, pages={ua_chk.today_pages}, pts={ua_chk.today_points}"
        )
    peer_msgs_to_b = [m for m in notif_bot.sent_messages if str(m["chat_id"]) == s20_peer_b]
    peer_msgs_to_a = [m for m in notif_bot.sent_messages if str(m["chat_id"]) == s20_peer_a and "عقب" in m["text"]]
    assert len(peer_msgs_to_b) == 1, f"باید دقیقاً ۱ اعلان انگیزشی برای کاربر B ارسال شود: {peer_msgs_to_b}"
    assert len(peer_msgs_to_a) == 0, "کاربر ثبت‌کننده نباید اعلان هم‌لیگی برای خودش دریافت کند"

    # ۵) تست حالت ترکیبی ۳ دکمه‌ای با میثاق اختصاصی فردی + اصطلاحات سفارشی مجموعه + عدم ارسال اعلان به کاربری که امروز ثبت کرده
    with get_db() as db:
        # تنظیم واژه‌نامه اختصاصی برای مجموعه ۲۰
        MessageService.set_term(db, g20_id, "meesaq", "پیمان")
        MessageService.set_term(db, g20_id, "half_coupon", "سهمیه نیم‌پیمان")
        MessageService.set_term(db, g20_id, "golden_coupon", "کارت طلایی")
        # تنظیم میثاق شخصی فرد (۱۵ دقیقه -> نصف میثاق باید ۸ دقیقه شود) برای کاربر B و روشن کردن اعلان برای کاربر A
        ub_edit = db.query(User).filter(User.id == s20_peer_b).first()
        ub_edit.user_floor = 15
        ua_edit = db.query(User).filter(User.id == s20_peer_a).first()
        ua_edit.peer_notify_enabled = True  # کاربر A امروز قبلاً ثبت کرده پس نباید اعلان بگیرد!
        db.commit()

    hybrid_bot = MockBot()
    u_b_today_state = make_fsm(storage, hybrid_bot.id, s20_peer_b)
    await handle_log_study_today(MockMessage(hybrid_bot, s20_peer_b, "📝 ثبت مطالعه امروز"), u_b_today_state)
    # بررسی کلیدهای ساخته‌شده با اصطلاحات سفارشی و میثاق شخصی ۱۵ (نصف = ۸)
    prompt_msg = hybrid_bot.sent_messages[-1]
    btn_texts = [
        btn.text
        for row in prompt_msg["reply_markup"].keyboard
        for btn in row
    ]
    assert "✅ پیمان کامل (15 دقیقه)" in btn_texts, f"کلید میثاق کامل با واژه‌نامه سفارشی یافت نشد: {btn_texts}"
    assert "🌗 نیم‌پیمان (8 دقیقه)" in btn_texts, f"کلید نصف میثاق (۸ دقیقه برای کف ۱۵) یافت نشد: {btn_texts}"
    assert "🌟 کارت طلایی (1 دقیقه)" in btn_texts, f"کلید سهمیه طلایی با واژه‌نامه سفارشی یافت نشد: {btn_texts}"

    # انتخاب دکمه «🌗 نیم‌پیمان (8 دقیقه)» توسط کاربر B و رد کردن صفحات
    await process_study_minutes(MockMessage(hybrid_bot, s20_peer_b, "🌗 نیم‌پیمان (8 دقیقه)"), u_b_today_state)
    await process_study_pages(MockMessage(hybrid_bot, s20_peer_b, SKIP_PAGES_TEXT), u_b_today_state)
    await asyncio.sleep(0.15)

    with get_db() as db:
        ub_chk = db.query(User).filter(User.id == s20_peer_b).first()
        assert ub_chk.today_minutes == 8 and ub_chk.today_points == 10.0 and ub_chk.half_coupons == 7, (
            f"تبدیل دکمه نصف میثاق به عدد ۸ نادرست بود: mins={ub_chk.today_minutes}, pts={ub_chk.today_points}, half={ub_chk.half_coupons}"
        )
    # کاربر A چون امروز قبلاً ثبت مطالعه داشته، با وجود روشن بودن peer_notify_enabled نباید اعلان بگیرد!
    msgs_to_a_after_b = [m for m in hybrid_bot.sent_messages if str(m["chat_id"]) == s20_peer_a]
    assert len(msgs_to_a_after_b) == 0, f"کاربری که امروز ثبت کرده نباید اعلان هم‌لیگی بگیرد: {msgs_to_a_after_b}"

    print("✅ [PASS] Scenario 20: Configurable league quotas (lq), edit yesterday (ey), peer study notifications (pn / /peer_notify), optional pages (op) & hybrid 3-option minutes verified.")





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
