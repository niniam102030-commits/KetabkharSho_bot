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

# کپی سورس کد پروژه به داخل کانتینر
COPY . .

# ایجاد دایرکتوری‌های داده و لاگ
RUN mkdir -p /app/data /app/logs /app/data/backups /app/data/reports

# دستور اجرای ربات
CMD ["python", "main.py"]
