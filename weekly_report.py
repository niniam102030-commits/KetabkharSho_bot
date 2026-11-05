import os
import logging
from typing import List, Set

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
from handlers import safe_send

logger = logging.getLogger(__name__)


async def send_weekly_reports(bot: Bot, force: bool = False) -> None:
    """
    جاب ساعت 02:00 بامداد روزهای جمعه:
    تولید فایل اکسل هر لیگ فعال و ارسال آن به همراه معرفی ۳ نفر برتر هفته
    (🏆 ۳ نفر برتر این هفته - لیگ ...) به ادمین‌های مجموعه و سوپرادمین‌ها
    (با پیشوند 👑 [گزارش مدیر کل] برای سوپرادمین‌ها).
    """
    today_str = DateService.today_str()

    with get_db() as db:
        last_run = get_system_state(db, "last_weekly_report_date")
        if last_run == today_str and not force:
            return

        active_leagues = (
            db.query(League)
            .filter(League.is_deleted == False, League.is_active == True)
            .order_by(League.id.asc())
            .all()
        )

        if not active_leagues:
            set_system_state(db, "last_weekly_report_date", today_str)
            return

        for lg in active_leagues:
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

            # ساخت متن معرفی ۳ نفر برتر هفته
            top_lines: List[str] = [
                f"🏆 *۳ نفر برتر این هفته - لیگ {escape_md(lg.name)}*",
                f"🏢 مجموعه: *{escape_md(group_name)}*",
                f"🔄 چله {cyc.cycle_number} | روز {current_day} از {settings.LEAGUE_DURATION}",
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
                        f"   ⭐️ امتیاز: *{pts}* | ⏱ زمان: *{mins}* دقیقه | 📄 صفحات: *{pgs}*"
                    )

            base_report_text = "\n".join(top_lines)
            base_report_text = MessageService.apply_terms(
                db, lg.group_id, base_report_text
            )
            super_admin_text = f"👑 [گزارش مدیر کل]\n{base_report_text}"

            # تولید فایل اکسل هفتگی لیگ
            excel_path = ReportService.generate_weekly_excel(
                league_name=lg.name,
                users_data=users,
                cycle_number=cyc.cycle_number,
                current_day=current_day,
                league_floor=lg.floor,
            )

            # استخراج لیست ادمین‌های مجموعه و سوپرادمین‌ها
            group_admin_rows = (
                db.query(GroupAdmin)
                .filter(GroupAdmin.group_id == lg.group_id)
                .all()
            )
            group_admin_ids: Set[str] = {str(r.user_id).strip() for r in group_admin_rows if r.user_id}
            super_admin_ids: Set[str] = {str(sa).strip() for sa in settings.ADMIN_IDS if str(sa).strip()}

            # ادمین‌های مجموعه که سوپرادمین نیستند پیام عادی دریافت می‌کنند
            only_group_admins = group_admin_ids - super_admin_ids

            try:
                base_caption = MessageService.apply_terms(
                    db,
                    lg.group_id,
                    f"📥 اکسل گزارش هفتگی لیگ «{lg.name}» (چله {cyc.cycle_number} - روز {current_day})",
                )
                super_caption = f"👑 [گزارش مدیر کل]\n{base_caption}"
                archive_caption = MessageService.apply_terms(
                    db,
                    lg.group_id,
                    f"📥 اکسل گزارش هفتگی لیگ «{lg.name}»",
                )

                # ۱. ارسال به ادمین‌های مجموعه
                for g_adm_id in only_group_admins:
                    await safe_send(bot, g_adm_id, base_report_text)
                    try:
                        await bot.send_document(
                            chat_id=g_adm_id,
                            document=FSInputFile(excel_path),
                            caption=base_caption,
                        )
                    except Exception as exc:
                        logger.warning(f"خطا در ارسال اکسل هفتگی به ادمین مجموعه {g_adm_id}: {exc}")

                # ۲. ارسال به سوپرادمین‌ها با پیشوند 👑 [گزارش مدیر کل]
                for s_adm_id in super_admin_ids:
                    await safe_send(bot, s_adm_id, super_admin_text)
                    try:
                        await bot.send_document(
                            chat_id=s_adm_id,
                            document=FSInputFile(excel_path),
                            caption=super_caption,
                        )
                    except Exception as exc:
                        logger.warning(f"خطا در ارسال اکسل هفتگی به سوپرادمین {s_adm_id}: {exc}")

                # ۳. ارسال به کانال آرشیو در صورت فعال بودن
                if settings.ARCHIVE_CHANNEL and lg.archive_enabled:
                    await safe_send(bot, settings.ARCHIVE_CHANNEL, base_report_text)
                    try:
                        await bot.send_document(
                            chat_id=settings.ARCHIVE_CHANNEL,
                            document=FSInputFile(excel_path),
                            caption=archive_caption,
                        )
                    except Exception as exc:
                        logger.warning(f"خطا در ارسال اکسل هفتگی به کانال آرشیو: {exc}")

            finally:
                if os.path.exists(excel_path):
                    try:
                        os.remove(excel_path)
                    except OSError:
                        pass

        set_system_state(db, "last_weekly_report_date", today_str)
        logger.info(f"گزارش‌های هفتگی جمعه برای تاریخ {today_str} با موفقیت ارسال شد.")