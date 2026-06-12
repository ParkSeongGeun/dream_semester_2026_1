# ============================================
# Stage 1: Builder - 의존성 설치
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.prod.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.prod.txt


# ============================================
# Stage 2: Runtime - 최종 이미지
# ============================================
FROM python:3.12-slim AS runtime

# non-root 유저 생성
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --create-home appuser

# Python 패키지 복사
COPY --from=builder /install /usr/local

WORKDIR /app

# 애플리케이션 코드 + Alembic 마이그레이션 복사
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh

# 소유권 변경 + entrypoint 실행 권한
RUN chown -R appuser:appuser /app && chmod +x /usr/local/bin/entrypoint.sh

# non-root 유저로 전환
USER appuser

# 환경변수 기본값
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

# 헬스체크 (curl 대신 Python 사용으로 이미지 경량화)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/ready')" || exit 1

# DB 마이그레이션(alembic upgrade head) 후 Gunicorn + Uvicorn worker로 실행
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "60", \
     "--access-logfile", "-"]
