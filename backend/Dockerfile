# ============================================
# Stage 1: Builder - 의존성 설치
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /build

# 빌드 의존성 설치 (asyncpg 컴파일에 필요)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.prod.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.prod.txt


# ============================================
# Stage 2: Runtime - 최종 이미지
# ============================================
FROM python:3.12-slim AS runtime

# libpq 런타임 라이브러리 (asyncpg에 필요)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# non-root 유저 생성
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --create-home appuser

# Python 패키지 복사
COPY --from=builder /install /usr/local

WORKDIR /app

# 애플리케이션 코드 복사
COPY app/ ./app/

# 소유권 변경
RUN chown -R appuser:appuser /app

# non-root 유저로 전환
USER appuser

# 환경변수 기본값
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Gunicorn + Uvicorn worker로 실행
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "60", \
     "--access-logfile", "-"]
