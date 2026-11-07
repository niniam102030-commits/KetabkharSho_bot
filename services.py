import re
import uuid
import logging
from pathlib import Path
from datetime import datetime, date, timedelta, timezone
from typing import Tuple, List, Dict, Any, Optional, Iterable, Union

try:
    from zoneinfo import ZoneInfo
    IRAN_TZ = ZoneInfo("Asia/Tehran")
except Exception:
    IRAN_TZ = timezone(timedelta(hours=3, minutes=30))

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session

from config import settings
from models import User, League, Cycle, ActivityLog, CycleResult, Group

logger = logging.getLogger(__name__)


def escape_md(text: Any) -> str:
    """ایمن‌سازی رشته‌ها برای ارسال در حالت parse_mode='Markdown'"""
    if text is None:
        return ""
    s = str(text)
    for ch in ("_", "*", "`", "["):
        s = s.replace(ch, f"\\{ch}")
    return s


# ===========================================================================
# ۱. سرویس تاریخ شمسی/میلادی و ساعت ایران (بدون نیاز به کتابخانه خارجی)
# ===========================================================================
class DateService:
    """مدیریت کامل تاریخ شمسی، میلادی، تبدیل ارقام فارسی و ساعت رسمی ایران"""

    PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
    ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
    ENGLISH_DIGITS = "0123456789"

    PERSIAN_WEEKDAYS = {
        0: "دوشنبه",
        1: "سه‌شنبه",
        2: "چهارشنبه",
        3: "پنج‌شنبه",
        4: "جمعه",
        5: "شنبه",
        6: "یک‌شنبه",
    }

    _TRANS_TABLE = str.maketrans(
        PERSIAN_DIGITS + ARABIC_DIGITS, ENGLISH_DIGITS * 2
    )

    @classmethod
    def normalize_digits(cls, text: Any) -> str:
        """تبدیل اعداد فارسی و عربی به انگلیسی"""
        if text is None:
            return ""
        return str(text).translate(cls._TRANS_TABLE).strip()

    @classmethod
    def now_iran(cls) -> datetime:
        """زمان فعلی دقیق به وقت تهران"""
        return datetime.now(IRAN_TZ)

    @classmethod
    def today_date(cls) -> date:
        """شیء date امروز به وقت ایران"""
        return cls.now_iran().date()

    @classmethod
    def today_str(cls) -> str:
        """تاریخ میلادی امروز با فرمت YYYY-MM-DD"""
        return cls.today_date().strftime("%Y-%m-%d")

    @classmethod
    def yesterday_date(cls) -> date:
        """شیء date دیروز به وقت ایران"""
        return cls.today_date() - timedelta(days=1)

    @classmethod
    def yesterday_str(cls) -> str:
        """تاریخ میلادی دیروز با فرمت YYYY-MM-DD"""
        return cls.yesterday_date().strftime("%Y-%m-%d")

    @staticmethod
    def gregorian_to_jalali(gy: int, gm: int, gd: int) -> Tuple[int, int, int]:
        """تبدیل دقیق تاریخ میلادی به شمسی (جلالی)"""
        g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
        if gy > 1600:
            jy = 979
            gy -= 1600
        else:
            jy = 0
            gy -= 621
        gy2 = gy + 1 if gm > 2 else gy
        days = (
            (365 * gy)
            + int((gy2 + 3) / 4)
            - int((gy2 + 99) / 100)
            + int((gy2 + 399) / 400)
            - 80
            + gd
            + g_d_m[gm - 1]
        )
        jy += 33 * int(days / 12053)
        days %= 12053
        jy += 4 * int(days / 1461)
        days %= 1461
        if days > 365:
            jy += int((days - 1) / 365)
            days = (days - 1) % 365
        if days < 186:
            jm = 1 + int(days / 31)
            jd = 1 + (days % 31)
        else:
            jm = 7 + int((days - 186) / 30)
            jd = 1 + ((days - 186) % 30)
        return jy, jm, jd

    @staticmethod
    def jalali_to_gregorian(jy: int, jm: int, jd: int) -> Tuple[int, int, int]:
        """تبدیل دقیق تاریخ شمسی (جلالی) به میلادی"""
        if jy > 979:
            gy = 1600
            jy -= 979
        else:
            gy = 621
        days = (
            (365 * jy)
            + (int(jy / 33) * 8)
            + int(((jy % 33) + 3) / 4)
            + 78
            + jd
            + ((jm - 1) * 31 if jm < 7 else ((jm - 7) * 30) + 186)
        )
        gy += 400 * int(days / 146097)
        days %= 146097
        if days > 36524:
            days -= 1
            gy += 100 * int(days / 36524)
            days %= 36524
            if days >= 365:
                days += 1
        gy += 4 * int(days / 1461)
        days %= 1461
        if days > 365:
            gy += int((days - 1) / 365)
            days = (days - 1) % 365
        gd = days + 1
        is_leap = (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)
        sal_a = [0, 31, 29 if is_leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        gm = 0
        while gm < 13 and gd > sal_a[gm]:
            gd -= sal_a[gm]
            gm += 1
        return gy, gm, gd

    @classmethod
    def today_shamsi(cls) -> str:
        """تاریخ شمسی امروز با فرمت YYYY/MM/DD (مثلاً 1405/07/01)"""
        d = cls.today_date()
        jy, jm, jd = cls.gregorian_to_jalali(d.year, d.month, d.day)
        return f"{jy:04d}/{jm:02d}/{jd:02d}"

    @classmethod
    def now_iran_time_str(cls) -> str:
        """ساعت دقیق فعلی به وقت ایران با فرمت HH:MM:SS"""
        return cls.now_iran().strftime("%H:%M:%S")

    @classmethod
    def today_shamsi_full(cls) -> str:
        """تاریخ شمسی کامل به همراه نام روز هفته (مثلا: پنج‌شنبه 1405/08/15)"""
        now_ir = cls.now_iran()
        day_name = cls.PERSIAN_WEEKDAYS.get(now_ir.weekday(), "")
        return f"{day_name} {cls.today_shamsi()}".strip()

    @classmethod
    def date_to_shamsi(cls, target: Union[str, date, datetime]) -> str:
        """تبدیل رشته YYYY-MM-DD یا شیء date/datetime به رشته شمسی YYYY/MM/DD"""
        if isinstance(target, datetime):
            d = target.date()
        elif isinstance(target, date):
            d = target
        else:
            clean = cls.normalize_digits(str(target))[:10]
            try:
                d = datetime.strptime(clean, "%Y-%m-%d").date()
            except ValueError:
                return cls.today_shamsi()
        jy, jm, jd = cls.gregorian_to_jalali(d.year, d.month, d.day)
        return f"{jy:04d}/{jm:02d}/{jd:02d}"

    @classmethod
    def shamsi_to_date(cls, shamsi_str: str) -> Optional[date]:
        """تبدیل رشته شمسی YYYY/MM/DD یا YYYY-MM-DD به شیء date میلادی"""
        if not shamsi_str:
            return None
        clean = cls.normalize_digits(shamsi_str).replace("-", "/")
        parts = clean.split("/")
        if len(parts) != 3:
            return None
        try:
            jy, jm, jd = int(parts[0]), int(parts[1]), int(parts[2])
            if not (1300 <= jy <= 1500 and 1 <= jm <= 12 and 1 <= jd <= 31):
                return None
            if jm > 6 and jd == 31:
                return None
            gy, gm, gd = cls.jalali_to_gregorian(jy, jm, jd)
            return date(gy, gm, gd)
        except ValueError:
            return None

    @classmethod
    def normalize_shamsi(cls, shamsi_str: str) -> Optional[str]:
        """اعتبارسنجی و استانداردسازی فرمت تاریخ شمسی به YYYY/MM/DD"""
        d = cls.shamsi_to_date(shamsi_str)
        if not d:
            return None
        jy, jm, jd = cls.gregorian_to_jalali(d.year, d.month, d.day)
        return f"{jy:04d}/{jm:02d}/{jd:02d}"

    @classmethod
    def calculate_raw_league_day(
        cls, start_shamsi: Optional[str], target_date: Optional[Union[date, str]] = None
    ) -> int:
        """
        محاسبه شماره روز واقعی چله بر اساس تاریخ شروع شمسی (بدون سقف ۴۰).
        برای تشخیص رسیدن به روز ۴۱ در ساعت ۸ صبح کاربرد دارد.
        """
        if not start_shamsi:
            return 1
        start_d = cls.shamsi_to_date(start_shamsi)
        if not start_d:
            return 1

        if target_date is None:
            curr_d = cls.today_date()
        elif isinstance(target_date, str):
            try:
                curr_d = datetime.strptime(target_date[:10], "%Y-%m-%d").date()
            except ValueError:
                curr_d = cls.today_date()
        else:
            curr_d = target_date

        diff = (curr_d - start_d).days + 1
        return max(1, diff)

    @classmethod
    def calculate_league_day(
        cls,
        start_shamsi: Optional[str],
        target_date: Optional[Union[date, str]] = None,
        clamp_to_duration: bool = True,
    ) -> int:
        """محاسبه روز جاری چله (محدود شده بین 1 تا LEAGUE_DURATION در حالت پیش‌فرض)"""
        raw_day = cls.calculate_raw_league_day(start_shamsi, target_date)
        if clamp_to_duration:
            return min(raw_day, settings.LEAGUE_DURATION)
        return raw_day

    @classmethod
    def get_date_for_league_day(cls, start_shamsi: Optional[str], day_number: int) -> str:
        """برگرداندن تاریخ میلادی YYYY-MM-DD متناظر با روز مشخصی از چله"""
        start_d = cls.shamsi_to_date(start_shamsi or "") or cls.today_date()
        target_d = start_d + timedelta(days=max(0, int(day_number) - 1))
        return target_d.strftime("%Y-%m-%d")

    @classmethod
    def user_joined_before_today(cls, user: User) -> bool:
        """بررسی اینکه آیا تاریخ عضویت کاربر قبل از امروز (به وقت ایران) بوده است"""
        if not user.created_at:
            return True
        created_dt = user.created_at
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc).astimezone(IRAN_TZ)
        else:
            created_dt = created_dt.astimezone(IRAN_TZ)
        return created_dt.date() < cls.today_date()


# ===========================================================================
# ۲. سرویس محاسبه امتیاز، سهمیه‌ها و رتبه‌بندی
# ===========================================================================
class ScoringService:
    """محاسبه امتیاز مطالعه روزانه، سهمیه‌ها و رتبه‌بندی استاندارد اعضای لیگ"""

    @staticmethod
    def calculate_points(
        minutes: int,
        floor: int,
        half_coupons: int,
        one_min_coupons: int,
    ) -> Tuple[float, int, int, str]:
        """
        محاسبه امتیاز و سهمیه مصرفی بر اساس قوانین باشگاه:
        خروجی: (points, half_coupon_used, one_min_coupon_used, status_message)
        """
        effective_floor = max(1, int(floor or settings.DEFAULT_FLOOR))
        mins = max(0, int(minutes or 0))
        half_rem = max(0, int(half_coupons or 0))
        one_rem = max(0, int(one_min_coupons or 0))

        if mins <= 0:
            return 0.0, 0, 0, "📉 زمان مطالعه ۰ دقیقه ثبت شد."

        # ۱. رسیدن کامل به میثاق روزانه
        if mins >= effective_floor:
            return (
                10.0,
                0,
                0,
                "🌟 عالی! میثاق روزانه شما رعایت شد و ۱۰ امتیاز کامل گرفتید.",
            )

        # ۲. حداقل نصف میثاق و داشتن سهمیه نصف میثاق
        if mins >= (effective_floor / 2.0) and half_rem > 0:
            return (
                10.0,
                1,
                0,
                "🌸 از سهمیه «نصف میثاق» استفاده شد و ۱۰ امتیاز کامل گرفتید.",
            )

        # ۳. حداقل ۱ دقیقه و داشتن سهمیه طلایی یک دقیقه‌ای
        if mins >= 1 and one_rem > 0:
            return (
                10.0,
                0,
                1,
                "👑 از سهمیه طلایی «دقیقه‌ای» استفاده شد و ۱۰ امتیاز کامل گرفتید.",
            )

        # ۴. تمام شدن سهمیه‌ها -> امتیاز تناسبی
        points = round((mins / float(effective_floor)) * 10.0, 1)
        return (
            points,
            0,
            0,
            f"📉 سهمیه‌ها تمام شده؛ امتیاز تناسبی: {points}",
        )

    @staticmethod
    def get_user_sort_key(user: User, league_floor: int) -> Tuple[float, int, int]:
        """
        کلید رتبه‌بندی استاندارد در کل پروژه:
        (user.points, user.get_effective_floor(league.floor), user.total_minutes)
        """
        pts = round(float(user.points or 0.0), 2)
        eff_floor = int(user.get_effective_floor(league_floor))
        tot_mins = int(user.total_minutes or 0)
        return (pts, eff_floor, tot_mins)

    @classmethod
    def rank_users(
        cls, users: Iterable[User], league_floor: int
    ) -> List[Tuple[int, User]]:
        """
        مرتب‌سازی نزولی کاربران و تخصیص رتبه نمایشی یکسان (Tie-breaking)
        در صورت برابری هر سه معیار.
        خروجی: لیستی از تاپل‌های (displayed_rank, user)
        """
        sorted_users = sorted(
            list(users),
            key=lambda u: cls.get_user_sort_key(u, league_floor),
            reverse=True,
        )
        ranked: List[Tuple[int, User]] = []
        prev_key: Optional[Tuple[float, int, int]] = None
        current_rank = 1

        for idx, u in enumerate(sorted_users, start=1):
            key = cls.get_user_sort_key(u, league_floor)
            if prev_key is not None and key == prev_key:
                rank_to_assign = current_rank
            else:
                rank_to_assign = idx
                current_rank = idx
                prev_key = key
            ranked.append((rank_to_assign, u))

        return ranked

    @classmethod
    def get_user_rank(cls, user: User, all_league_users: Iterable[User], league_floor: int) -> int:
        """محاسبه رتبه یک کاربر خاص در بین اعضای لیگ"""
        ranked = cls.rank_users(all_league_users, league_floor)
        for rank, u in ranked:
            if u.id == user.id:
                return rank
        return len(ranked) + 1


# ===========================================================================
# ۳. سرویس تولید فایل‌های اکسل حرفه‌ای (ReportService)
# ===========================================================================
class ReportService:
    """ساخت ۳ نوع گزارش اکسل حرفه‌ای و راست‌به‌چپ با openpyxl و pandas"""

    HEADER_FILL = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    HEADER_FONT = Font(name="Tahoma", size=11, bold=True, color="FFFFFF")
    ROW_EVEN_FILL = PatternFill(start_color="F2F7FB", end_color="F2F7FB", fill_type="solid")
    ROW_ODD_FILL = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    GOLD_FILL = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    DATA_FONT = Font(name="Tahoma", size=10, bold=False, color="000000")
    BOLD_FONT = Font(name="Tahoma", size=10, bold=True, color="000000")
    THIN_BORDER = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )
    CENTER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        clean = re.sub(r'[\\/*?:"<>|\s]+', "_", str(name or "league").strip())
        return clean[:50] or "report"

    @classmethod
    def _extract_row_dict(cls, item: Union[User, Dict[str, Any]], league_floor: int = 10) -> Dict[str, Any]:
        """
        استخراج یکپارچه اطلاعات کاربر چه به صورت شیء User پاس داده شود
        و چه به صورت دیکشنری با کلیدهای مختلف (minutes / total_minutes و غیره).
        """
        if isinstance(item, User):
            eff_floor = item.get_effective_floor(league_floor)
            half_rem = int(item.half_coupons or 0)
            one_rem = int(item.one_min_coupons or 0)
            return {
                "user_id": item.telegram_id or item.id,
                "name": item.name,
                "display_name": item.get_display_name(),
                "points": round(float(item.points or 0.0), 1),
                "floor": eff_floor,
                "total_minutes": int(item.total_minutes or 0),
                "minutes": int(item.total_minutes or 0),
                "total_pages": int(item.total_pages or 0),
                "pages": int(item.total_pages or 0),
                "streak": int(item.streak or 0),
                "no_study_days": int(item.no_study_days or 0),
                "no_study": int(item.no_study_days or 0),
                "absent_days_list": item.absent_days_list or "-",
                "late_days_list": item.late_days_list or "-",
                "half_coupons_remaining": half_rem,
                "one_min_coupons_remaining": one_rem,
                "half_coupons_used": max(0, settings.DEFAULT_HALF_COUPONS - half_rem),
                "one_min_coupons_used": max(0, settings.DEFAULT_ONE_MIN_COUPONS - one_rem),
                "today_minutes": int(item.today_minutes or 0),
                "today_pages": int(item.today_pages or 0),
            }

        # پشتیبانی کامل از هر دو نوع کلید در دیکشنری ورودی (بند ۹.۴ مشخصات)
        points = round(float(item.get("points", 0.0) or 0.0), 1)
        floor = int(
            item.get("floor")
            or item.get("effective_floor")
            or item.get("user_floor")
            or league_floor
            or 10
        )
        minutes = int(
            item.get("total_minutes")
            if item.get("total_minutes") is not None
            else (item.get("minutes", 0) or 0)
        )
        pages = int(
            item.get("total_pages")
            if item.get("total_pages") is not None
            else (item.get("pages", 0) or 0)
        )
        no_study = int(
            item.get("no_study_days")
            if item.get("no_study_days") is not None
            else (item.get("no_study", 0) or 0)
        )
        half_rem = int(
            item.get("half_coupons_remaining")
            if item.get("half_coupons_remaining") is not None
            else (item.get("half_coupons", settings.DEFAULT_HALF_COUPONS) or 0)
        )
        one_rem = int(
            item.get("one_min_coupons_remaining")
            if item.get("one_min_coupons_remaining") is not None
            else (item.get("one_min_coupons", settings.DEFAULT_ONE_MIN_COUPONS) or 0)
        )
        half_used = int(
            item.get("half_coupons_used")
            if item.get("half_coupons_used") is not None
            else max(0, settings.DEFAULT_HALF_COUPONS - half_rem)
        )
        one_used = int(
            item.get("one_min_coupons_used")
            if item.get("one_min_coupons_used") is not None
            else max(0, settings.DEFAULT_ONE_MIN_COUPONS - one_rem)
        )

        return {
            "user_id": item.get("user_id") or item.get("telegram_id") or item.get("id") or "",
            "name": item.get("name") or item.get("user_name") or "کاربر",
            "display_name": item.get("display_name") or item.get("name") or item.get("user_name") or "کاربر",
            "points": points,
            "floor": floor,
            "total_minutes": minutes,
            "minutes": minutes,
            "total_pages": pages,
            "pages": pages,
            "streak": int(item.get("streak", 0) or 0),
            "no_study_days": no_study,
            "no_study": no_study,
            "absent_days_list": item.get("absent_days_list") or item.get("absent_days") or "-",
            "late_days_list": item.get("late_days_list") or item.get("late_days") or "-",
            "half_coupons_remaining": half_rem,
            "one_min_coupons_remaining": one_rem,
            "half_coupons_used": half_used,
            "one_min_coupons_used": one_used,
            "today_minutes": int(item.get("today_minutes", 0) or 0),
            "today_pages": int(item.get("today_pages", 0) or 0),
            "weekly_minutes": int(item.get("weekly_minutes", 0) or 0),
            "weekly_pages": int(item.get("weekly_pages", 0) or 0),
        }

    @classmethod
    def _style_worksheet(cls, ws, headers: List[str], rows: List[List[Any]], highlight_top3: bool = True) -> None:
        """اعمال استایل راست‌به‌چپ، رنگ‌بندی هدرها و تنظیم خودکار عرض ستون‌ها"""
        ws.sheet_view.rightToLeft = True
        ws.append(headers)

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = cls.HEADER_FILL
            cell.font = cls.HEADER_FONT
            cell.alignment = cls.CENTER_ALIGN
            cell.border = cls.THIN_BORDER
        ws.row_dimensions[1].height = 26

        for r_idx, row_vals in enumerate(rows, start=2):
            ws.append(row_vals)
            ws.row_dimensions[r_idx].height = 22
            rank_val = row_vals[0] if row_vals else r_idx - 1
            is_top3 = highlight_top3 and isinstance(rank_val, int) and rank_val <= 3

            row_fill = (
                cls.GOLD_FILL
                if is_top3
                else (cls.ROW_EVEN_FILL if r_idx % 2 == 0 else cls.ROW_ODD_FILL)
            )
            for c_idx in range(1, len(row_vals) + 1):
                cell = ws.cell(row=r_idx, column=c_idx)
                cell.fill = row_fill
                cell.font = cls.BOLD_FONT if is_top3 else cls.DATA_FONT
                cell.alignment = cls.CENTER_ALIGN
                cell.border = cls.THIN_BORDER

        for c_idx in range(len(headers)):
            max_len = len(str(headers[c_idx] or ""))
            for row_vals in rows:
                if c_idx < len(row_vals):
                    max_len = max(max_len, len(str(row_vals[c_idx] or "")))
            ws.column_dimensions[get_column_letter(c_idx + 1)].width = max(
                12, min(40, max_len + 5)
            )

    @classmethod
    def generate_excel(
        cls,
        league_name: str,
        users_data: Iterable[Union[User, Dict[str, Any]]],
        cycle_number: int = 1,
        current_day: int = 1,
        league_floor: int = 10,
        output_path: Optional[str] = None,
    ) -> str:
        """
        ۱. تولید فایل اکسل وضعیت فعلی لیگ فعال (یا پایان چله).
        سازگار با هر دو کلید minutes / total_minutes، pages / total_pages و no_study / no_study_days.
        """
        normalized = [cls._extract_row_dict(u, league_floor=league_floor) for u in users_data]

        # مرتب‌سازی نزولی بر اساس (points, floor, total_minutes)
        normalized.sort(
            key=lambda x: (
                round(float(x.get("points", 0.0)), 2),
                int(x.get("floor", league_floor)),
                int(x.get("total_minutes", x.get("minutes", 0))),
            ),
            reverse=True,
        )

        headers = [
            "رتبه",
            "نام و نام خانوادگی",
            "میثاق (دقیقه)",
            "امتیاز کل",
            "زمان کل (دقیقه)",
            "صفحات کل",
            "زنجیره استمرار",
            "تعداد غیبت",
            "روزهای غیبت",
            "روزهای ثبت با تاخیر",
            "سهمیه نصف میثاق مانده",
            "سهمیه طلایی مانده",
        ]

        rows: List[List[Any]] = []
        prev_key: Optional[Tuple[float, int, int]] = None
        current_rank = 1

        for idx, item in enumerate(normalized, start=1):
            current_key = (
                round(float(item.get("points", 0.0)), 2),
                int(item.get("floor", league_floor)),
                int(item.get("total_minutes", item.get("minutes", 0))),
            )
            if prev_key is not None and current_key == prev_key:
                rank = current_rank
            else:
                rank = idx
                current_rank = idx
                prev_key = current_key

            rows.append(
                [
                    rank,
                    item["name"],
                    item["floor"],
                    item["points"],
                    item["total_minutes"],
                    item["total_pages"],
                    item["streak"],
                    item["no_study_days"],
                    item["absent_days_list"] or "-",
                    item["late_days_list"] or "-",
                    item["half_coupons_remaining"],
                    item["one_min_coupons_remaining"],
                ]
            )

        wb = Workbook()
        ws = wb.active
        ws.title = f"چله {cycle_number} - روز {current_day}"[:31]
        cls._style_worksheet(ws, headers, rows, highlight_top3=True)

        if not output_path:
            reports_dir = Path("./reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            safe_name = cls._sanitize_filename(league_name)
            ts = DateService.now_iran().strftime("%Y%m%d_%H%M%S")
            uid_short = uuid.uuid4().hex[:6]
            output_path = str(reports_dir / f"league_{safe_name}_c{cycle_number}_d{current_day}_{ts}_{uid_short}.xlsx")

        wb.save(output_path)
        wb.close()
        return output_path

    @classmethod
    def generate_weekly_excel(
        cls,
        league_name: str,
        users_data: Iterable[Union[User, Dict[str, Any]]],
        cycle_number: int = 1,
        current_day: int = 1,
        league_floor: int = 10,
    ) -> str:
        """۲. تولید فایل اکسل گزارش هفتگی جمعه"""
        reports_dir = Path("./reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        safe_name = cls._sanitize_filename(league_name)
        ts = DateService.now_iran().strftime("%Y%m%d_%H%M%S")
        uid_short = uuid.uuid4().hex[:6]
        out_file = str(reports_dir / f"weekly_{safe_name}_c{cycle_number}_{ts}_{uid_short}.xlsx")
        return cls.generate_excel(
            league_name=league_name,
            users_data=users_data,
            cycle_number=cycle_number,
            current_day=current_day,
            league_floor=league_floor,
            output_path=out_file,
        )

    @classmethod
    def generate_cycle_history_excel(
        cls,
        db_or_data: Union[Session, List[Dict[str, Any]]],
        group_ids: Optional[List[int]] = None,
        league_id: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """
        ۳. تولید فایل اکسل چندشیتی آرشیو تاریخچه چله‌های فعال و پایان‌یافته (دستور sr).
        می‌تواند مستقیماً نشست دیتابیس (Session) یا لیست دیکشنری‌های آماده را دریافت کند.
        """
        wb = Workbook()
        # حذف شیت پیش‌فرض پس از افزودن شیت‌های واقعی
        default_sheet = wb.active
        sheets_added = 0

        if isinstance(db_or_data, Session):
            db = db_or_data
            if group_ids is not None and len(group_ids) == 0:
                leagues = []
            else:
                league_query = db.query(League).filter(League.is_deleted == False)
                if group_ids is not None:
                    league_query = league_query.filter(League.group_id.in_(group_ids))
                if league_id is not None:
                    league_query = league_query.filter(League.id == league_id)
                leagues = league_query.order_by(League.group_id.asc(), League.id.asc()).all()

            multi_group = group_ids is None or len(set(group_ids)) > 1
            for lg in leagues:
                cycles = (
                    db.query(Cycle)
                    .filter(Cycle.league_id == lg.id)
                    .order_by(Cycle.cycle_number.desc(), Cycle.id.desc())
                    .all()
                )
                grp_prefix = f"G{lg.group_id}_" if multi_group else ""
                for cyc in cycles:
                    sheet_title = f"{grp_prefix}{lg.name[:12]}_چله{cyc.cycle_number}_{'فعال' if cyc.status == 'active' else 'پایان'}"
                    sheet_title = re.sub(r'[\/*?:\[\]]', "_", sheet_title)[:31]
                    if sheet_title in wb.sheetnames:
                        sheet_title = f"{sheet_title[:27]}_{cyc.id}"[:31]

                    ws = wb.create_sheet(title=sheet_title)
                    sheets_added += 1

                    headers = [
                        "رتبه",
                        "نام و نام خانوادگی",
                        "امتیاز",
                        "زمان کل (دقیقه)",
                        "صفحات کل",
                        "زنجیره استمرار",
                        "تعداد غیبت",
                        "روزهای غیبت",
                        "روزهای تاخیر",
                        "نصف میثاق مصرفی",
                        "طلایی مصرفی",
                        "نصف میثاق مانده",
                        "طلایی مانده",
                    ]
                    rows: List[List[Any]] = []

                    if cyc.status == "finished":
                        results = (
                            db.query(CycleResult)
                            .filter(CycleResult.cycle_id == cyc.id)
                            .order_by(CycleResult.final_rank.asc(), CycleResult.points.desc())
                            .all()
                        )
                        for res in results:
                            rows.append(
                                [
                                    res.final_rank,
                                    res.user_name,
                                    round(float(res.points or 0.0), 1),
                                    res.total_minutes,
                                    res.total_pages,
                                    res.streak,
                                    res.no_study_days,
                                    res.absent_days_list or "-",
                                    res.late_days_list or "-",
                                    res.half_coupons_used,
                                    res.one_min_coupons_used,
                                    res.half_coupons_remaining,
                                    res.one_min_coupons_remaining,
                                ]
                            )
                    else:
                        active_users = (
                            db.query(User)
                            .filter(User.league_id == lg.id, User.is_active == True)
                            .all()
                        )
                        ranked_users = ScoringService.rank_users(active_users, lg.floor)
                        for rnk, u in ranked_users:
                            half_rem = int(u.half_coupons or 0)
                            one_rem = int(u.one_min_coupons or 0)
                            rows.append(
                                [
                                    rnk,
                                    u.name,
                                    round(float(u.points or 0.0), 1),
                                    int(u.total_minutes or 0),
                                    int(u.total_pages or 0),
                                    int(u.streak or 0),
                                    int(u.no_study_days or 0),
                                    u.absent_days_list or "-",
                                    u.late_days_list or "-",
                                    max(0, settings.DEFAULT_HALF_COUPONS - half_rem),
                                    max(0, settings.DEFAULT_ONE_MIN_COUPONS - one_rem),
                                    half_rem,
                                    one_rem,
                                ]
                            )

                    cls._style_worksheet(ws, headers, rows, highlight_top3=True)

        elif isinstance(db_or_data, list):
            for idx, sheet_info in enumerate(db_or_data, start=1):
                title = str(sheet_info.get("title") or f"Cycle_{idx}")[:31]
                title = re.sub(r'[\\/*?:\[\]]', "_", title)
                ws = wb.create_sheet(title=title)
                sheets_added += 1
                users_list = sheet_info.get("users", [])
                floor_val = int(sheet_info.get("floor", 10))
                normalized = [cls._extract_row_dict(u, floor_val) for u in users_list]
                headers = [
                    "رتبه",
                    "نام و نام خانوادگی",
                    "امتیاز",
                    "زمان کل (دقیقه)",
                    "صفحات کل",
                    "زنجیره استمرار",
                    "تعداد غیبت",
                    "روزهای غیبت",
                    "روزهای تاخیر",
                ]
                rows = []
                for r_i, item in enumerate(normalized, start=1):
                    rows.append(
                        [
                            item.get("final_rank", r_i),
                            item["name"],
                            item["points"],
                            item["total_minutes"],
                            item["total_pages"],
                            item["streak"],
                            item["no_study_days"],
                            item["absent_days_list"],
                            item["late_days_list"],
                        ]
                    )
                cls._style_worksheet(ws, headers, rows, highlight_top3=True)

        if sheets_added > 0 and default_sheet in wb.worksheets:
            wb.remove(default_sheet)
        else:
            default_sheet.title = "بدون داده"
            cls._style_worksheet(default_sheet, ["وضعیت"], [["هیچ چله‌ای یافت نشد"]], highlight_top3=False)

        if not output_path:
            reports_dir = Path("./reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            ts = DateService.now_iran().strftime("%Y%m%d_%H%M%S")
            uid_short = uuid.uuid4().hex[:6]
            output_path = str(reports_dir / f"cycles_history_archive_{ts}_{uid_short}.xlsx")

        wb.save(output_path)
        wb.close()
        return output_path


# ===========================================================================
# ۴. سرویس محاسبه غیبت‌ها، ترمیم شکاف‌های تاریخی و بازسازی زنجیره استمرار
# ===========================================================================
class AbsenceService:
    """مدیریت غیبت‌های روزانه، همگام‌سازی لیست روزهای غیبت/تاخیر و بازسازی زنجیره (Streak)"""

    @staticmethod
    def parse_days_list(days_str: Optional[str]) -> List[int]:
        """تبدیل رشته روزهای جداشده با ویرگول (مثلاً '2,5,8') به لیست مرتب و یکتای اعداد صحیح"""
        if not days_str:
            return []
        result = set()
        for part in str(days_str).split(","):
            part = DateService.normalize_digits(part.strip())
            if part.isdigit():
                val = int(part)
                if val > 0:
                    result.add(val)
        return sorted(result)

    @staticmethod
    def format_days_list(days: Iterable[int]) -> str:
        """تبدیل مجموعه اعداد روزها به رشته استاندارد جداشده با ویرگول"""
        clean = sorted({int(d) for d in days if int(d) > 0})
        return ",".join(str(d) for d in clean)

    @classmethod
    def sync_days_list_with_count(
        cls,
        current_list_str: Optional[str],
        target_count: int,
        max_day: int = 40,
        exclude_days: Optional[Iterable[int]] = None,
        preferred_days: Optional[Iterable[int]] = None,
        current_day: Optional[int] = None,
    ) -> str:
        """
        همگام‌سازی لیست روزها (absent_days_list یا late_days_list) هنگامی که ادمین
        تعداد غیبت یا تاخیر را به صورت دستی ویرایش می‌کند.
        """
        target_count = max(0, int(target_count))
        excluded = {int(d) for d in (exclude_days or []) if int(d) > 0}
        days = [d for d in cls.parse_days_list(current_list_str) if d not in excluded]

        if target_count == 0:
            return ""
        if len(days) == target_count:
            return cls.format_days_list(days)
        if len(days) > target_count:
            # حذف از انتهای لیست تا به تعداد جدید برسد
            return cls.format_days_list(days[:target_count])

        existing_set = set(days)

        # ۱. اولویت اول: روزهای پیشنهادی (مثلاً روزهای گذشته چله برای غیبت، یا روزهای دارای لاگ برای تاخیر)
        if preferred_days:
            for p_day in preferred_days:
                if len(existing_set) >= target_count:
                    break
                p_val = int(p_day)
                if p_val > 0 and p_val not in existing_set and p_val not in excluded:
                    existing_set.add(p_val)

        # ۲. اولویت دوم: روزهای گذشته قبل از امروز (۱ تا current_day - 1)
        if current_day and current_day > 1:
            for cand in range(1, int(current_day)):
                if len(existing_set) >= target_count:
                    break
                if cand not in existing_set and cand not in excluded:
                    existing_set.add(cand)

        # ۳. اولویت سوم: از انتهای چله به عقب (۴۰، ۳۹، ...) تا با ثبت مطالعه امروز و فردا تداخل نکند
        upper_bound = max(max_day, target_count + len(excluded) + 10)
        for cand in range(max_day, 0, -1):
            if len(existing_set) >= target_count:
                break
            if cand not in existing_set and cand not in excluded and cand != current_day:
                existing_set.add(cand)

        candidate = 1
        while len(existing_set) < target_count and candidate <= upper_bound:
            if candidate not in existing_set and candidate not in excluded:
                existing_set.add(candidate)
            candidate += 1

        # اگر باز هم به تعداد نرسید (مثلاً تمام روزها پر بودند)، از انتهای دوره پر می‌کنیم
        for cand in range(upper_bound, 0, -1):
            if len(existing_set) >= target_count:
                break
            if cand not in existing_set:
                existing_set.add(cand)
        return cls.format_days_list(existing_set)

    @classmethod
    def get_missing_dates(
        cls,
        last_job_date_str: Optional[str],
        up_to_yesterday_str: Optional[str] = None,
    ) -> List[str]:
        """
        محاسبه لیست تاریخ‌های میلادی (YYYY-MM-DD) که بین آخرین اجرای جاب نیمه‌شب
        و روز گذشته جا افتاده‌اند.
        """
        yesterday_d = (
            datetime.strptime(up_to_yesterday_str[:10], "%Y-%m-%d").date()
            if up_to_yesterday_str
            else DateService.yesterday_date()
        )
        if not last_job_date_str:
            return [yesterday_d.strftime("%Y-%m-%d")]

        try:
            last_processed_d = datetime.strptime(last_job_date_str[:10], "%Y-%m-%d").date() - timedelta(days=1)
        except ValueError:
            return [yesterday_d.strftime("%Y-%m-%d")]

        missing: List[str] = []
        curr = last_processed_d + timedelta(days=1)
        # حداکثر بررسی ۴۰ روز گذشته برای جلوگیری از حلقه بی‌نهایت
        if (yesterday_d - curr).days > settings.LEAGUE_DURATION:
            curr = yesterday_d - timedelta(days=settings.LEAGUE_DURATION)

        while curr <= yesterday_d:
            missing.append(curr.strftime("%Y-%m-%d"))
            curr += timedelta(days=1)

        return missing

    @classmethod
    def process_absences_for_dates(cls, db: Session, dates: List[str]) -> int:
        """
        بررسی و ثبت غیبت برای تمام کاربران فعال در لیگ‌های فعال به ازای تاریخ‌های داده‌شده.
        برمی‌گرداند: تعداد غیبت‌های جدید ثبت‌شده.
        """
        if not dates:
            return 0

        from database import get_or_create_active_cycle

        total_absences_recorded = 0
        active_leagues = (
            db.query(League)
            .filter(League.is_deleted == False, League.is_active == True)
            .all()
        )

        for lg in active_leagues:
            if not lg.start_shamsi:
                lg.start_shamsi = DateService.today_shamsi()
            active_cycle = get_or_create_active_cycle(db, lg)

            users = (
                db.query(User)
                .filter(User.league_id == lg.id, User.is_active == True)
                .all()
            )
            for dt_str in dates:
                try:
                    target_date = datetime.strptime(dt_str[:10], "%Y-%m-%d").date()
                except ValueError:
                    continue

                start_date = DateService.shamsi_to_date(active_cycle.start_shamsi or lg.start_shamsi)
                if not start_date or target_date < start_date:
                    continue

                day_num = (target_date - start_date).days + 1
                if day_num < 1 or day_num > settings.LEAGUE_DURATION:
                    continue

                for u in users:
                    # بررسی تاریخ عضویت کاربر در لیگ (کاربر نباید برای روزهای قبل از عضویتش غیبت بخورد)
                    if u.created_at:
                        u_created = u.created_at
                        if u_created.tzinfo is None:
                            u_created = u_created.replace(tzinfo=timezone.utc).astimezone(IRAN_TZ)
                        else:
                            u_created = u_created.astimezone(IRAN_TZ)
                        if u_created.date() > target_date:
                            continue

                    # آیا کاربر برای این روز یا این تاریخ در چله فعلی لاگ معتبری ثبت کرده است؟
                    has_log = (
                        db.query(ActivityLog)
                        .filter(
                            ActivityLog.user_id == u.id,
                            ActivityLog.league_id == lg.id,
                            (ActivityLog.cycle_id == active_cycle.id)
                            | (
                                (ActivityLog.cycle_id == None)
                                & (ActivityLog.cycle_number == lg.cycle_number)
                            ),
                            (ActivityLog.log_date == dt_str)
                            | (ActivityLog.league_day == day_num),
                            ActivityLog.minutes > 0,
                        )
                        .first()
                    )
                    if not has_log:
                        from database import set_system_state
                        absent_days = cls.parse_days_list(u.absent_days_list)
                        late_days = cls.parse_days_list(u.late_days_list)
                        if day_num not in absent_days and day_num not in late_days:
                            absent_days.append(day_num)
                            u.absent_days_list = cls.format_days_list(absent_days)
                            u.no_study_days = len(absent_days)
                            u.streak = 0
                            set_system_state(db, f"streak_offset_{u.id}", "0")
                            total_absences_recorded += 1

        db.commit()
        return total_absences_recorded

    @classmethod
    def reconcile_historical_gaps(
        cls,
        db: Session,
        user: Optional[User] = None,
        league: Optional[League] = None,
    ) -> int:
        """
        ترمیم شکاف‌های تاریخی:
        اگر کاربری برای روزی لاگ ثبت کرده باشد (مثلاً ثبت با تاخیر دیروز)، آن روز را از
        absent_days_list حذف کرده و شمارنده no_study_days را دقیقاً با طول absent_days_list همگام می‌کند.
        """
        from database import get_or_create_active_cycle

        updated_count = 0
        if user is not None:
            users_to_check = [user]
        elif league is not None:
            users_to_check = (
                db.query(User)
                .filter(User.league_id == league.id, User.is_active == True)
                .all()
            )
        else:
            users_to_check = db.query(User).filter(User.is_active == True, User.league_id.isnot(None)).all()

        league_cache: Dict[str, Optional[League]] = {}
        cycle_cache: Dict[str, Optional[Cycle]] = {}

        for u in users_to_check:
            if not u.league_id:
                continue
            if u.league_id not in league_cache:
                league_cache[u.league_id] = (
                    league
                    if (league and league.id == u.league_id)
                    else db.query(League).filter(League.id == u.league_id).first()
                )
            lg = league_cache[u.league_id]
            if not lg or lg.is_deleted:
                continue

            if lg.id not in cycle_cache:
                cycle_cache[lg.id] = get_or_create_active_cycle(db, lg)
            cyc = cycle_cache[lg.id]

            logs = (
                db.query(ActivityLog)
                .filter(
                    ActivityLog.user_id == u.id,
                    ActivityLog.league_id == lg.id,
                    (ActivityLog.cycle_id == cyc.id)
                    | (
                        (ActivityLog.cycle_id == None)
                        & (ActivityLog.cycle_number == lg.cycle_number)
                    ),
                    ActivityLog.minutes > 0,
                )
                .all()
            )

            logged_days = set()
            start_d = DateService.shamsi_to_date(cyc.start_shamsi or lg.start_shamsi)
            for log in logs:
                if log.league_day is not None and 1 <= int(log.league_day) <= settings.LEAGUE_DURATION:
                    logged_days.add(int(log.league_day))
                elif log.league_day is None and log.log_date and start_d:
                    try:
                        ld = datetime.strptime(log.log_date[:10], "%Y-%m-%d").date()
                        d_num = (ld - start_d).days + 1
                        if 1 <= d_num <= settings.LEAGUE_DURATION:
                            logged_days.add(d_num)
                    except ValueError:
                        pass

            absent_days = cls.parse_days_list(u.absent_days_list)
            cleaned_absent = [d for d in absent_days if d not in logged_days]

            new_absent_str = cls.format_days_list(cleaned_absent)
            if u.absent_days_list != new_absent_str or u.no_study_days != len(cleaned_absent):
                u.absent_days_list = new_absent_str
                u.no_study_days = len(cleaned_absent)
                updated_count += 1

        db.commit()
        return updated_count

    @classmethod
    def _compute_raw_streak_from_logs(
        cls,
        db: Session,
        u: User,
        lg: League,
        cyc: Cycle,
    ) -> int:
        """محاسبه زنجیره خام صرفاً بر اساس پیوستگی لاگ‌های ثبت‌شده در چله فعال"""
        today_str = DateService.today_str()
        yesterday_str = DateService.yesterday_str()

        logs = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.user_id == u.id,
                ActivityLog.league_id == lg.id,
                (ActivityLog.cycle_id == cyc.id)
                | (
                    (ActivityLog.cycle_id == None)
                    & (ActivityLog.cycle_number == lg.cycle_number)
                ),
                ActivityLog.minutes > 0,
            )
            .all()
        )

        start_d = DateService.shamsi_to_date(cyc.start_shamsi or lg.start_shamsi)
        end_d = (start_d + timedelta(days=settings.LEAGUE_DURATION - 1)) if start_d else None
        logged_dates = set()
        for log in logs:
            if log.log_date and (
                log.league_day is None or 1 <= int(log.league_day) <= settings.LEAGUE_DURATION
            ):
                try:
                    ld_obj = datetime.strptime(log.log_date[:10], "%Y-%m-%d").date()
                    if start_d and ld_obj < start_d:
                        continue
                    if end_d and ld_obj > end_d:
                        continue
                    logged_dates.add(log.log_date[:10])
                except ValueError:
                    logged_dates.add(log.log_date[:10])
        logged_days = {
            int(log.league_day)
            for log in logs
            if log.league_day is not None and 1 <= int(log.league_day) <= settings.LEAGUE_DURATION
        }

        raw_current_day = DateService.calculate_raw_league_day(
            cyc.start_shamsi or lg.start_shamsi
        )
        current_day = min(raw_current_day, settings.LEAGUE_DURATION)

        if raw_current_day <= settings.LEAGUE_DURATION:
            if current_day in logged_days or today_str in logged_dates:
                anchor_day = current_day
                anchor_date = DateService.today_date()
            elif (
                current_day > 1
                and ((current_day - 1) in logged_days or yesterday_str in logged_dates)
            ):
                anchor_day = current_day - 1
                anchor_date = DateService.yesterday_date()
            else:
                return 0
        else:
            last_cycle_day = settings.LEAGUE_DURATION
            end_date_str = end_d.strftime("%Y-%m-%d") if end_d else yesterday_str
            if last_cycle_day in logged_days or end_date_str in logged_dates:
                anchor_day = last_cycle_day
                anchor_date = end_d or DateService.yesterday_date()
            else:
                return 0

        streak_by_day = 0
        d_cursor = anchor_day
        while d_cursor >= 1 and d_cursor in logged_days:
            streak_by_day += 1
            d_cursor -= 1

        streak_by_date = 0
        dt_cursor = anchor_date
        while dt_cursor.strftime("%Y-%m-%d") in logged_dates:
            streak_by_date += 1
            dt_cursor -= timedelta(days=1)

        return max(streak_by_day, streak_by_date)

    @classmethod
    def reconcile_streaks(
        cls,
        db: Session,
        user: Optional[User] = None,
        league: Optional[League] = None,
    ) -> int:
        """
        محاسبه مجدد زنجیره استمرار (Streak) بر اساس پیوستگی واقعی لاگ‌های کاربر در چله جاری
        با حفظ آفست ویرایش دستی ادمین در صورت برقرار بودن زنجیره.
        """
        from database import get_or_create_active_cycle, get_system_state, set_system_state

        if user is not None:
            users_to_check = [user]
        elif league is not None:
            users_to_check = (
                db.query(User)
                .filter(User.league_id == league.id, User.is_active == True)
                .all()
            )
        else:
            users_to_check = db.query(User).filter(User.is_active == True, User.league_id.isnot(None)).all()

        last_streak = 0

        for u in users_to_check:
            if not u.league_id:
                continue
            lg = (
                league
                if (league and league.id == u.league_id)
                else db.query(League).filter(League.id == u.league_id).first()
            )
            if not lg or lg.is_deleted:
                continue

            cyc = get_or_create_active_cycle(db, lg)
            raw_streak = cls._compute_raw_streak_from_logs(db, u, lg, cyc)

            raw_offset_str = get_system_state(db, f"streak_offset_{u.id}", "0")
            try:
                offset = int(raw_offset_str or "0")
            except ValueError:
                offset = 0

            if raw_streak == 0:
                raw_current_day = DateService.calculate_raw_league_day(
                    cyc.start_shamsi or lg.start_shamsi
                )
                yesterday_day = raw_current_day - 1
                absent_days = cls.parse_days_list(u.absent_days_list)
                if offset > 0 and (yesterday_day < 1 or yesterday_day not in absent_days):
                    u.streak = offset
                else:
                    u.streak = 0
                    if offset != 0:
                        set_system_state(db, f"streak_offset_{u.id}", "0")
            else:
                u.streak = max(0, raw_streak + offset)

            last_streak = u.streak

        db.commit()
        return last_streak