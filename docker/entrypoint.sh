#!/bin/sh
# نقطه ورود کانتینر ربات کتابخوارشو
# کانتینر با روت شروع می‌شود تا مالکیت حجم‌های data/logs (که روی هاست ممکن است
# متعلق به روت یا UID قدیمی باشند) برای کاربر app اصلاح شود، سپس ربات با gosu
# تحت کاربر غیرروت app اجرا می‌شود. chown به‌صورت best-effort است و هرگز نباید
# مانع بالا آمدن ربات شود.
mkdir -p /app/data /app/logs /app/data/backups /app/data/reports
chown -R app:app /app/data /app/logs 2>/dev/null || true
exec gosu app "$@"
