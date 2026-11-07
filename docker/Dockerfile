# ==============================================================================
# KetabKharsho Telegram/Bale Bot - Production Dockerfile
# Base Image: Python 3.12 Slim (Debian Bookworm)
# ==============================================================================
FROM python:3.12-slim

# تنظیم متغیرهای سیستمی و پایتون
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Tehran \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# تست اعتبارسنجی حین بیلد (Smoke Test):
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

COPY . .

RUN mkdir -p /app/data /app/logs /app/data/backups /app/data/reports

CMD ["python", "main.py"]
