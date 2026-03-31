# ComfortableMove Backend

임산부 배려석 알림 서비스 백엔드 API

---

## 📋 프로젝트 개요

**ComfortableMove (맘편한 이동)**의 백엔드 서버입니다. iOS 앱에서 사용하는 서울시 버스 API를 프록시하고, 사용자 탑승 기록 및 통계를 제공합니다.

### 주요 기능

- 🚌 **버스 도착 정보 제공** (Redis 캐싱 적용)
- 📊 **탑승 기록 저장 및 통계 분석**
- 🔍 **서울시 버스 API 통합**
- ⚡ **고성능 캐싱 시스템**

---

## 🛠️ 기술 스택

### Core

- **FastAPI** 0.109.0 - 웹 프레임워크
- **Python** 3.11+ - 프로그래밍 언어
- **PostgreSQL** 15 - 데이터베이스
- **Redis** 7 - 캐싱

### Libraries

- **SQLAlchemy** 2.0 - ORM
- **Pydantic** 2.5 - 데이터 검증
- **httpx** - 비동기 HTTP 클라이언트
- **pytest** - 테스트 프레임워크

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose v2
- Git

### 방법 1: Docker Compose 원클릭 실행 (권장)

```bash
# 1. 환경 변수 설정
cp .env.example .env.docker
# .env.docker 파일을 열어 SEOUL_BUS_API_KEY 등 필요한 값을 입력

# 2. 전체 스택 실행 (Backend + PostgreSQL + Redis)
docker compose up -d

# 3. 상태 확인
docker compose ps

# 4. API 문서 확인
# 브라우저에서 http://localhost:8000/docs 접속
```

### 방법 2: 개발 환경 (핫리로드 지원)

```bash
# 1. 환경 변수 설정
cp .env.example .env.dev
# .env.dev 파일을 열어 필요한 값을 입력

# 2. 개발 모드 실행 (소스코드 변경 시 자동 재시작)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 3. 로그 실시간 확인
docker compose logs -f backend
```

### 방법 3: 로컬 직접 실행

```bash
# 1. 가상환경 설정
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 환경 변수 설정
cp .env.example .env

# 3. PostgreSQL + Redis만 Docker로 실행
docker compose up -d postgres redis

# 4. FastAPI 서버 실행
uvicorn app.main:app --reload
```

### 환경별 Docker Compose 구성

| 환경 | 명령어 | 환경변수 | 특징 |
|---|---|---|---|
| **프로덕션** | `docker compose up -d` | `.env.docker` | Gunicorn, 최적화 |
| **개발** | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d` | `.env.dev` | 핫리로드, 디버그 |
| **테스트** | `docker compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit` | `.env.test` | pytest 자동 실행 |

### 유용한 명령어

```bash
# 전체 컨테이너 중지
docker compose down

# 볼륨 포함 완전 삭제 (데이터 초기화)
docker compose down -v

# PostgreSQL 데이터 영속성 테스트
bash scripts/test_persistence.sh

# 캐시 상태 확인
curl http://localhost:8000/api/v1/health/cache
```

---

## 📡 API 엔드포인트

### Health Check

```
GET /health
```

### 버스 도착 정보 조회

```
GET /api/v1/bus/arrivals?ars_id={ars_id}
```

### 탑승 기록 저장

```
POST /api/v1/boarding/record
```

### 사용자 통계 조회

```
GET /api/v1/statistics/user/{device_id}?period={period}
```

### 전역 통계 조회

```
GET /api/v1/statistics/global?period={period}
```

**자세한 내용**: [API_SPECIFICATION.md](./docs/API_SPECIFICATION.md)

---

## 🗄️ 데이터베이스 스키마

### 테이블

1. **users_devices** - iOS 기기 정보
2. **boarding_records** - 탑승 기록

**자세한 내용**: [DATABASE_SCHEMA.md](./docs/DATABASE_SCHEMA.md)

---

## 🧪 테스트

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함
pytest --cov=app --cov-report=html

# 통합 테스트만 실행
pytest tests/integration/

# 특정 파일 테스트
pytest tests/integration/test_seoul_bus_api.py -v
```

---

## 📚 문서

- [API Specification](./docs/API_SPECIFICATION.md) - API 명세서
- [Database Schema](./docs/DATABASE_SCHEMA.md) - 데이터베이스 스키마
- [ERD](./docs/ERD.md) - 테이블 관계도
- [Seoul Bus API Analysis](./docs/SEOUL_BUS_API_ANALYSIS.md) - Seoul API 분석
- [Development Guide](./docs/DEVELOPMENT_GUIDE.md) - 개발 가이드

---

## 🏗️ 프로젝트 구조

```
backend/
├── app/                        # 애플리케이션 코드
│   ├── api/v1/                 # API 엔드포인트
│   ├── models/                 # SQLAlchemy 모델
│   ├── schemas/                # Pydantic 스키마
│   ├── services/               # 비즈니스 로직
│   ├── core/                   # 핵심 유틸리티 (config, redis)
│   └── db/                     # 데이터베이스 세션
├── tests/                      # 테스트 코드 (99개)
├── scripts/                    # 유틸리티 스크립트
├── docs/                       # 문서
├── Dockerfile                  # 프로덕션 빌드
├── Dockerfile.test             # 테스트 빌드
├── docker-compose.yml          # 기본 Compose (3서비스)
├── docker-compose.dev.yml      # 개발환경 오버라이드
├── docker-compose.test.yml     # 테스트환경 오버라이드
├── requirements.txt            # 전체 의존성
└── requirements.prod.txt       # 프로덕션 의존성
```

---

## 🔧 개발 워크플로우

### Week 2 (현재) - 설계 & 문서화 📝

- [x] 프로젝트 구조 설계
- [x] 데이터베이스 스키마 설계
- [x] API 명세서 작성
- [x] Seoul Bus API 분석
- [x] 테스트 계획 수립

### Week 3 (다음 주) - 구현 💻

- [ ] FastAPI 애플리케이션 구현
- [ ] 데이터베이스 연결 및 ORM
- [ ] Seoul Bus API 통합
- [ ] Redis 캐싱 구현
- [ ] 단위 & 통합 테스트

### Week 4 - 배포 🚀

- [ ] Docker 컨테이너화
- [ ] AWS 인프라 구축
- [ ] CI/CD 파이프라인
- [ ] 모니터링 설정

---

## 🌟 주요 특징

### 1. Redis 캐싱

- 버스 도착 정보: 60초 TTL
- 정류장 정보: 300초 TTL
- 예상 캐시 히트율: 80%+

### 2. Seoul Bus API 통합

- iOS 앱과 동일한 로직
- 버스 유형 자동 분류 (7가지)
- 혼잡도 파싱 (4단계)

### 3. 통계 분석

- 사용자별 탑승 이력
- 인기 노선/정류장 분석
- 요일별 활동 패턴

---

## 🔒 보안

- SQL Injection 방지 (SQLAlchemy ORM)
- XSS 방지 (Pydantic 검증)
- 환경 변수로 민감 정보 관리
- CORS 설정

---

## 📈 성능 최적화

- 비동기 I/O (FastAPI + httpx)
- Redis 캐싱
- 데이터베이스 인덱싱
- Connection Pooling

---

## 🐛 트러블슈팅

**DB 연결 실패:**
```bash
docker-compose restart postgres
```

**Redis 연결 실패:**
```bash
docker-compose restart redis
```

**Seoul API Timeout:**
- 재시도 로직 자동 실행 (최대 3회)

---

## 🤝 Contributing

1. 브랜치 생성: `git checkout -b feature/new-feature`
2. 변경사항 커밋: `git commit -m "[Feat] Add feature"`
3. 푸시: `git push origin feature/new-feature`
4. Pull Request 생성

---

## 📞 Contact

- **개발자**: 박성근
- **프로젝트**: ComfortableMove (맘편한 이동)

---

## 📄 License

This project is part of Dream Semester 2026-1.

---

**버전**: 1.1.0
**최종 수정**: 2026-03-31
