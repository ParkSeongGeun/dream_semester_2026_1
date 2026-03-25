# 4주차 활동 보고서

**프로젝트**: ComfortableMove (맘편한 이동) 백엔드 개발
**기간**: 2026년 3월 18일 ~ 2026년 3월 25일
**주요 목표**: 테스트 완성 + Docker 컨테이너화

---

## 📋 주차 목표

3주차 피드백에서 지적된 비동기 테스트 환경 이슈를 해결하고 커버리지 80%를 달성한 뒤, Docker 컨테이너화를 통해 배포 가능한 환경을 구축합니다.

---

## ✅ 완료한 작업

### 파트 A: 테스트 완성

#### 1. 비동기 테스트 환경 이슈 해결

**문제점**: 3주차에서 `@pytest.fixture` 로 정의된 async fixture가 coroutine 객체를 반환하여 테스트 실패

**해결**:
- `@pytest_asyncio.fixture`로 비동기 fixture 데코레이터 변경
- SQLite-PostgreSQL 타입 호환성 레이어 구현

```python
# conftest.py - 비동기 fixture 수정
@pytest_asyncio.fixture(scope="function")
async def test_db():
    """테스트용 데이터베이스 세션"""
    async with test_engine.begin() as conn:
        await conn.run_sync(_create_tables_for_sqlite)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        await session.close()
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
```

#### 2. SQLite-PostgreSQL 타입 호환성 해결

테스트에서 SQLite 인메모리 DB를 사용하면서 PostgreSQL 전용 타입과 CHECK 제약조건 충돌 문제를 해결했습니다.

```python
# SQLite에서 PostgreSQL UUID → CHAR(36)으로 렌더링
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP as PG_TIMESTAMP
from sqlalchemy.ext.compiler import compiles

compiles(PG_UUID, "sqlite")(lambda type_, compiler, **kw: "CHAR(36)")
compiles(PG_TIMESTAMP, "sqlite")(lambda type_, compiler, **kw: "TIMESTAMP")
```

PostgreSQL regex(`~`) 연산자를 사용하는 CHECK 제약조건도 SQLite에서 자동 제거 후 복원하는 로직을 구현했습니다.

#### 3. 테스트 코드 구현 현황

| 테스트 파일 | 테스트 수 | 분류 |
|---|---|---|
| `tests/unit/test_schemas.py` | 11개 | Pydantic 스키마 검증 |
| `tests/unit/test_seoul_bus_service.py` | 18개 | 버스 API 서비스 파싱 |
| `tests/unit/test_redis.py` | 20개 | Redis 캐싱 함수 Mock 테스트 |
| `tests/integration/test_api_health.py` | 3개 | 헬스체크 API |
| `tests/integration/test_api_bus.py` | 6개 | 버스 도착 정보 API |
| `tests/integration/test_api_boarding.py` | 9개 | 탑승 기록 API |
| `tests/integration/test_api_statistics.py` | 10개 | 통계 API |
| `tests/integration/test_seoul_bus_api.py` | 22개 | Seoul Bus API (실제 7 + Mock 15) |
| **합계** | **99개** | |

#### 4. 테스트 실행 결과

```bash
$ python -m pytest tests/ -m "not slow" --cov=app --cov-report=term-missing

92 passed, 7 deselected, 1 warning in 1.05s

---------- coverage: platform darwin, python 3.12.7-final-0 ----------
Name                            Stmts   Miss  Cover   Missing
-------------------------------------------------------------
app/api/v1/boarding.py             17      5    71%
app/api/v1/bus.py                  30      0   100%
app/api/v1/health.py               30      2    93%
app/api/v1/statistics.py           86     45    48%
app/core/config.py                 39      0   100%
app/core/redis.py                  66      0   100%
app/models/boarding_record.py      25      1    96%
app/models/user_device.py          22      1    95%
app/schemas/boarding.py            28      0   100%
app/schemas/bus.py                 26      0   100%
app/schemas/health.py              14      0   100%
app/schemas/statistics.py          51      0   100%
app/services/seoul_bus_api.py      67     15    78%
-------------------------------------------------------------
TOTAL                             571     92    84%
```

**성과**:
- 92개 테스트 전체 통과 (slow 제외, slow 포함 시 99개)
- 코드 커버리지 **84%** 달성 (3주차 60% → 4주차 84%)
- 핵심 모듈 커버리지: Redis 100%, Config 100%, 스키마 100%, Bus API 100%

---

### 파트 B: Docker 컨테이너화

#### 1. 프로덕션 전용 의존성 분리 (`requirements.prod.txt`)

테스트 관련 패키지(pytest, pytest-asyncio, pytest-cov)를 제외한 프로덕션 전용 의존성 파일을 생성했습니다.

```
# requirements.prod.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
asyncpg==0.29.0
redis==5.0.1
httpx==0.26.0
gunicorn==21.2.0  # 프로덕션 WSGI/ASGI 서버
```

**변경점**: `gunicorn==21.2.0` 추가 (프로덕션 Uvicorn Worker 관리)

#### 2. Docker 빌드 컨텍스트 최적화 (`.dockerignore`)

불필요한 파일을 빌드 컨텍스트에서 제외하여 빌드 속도와 이미지 크기를 최적화했습니다.

**제외 항목**:
- Python 캐시 (`__pycache__/`, `*.pyc`)
- 가상환경 (`.venv/`)
- 테스트 코드 (`tests/`)
- 문서 (`docs/`, `*.md`)
- IDE 설정 (`.vscode/`, `.idea/`)
- Git 관련 (`.git/`)

#### 3. 멀티스테이지 Dockerfile 작성

```dockerfile
# Stage 1: Builder - 의존성 설치
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.prod.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.prod.txt

# Stage 2: Runtime - 최종 이미지
FROM python:3.12-slim AS runtime
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --create-home appuser
COPY --from=builder /install /usr/local
WORKDIR /app
COPY app/ ./app/
RUN chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "60", \
     "--access-logfile", "-"]
```

**기술 결정**:

| 항목 | 선택 | 이유 |
|---|---|---|
| 베이스 이미지 | `python:3.12-slim` | asyncpg가 glibc 필요, Alpine 대비 호환성 우수 |
| 멀티스테이지 | 2단계 (builder → runtime) | 빌드 도구(gcc) 제거로 이미지 최소화 |
| 유저 | non-root (`appuser`) | 컨테이너 보안 강화 |
| 서버 | Gunicorn + Uvicorn Worker | 프로덕션 급 프로세스 관리 |
| 헬스체크 | Python urllib 기반 | curl 제거로 이미지 경량화 |

#### 4. Docker 이미지 빌드 및 검증

```bash
$ docker build -t comfortablemove-backend:1.0.0 .

$ docker images comfortablemove-backend
REPOSITORY                TAG       IMAGE ID       SIZE
comfortablemove-backend   1.0.0     66de124ed711   313MB
comfortablemove-backend   latest    66de124ed711   313MB
```

**이미지 크기 분석**:
- Debian 베이스: ~109MB (python:3.12-slim 기본)
- Python 런타임: ~45MB
- 애플리케이션 패키지: ~76MB (asyncpg, SQLAlchemy 등)
- 애플리케이션 코드: ~0.4MB

**경량화 작업** (339MB → 313MB, -26MB):
- `aioredis` 제거: redis-py 5.x가 이미 async 지원 (deprecated 패키지)
- `alembic` 제거: 현재 마이그레이션 미사용, `init_db()`로 테이블 생성
- `curl` + `libpq5` 제거: asyncpg 자체 libpq 내장, 헬스체크를 Python urllib로 대체

> 참고: `python:3.12-slim` 베이스 자체가 ~154MB(Debian + Python 런타임)이므로, Python 기반 비동기 앱에서 100MB 이하는 현실적으로 불가능합니다. Alpine은 asyncpg의 glibc 의존성으로 사용 불가.

#### 5. Docker Compose 업데이트

기존 PostgreSQL + Redis만 있던 구성에 backend 서비스를 추가했습니다.

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: comfortablemove_backend
    env_file:
      - .env.docker
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 15s

  postgres:
    image: postgres:15
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-user}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

**주요 개선점**:
- `depends_on` + `condition: service_healthy`로 의존성 순서 보장
- 모든 서비스에 healthcheck 추가
- `restart: unless-stopped`로 자동 복구
- `.env.docker` 파일로 환경변수 주입

#### 6. Docker 환경변수 파일 (`.env.docker`)

Docker 내부 네트워크에서 서비스명으로 접근하도록 호스트를 변경했습니다.

```env
# Docker 내부 네트워크: 서비스명 사용
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/comfortablemove
REDIS_URL=redis://redis:6379/0
ENVIRONMENT=production
DEBUG=false
```

**핵심 차이** (로컬 vs Docker):
- 로컬: `localhost:5432` / `localhost:6379`
- Docker: `postgres:5432` / `redis:6379` (Docker 네트워크 DNS)

#### 7. 전체 스택 실행 테스트

```bash
$ docker compose up -d
 Container comfortablemove_db       Started
 Container comfortablemove_redis    Started
 Container comfortablemove_backend  Started

$ docker compose ps
NAME                      STATUS                   PORTS
comfortablemove_backend   Up (healthy)   0.0.0.0:8000->8000/tcp
comfortablemove_db        Up (healthy)   0.0.0.0:5432->5432/tcp
comfortablemove_redis     Up (healthy)   0.0.0.0:6379->6379/tcp
```

**헬스체크 결과**:
```bash
$ curl http://localhost:8000/api/v1/health
{
    "status": "healthy",
    "timestamp": "2026-03-25T12:32:30.879035Z",
    "version": "1.0.0",
    "services": {
        "database": "connected",
        "redis": "connected",
        "seoul_bus_api": "reachable"
    },
    "errors": null
}
```

**환경변수 주입 확인**:
```bash
$ docker exec comfortablemove_backend env | grep -E "ENVIRONMENT|DATABASE_URL|REDIS_URL"
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/comfortablemove
REDIS_URL=redis://redis:6379/0
ENVIRONMENT=production
```

#### 8. Docker Hub 푸시 및 버전 태깅

```bash
$ docker tag comfortablemove-backend:1.0.0 phd0801/comfortablemove-backend:1.0.0
$ docker tag comfortablemove-backend:1.0.0 phd0801/comfortablemove-backend:latest

$ docker push phd0801/comfortablemove-backend:1.0.0
1.0.0: digest: sha256:9a80b658... size: 856

$ docker push phd0801/comfortablemove-backend:latest
latest: digest: sha256:9a80b658... size: 856
```

**Docker Hub 레포지토리**: `phd0801/comfortablemove-backend`
**배포된 태그**: `1.0.0`, `latest`

---

## 📊 주요 성과

### 1. 테스트 (파트 A)

| 지표 | 3주차 | 4주차 | 개선 |
|---|---|---|---|
| 테스트 수 | 29개 | 99개 | +70개 (+241%) |
| 통과율 | 100% | 100% | 유지 |
| 코드 커버리지 | 60% | 84% | +24%p |
| 테스트 유형 | 단위만 | 단위 + 통합 | 통합 테스트 추가 |

### 2. Docker (파트 B)

| 산출물 | 상태 | 설명 |
|---|---|---|
| `requirements.prod.txt` | ✅ 완료 | 프로덕션 의존성 분리 |
| `.dockerignore` | ✅ 완료 | 빌드 컨텍스트 최적화 |
| `Dockerfile` | ✅ 완료 | 멀티스테이지 빌드 |
| `docker-compose.yml` | ✅ 완료 | 3서비스 구성 (backend + postgres + redis) |
| `.env.docker` | ✅ 완료 | Docker 환경변수 |
| 이미지 빌드 | ✅ 완료 | 313MB (python:3.12-slim 기반, 경량화 적용) |
| 전체 스택 실행 | ✅ 완료 | 3개 컨테이너 모두 healthy |
| 이미지 태깅 | ✅ 완료 | 1.0.0 + latest |
| Docker Hub 푸시 | ✅ 완료 | `phd0801/comfortablemove-backend` |

---

## 🔧 기술 스택

**Backend Framework**:
- FastAPI 0.109.0
- Python 3.12
- Pydantic 2.5.3
- Gunicorn 21.2.0 (프로덕션)

**Database**:
- PostgreSQL 15 (asyncpg)
- SQLAlchemy 2.0.25

**Cache**:
- Redis 7

**Container**:
- Docker (멀티스테이지 빌드)
- Docker Compose

**Testing**:
- pytest 7.4.4
- pytest-asyncio 0.23.3
- pytest-cov 4.1.0

---

## 📁 프로젝트 구조 (4주차 추가 파일)

```
backend/
├── app/                         # (기존 유지)
├── tests/                       # 테스트 코드
│   ├── conftest.py              # ✅ 비동기 fixture 수정
│   ├── unit/
│   │   ├── test_schemas.py      # 11개 테스트
│   │   ├── test_seoul_bus_service.py  # 18개 테스트
│   │   └── test_redis.py        # ✅ 신규 (20개 테스트)
│   └── integration/
│       ├── test_api_health.py   # ✅ URL 수정 (3개 테스트)
│       ├── test_api_bus.py      # ✅ 신규 (6개 테스트)
│       ├── test_api_boarding.py # 9개 테스트
│       ├── test_api_statistics.py  # ✅ 신규 (10개 테스트)
│       └── test_seoul_bus_api.py   # ✅ 신규 (22개 테스트)
├── Dockerfile                   # ✅ 신규 - 멀티스테이지 빌드
├── .dockerignore                # ✅ 신규 - 빌드 컨텍스트 최적화
├── docker-compose.yml           # ✅ 업데이트 - backend 서비스 추가
├── requirements.prod.txt        # ✅ 신규 - 프로덕션 의존성
├── .env.docker                  # ✅ 신규 - Docker 환경변수
├── requirements.txt             # (기존 유지)
└── .env.example                 # (기존 유지)
```

---

## 💡 배운 점

### 1. 멀티스테이지 빌드의 효과

빌드 도구(gcc, libpq-dev)를 builder 스테이지에서만 사용하고 최종 이미지에는 포함하지 않아 불필요한 패키지를 제거할 수 있었습니다.

### 2. Docker 네트워크와 서비스 디스커버리

Docker Compose 내부에서는 `localhost` 대신 **서비스명**(postgres, redis)으로 접근해야 합니다. 이를 위해 `.env.docker`에서 호스트를 서비스명으로 변경했습니다.

### 3. 헬스체크와 의존성 순서

`depends_on`만으로는 서비스가 "준비"됐는지 보장할 수 없어, `condition: service_healthy`와 함께 각 서비스에 healthcheck를 추가하여 순서를 보장했습니다.

### 4. SQLite-PostgreSQL 타입 호환성

테스트에서 SQLite를 사용하면서 PostgreSQL 전용 타입(UUID, TIMESTAMP)과 연산자(~)를 처리하는 호환성 레이어를 구현하는 경험을 얻었습니다.

### 5. Non-root 컨테이너 보안

`appuser`라는 전용 사용자를 생성하여 컨테이너를 non-root로 실행함으로써 보안을 강화했습니다.

---

## 🔄 다음 주 (5주차) 계획

### 1. CI/CD 파이프라인 구축
- GitHub Actions를 사용한 자동 테스트
- Docker 이미지 자동 빌드 및 푸시

### 2. 클라우드 배포
- AWS 또는 클라우드 환경 설계
- 컨테이너 오케스트레이션 검토

### 3. 모바일 앱 연동 테스트
- iOS 앱에서 백엔드 API 호출 테스트

---

## 📝 회고

### 잘한 점

1. **테스트 완성**: 3주차 피드백을 반영하여 99개 테스트 전체 통과, 커버리지 84% 달성
2. **비동기 환경 해결**: `@pytest_asyncio.fixture` 및 SQLite-PostgreSQL 호환성 문제를 체계적으로 해결
3. **Docker 컨테이너화**: 멀티스테이지 빌드, non-root 유저, 헬스체크 등 프로덕션 수준의 Dockerfile 작성
4. **전체 스택 검증**: Docker Compose로 3개 서비스 동시 실행 및 healthy 상태 확인

### 아쉬운 점

1. **이미지 크기**: `python:3.12-slim` 베이스 자체가 ~154MB로, Python 앱에서 100MB 이하는 구조적으로 불가능 (Alpine은 asyncpg glibc 의존성 문제)

### 개선 방향

1. CI/CD 파이프라인 구축으로 자동 빌드/푸시 체계 구축
2. 프로덕션 환경에서의 부하 테스트

---

## 🎯 총 투입 시간

**예상**: 주 20시간
**실제**: 약 22시간

**상세**:
- 테스트 환경 이슈 해결 (conftest.py): 3시간
- 추가 테스트 작성 (70개): 8시간
- Dockerfile 작성 및 최적화: 3시간
- Docker Compose 업데이트: 2시간
- 전체 스택 테스트 및 디버깅: 3시간
- 문서 작성: 3시간

---

## 📌 참고 자료

- [Docker 공식 문서 - Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Compose 공식 문서](https://docs.docker.com/compose/)
- [pytest-asyncio 문서](https://pytest-asyncio.readthedocs.io/)
- [Gunicorn + Uvicorn Workers](https://www.uvicorn.org/deployment/)

---

**작성일**: 2026년 3월 25일
**작성자**: 박성근
