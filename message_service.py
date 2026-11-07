import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session

from models import GroupMessage, GroupTerm

logger = logging.getLogger(__name__)

# ۵ اصطلاح پایه قابل شخصی‌سازی برای هر مجموعه
DEFAULT_TERMS: Dict[str, str] = {
    "meesaq": "میثاق",
    "cheleh": "چله",
    "half_coupon": "سهمیه نصف میثاق",
    "golden_coupon": "سهمیه طلایی",
    "league": "لیگ",
}

TERM_LABELS: Dict[str, str] = {
    "meesaq": "میثاق (کف مطالعه)",
    "cheleh": "چله (دوره ۴۰ روزه)",
    "half_coupon": "سهمیه نصف میثاق",
    "golden_coupon": "سهمیه طلایی",
    "league": "لیگ",
}

# ۷ پیام اصلی قابل شخصی‌سازی برای هر مجموعه
DEFAULT_MESSAGES: Dict[str, str] = {
    "welcome": "به بازوی ثبت مطالعه خوش آمدید 👋",
    "enter_pwd": "لطفا رمز ورود به بازو را وارد کنید",
    "study_logged": "📝 *گزارش مطالعه امروز ثبت شد!*\n\n✨ به مسیرت ادامه بده! 📚",
    "late_logged": "⏳ *گزارش مطالعه دیروز با موفقیت ثبت شد!*\n\n✨ آفرین به پشتکار شما! 📚",
    "reminder_night": (
        "⏰ *یادآوری مطالعه*\n\n"
        "📚 شما هنوز ثبت مطالعه‌ی امروز خود را انجام نداده‌اید.\n\n"
        "📝 لطفاً مطالعه خود را انجام داده و با ربات ثبت کنید."
    ),
    "cycle_finished": "🎉 چله لیگ به پایان رسید و نتایج نهایی ثبت شد. چله جدید از روز ۱ آغاز شد.",
    "rules_help": (
        "❓ *راهنمای کتابخوارشو*\n\n"
        "📝 از گزینه ثبت مطالعه برای وارد کردن زمان و صفحات استفاده کنید.\n"
        "🏆 جدول باشگاه رتبه شما و اعضای لیگ را نشان می‌دهد.\n"
        "👤 در حساب کاربری، امتیازها و سهمیه‌های خود را ببینید.\n\n"
        "⭐️ *نحوه امتیازدهی و سهمیه‌ها*\n"
        "✅ با رسیدن به میثاق روزانه، ۱۰ امتیاز کامل می‌گیرید.\n"
        "🌸 اگر حداقل نصف میثاق را مطالعه کنید، یک سهمیه «نصف میثاق» مصرف می‌شود و ۱۰ امتیاز می‌گیرید.\n"
        "👑 اگر سهمیه نصف میثاق نداشته باشید و حداقل ۱ دقیقه مطالعه کنید، سهمیه طلایی یک دقیقه‌ای مصرف می‌شود و ۱۰ امتیاز می‌گیرید.\n"
        "📉 اگر سهمیه‌ای باقی نمانده باشد، امتیاز شما متناسب با زمان مطالعه محاسبه می‌شود.\n"
        "🎫 سهمیه‌های پیش‌فرض هر دوره: ۵ سهمیه نصف میثاق و ۱ سهمیه طلایی یک دقیقه‌ای.\n\n"
        "⏳ *ثبت مطالعه با تاخیر (دیروز)*\n"
        "اگر روز گذشته مطالعه خود را ثبت نکرده باشید، دکمه‌ی «ثبت مطالعه دیروز» برای شما فعال می‌شود.\n"
        "با ثبت مطالعه از این طریق، نیمی (۵۰٪) از امتیازِ کسب شده کسر می‌شود، اما از ثبت غیبت کامل برای روز قبل جلوگیری می‌گردد."
    ),
}

MESSAGE_LABELS: Dict[str, str] = {
    "welcome": "پیام خوش‌آمدگویی اولیه",
    "enter_pwd": "درخواست رمز ورود مجموعه",
    "study_logged": "تایید ثبت مطالعه امروز",
    "late_logged": "تایید ثبت مطالعه دیروز (با تاخیر)",
    "reminder_night": "یادآوری مطالعه شبانه",
    "cycle_finished": "پیام پایان چله ۴۰ روزه",
    "rules_help": "متن راهنما و قوانین باشگاه",
}


class MessageService:
    """سرویس مدیریت واژه‌نامه اختصاصی و پیام‌های سفارشی هر مجموعه"""

    @classmethod
    def get_terms(cls, db: Session, group_id: Optional[int]) -> Dict[str, str]:
        """دریافت دیکشنری کامل اصطلاحات مجموعه (ترکیب پیش‌فرض و سفارشی)"""
        terms = dict(DEFAULT_TERMS)
        if not group_id:
            return terms

        custom_rows = (
            db.query(GroupTerm).filter(GroupTerm.group_id == int(group_id)).all()
        )
        for row in custom_rows:
            if row.term_key in terms and row.custom_term and row.custom_term.strip():
                terms[row.term_key] = row.custom_term.strip()
        return terms

    @classmethod
    def get_term(cls, db: Session, group_id: Optional[int], term_key: str) -> str:
        """دریافت یک اصطلاح خاص برای مجموعه"""
        terms = cls.get_terms(db, group_id)
        return terms.get(term_key, DEFAULT_TERMS.get(term_key, term_key))

    @classmethod
    def set_term(cls, db: Session, group_id: int, term_key: str, custom_term: str) -> None:
        """ذخیره یا ویرایش یک اصطلاح سفارشی برای مجموعه"""
        if term_key not in DEFAULT_TERMS:
            return
        record = (
            db.query(GroupTerm)
            .filter(GroupTerm.group_id == int(group_id), GroupTerm.term_key == term_key)
            .first()
        )
        if record:
            record.custom_term = custom_term.strip()
        else:
            db.add(
                GroupTerm(
                    group_id=int(group_id),
                    term_key=term_key,
                    custom_term=custom_term.strip(),
                )
            )
        db.commit()

    @classmethod
    def reset_term(cls, db: Session, group_id: int, term_key: str) -> None:
        """بازنشانی یک اصطلاح مجموعه به مقدار پیش‌فرض"""
        db.query(GroupTerm).filter(
            GroupTerm.group_id == int(group_id), GroupTerm.term_key == term_key
        ).delete()
        db.commit()

    @classmethod
    def apply_terms(
        cls,
        db: Session,
        group_id: Optional[int],
        text: str,
        terms: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        جایگزینی هوشمند اصطلاحات پیش‌فرض در متن با معادل‌های اختصاصی مجموعه.
        از توکن‌های میانی استفاده می‌شود تا جایگزینی عبارات طولانی‌تر مثل «سهمیه نصف میثاق»
        با کلمه «میثاق» تداخل پیدا نکند.
        پارامتر terms (اختیاری): واژه‌نامه از پیش‌خوانده‌شده برای جلوگیری از کوئری تکراری در ارسال انبوه.
        """
        if not text or not group_id:
            return text

        if terms is None:
            terms = cls.get_terms(db, group_id)
        if terms == DEFAULT_TERMS:
            return text

        # ترتیب جایگزینی از طولانی‌ترین عبارت به کوتاه‌ترین عبارت
        ordered_keys = [
            "half_coupon",
            "golden_coupon",
            "meesaq",
            "cheleh",
            "league",
        ]
        result = text
        placeholders: Dict[str, str] = {}

        for idx, key in enumerate(ordered_keys):
            default_val = DEFAULT_TERMS[key]
            custom_val = terms.get(key, default_val)
            placeholder = f"%%TERM_PLACEHOLDER_{idx}%%"
            placeholders[placeholder] = custom_val
            result = result.replace(default_val, placeholder)

            # پشتیبانی از حالت گیومه‌دار «سهمیه «نصف میثاق»» و حالت کوتاه «نصف میثاق»
            if key == "half_coupon" and custom_val != default_val:
                quoted_half_ph = "%%TERM_QUOTED_HALF%%"
                placeholders[quoted_half_ph] = f"«{custom_val}»"
                result = result.replace("سهمیه «نصف میثاق»", quoted_half_ph)

                short_half_placeholder = "%%TERM_SHORT_HALF%%"
                short_custom = (
                    custom_val.replace("سهمیه ", "", 1)
                    if custom_val.startswith("سهمیه ")
                    else custom_val
                )
                placeholders[short_half_placeholder] = short_custom
                result = result.replace("نصف میثاق", short_half_placeholder)

        for ph, final_val in placeholders.items():
            result = result.replace(ph, final_val)

        return result

    @classmethod
    def get_message(
        cls,
        db: Session,
        group_id: Optional[int],
        msg_key: str,
        apply_group_terms: bool = True,
    ) -> str:
        """دریافت متن پیام مجموعه (سفارشی یا پیش‌فرض) به همراه اعمال واژه‌نامه مجموعه"""
        base_text = DEFAULT_MESSAGES.get(msg_key, "")
        if group_id:
            custom_row = (
                db.query(GroupMessage)
                .filter(
                    GroupMessage.group_id == int(group_id),
                    GroupMessage.msg_key == msg_key,
                )
                .first()
            )
            if custom_row and custom_row.custom_text and custom_row.custom_text.strip():
                base_text = custom_row.custom_text.strip()

        if apply_group_terms and group_id:
            return cls.apply_terms(db, group_id, base_text)
        return base_text

    @classmethod
    def set_message(cls, db: Session, group_id: int, msg_key: str, custom_text: str) -> None:
        """ذخیره یا ویرایش یک پیام سفارشی برای مجموعه"""
        if msg_key not in DEFAULT_MESSAGES:
            return
        record = (
            db.query(GroupMessage)
            .filter(
                GroupMessage.group_id == int(group_id),
                GroupMessage.msg_key == msg_key,
            )
            .first()
        )
        if record:
            record.custom_text = custom_text.strip()
        else:
            db.add(
                GroupMessage(
                    group_id=int(group_id),
                    msg_key=msg_key,
                    custom_text=custom_text.strip(),
                )
            )
        db.commit()

    @classmethod
    def reset_message(cls, db: Session, group_id: int, msg_key: str) -> None:
        """بازنشانی یک پیام مجموعه به متن پیش‌فرض"""
        db.query(GroupMessage).filter(
            GroupMessage.group_id == int(group_id),
            GroupMessage.msg_key == msg_key,
        ).delete()
        db.commit()