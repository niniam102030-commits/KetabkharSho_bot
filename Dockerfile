# ==============================================================================
# KetabKharsho Telegram/Bale Bot - Production Dockerfile
# Base Image: Python 3.12 Slim (Debian Bookworm)
# ==============================================================================
FROM python:3.12-slim

# تنظیم متغیرهای سیستمی و پایتون
# PYTHONUNBUFFERED=1: خروجی لاگ‌ها بدون بافر فورا در docker logs نمایش داده می‌شود
# PYTHONDONTWRITEBYTECODE=1: از تولید فایل‌های .pyc اضافی در کانتینر جلوگیری می‌کند
# TZ=Asia/Tehran: تنظیم پیش‌فرض منطقه زمانی کانتینر به ایران
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Tehran \
    DEBIAN_FRONTEND=noninteractive

# تعیین دایرکتوری کاری در کانتینر
WORKDIR /app

# نصب ابزارهای پایه و داده‌های زمانی IANA
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ارتقای ابزارهای پکیج‌منیجر پایتون به آخرین نسخه
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# کپی requirements.txt به تنهایی (برای استفاده بهینه از کش داکر در هنگام بیلد مجدد)
COPY requirements.txt .

# نصب کلیه وابستگی‌های مورد نیاز با نسخه‌های دقیق و رسمی
RUN pip install --no-cache-dir -r requirements.txt

# تست اعتبارسنجی حین بیلد (Smoke Test):
# اطمینان 100% از نصب aiogram نسخه 3 و ماژول‌های کلاینت آن (مانند DefaultBotProperties و AiohttpSession)
RUN python -c "\
import aiogram; \
from aiogram import Bot, Dispatcher; \
from aiogram.client.default import DefaultBotProperties; \
from aiogram.client.session.aiohttp import AiohttpSession; \
from aiogram.client.telegram import TelegramAPIServer; \
import sqlalchemy; \
import apscheduler; \
import openpyxl; \
print(f'>>> تست موفق: aiogram نسخه {aiogram.__version__} و تمام وابستگی‌ها به درستی نصب شدند.'); \
"

# ایجاد کاربر غیرروت با شناسه ثابت (UID/GID=10001) پیش از کپی کد و تنظیم دایرکتوری‌های داده
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app app \
    && mkdir -p /app/data /app/logs /app/data/backups /app/data/reports \
    && chown -R app:app /app

# کپی سورس کد پروژه به داخل کانتینر با مالکیت کاربر غیرروت
COPY --chown=app:app . .

# ثبت شناسه کامیت در محیط کانتینر برای نمایش در اعلان استارتاپ و بکاپ‌ها
ARG GIT_COMMIT=""
ENV GIT_COMMIT=${GIT_COMMIT}

# تضمین مالکیت دایرکتوری‌های پیش‌فرض برای کاربر غیرروت
RUN mkdir -p /app/data /app/logs /app/data/backups /app/data/reports \
    && chown -R app:app /app/data /app/logs

USER app

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import os, pathlib; assert any('main.py' in p.read_text(errors='ignore') for p in pathlib.Path('/proc').glob('[0-9]*/cmdline')); assert os.access('/app/data', os.W_OK)" || exit 1

# دستور اجرای ربات
CMD ["python", "main.py"]
