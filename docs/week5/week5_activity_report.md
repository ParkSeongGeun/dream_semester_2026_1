# 5주차 활동 보고서

**프로젝트**: ComfortableMove (맘편한 이동) 백엔드 개발
**기간**: 2026년 3월 25일 ~ 2026년 3월 31일
**주요 목표**: Docker Compose 및 멀티 컨테이너 환경 구축

---

## 📋 주차 목표

Docker Compose를 활용하여 맘편한 이동 로컬 개발 환경을 구성합니다. API 서버, PostgreSQL, Redis를 연동한 멀티 컨테이너 환경을 구축하고, 개발/테스트 환경을 분리합니다.

---

## ✅ 완료한 작업

### 1. Docker Compose 기본 구성 개선 (`docker-compose.yml`)

4주차에 작성한 기본 docker-compose.yml을 개선하여 networks, volumes 섹션을 명시적으로 구성했습니다.

```yaml
# 주요 개선 사항
services:
  backend:
    networks:
      - comfortablemove_network
  postgres:
    networks:
      - comfortablemove_network
  redis:
    command: redis-server --appendonly yes --maxmemory 128mb --maxmemory-policy allkeys-lru
    networks:
      - comfortablemove_network

networks:
  comfortablemove_network:
    driver: bridge
    name: comfortablemove_network

volumes:
  postgres_data:
    name: comfortablemove_postgres_data
  redis_data:
    name: comfortablemove_redis_data
```

**개선점**:
- `networks` 섹션 추가: bridge 드라이버로 서비스 간 격리된 네트워크 구성
- `volumes` 명시적 네이밍: `comfortablemove_postgres_data`, `comfortablemove_redis_data`
- Redis 메모리 정책 설정: `maxmemory 128mb`, `allkeys-lru` 정책
- Redis AOF 영속성 활성화: `--appendonly yes`

### 2. 개발환경 오버라이드 (`docker-compose.dev.yml`)

개발환경 전용 오버라이드 파일을 작성하여 프로덕션과 개발 설정을 분리했습니다.

```yaml
services:
  backend:
    env_file:
      - .env.dev
    volumes:
      - ./app:/app/app:cached          # 소스코드 바인드 마운트
    command: >
      python -m uvicorn app.main:app
      --host 0.0.0.0 --port 8000
      --reload --reload-dir /app/app    # 핫리로드
      --log-level debug
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - DB_ECHO=true                    # SQL 쿼리 로깅
```

**개발환경 특징**:

| 항목 | 프로덕션 | 개발환경 |
|---|---|---|
| 서버 | Gunicorn + Uvicorn Worker | Uvicorn `--reload` |
| 소스코드 | 이미지 내 COPY | 바인드 마운트 (핫리로드) |
| 디버그 | `false` | `true` |
| SQL 로깅 | 비활성 | 활성 (`DB_ECHO=true`) |
| Redis 영속성 | AOF 활성 | AOF 비활성 |

**사용법**:
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 3. 테스트환경 오버라이드 (`docker-compose.test.yml`)

테스트 전용 Compose 파일과 Dockerfile을 작성했습니다.

```yaml
services:
  backend:
    build:
      dockerfile: Dockerfile.test       # pytest 포함 이미지
    command: >
      python -m pytest tests/ -v
      --cov=app --cov-report=term-missing
      -m "not slow"
    environment:
      - ENVIRONMENT=testing

  postgres:
    # 테스트 전용 DB (격리)
    environment:
      POSTGRES_DB: comfortablemove_test

  redis:
    # 영속성 비활성, 최소 메모리
    command: redis-server --appendonly no --save "" --maxmemory 32mb
```

**Dockerfile.test 특징**:
- `requirements.txt` 기반 (pytest, pytest-cov 포함)
- 테스트 코드(`tests/`) 포함
- 멀티스테이지 빌드로 이미지 최적화

**사용법**:
```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit
```

### 4. 환경변수 파일 체계 구성

환경별로 `.env` 파일을 분리하여 관리 체계를 구축했습니다.

| 파일 | 용도 | DB 호스트 | Redis 호스트 | 비고 |
|---|---|---|---|---|
| `.env` | 로컬 직접 실행 | `localhost` | `localhost` | Docker 미사용 |
| `.env.docker` | Docker 프로덕션 | `postgres` | `redis` | 서비스명 DNS |
| `.env.dev` | Docker 개발환경 | `postgres` | `redis` | 디버그 활성 |
| `.env.test` | Docker 테스트환경 | `postgres` | `redis` | 짧은 TTL |
| `.env.example` | 템플릿 | - | - | Git 추적됨 |

**핵심 차이점 (로컬 vs Docker)**:
```
# 로컬 (.env)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/comfortablemove

# Docker (.env.docker / .env.dev)
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/comfortablemove
```

Docker Compose 내부에서는 서비스명(`postgres`, `redis`)이 DNS로 해석되어 컨테이너 간 통신이 가능합니다.

`.gitignore` 업데이트:
```
.env
.env.local
.env.docker
.env.dev
.env.test
```

### 5. Redis 캐싱 로직 개선

기존 Redis 캐싱 모듈(`app/core/redis.py`)을 개선했습니다.

**5-1. 구조적 로깅 도입**

`print()` 기반 에러 출력을 Python `logging` 모듈로 교체했습니다.

```python
import logging
logger = logging.getLogger(__name__)

# 변경 전
print(f"Redis set error: {e}")

# 변경 후
logger.warning(f"Redis set error: {e}")
logger.debug(f"Cache HIT: {key}")
logger.debug(f"Cache MISS: {key}")
logger.debug(f"Cache SET: {key} (TTL={ttl}s)")
```

**5-2. 캐시 통계 조회 함수 추가**

```python
async def get_cache_stats() -> dict[str, Any]:
    """Redis 캐시 통계를 조회합니다."""
    client = await get_redis()
    info = await client.info("memory")
    db_size = await client.dbsize()

    arrival_keys = await client.keys("arrivals:*")
    stats_keys = await client.keys("stats:*")

    return {
        "total_keys": db_size,
        "arrival_cache_keys": len(arrival_keys),
        "statistics_cache_keys": len(stats_keys),
        "used_memory_human": info.get("used_memory_human"),
        "maxmemory_human": info.get("maxmemory_human"),
    }
```

**5-3. 캐시 상태 확인 API 엔드포인트 추가**

```python
@router.get("/health/cache")
async def cache_health():
    stats = await get_cache_stats()
    return JSONResponse(content=stats)
```

`GET /api/v1/health/cache` 엔드포인트로 캐시 키 분류별 개수, 메모리 사용량을 실시간 확인할 수 있습니다.

### 6. PostgreSQL 데이터 영속성 테스트 스크립트

컨테이너 재시작 후에도 데이터가 유지되는지 자동 검증하는 스크립트를 작성했습니다.

```bash
# scripts/test_persistence.sh
# 테스트 순서:
# 1. PostgreSQL 컨테이너 상태 확인
# 2. 테스트 테이블 생성 및 데이터 삽입
# 3. 재시작 전 레코드 수 확인
# 4. docker compose restart postgres
# 5. 재시작 후 레코드 수 확인 (동일해야 통과)
# 6. 테스트 데이터 정리 (DROP TABLE)
```

**영속성 보장 원리**:
- `docker-compose.yml`에서 `postgres_data` named volume을 `/var/lib/postgresql/data`에 마운트
- `docker compose down`으로 컨테이너를 삭제해도 volume은 유지
- `docker compose down -v`를 사용해야만 volume이 삭제됨

### 7. 전체 스택 실행 및 검증

#### 7-1. Docker Compose 전체 스택 기동

```bash
$ docker compose up -d
 Network comfortablemove_network  Created
 Volume comfortablemove_redis_data  Created
 Volume comfortablemove_postgres_data  Created
 Container comfortablemove_redis  Created
 Container comfortablemove_db  Created
 Container comfortablemove_backend  Created

$ docker compose ps
NAME                      IMAGE             STATUS                    PORTS
comfortablemove_backend   backend-backend   Up 30 seconds (healthy)   0.0.0.0:8000->8000/tcp
comfortablemove_db        postgres:15       Up 41 seconds (healthy)   0.0.0.0:5432->5432/tcp
comfortablemove_redis     redis:7           Up 41 seconds (healthy)   0.0.0.0:6379->6379/tcp
```

3개 컨테이너 모두 `healthy` 상태로 정상 구동 확인.

#### 7-2. 헬스체크 API 확인

```bash
$ curl http://localhost:8000/api/v1/health
{
    "status": "healthy",
    "timestamp": "2026-03-31T05:41:42.379966Z",
    "version": "1.0.0",
    "services": {
        "database": "connected",
        "redis": "connected",
        "seoul_bus_api": "reachable"
    },
    "errors": null
}
```

#### 7-3. 캐시 상태 API 확인

```bash
$ curl http://localhost:8000/api/v1/health/cache
{
    "total_keys": 0,
    "arrival_cache_keys": 0,
    "statistics_cache_keys": 0,
    "used_memory_human": "1.02M",
    "used_memory_bytes": 1071872,
    "maxmemory_human": "128.00M"
}
```

#### 7-4. PostgreSQL 데이터 영속성 테스트

```bash
$ bash scripts/test_persistence.sh
========================================
 PostgreSQL 데이터 영속성 테스트
========================================
[Step 1] 컨테이너 상태 확인... PostgreSQL 준비 완료
[Step 2] 테스트 데이터 삽입... 데이터 삽입 완료
[Step 3] 재시작 전 데이터 확인... 현재 레코드 수: 1
[Step 4] PostgreSQL 컨테이너 재시작... PostgreSQL 재시작 완료
[Step 5] 재시작 후 데이터 확인... 재시작 후 레코드 수: 1
========================================
 영속성 테스트 통과!
 재시작 전: 1개 → 재시작 후: 1개
========================================
[Step 6] 테스트 데이터 정리... 정리 완료
```

컨테이너 재시작 후에도 PostgreSQL 데이터가 정상 유지되는 것을 확인했습니다.

### 8. README 로컬 환경 구축 가이드

README.md에 3가지 방식의 환경 구축 가이드를 작성했습니다.

| 방법 | 대상 | 특징 |
|---|---|---|
| **방법 1**: Docker Compose 원클릭 | 빠른 실행 | `docker compose up -d` 하나로 전체 스택 |
| **방법 2**: 개발 환경 | 개발자 | 핫리로드, 디버그 모드 |
| **방법 3**: 로컬 직접 실행 | IDE 디버깅 | DB/Redis만 Docker, 서버는 로컬 |

프로젝트 구조, 유용한 명령어, 환경별 Compose 구성 표도 추가했습니다.

---

## 📊 주요 성과

### Docker Compose 환경 구성

| 산출물 | 상태 | 설명 |
|---|---|---|
| `docker-compose.yml` | ✅ 개선 | networks/volumes 명시, Redis 메모리 정책 |
| `docker-compose.dev.yml` | ✅ 신규 | 핫리로드, 바인드 마운트, 디버그 모드 |
| `docker-compose.test.yml` | ✅ 신규 | pytest 자동 실행, 격리 환경 |
| `Dockerfile.test` | ✅ 신규 | 테스트 전용 이미지 |
| `.env.dev` | ✅ 신규 | 개발환경 변수 |
| `.env.test` | ✅ 신규 | 테스트환경 변수 |
| `.env.example` | ✅ 업데이트 | 환경별 구성 설명 추가 |
| `app/core/redis.py` | ✅ 개선 | 로깅, 캐시 통계 함수 |
| `app/api/v1/health.py` | ✅ 개선 | `/health/cache` 엔드포인트 |
| `scripts/test_persistence.sh` | ✅ 신규 | DB 영속성 자동 검증 |
| `README.md` | ✅ 업데이트 | 로컬 환경 구축 가이드 |

### Docker Compose 기능 요약

| 기능 | 구현 상태 |
|---|---|
| `docker compose up` 원클릭 실행 | ✅ |
| 서비스 간 네트워크 연결 (bridge) | ✅ |
| `depends_on` + healthcheck 의존성 관리 | ✅ |
| PostgreSQL 데이터 영속성 (named volume) | ✅ |
| 환경변수 `.env` 파일 연동 | ✅ |
| 개발환경 오버라이드 (핫리로드) | ✅ |
| 테스트환경 오버라이드 (pytest 자동 실행) | ✅ |
| Redis 캐싱 모니터링 | ✅ |

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
- Redis 7 (maxmemory 128mb, allkeys-lru)

**Container**:
- Docker (멀티스테이지 빌드)
- Docker Compose v2 (멀티 환경 오버라이드)

**Testing**:
- pytest 7.4.4
- pytest-asyncio 0.23.3
- pytest-cov 4.1.0

---

## 📁 프로젝트 구조 (5주차 추가/변경 파일)

```
backend/
├── app/
│   ├── api/v1/
│   │   └── health.py              # ✅ 개선 - /health/cache 엔드포인트 추가
│   └── core/
│       └── redis.py               # ✅ 개선 - 로깅, get_cache_stats() 추가
├── scripts/
│   └── test_persistence.sh        # ✅ 신규 - DB 영속성 테스트
├── docker-compose.yml             # ✅ 개선 - networks/volumes 명시
├── docker-compose.dev.yml         # ✅ 신규 - 개발환경 오버라이드
├── docker-compose.test.yml        # ✅ 신규 - 테스트환경 오버라이드
├── Dockerfile.test                # ✅ 신규 - 테스트 전용 이미지
├── .env.dev                       # ✅ 신규 - 개발환경 변수
├── .env.test                      # ✅ 신규 - 테스트환경 변수
├── .env.example                   # ✅ 업데이트 - 환경별 설명 추가
├── .gitignore                     # ✅ 업데이트 - .env.dev, .env.test 추가
└── README.md                      # ✅ 업데이트 - 로컬 환경 가이드
```

---

## 💡 배운 점

### 1. Docker Compose 오버라이드 패턴

`-f` 플래그로 여러 Compose 파일을 병합할 수 있습니다. 기본 파일에 공통 설정을 두고, 환경별 오버라이드 파일에서 차이점만 정의하면 DRY 원칙을 지키면서 환경 분리가 가능합니다.

```bash
# 기본 + 개발 병합
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

단, `volumes: []`로 base 볼륨을 비우려는 시도는 동작하지 않습니다. 오버라이드에서는 기존 볼륨을 제거할 수 없고 추가만 가능하므로, 테스트 환경에서는 볼륨 데이터를 무시하는 방식(Redis `--save ""`)으로 우회했습니다.

### 2. Docker 네트워크와 서비스 디스커버리

Docker Compose의 기본 네트워크에서도 서비스명으로 통신이 가능하지만, 명시적으로 `networks` 섹션을 정의하면:
- 네트워크 이름을 고정할 수 있어 디버깅이 용이
- 다른 Compose 프로젝트와의 네트워크 충돌 방지
- 외부 서비스와의 연동 시 네트워크 참조 가능

### 3. Redis 메모리 정책의 중요성

`maxmemory-policy allkeys-lru`를 설정하지 않으면 메모리 한도 도달 시 Redis가 새 키 저장을 거부합니다. LRU 정책을 적용하면 가장 오래된 캐시부터 자동 제거되어 캐시 서버로서 안정적으로 동작합니다.

### 4. 환경변수 파일 분리의 필요성

하나의 `.env` 파일로 모든 환경을 관리하면 실수로 프로덕션 설정이 개발에 적용되거나 그 반대가 발생할 수 있습니다. 환경별 `.env` 파일을 분리하고 `.gitignore`에 등록하여:
- 민감 정보(API 키, DB 비밀번호)가 Git에 커밋되지 않음
- 환경 간 설정 혼동 방지
- `.env.example`만 추적하여 팀원에게 필요한 변수 목록 공유

### 5. PostgreSQL Named Volume과 영속성

Docker의 named volume(`postgres_data:/var/lib/postgresql/data`)은 컨테이너 생명주기와 독립적입니다:
- `docker compose restart`: 데이터 유지 ✅
- `docker compose down`: 데이터 유지 ✅
- `docker compose down -v`: 데이터 삭제 ❌ (볼륨 함께 제거)

이를 검증하기 위해 자동화된 영속성 테스트 스크립트를 작성했습니다.

---

## 🔄 다음 주 (6주차) 계획

### 1. CI/CD 파이프라인 구축
- GitHub Actions를 사용한 자동 테스트
- Docker 이미지 자동 빌드 및 Docker Hub 푸시

### 2. 클라우드 배포 설계
- AWS 또는 클라우드 환경 아키텍처 설계
- 컨테이너 오케스트레이션 검토

### 3. 모니터링 구축
- 로깅 체계 강화
- 헬스체크 대시보드 구성

---

## 📝 회고

### 잘한 점

1. **환경 분리 체계화**: 프로덕션/개발/테스트 환경을 Compose 오버라이드 패턴으로 명확히 분리
2. **원클릭 실행 달성**: `docker compose up -d` 하나로 전체 스택 구동, 3개 컨테이너 모두 healthy 확인
3. **영속성 검증 자동화**: 스크립트로 자동 검증 → 컨테이너 재시작 후 데이터 유지 확인 (1개 → 1개)
4. **캐싱 모니터링**: `/health/cache` 엔드포인트로 Redis 메모리 사용량, 키 분류별 개수 실시간 확인
5. **README 가이드**: 3가지 방식의 환경 구축 가이드로 다양한 사용자 지원

### 아쉬운 점

1. **개발환경 오버라이드 실행 미검증**: `docker-compose.dev.yml` 오버라이드의 핫리로드가 실제 코드 변경 시 정상 반영되는지 장시간 테스트하지 못함
2. **테스트환경 실행 미검증**: `docker-compose.test.yml`로 컨테이너 내부에서 pytest 자동 실행까지는 검증하지 못함 (Dockerfile.test 빌드 필요)

### 개선 방향

1. CI/CD 파이프라인에서 docker-compose.test.yml 기반 자동 테스트 통합
2. 프로덕션 환경에서의 부하 테스트
3. Docker 이미지 태깅 자동화 (Git 태그 연동)

---

## 🎯 총 투입 시간

**예상**: 주 35시간
**실제**: 약 30시간

**상세**:
- Docker Compose 학습 및 YAML 문법 이해: 4시간
- docker-compose.yml 개선 (networks, volumes): 3시간
- docker-compose.dev.yml 개발환경 구성: 4시간
- docker-compose.test.yml 테스트환경 구성: 4시간
- 환경변수 파일 체계 구성: 3시간
- Redis 캐싱 로직 개선: 4시간
- PostgreSQL 영속성 테스트 스크립트: 2시간
- README 로컬 환경 가이드 작성: 3시간
- 보고서 작성: 3시간

---

## 📌 참고 자료

- [Docker Compose 공식 문서](https://docs.docker.com/compose/)
- [Docker Compose - Multiple Compose files](https://docs.docker.com/compose/how-tos/multiple-compose-files/)
- [Docker Networking](https://docs.docker.com/engine/network/)
- [Docker Volumes](https://docs.docker.com/engine/storage/volumes/)
- [Redis Configuration](https://redis.io/docs/latest/operate/oss_and_stack/management/config/)

---

**작성일**: 2026년 3월 31일
**작성자**: 박성근
