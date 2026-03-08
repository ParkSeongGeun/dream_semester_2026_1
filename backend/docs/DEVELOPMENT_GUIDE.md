# Development Guide

ComfortableMove Backend 개발 가이드

---

## 🚀 Quick Start

### 1. 환경 설정

#### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

#### 프로젝트 클론

```bash
cd /Users/parkseonggeun/Desktop/드림학기제/dream_semester_2026_1
cd backend
```

---

### 2. Python 가상환경 설정

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화 (Mac/Linux)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

---

### 3. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (필요시)
vim .env
```

**.env 내용:**
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/comfortablemove

# Redis
REDIS_URL=redis://localhost:6379/0

# Seoul Bus API
SEOUL_BUS_API_KEY=YOUR_API_KEY_HERE

# App
APP_VERSION=1.0.0
DEBUG=true
```

---

### 4. Docker 컨테이너 실행

PostgreSQL과 Redis를 Docker로 실행:

```bash
# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down

# 완전 삭제 (데이터 포함)
docker-compose down -v
```

---

### 5. 데이터베이스 초기화

```bash
# DB 마이그레이션 (Week 3에서 구현)
alembic upgrade head

# 또는 수동 초기화
python -m app.db.init_db
```

---

### 6. 서버 실행

```bash
# 개발 서버 실행 (hot reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**브라우저에서 확인:**
- API 문서: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## 📁 프로젝트 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── config.py               # 환경 변수 설정
│   │
│   ├── api/                    # API 엔드포인트
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── health.py       # Health check
│   │       ├── bus.py          # 버스 정보 API
│   │       ├── boarding.py     # 탑승 기록 API
│   │       └── statistics.py   # 통계 API
│   │
│   ├── models/                 # SQLAlchemy ORM 모델
│   │   ├── __init__.py
│   │   ├── user.py             # UserDevice 모델
│   │   └── boarding_record.py  # BoardingRecord 모델
│   │
│   ├── schemas/                # Pydantic 스키마
│   │   ├── __init__.py
│   │   ├── bus.py              # 버스 관련 스키마
│   │   ├── boarding.py         # 탑승 기록 스키마
│   │   └── statistics.py       # 통계 스키마
│   │
│   ├── services/               # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── seoul_bus_api.py    # Seoul Bus API 클라이언트
│   │   ├── cache_service.py    # Redis 캐싱
│   │   └── statistics_service.py # 통계 계산
│   │
│   ├── core/                   # 핵심 유틸리티
│   │   ├── __init__.py
│   │   ├── database.py         # DB 연결 관리
│   │   ├── cache.py            # Redis 연결 관리
│   │   └── exceptions.py       # 커스텀 예외
│   │
│   └── db/                     # 데이터베이스 초기화
│       ├── __init__.py
│       └── init_db.py          # DB 초기 설정 스크립트
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest 설정 및 fixtures
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_seoul_bus_api.py
│   └── unit/
│       ├── __init__.py
│       └── test_endpoints.py
│
├── docs/                       # 문서
│   ├── API_SPECIFICATION.md
│   ├── DATABASE_SCHEMA.md
│   ├── ERD.md
│   ├── SEOUL_BUS_API_ANALYSIS.md
│   └── DEVELOPMENT_GUIDE.md
│
├── .env                        # 환경 변수 (git ignore)
├── .env.example                # 환경 변수 예시
├── .gitignore
├── requirements.txt            # Python 의존성
├── docker-compose.yml          # Docker 설정
└── README.md                   # 프로젝트 개요
```

---

## 🧪 테스트

### 전체 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 커버리지 포함 실행
pytest --cov=app --cov-report=html

# 특정 파일만 테스트
pytest tests/integration/test_seoul_bus_api.py

# 특정 테스트 함수만 실행
pytest tests/integration/test_seoul_bus_api.py::test_get_station_by_position

# verbose 모드
pytest -v

# 실패한 테스트만 재실행
pytest --lf
```

### 통합 테스트 (Seoul Bus API)

```bash
# Seoul Bus API 통합 테스트
pytest tests/integration/test_seoul_bus_api.py -v

# 느린 테스트 스킵
pytest -m "not slow"
```

### 테스트 작성 예시

```python
# tests/unit/test_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_bus_arrivals():
    response = client.get("/api/v1/bus/arrivals?ars_id=01234")
    assert response.status_code == 200
    data = response.json()
    assert "arrivals" in data
```

---

## 🔧 개발 워크플로우

### Week 3 구현 순서

#### Day 1: 프로젝트 기본 설정

```bash
# 1. app/main.py 작성
# 2. app/config.py 작성 (환경 변수 로드)
# 3. 서버 실행 테스트
uvicorn app.main:app --reload
```

**app/main.py 예시:**
```python
from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title="ComfortableMove API",
    version="1.0.0",
    description="임산부 배려석 알림 서비스 백엔드"
)

@app.get("/")
def root():
    return {"message": "ComfortableMove API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

---

#### Day 2: 데이터베이스 설정

```bash
# 1. app/core/database.py 작성 (DB 연결)
# 2. app/models/user.py 작성
# 3. app/models/boarding_record.py 작성
# 4. Alembic 초기화
alembic init alembic

# 5. 마이그레이션 생성
alembic revision --autogenerate -m "Initial schema"

# 6. 마이그레이션 실행
alembic upgrade head
```

**app/core/database.py 예시:**
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

#### Day 3: Seoul Bus API 서비스

```bash
# 1. app/services/seoul_bus_api.py 작성
# 2. 버스 유형 분류 함수 구현
# 3. 혼잡도 파싱 함수 구현
# 4. 통합 테스트 실행
pytest tests/integration/test_seoul_bus_api.py
```

**app/services/seoul_bus_api.py 구조:**
```python
import httpx
from typing import Optional, List

class SeoulBusAPIService:
    BASE_URL = "http://ws.bus.go.kr/api/rest"

    async def get_stations_by_position(
        self, latitude: float, longitude: float, radius: int = 100
    ) -> dict:
        """위치 기반 정류장 조회"""
        pass

    async def get_arrivals_by_station(self, ars_id: str) -> dict:
        """정류장별 버스 도착 정보 조회"""
        pass

def classify_bus_type(bus_number: str) -> str:
    """버스 유형 분류 (iOS 로직과 동일)"""
    pass

def parse_congestion(code: Optional[str]) -> str:
    """혼잡도 파싱 (iOS 로직과 동일)"""
    pass
```

---

#### Day 4-5: API 엔드포인트 구현

```bash
# 1. app/api/v1/health.py
# 2. app/api/v1/bus.py
# 3. app/api/v1/boarding.py
# 4. app/api/v1/statistics.py
# 5. app/schemas/ 작성
# 6. 단위 테스트 작성
pytest tests/unit/
```

**app/api/v1/bus.py 구조:**
```python
from fastapi import APIRouter, Depends, HTTPException
from app.services.seoul_bus_api import SeoulBusAPIService
from app.schemas.bus import BusArrivalResponse

router = APIRouter(prefix="/bus", tags=["bus"])

@router.get("/arrivals", response_model=BusArrivalResponse)
async def get_bus_arrivals(ars_id: str):
    """버스 도착 정보 조회"""
    pass
```

---

#### Day 6: Redis 캐싱 구현

```bash
# 1. app/core/cache.py 작성
# 2. app/services/cache_service.py 작성
# 3. 버스 도착 정보 캐싱 적용
# 4. 캐시 성능 테스트
```

**app/core/cache.py 예시:**
```python
import redis.asyncio as redis
from app.config import settings

redis_client = redis.from_url(settings.REDIS_URL)

async def get_cache(key: str) -> Optional[str]:
    return await redis_client.get(key)

async def set_cache(key: str, value: str, ttl: int):
    await redis_client.setex(key, ttl, value)
```

---

#### Day 7: 최종 통합 테스트

```bash
# 1. 전체 테스트 실행
pytest --cov=app

# 2. API 문서 확인
# http://localhost:8000/docs

# 3. 수동 테스트
curl http://localhost:8000/api/v1/bus/arrivals?ars_id=01234

# 4. 성능 테스트 (optional)
ab -n 1000 -c 10 http://localhost:8000/health
```

---

## 🐛 디버깅

### FastAPI 디버그 모드

```python
# app/main.py
import logging

logging.basicConfig(level=logging.DEBUG)

app = FastAPI(debug=True)
```

### 로그 확인

```bash
# uvicorn 로그
uvicorn app.main:app --reload --log-level debug

# Docker 로그
docker-compose logs -f postgres
docker-compose logs -f redis
```

### PostgreSQL 직접 접속

```bash
# psql 접속
docker exec -it comfortablemove_db psql -U user -d comfortablemove

# 테이블 확인
\dt

# 데이터 확인
SELECT * FROM users_devices;
SELECT * FROM boarding_records LIMIT 10;

# 종료
\q
```

### Redis 직접 접속

```bash
# redis-cli 접속
docker exec -it comfortablemove_redis redis-cli

# 모든 키 확인
KEYS *

# 특정 키 조회
GET arrivals:01234

# TTL 확인
TTL arrivals:01234

# 종료
exit
```

---

## 📦 배포 (Week 4)

### Docker 이미지 빌드

```bash
# Dockerfile 작성 후
docker build -t comfortablemove-backend:latest .

# 실행
docker run -p 8000:8000 comfortablemove-backend:latest
```

### AWS 배포 (예시)

```bash
# ECR에 푸시
aws ecr get-login-password | docker login --username AWS --password-stdin <ECR_URL>
docker tag comfortablemove-backend:latest <ECR_URL>/comfortablemove:latest
docker push <ECR_URL>/comfortablemove:latest

# ECS에 배포
aws ecs update-service --cluster comfortablemove --service api --force-new-deployment
```

---

## 🔒 보안 체크리스트

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는가?
- [ ] API 키가 코드에 하드코딩되지 않았는가?
- [ ] SQL Injection 방지 (SQLAlchemy ORM 사용)
- [ ] XSS 방지 (Pydantic 입력 검증)
- [ ] CORS 설정이 적절한가?
- [ ] Rate Limiting 구현 (향후)
- [ ] JWT 인증 구현 (향후)

---

## 🚨 트러블슈팅

### 문제 1: DB 연결 실패

**에러:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**해결:**
```bash
# Docker 컨테이너 확인
docker-compose ps

# PostgreSQL 재시작
docker-compose restart postgres
```

---

### 문제 2: Redis 연결 실패

**에러:**
```
redis.exceptions.ConnectionError
```

**해결:**
```bash
# Redis 재시작
docker-compose restart redis

# 연결 테스트
docker exec -it comfortablemove_redis redis-cli ping
```

---

### 문제 3: Seoul Bus API Timeout

**에러:**
```
httpx.TimeoutException
```

**해결:**
1. Seoul API가 일시적으로 느릴 수 있음 → 재시도
2. 네트워크 확인
3. API 키 확인

---

## 📚 유용한 명령어

### Git

```bash
# 새 브랜치 생성
git checkout -b feature/week3-implementation

# 커밋
git add .
git commit -m "[Feat] Add Seoul Bus API service"

# 푸시
git push origin feature/week3-implementation
```

### Python

```bash
# 의존성 업데이트
pip install --upgrade -r requirements.txt

# requirements.txt 갱신
pip freeze > requirements.txt

# 코드 포맷팅 (black)
pip install black
black app/

# 타입 체크 (mypy)
pip install mypy
mypy app/
```

### Docker

```bash
# 전체 재시작
docker-compose down && docker-compose up -d

# 로그 실시간 확인
docker-compose logs -f

# 컨테이너 상태 확인
docker-compose ps

# 볼륨 삭제 (데이터 초기화)
docker-compose down -v
```

---

## 🎓 학습 자료

### FastAPI

- 공식 문서: https://fastapi.tiangolo.com/
- 튜토리얼: https://fastapi.tiangolo.com/tutorial/

### SQLAlchemy

- 공식 문서: https://docs.sqlalchemy.org/
- ORM 튜토리얼: https://docs.sqlalchemy.org/en/20/orm/

### PostgreSQL

- 공식 문서: https://www.postgresql.org/docs/

### Redis

- 공식 문서: https://redis.io/docs/

---

## 📞 문의

문제가 발생하면:
1. 먼저 로그 확인 (`docker-compose logs`)
2. 문서 재확인 (API_SPECIFICATION.md 등)
3. GitHub Issues에 질문

---

**문서 버전**: 1.0.0
**최종 수정일**: 2026-03-08
