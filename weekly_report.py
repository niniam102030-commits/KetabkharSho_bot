import os
import asyncio
import logging
from typing import List, Set, Dict, Any, Optional

from aiogram import Bot
from aiogram.types import FSInputFile

from config import settings
from database import (
    get_db,
    get_or_create_active_cycle,
    get_system_state,
    set_system_state,
)
from models import League, User, GroupAdmin, Group
from services import (
    DateService,
    ScoringService,
    ReportService,
    escape_md,
)
from message_service import MessageService
from handlers import safe_send, safe_send_document, BroadcastThrottle

logger = logging.getLogger(__name__)


async def send_weekly_reports(bot: Bot, force: bool = False) -> None:
    """
    جاب ساعت 02:00 بامداد روزهای جمعه:
    تولید فایل اکسل وضعیت چله هر لیگ فعال و ارسال گزارش هفتگی از وضعیت جدول چله (تا پایان هفته جاری)
    به صورت پلکانی و لیگ به لیگ، با حداقل مصرف حافظه RAM.
    """
    today_str = DateService.today_str()
    super_admin_ids: Set[str] = {
        str(sa).strip() for sa in settings.ADMIN_IDS if str(sa).strip()
    }

    with get_db() as db:
        last_run = get_system_state(db, "last_weekly_report_date")
        if last_run == today_str and not force:
            return

        league_ids = [
            r[0]
            for r in db.query(League.id)
            .filter(League.is_deleted == False, League.is_active == True)
            .order_by(League.id.asc())
            .all()
        ]
        set_system_state(db, "last_weekly_report_date", today_str)

    if not league_ids:
        return

    throttle = BroadcastThrottle()

    async def _deliver(rcpt: str, text: str, caption: str, path: str) -> None:
        """ارسال متن و اکسل به یک گیرنده؛ خطای یک گیرنده بقیه را متوقف نمی‌کند"""
        try:
            await safe_send(bot, rcpt, text)
            await throttle.tick()
            ok = await safe_send_document(bot, rcpt, path, caption=caption, throttle=throttle)
            if not ok:
                logger.warning(f"ارسال اکسل هفتگی به {rcpt} ناموفق بود.")
        except Exception as exc:
            logger.warning(f"خطا در ارسال گزارش هفتگی به {rcpt}: {exc}")

    # هر بار فقط یک لیگ در حافظه است؛ کوئری و تولید اکسل در ترد جداگانه
    for league_id in league_ids:
        task: Optional[Dict[str, Any]] = None
        excel_path = ""
        try:
            task = await asyncio.to_thread(
                _build_weekly_task_sync, league_id, super_admin_ids
            )
            if not task:
                continue

            excel_path = await asyncio.to_thread(
                ReportService.generate_weekly_excel,
                league_name=task["league_name"],
                users_data=task["users_data"],
                cycle_number=task["cycle_number"],
                current_day=task["current_day"],
                league_floor=task["league_floor"],
            )
            task["users_data"] = []  # آزادسازی داده‌های حجیم بعد از ساخت اکسل

            # ۱. ارسال به ادمین‌های مجموعه
            for g_adm_id in sorted(task["only_group_admins"]):
                await _deliver(g_adm_id, task["base_report_text"], task["base_caption"], excel_path)

            # ۲. ارسال به سوپرادمین‌ها با پیشوند 👑 [گزارش مدیر کل]
            for s_adm_id in sorted(super_admin_ids):
                await _deliver(s_adm_id, task["super_admin_text"], task["super_caption"], excel_path)

            # ۳. ارسال به کانال آرشیو در صورت فعال بودن
            if settings.ARCHIVE_CHANNEL and task["archive_enabled"]:
                await _deliver(
                    settings.ARCHIVE_CHANNEL,
                    task["base_report_text"],
                    task["archive_caption"],
                    excel_path,
                )

        except Exception as exc:
            logger.error(f"خطا در گزارش هفتگی لیگ {league_id}: {exc}", exc_info=True)
        finally:
            if excel_path and os.path.exists(excel_path):
                try:
                    os.remove(excel_path)
                except OSError:
                    pass
            task = None

    logger.info(f"گزارش‌های هفتگی جمعه برای تاریخ {today_str} با موفقیت ارسال شد.")


def _build_weekly_task_sync(
    league_id: str, super_admin_ids: Set[str]
) -> Optional[Dict[str, Any]]:
    """ساخت تسک گزارش هفتگی یک لیگ با نشست دیتابیس مستقل (اجرا در ترد جداگانه)"""
    with get_db() as db:
        lg = db.get(League, league_id)
        if not lg or lg.is_deleted or not lg.is_active:
            return None

        cyc = get_or_create_active_cycle(db, lg)
        current_day = DateService.calculate_league_day(
            cyc.start_shamsi or lg.start_shamsi
        )
        grp = db.query(Group).filter(Group.id == lg.group_id).first()
        group_name = grp.name if grp else "پیش‌فرض"

        users = (
            db.query(User)
            .filter(User.league_id == lg.id, User.is_active == True)
            .all()
        )
        ranked_users = ScoringService.rank_users(users, lg.floor)

        top_lines: List[str] = [
            f"📊 *گزارش هفتگی جمعه - لیگ {escape_md(lg.name)}*",
            f"🏢 مجموعه: *{escape_md(group_name)}*",
            f"🔄 چله {cyc.cycle_number} | روز {current_day} از {settings.LEAGUE_DURATION}",
            f"🏆 *۳ نفر برتر جدول چله (تا پایان این هفته):*",
            "───────────────────",
        ]

        if not ranked_users:
            top_lines.append("📭 هنوز عضوی در این لیگ فعالیت ثبت نکرده است.")
        else:
            medals = {1: "🥇 نفر اول", 2: "🥈 نفر دوم", 3: "🥉 نفر سوم"}
            top_three = [item for item in ranked_users if item[0] <= 3][:3]
            if not top_three:
                top_three = ranked_users[:3]

            for idx, (rnk, u) in enumerate(top_three, start=1):
                medal_label = medals.get(rnk, medals.get(idx, f"🔹 رتبه {rnk}"))
                pts = round(float(u.points or 0.0), 1)
                mins = int(u.total_minutes or 0)
                pgs = int(u.total_pages or 0)
                top_lines.append(
                    f"{medal_label}: *{escape_md(u.name)}*\n"
                    f"   ⭐️ امتیاز کل: *{pts}* | ⏱ زمان کل: *{mins}* دقیقه | 📄 صفحات کل: *{pgs}*"
                )

        base_report_text = MessageService.apply_terms(
            db, lg.group_id, "\n".join(top_lines)
        )
        super_admin_text = f"👑 [گزارش مدیر کل]\n{base_report_text}"

        base_caption = MessageService.apply_terms(
            db,
            lg.group_id,
            f"📥 اکسل گزارش هفتگی وضعیت چله - لیگ «{lg.name}» (چله {cyc.cycle_number} - روز {current_day})",
        )
        super_caption = f"👑 [گزارش مدیر کل]\n{base_caption}"
        archive_caption = MessageService.apply_terms(
            db,
            lg.group_id,
            f"📥 اکسل گزارش هفتگی وضعیت چله - لیگ «{lg.name}»",
        )

        group_admin_rows = (
            db.query(GroupAdmin.user_id)
            .filter(GroupAdmin.group_id == lg.group_id)
            .all()
        )
        group_admin_ids: Set[str] = {
            str(r[0]).strip() for r in group_admin_rows if r[0]
        }

        return {
            "league_id": lg.id,
            "league_name": lg.name,
            "cycle_number": cyc.cycle_number,
            "current_day": current_day,
            "league_floor": lg.floor,
            "archive_enabled": lg.archive_enabled,
            "users_data": [
                ReportService._extract_row_dict(u, league_floor=lg.floor)
                for u in users
            ],
            "only_group_admins": group_admin_ids - super_admin_ids,
            "base_report_text": base_report_text,
            "super_admin_text": super_admin_text,
            "base_caption": base_caption,
            "super_caption": super_caption,
            "archive_caption": archive_caption,
        }
