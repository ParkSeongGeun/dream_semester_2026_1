# 부하 테스트 가이드

## 개요

출퇴근 시간에 특정 버스에 대한 요청이 많을 때 시스템이 정상적으로 작동하는지 검증합니다.

**테스트 도구**: Locust
**테스트 시나리오**: 버스 도착 정보 조회 집중 테스트
**동시 사용자**: 100명
**목표**: 캐시 효과 검증 및 응답 시간 측정

---

## 사전 준비

### 1. 서버 실행

```bash
# Docker Compose 시작 (PostgreSQL + Redis)
docker-compose up -d

# FastAPI 서버 시작
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Locust 설치

```bash
pip install locust
```

---

## 부하 테스트 실행

### 방법 1: Web UI 사용 (권장)

```bash
# Locust 서버 시작
locust -f locustfile.py --host=http://localhost:8000

# 브라우저에서 http://localhost:8089 접속
# - Number of users: 100
# - Spawn rate: 10 (초당 10명씩 증가)
# - Host: http://localhost:8000
```

**Web UI에서 확인 가능한 지표**:
- 총 요청 수 (Total Requests)
- 실패 요청 수 (Failures)
- 평균 응답 시간 (Average Response Time)
- 중간값 응답 시간 (Median Response Time)
- 95th percentile 응답 시간
- 초당 요청 수 (RPS - Requests Per Second)

### 방법 2: 헤드리스 모드 (자동화)

```bash
# 100명 사용자, 60초 동안 테스트
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 60s \
  --headless \
  --html=load_test_report.html
```

**결과 파일**: `load_test_report.html` (브라우저에서 열어서 확인)

---

## 테스트 시나리오

### 1. BusUserBehavior (일반 사용자)

**행동 패턴**:
- 자주 이용하는 정류장 1~2개 선택
- 자주 이용하는 정류장 조회: 50% (높은 빈도)
- 랜덤 정류장 조회: 10% (낮은 빈도)
- 탑승 기록 저장: 20%
- 헬스체크: 10%

**요청 간격**: 2~5초

### 2. PeakHourUser (출퇴근 시간 사용자)

**행동 패턴**:
- 특정 정류장에 집중
- 버스 도착 정보 반복 조회

**요청 간격**: 1~3초 (더 짧음)

---

## 캐시 효과 검증

부하 테스트 실행 시 자동으로 캐시 통계를 수집합니다.

### 측정 지표

1. **캐시 히트율** = (캐시 히트 / 총 요청) × 100
2. **평균 응답 시간** (캐시 히트 vs 미스 비교)
3. **초당 처리 가능 요청 수** (RPS)

### 예상 결과

**캐시 미적용 시**:
- 평균 응답 시간: 300~500ms
- 초당 요청 수: ~20 RPS

**캐시 적용 시 (TTL: 60초)**:
- 캐시 히트율: 80%+
- 캐시 히트 시 응답 시간: < 50ms
- 캐시 미스 시 응답 시간: ~300ms
- 평균 응답 시간: < 100ms
- 초당 요청 수: ~100 RPS

---

## 성능 기준 (SLA)

### ✅ 통과 기준

- **평균 응답 시간**: < 200ms
- **95th percentile**: < 500ms
- **실패율**: < 1%
- **캐시 히트율**: > 70%
- **동시 사용자 100명 처리 가능**

### ❌ 실패 기준

- 평균 응답 시간 > 1000ms
- 실패율 > 5%
- 서버 다운 또는 타임아웃 발생

---

## 테스트 결과 분석

### 1. 캐시 효과

테스트 종료 시 자동으로 출력되는 캐시 통계 확인:

```
===============================================
📊 부하 테스트 결과 요약
===============================================
🔵 총 캐시 히트: 8250
🔴 총 캐시 미스: 1750
✅ 캐시 히트율: 82.50%
📈 예상 성능 개선: 82.5% 요청이 빠른 응답
===============================================
```

### 2. 응답 시간 분포

**Locust Web UI에서 확인**:
- Median: 중간값 (50% 사용자가 경험하는 응답 시간)
- 95th percentile: 95% 사용자가 경험하는 최대 응답 시간
- 99th percentile: 최악의 경우 응답 시간

### 3. 처리량 (Throughput)

**RPS (Requests Per Second)**:
- 서버가 초당 처리할 수 있는 요청 수
- 높을수록 좋음

### 4. 에러율

**Failures**:
- HTTP 4xx, 5xx 에러
- 타임아웃
- 낮을수록 좋음 (목표: < 1%)

---

## 다양한 시나리오 테스트

### 시나리오 1: 평상시 (낮은 부하)

```bash
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 20 \
  --spawn-rate 2 \
  --run-time 60s \
  --headless
```

### 시나리오 2: 출퇴근 시간 (높은 부하)

```bash
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 20 \
  --run-time 120s \
  --headless
```

### 시나리오 3: 스트레스 테스트 (과부하)

```bash
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 500 \
  --spawn-rate 50 \
  --run-time 60s \
  --headless
```

---

## 문제 발생 시 대응

### 1. 평균 응답 시간이 너무 느림 (> 1초)

**원인**:
- Redis 미작동
- 서울시 버스 API 느림
- 데이터베이스 병목

**해결**:
```bash
# Redis 상태 확인
docker-compose ps redis
redis-cli ping

# 데이터베이스 연결 확인
docker-compose ps postgres
```

### 2. 에러율이 높음 (> 5%)

**원인**:
- 서버 다운
- 타임아웃
- 데이터베이스 연결 실패

**해결**:
```bash
# 서버 로그 확인
tail -f server.log

# Docker 로그 확인
docker-compose logs
```

### 3. 캐시 히트율이 낮음 (< 50%)

**원인**:
- Redis TTL이 너무 짧음
- 사용자가 너무 다양한 정류장 조회

**해결**:
- TTL 조정 (app/core/config.py)
- 테스트 시나리오 조정

---

## 부하 테스트 결과 예시

### 좋은 결과 (✅ PASS)

```
Summary:
  Total requests: 12,500
  Failures: 15 (0.12%)
  Average response time: 85ms
  Median: 45ms
  95th percentile: 320ms
  RPS: 208

Cache Statistics:
  Cache hits: 10,250 (82%)
  Cache misses: 2,250 (18%)
```

### 나쁜 결과 (❌ FAIL)

```
Summary:
  Total requests: 5,200
  Failures: 420 (8.08%)
  Average response time: 1,850ms
  Median: 1,200ms
  95th percentile: 3,500ms
  RPS: 43

Cache Statistics:
  Cache hits: 2,100 (40%)
  Cache misses: 3,100 (60%)
```

---

## 성능 최적화 팁

### 1. Redis 캐싱 최적화

- TTL 조정: 60초 → 120초 (더 긴 캐시)
- Cache Key 전략 개선
- Redis 메모리 증가

### 2. 데이터베이스 최적화

- 인덱스 추가
- 쿼리 최적화
- Connection Pool 크기 조정

### 3. 서버 스케일링

- 수직 스케일링: CPU/메모리 증가
- 수평 스케일링: 서버 인스턴스 추가
- 로드 밸런서 도입

---

## 참고 자료

- [Locust 공식 문서](https://docs.locust.io/)
- [성능 테스트 베스트 프랙티스](https://docs.locust.io/en/stable/writing-a-locustfile.html)
- [Redis 성능 최적화](https://redis.io/docs/management/optimization/)

---

**작성일**: 2026-03-18
**버전**: 1.0.0
