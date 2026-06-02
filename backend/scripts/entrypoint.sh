#!/bin/sh
# ============================================
# 컨테이너 시작 시 DB 마이그레이션 후 앱 실행
# ============================================
set -e

echo "=== Running Alembic migrations (upgrade head) ==="
alembic upgrade head

echo "=== Starting application ==="
exec "$@"
