#!/usr/bin/env bash
# ==============================================================================
# اسکریپت بروزرسانی خودکار و دیپلوی نسخه جدید ربات کتابخوارشو روی سرور
# نحوه اجرا روی سرور لینوکس:
# chmod +x docker/deploy.sh
# ./docker/deploy.sh [commit_sha_or_tag]
# ==============================================================================

set -euo pipefail

echo "=================================================="
echo "🚀 1. دریافت آخرین تغییرات و کدهای جدید از گیت‌هاب..."
echo "=================================================="
git pull origin main

TARGET_TAG="${1:-$(git rev-parse HEAD)}"
export BOT_IMAGE_TAG="$TARGET_TAG"
echo "🔖 تگ هدف ایمیج برای دیپلوی: ${BOT_IMAGE_TAG}"

echo ""
echo "=================================================="
echo "📁 2. آماده‌سازی دایرکتوری‌های داده و دسترسی کاربر غیرروت (10001)..."
echo "=================================================="
mkdir -p data data/backups data/reports logs
chown -R 10001:10001 data logs 2>/dev/null || true

echo ""
echo "=================================================="
echo "📦 3. دریافت ایمیج دقیق نسخه ${BOT_IMAGE_TAG} از GHCR (با انتظار برای بیلد در حال انجام)..."
echo "=================================================="
MAX_PULL_WAIT=180
PULL_ELAPSED=0
PULLED=0
while [ "$PULL_ELAPSED" -lt "$MAX_PULL_WAIT" ]; do
  if docker compose pull; then
    PULLED=1
    break
  fi
  echo "⏳ ایمیج ${BOT_IMAGE_TAG} هنوز آماده نیست؛ انتظار ۱۰ ثانیه‌ای (${PULL_ELAPSED}/${MAX_PULL_WAIT}s)..."
  sleep 10
  PULL_ELAPSED=$((PULL_ELAPSED + 10))
done

if [ "$PULLED" -ne 1 ]; then
  echo "❌ دریافت ایمیج ${BOT_IMAGE_TAG} پس از ${MAX_PULL_WAIT} ثانیه ناموفق بود."
  exit 1
fi

echo ""
echo "=================================================="
echo "🔄 4. راه‌اندازی کانتینر با نسخه ${BOT_IMAGE_TAG}..."
echo "=================================================="
docker compose up -d --remove-orphans

echo ""
echo "=================================================="
echo "🩺 5. بررسی سلامت واقعی کانتینر (Healthcheck)..."
echo "=================================================="
MAX_HEALTH_WAIT=45
HEALTH_ELAPSED=0
while [ "$HEALTH_ELAPSED" -lt "$MAX_HEALTH_WAIT" ]; do
  HEALTH_STATUS=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' ketabkharsho_bot 2>/dev/null || echo "missing")
  if [ "$HEALTH_STATUS" = "healthy" ]; then
    break
  fi
  if [ "$HEALTH_STATUS" = "unhealthy" ] || [ "$HEALTH_STATUS" = "exited" ] || [ "$HEALTH_STATUS" = "dead" ]; then
    echo "❌ وضعیت کانتینر نامطلوب است (${HEALTH_STATUS})؛ لاگ‌های اخیر:"
    docker compose logs --tail=100 ketabkharsho-bot
    exit 1
  fi
  sleep 3
  HEALTH_ELAPSED=$((HEALTH_ELAPSED + 3))
done

FINAL_STATUS=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' ketabkharsho_bot 2>/dev/null || echo "missing")
if [ "$FINAL_STATUS" != "healthy" ]; then
  echo "❌ کانتینر در مهلت ${MAX_HEALTH_WAIT} ثانیه به وضعیت healthy نرسید (${FINAL_STATUS})؛ لاگ‌های اخیر:"
  docker compose logs --tail=100 ketabkharsho-bot
  exit 1
fi

echo ""
echo "=================================================="
echo "🧹 6. پاکسازی ایمیج‌های موقت و بدون استفاده..."
echo "=================================================="
docker image prune -f

echo "✅ نسخه ${BOT_IMAGE_TAG} با موفقیت فعال و سالم (healthy) اجرا شد!"
echo "=================================================="
docker compose ps
