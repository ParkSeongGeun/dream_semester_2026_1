# API Specification

ComfortableMove Backend RESTful API 명세서

---

## 📋 기본 정보

### Base URL

- **개발 환경**: `http://localhost:8000`
- **프로덕션**: `https://api.comfortablemove.com`

### API 버전

- **현재 버전**: v1
- **엔드포인트 접두사**: `/api/v1`

### 공통 응답 형식

**성공 응답:**
```json
{
  "data": { ... },
  "timestamp": "2026-03-08T10:30:00Z"
}
```

**에러 응답:**
```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2026-03-08T10:30:00Z"
}
```

---

## 🏥 1. Health Check

### `GET /health`

서비스 상태 확인 (로드 밸런서 헬스 체크용)

#### Request

**Headers:** 없음

**Query Parameters:** 없음

#### Response

**200 OK** - 서비스 정상

```json
{
  "status": "healthy",
  "timestamp": "2026-03-08T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "seoul_bus_api": "reachable"
  }
}
```

**503 Service Unavailable** - 서비스 장애

```json
{
  "status": "unhealthy",
  "timestamp": "2026-03-08T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "disconnected",
    "seoul_bus_api": "reachable"
  },
  "errors": ["Redis connection failed"]
}
```

#### 구현 요구사항

- 응답 시간: < 2초
- 실제 의존성 체크 (DB, Redis, Seoul API)
- AWS ALB Health Check 경로로 사용

---

## 🚌 2. 버스 도착 정보 조회

### `GET /api/v1/bus/arrivals`

특정 정류장의 실시간 버스 도착 정보 조회

#### Request

**Headers:** 없음 (현재는 인증 미구현)

**Query Parameters:**

| 파라미터 | 필수 | 타입 | 설명 | 예시 |
|---------|------|------|------|------|
| `ars_id` | ✅ | String | 정류장 고유번호 | `"01234"` |

**예시:**
```
GET /api/v1/bus/arrivals?ars_id=01234
```

#### Response

**200 OK** - 조회 성공

```json
{
  "ars_id": "01234",
  "station_name": "신설동역",
  "arrivals": [
    {
      "route_name": "721",
      "route_type": "간선",
      "arrival_message": "2분후[2번째 전]",
      "direction": "신설동",
      "congestion": "empty",
      "is_full": false,
      "is_last_bus": false,
      "bus_type": "gangseon"
    },
    {
      "route_name": "2012",
      "route_type": "지선",
      "arrival_message": "5분후[5번째 전]",
      "direction": "종암동",
      "congestion": "normal",
      "is_full": false,
      "is_last_bus": false,
      "bus_type": "jiseon"
    }
  ],
  "cached": true,
  "cached_at": "2026-03-08T10:29:30Z",
  "expires_at": "2026-03-08T10:30:30Z"
}
```

**Response Fields:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `ars_id` | String | 정류장 고유번호 |
| `station_name` | String | 정류장 이름 |
| `arrivals` | Array | 버스 도착 정보 배열 |
| `arrivals[].route_name` | String | 버스 노선명 (예: "721") |
| `arrivals[].route_type` | String | 노선 유형 (간선, 지선 등) |
| `arrivals[].arrival_message` | String | 도착 메시지 |
| `arrivals[].direction` | String | 방향 (종점) |
| `arrivals[].congestion` | String | 혼잡도 (empty, normal, crowded, unknown) |
| `arrivals[].is_full` | Boolean | 만차 여부 |
| `arrivals[].is_last_bus` | Boolean | 막차 여부 |
| `arrivals[].bus_type` | String | 버스 유형 (gangseon, jiseon 등) |
| `cached` | Boolean | 캐시 데이터 여부 |
| `cached_at` | String (ISO 8601) | 캐시 저장 시간 |
| `expires_at` | String (ISO 8601) | 캐시 만료 시간 |

**404 Not Found** - 정류장 정보 없음

```json
{
  "detail": "No bus information found for this station",
  "error_code": "NO_BUS_INFO",
  "ars_id": "99999"
}
```

**503 Service Unavailable** - Seoul API 오류

```json
{
  "detail": "Seoul Bus API is currently unavailable",
  "error_code": "EXTERNAL_API_ERROR",
  "retry_after": 60
}
```

#### 캐싱 정책

- **Cache TTL**: 60초
- **Cache Key**: `arrivals:{ars_id}`
- **캐시 히트 시**: Redis에서 즉시 응답 (< 50ms)
- **캐시 미스 시**: Seoul API 호출 → Redis 저장 → 응답 (< 500ms)

#### 구현 요구사항

- iOS `BusArrivalService.getStationArrivalInfo()` 로직과 동일
- 버스 유형 분류: `BusRouteType.from()` 로직 사용
- 혼잡도 파싱: `BusCongestion` 로직 사용
- Seoul API 타임아웃: 5초
- 재시도: 최대 3회 (Exponential backoff)

---

## 📝 3. 탑승 기록 저장

### `POST /api/v1/boarding/record`

사용자가 배려석 알림을 보낸 기록 저장

#### Request

**Headers:**

| 헤더 | 필수 | 값 |
|------|------|-----|
| `Content-Type` | ✅ | `application/json` |

**Body (JSON):**

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "route_name": "721",
  "route_type": "간선",
  "bus_device_id": "BF_DREAM_721",
  "station_id": "123000001",
  "station_name": "신설동역",
  "ars_id": "01234",
  "latitude": 37.575000,
  "longitude": 127.025000,
  "sound_enabled": true,
  "notification_status": "success"
}
```

**Body Fields:**

| 필드 | 필수 | 타입 | 제약조건 | 설명 |
|------|------|------|---------|------|
| `device_id` | ❌ | UUID | UUID v4 | 기기 고유 ID (선택) |
| `route_name` | ✅ | String | 1-20자 | 버스 노선명 |
| `route_type` | ❌ | String | 1-10자 | 노선 유형 |
| `bus_device_id` | ❌ | String | 1-50자 | BLE 기기 ID |
| `station_id` | ❌ | String | 1-20자 | 정류장 ID |
| `station_name` | ❌ | String | 1-100자 | 정류장 이름 |
| `ars_id` | ❌ | String | 1-20자 | 정류장 고유번호 |
| `latitude` | ❌ | Number | -90 ~ 90 | 위도 |
| `longitude` | ❌ | Number | -180 ~ 180 | 경도 |
| `sound_enabled` | ✅ | Boolean | - | 알림음 사용 여부 |
| `notification_status` | ✅ | String | success, device_not_found, failure | 전송 결과 |

#### Response

**201 Created** - 저장 성공

```json
{
  "record_id": "660e8400-e29b-41d4-a716-446655440001",
  "message": "Boarding record saved successfully",
  "boarded_at": "2026-03-08T10:30:00Z"
}
```

**400 Bad Request** - 유효성 검증 실패

```json
{
  "detail": "Invalid notification_status value",
  "error_code": "VALIDATION_ERROR",
  "field": "notification_status",
  "allowed_values": ["success", "device_not_found", "failure"]
}
```

#### 구현 요구사항

- 응답 시간: < 200ms (Fire-and-forget)
- `device_id` 없이도 저장 가능 (익명 사용자)
- DB 저장 실패 시에도 200 응답 (로깅만 수행)
- Async 저장 권장

---

## 📊 4. 사용자 통계 조회

### `GET /api/v1/statistics/user/{device_id}`

특정 기기의 사용 통계 조회

#### Request

**Path Parameters:**

| 파라미터 | 필수 | 타입 | 설명 |
|---------|------|------|------|
| `device_id` | ✅ | UUID | 기기 고유 ID |

**Query Parameters:**

| 파라미터 | 필수 | 타입 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `period` | ❌ | String | `30d` | 기간 (7d, 30d, 90d, all) |

**예시:**
```
GET /api/v1/statistics/user/550e8400-e29b-41d4-a716-446655440000?period=30d
```

#### Response

**200 OK** - 조회 성공

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "period": "30d",
  "period_start": "2026-02-06T00:00:00Z",
  "period_end": "2026-03-08T23:59:59Z",
  "statistics": {
    "total_notifications": 42,
    "successful_notifications": 38,
    "failed_notifications": 4,
    "success_rate": 90.48,
    "most_used_routes": [
      {
        "route_name": "721",
        "count": 15,
        "route_type": "간선"
      },
      {
        "route_name": "2012",
        "count": 10,
        "route_type": "지선"
      }
    ],
    "most_used_stations": [
      {
        "station_name": "신설동역",
        "ars_id": "01234",
        "count": 15
      }
    ],
    "activity_by_day_of_week": {
      "monday": 8,
      "tuesday": 7,
      "wednesday": 6,
      "thursday": 7,
      "friday": 8,
      "saturday": 3,
      "sunday": 3
    },
    "last_used": "2026-03-08T09:15:00Z"
  }
}
```

**404 Not Found** - 기기 없음

```json
{
  "detail": "Device not found",
  "error_code": "DEVICE_NOT_FOUND",
  "device_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### 캐싱 정책

- **Cache TTL**: 300초 (5분)
- **Cache Key**: `stats:user:{device_id}:{period}`

#### 구현 요구사항

- 복잡한 집계 쿼리 → 인덱스 최적화 필수
- `most_used_routes`: Top 5
- `most_used_stations`: Top 3
- `activity_by_day_of_week`: 요일별 집계

---

## 🌍 5. 전역 통계 조회

### `GET /api/v1/statistics/global`

전체 서비스 통계 조회 (관리자용)

#### Request

**Query Parameters:**

| 파라미터 | 필수 | 타입 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `period` | ❌ | String | `7d` | 기간 (24h, 7d, 30d, all) |

**예시:**
```
GET /api/v1/statistics/global?period=7d
```

#### Response

**200 OK** - 조회 성공

```json
{
  "period": "7d",
  "period_start": "2026-03-01T00:00:00Z",
  "period_end": "2026-03-08T23:59:59Z",
  "statistics": {
    "total_users": 1247,
    "active_users_7d": 523,
    "total_notifications": 8932,
    "successful_notifications": 8104,
    "failed_notifications": 828,
    "success_rate": 90.73,
    "top_routes": [
      {
        "route_name": "721",
        "count": 523,
        "route_type": "간선"
      },
      {
        "route_name": "2012",
        "count": 412,
        "route_type": "지선"
      }
    ],
    "top_stations": [
      {
        "station_name": "신설동역",
        "ars_id": "01234",
        "count": 234
      },
      {
        "station_name": "강남역",
        "ars_id": "23288",
        "count": 189
      }
    ]
  }
}
```

#### 캐싱 정책

- **Cache TTL**: 600초 (10분)
- **Cache Key**: `stats:global:{period}`

#### 구현 요구사항

- 대용량 집계 쿼리 → DB 인덱스 필수
- `top_routes`: Top 10
- `top_stations`: Top 10

---

## ⚠️ 에러 코드

### 공통 에러 코드

| 코드 | HTTP 상태 | 설명 |
|------|-----------|------|
| `VALIDATION_ERROR` | 400 | 요청 데이터 유효성 검증 실패 |
| `NOT_FOUND` | 404 | 리소스를 찾을 수 없음 |
| `INTERNAL_SERVER_ERROR` | 500 | 서버 내부 오류 |

### 비즈니스 에러 코드

| 코드 | HTTP 상태 | 설명 |
|------|-----------|------|
| `NO_BUS_INFO` | 404 | 버스 정보 없음 (서울 외 지역) |
| `EXTERNAL_API_ERROR` | 503 | Seoul Bus API 장애 |
| `DEVICE_NOT_FOUND` | 404 | 기기를 찾을 수 없음 |

---

## 🔒 인증 (향후 구현)

현재는 인증 미구현이지만, Week 4에서 추가 예정:

### JWT Bearer Token

**Request Header:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (인증 실패):**
```json
{
  "detail": "Invalid or expired token",
  "error_code": "UNAUTHORIZED"
}
```

---

## 📈 Rate Limiting (향후 구현)

### 제한 정책

- **일반 사용자**: 분당 60 요청
- **인증된 사용자**: 분당 300 요청

**Response (제한 초과):**
```json
{
  "detail": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 45
}
```

---

## 🧪 테스트 시나리오

### Scenario 1: 버스 도착 정보 조회

```bash
# 요청
curl -X GET "http://localhost:8000/api/v1/bus/arrivals?ars_id=01234"

# 예상 응답: 200 OK
{
  "ars_id": "01234",
  "arrivals": [ ... ],
  "cached": false
}
```

### Scenario 2: 탑승 기록 저장

```bash
# 요청
curl -X POST "http://localhost:8000/api/v1/boarding/record" \
  -H "Content-Type: application/json" \
  -d '{
    "route_name": "721",
    "notification_status": "success"
  }'

# 예상 응답: 201 Created
{
  "record_id": "...",
  "message": "Boarding record saved successfully"
}
```

### Scenario 3: 사용자 통계 조회

```bash
# 요청
curl -X GET "http://localhost:8000/api/v1/statistics/user/550e8400-e29b-41d4-a716-446655440000"

# 예상 응답: 200 OK
{
  "statistics": {
    "total_notifications": 42,
    ...
  }
}
```

---

## 📚 OpenAPI 문서

FastAPI는 자동으로 OpenAPI 문서를 생성합니다:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## 🔄 버전 관리

### API 버전 정책

- **현재**: v1 (`/api/v1/...`)
- **향후**: v2 추가 시에도 v1 유지 (Breaking change 방지)

### Deprecation 정책

API 변경 시:
1. 새 버전 출시 (v2)
2. 구 버전 6개월 유지 (v1)
3. 6개월 후 구 버전 종료 공지
4. 3개월 후 구 버전 완전 종료

---

## 📝 Changelog

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0.0 | 2026-03-08 | 초기 API 설계 |

---

## 📖 참고 문서

- [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) - 데이터베이스 스키마
- [SEOUL_BUS_API_ANALYSIS.md](./SEOUL_BUS_API_ANALYSIS.md) - Seoul API 분석
- [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) - 개발 가이드
