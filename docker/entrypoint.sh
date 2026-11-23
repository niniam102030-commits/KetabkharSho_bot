#!/bin/sh
set -e

mkdir -p /app/data /app/logs /app/data/backups /app/data/reports
chown -R app:app /app/data /app/logs

exec gosu app "$@"
