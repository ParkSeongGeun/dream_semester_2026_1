# Seoul Bus API Analysis

서울시 버스 정보 API 분석 및 통합 가이드

---

## 📋 개요

### API 기본 정보

- **제공 기관**: 서울특별시
- **API 이름**: 서울시 버스도착정보 조회 서비스
- **Base URL**: `http://ws.bus.go.kr/api/rest`
- **인증 방식**: Service Key (Query Parameter)
- **응답 형식**: XML, JSON (우리는 JSON 사용)
- **프로토콜**: HTTP (HTTPS 아님)

### API 키

```
29b4ab63713865b3f2cdf31264b27efa9dfac8019d464980fdccef522c46e39e
```

⚠️ **주의**: iOS 앱 Config.xcconfig에서 동일한 API 키 사용 중

---

## 🔌 엔드포인트 분석

### 1. 위치 기반 정류장 조회

**iOS 사용처**: `BusStopService.getStations()`

#### 요청

```
GET /stationinfo/getStationByPos
```

**Query Parameters:**

| 파라미터 | 필수 | 타입 | 설명 | 예시 |
|---------|------|------|------|------|
| `ServiceKey` | ✅ | String | API 인증 키 | `29b4ab6371...` |
| `tmX` | ✅ | Double | 경도 (Longitude) | `127.025000` |
| `tmY` | ✅ | Double | 위도 (Latitude) | `37.575000` |
| `radius` | ❌ | Integer | 검색 반경 (미터) | `100` (기본값) |
| `resultType` | ✅ | String | 응답 형식 | `json` |

**전체 URL 예시:**
```
http://ws.bus.go.kr/api/rest/stationinfo/getStationByPos?ServiceKey=29b4ab63713865b3f2cdf31264b27efa9dfac8019d464980fdccef522c46e39e&tmX=127.025000&tmY=37.575000&radius=100&resultType=json
```

#### 응답 구조

**성공 응답 (headerCd: "0"):**

```json
{
  "msgHeader": {
    "headerCd": "0",
    "headerMsg": "정상적으로처리되었습니다.",
    "itemCount": 3
  },
  "msgBody": {
    "itemList": [
      {
        "stationId": "123000001",
        "stationNm": "신설동역",
        "arsId": "01234",
        "gpsX": "127.025000",
        "gpsY": "37.575000",
        "dist": "50",
        "stationTp": "0"
      },
      {
        "stationId": "123000002",
        "stationNm": "신설동역.동묘앞역",
        "arsId": "01235",
        "gpsX": "127.026000",
        "gpsY": "37.576000",
        "dist": "85",
        "stationTp": "0"
      }
    ]
  }
}
```

**데이터 없음 (headerCd: "4"):**

```json
{
  "msgHeader": {
    "headerCd": "4",
    "headerMsg": "해당하는 데이터가 없습니다.",
    "itemCount": 0
  },
  "msgBody": null
}
```

#### 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `stationId` | String | 정류소 고유 ID |
| `stationNm` | String | 정류소 이름 |
| `arsId` | String | 정류소 고유번호 (다음 API 호출에 사용) |
| `gpsX` | String | 경도 (WGS84) |
| `gpsY` | String | 위도 (WGS84) |
| `dist` | String | 사용자로부터 거리 (미터) |
| `stationTp` | String | 정류소 타입 (0: 일반) |

---

### 2. 정류소별 버스 도착 정보 조회

**iOS 사용처**: `BusArrivalService.getStationArrivalInfo()`

#### 요청

```
GET /stationinfo/getStationByUid
```

**Query Parameters:**

| 파라미터 | 필수 | 타입 | 설명 | 예시 |
|---------|------|------|------|------|
| `ServiceKey` | ✅ | String | API 인증 키 | `29b4ab6371...` |
| `arsId` | ✅ | String | 정류소 고유번호 | `01234` |
| `resultType` | ✅ | String | 응답 형식 | `json` |

**전체 URL 예시:**
```
http://ws.bus.go.kr/api/rest/stationinfo/getStationByUid?ServiceKey=29b4ab63713865b3f2cdf31264b27efa9dfac8019d464980fdccef522c46e39e&arsId=01234&resultType=json
```

#### 응답 구조

**성공 응답:**

```json
{
  "msgHeader": {
    "headerCd": "0",
    "headerMsg": "정상적으로처리되었습니다.",
    "itemCount": 5
  },
  "msgBody": {
    "itemList": [
      {
        "stId": "123000001",
        "stNm": "신설동역",
        "arsId": "01234",
        "busRouteId": "100100001",
        "rtNm": "721",
        "busRouteAbrv": "721",
        "sectNm": "신설동",
        "gpsX": "127.025000",
        "gpsY": "37.575000",
        "posX": "127.025000",
        "posY": "37.575000",
        "stationTp": "0",
        "firstTm": "04:00",
        "lastTm": "24:00",
        "term": "8",
        "routeType": "4",
        "nextBus": "0",
        "staOrd": "20",
        "vehId1": "123456789",
        "plainNo1": "서울70바1234",
        "sectOrd1": "18",
        "stationNm1": "광희동",
        "traTime1": "2",
        "traSpd1": "0",
        "isArrive1": "0",
        "repTm1": "0",
        "isLast1": "0",
        "busType1": "0",
        "avgCf1": "0",
        "expCf1": "0",
        "exps1": "0",
        "deTourAt1": "0",
        "arsId": "01234",
        "isFullFlag1": "0",
        "goal": "신설동",
        "dir": "신설동",
        "arrmsg1": "2분후[2번째 전]",
        "arrmsg2": "15분후[10번째 전]",
        "arrmsgSec1": "120",
        "arrmsgSec2": "900",
        "adirection": "신설동",
        "deTourAt": "0",
        "congestion1": "3",
        "congestion2": "4"
      },
      {
        "rtNm": "2012",
        "routeType": "5",
        "arrmsg1": "5분후[5번째 전]",
        "adirection": "종암동",
        "congestion1": "4",
        "isFullFlag1": "0",
        "isLast1": "0"
      }
    ]
  }
}
```

#### 중요 필드 설명

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `rtNm` | String | 노선명 (버스 번호) | `"721"`, `"강동01"`, `"N16"` |
| `routeType` | String | 노선 유형 코드 | `"3"`, `"4"`, `"5"` 등 |
| `arrmsg1` | String | 첫 번째 버스 도착 메시지 | `"2분후[2번째 전]"` |
| `arrmsg2` | String | 두 번째 버스 도착 메시지 | `"15분후[10번째 전]"` |
| `adirection` | String | 방향 (종점) | `"신설동"` |
| `congestion1` | String | 첫 번째 버스 혼잡도 | `"3"`, `"4"`, `"5"` |
| `congestion2` | String | 두 번째 버스 혼잡도 | `"3"`, `"4"`, `"5"` |
| `isFullFlag1` | String | 만차 여부 | `"0"` (여유), `"1"` (만차) |
| `isLast1` | String | 막차 여부 | `"0"` (일반), `"1"` (막차) |

---

## 🚌 버스 유형 분류 로직

### iOS 앱 로직 (`BusRouteType.from(busNumber:)`)

iOS 앱에서 사용하는 버스 유형 분류 로직을 **그대로** 백엔드에 구현해야 합니다.

#### 분류 규칙

```python
def classify_bus_type(bus_number: str) -> str:
    """
    버스 번호로 노선 유형 분류 (iOS BusRouteType 로직과 동일)

    Args:
        bus_number: 버스 노선명 (예: "721", "강동01", "N16")

    Returns:
        버스 유형: gangseon, jiseon, sunhwan, gwangyeok, maeul, simya, gongHang, unknown
    """
    # 1. 심야버스 (Night bus): N으로 시작
    if bus_number.startswith("N"):
        return "simya"

    # 2. 공항버스 (Airport bus): 4자리 숫자 + 6으로 시작
    if len(bus_number) == 4 and bus_number.startswith("6") and bus_number.isdigit():
        return "gongHang"

    # 3. 광역버스 (Wide-area bus): 4자리 숫자 + 9로 시작
    if len(bus_number) == 4 and bus_number.startswith("9") and bus_number.isdigit():
        return "gwangyeok"

    # 4. 간선버스 (Trunk bus): 3자리 숫자
    if len(bus_number) == 3 and bus_number.isdigit():
        return "gangseon"

    # 5. 지선버스 (Feeder bus): 4자리 숫자 (6, 9 제외)
    if len(bus_number) == 4 and bus_number.isdigit():
        return "jiseon"

    # 6. 순환버스 (Circular bus): 2자리 숫자
    if len(bus_number) == 2 and bus_number.isdigit():
        return "sunhwan"

    # 7. 마을버스 (Town bus): 한글 포함
    if any('\uac00' <= c <= '\ud7a3' for c in bus_number):
        return "maeul"

    return "unknown"
```

#### 테스트 케이스

| 버스 번호 | 예상 결과 | 설명 |
|----------|----------|------|
| `721` | `gangseon` | 3자리 = 간선 |
| `2012` | `jiseon` | 4자리 (6,9 제외) = 지선 |
| `9403` | `gwangyeok` | 9로 시작하는 4자리 = 광역 |
| `6705` | `gongHang` | 6으로 시작하는 4자리 = 공항 |
| `01` | `sunhwan` | 2자리 = 순환 |
| `N16` | `simya` | N으로 시작 = 심야 |
| `강동01` | `maeul` | 한글 포함 = 마을 |
| `M5107` | `unknown` | 규칙에 없음 |

---

## 📊 혼잡도 파싱 로직

### iOS 앱 로직 (`BusCongestion` enum)

```python
def parse_congestion(code: str | None) -> str:
    """
    혼잡도 코드를 문자열로 변환 (iOS BusCongestion 로직과 동일)

    Args:
        code: 혼잡도 코드 ("0", "3", "4", "5", "6", None)

    Returns:
        혼잡도: empty, normal, crowded, unknown
    """
    if code in ["0", "3"]:
        return "empty"      # 여유
    elif code == "4":
        return "normal"     # 보통
    elif code in ["5", "6"]:
        return "crowded"    # 혼잡
    else:
        return "unknown"    # 정보 없음
```

#### 코드 매핑표

| API 코드 | 백엔드 값 | 한글 표시 | iOS Enum |
|---------|----------|----------|----------|
| `"0"` | `empty` | 여유 | `.empty` |
| `"3"` | `empty` | 여유 | `.empty` |
| `"4"` | `normal` | 보통 | `.normal` |
| `"5"` | `crowded` | 혼잡 | `.crowded` |
| `"6"` | `crowded` | 혼잡 | `.crowded` |
| `null` | `unknown` | - | `.unknown` |

---

## ⚠️ 에러 처리 전략

### headerCd 코드별 처리

| headerCd | headerMsg | 의미 | 백엔드 처리 |
|----------|-----------|------|------------|
| `"0"` | 정상적으로처리되었습니다. | 성공 | 200 OK 응답 |
| `"4"` | 해당하는 데이터가 없습니다. | 데이터 없음 | 404 Not Found (서울 외 지역) |
| `"5"` | 필수 값이 누락되어 있습니다. | 파라미터 오류 | 500 (재시도 안 함) |
| 기타 | - | API 오류 | 503 Service Unavailable |

### 백엔드 에러 응답 예시

**Case 1: 서울 외 지역 (headerCd: "4")**

```json
{
  "detail": "No bus information found for this location",
  "error_code": "NO_BUS_INFO",
  "ars_id": "99999"
}
```

**Case 2: 서울시 API 오류 (timeout, network error)**

```json
{
  "detail": "Seoul Bus API is currently unavailable",
  "error_code": "EXTERNAL_API_ERROR",
  "retry_after": 60
}
```

---

## 🔄 재시도 전략

### Exponential Backoff

서울시 API 호출 실패 시 재시도 로직:

```python
import httpx
import asyncio

async def call_seoul_api_with_retry(url: str, params: dict, max_retries: int = 3):
    """
    Exponential backoff 재시도 로직
    """
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1초, 2초, 4초
                await asyncio.sleep(wait_time)
                continue
            raise

        except httpx.HTTPError as e:
            # HTTP 에러는 재시도하지 않음
            raise

    raise Exception("Max retries exceeded")
```

**재시도 간격:**
- 1차 실패: 1초 대기 후 재시도
- 2차 실패: 2초 대기 후 재시도
- 3차 실패: 4초 대기 후 재시도
- 3회 모두 실패: 에러 응답

---

## ⏱️ 성능 최적화

### 캐싱 전략

#### 버스 도착 정보 (높은 변동성)

```python
# Redis 캐시 키: arrivals:{ars_id}
# TTL: 60초 (1분)

cache_key = f"arrivals:{ars_id}"
cached_data = await redis.get(cache_key)

if cached_data:
    # 캐시 히트 → 즉시 응답 (< 50ms)
    return json.loads(cached_data)

# 캐시 미스 → Seoul API 호출
data = await call_seoul_api(ars_id)

# 캐시 저장
await redis.setex(cache_key, 60, json.dumps(data))
return data
```

**예상 캐시 히트율:** 80% 이상
- iOS 앱도 1분마다 새로고침
- 같은 정류장을 여러 사용자가 조회할 가능성 높음

#### 정류장 정보 (낮은 변동성)

```python
# Redis 캐시 키: stations:{lat}:{lon}:{radius}
# TTL: 300초 (5분)

cache_key = f"stations:{lat}:{lon}:{radius}"
```

**예상 캐시 히트율:** 60% 이상
- GPS 좌표는 약간씩 다르지만 반올림하면 비슷함

---

## 📡 HTTP 클라이언트 설정

### httpx 설정 예시

```python
import httpx

# AsyncClient 설정
async with httpx.AsyncClient(
    timeout=httpx.Timeout(5.0, connect=2.0),  # 전체 5초, 연결 2초
    limits=httpx.Limits(max_connections=100),
    http2=False,  # Seoul API는 HTTP/1.1만 지원
) as client:
    response = await client.get(url, params=params)
```

---

## 🧪 테스트 시나리오

### 테스트 1: 정류장 조회 (신설동역)

**요청:**
```python
latitude = 37.575124
longitude = 127.025069
radius = 100
```

**예상 결과:**
- `headerCd`: "0"
- `itemCount` > 0
- 첫 번째 정류장: "신설동역" 포함

---

### 테스트 2: 버스 도착 정보 (강남역)

**요청:**
```python
ars_id = "23288"  # 강남역
```

**예상 결과:**
- `headerCd`: "0"
- `itemList`에 여러 버스 포함
- 각 버스는 `rtNm`, `arrmsg1`, `congestion1` 필드 보유

---

### 테스트 3: 서울 외 지역 (부산)

**요청:**
```python
latitude = 35.1796
longitude = 129.0756
```

**예상 결과:**
- `headerCd`: "4"
- `msgBody`: null

---

### 테스트 4: 버스 유형 분류

**테스트 데이터:**
```python
test_cases = [
    ("721", "gangseon"),
    ("2012", "jiseon"),
    ("9403", "gwangyeok"),
    ("6705", "gongHang"),
    ("01", "sunhwan"),
    ("N16", "simya"),
    ("강동01", "maeul"),
]
```

---

## 📌 iOS 앱과의 호환성 체크리스트

백엔드 구현 시 iOS 앱과 **완전히 동일한** 로직을 사용해야 합니다:

- [ ] 버스 유형 분류 로직 일치 (`BusRouteType.from()`)
- [ ] 혼잡도 파싱 로직 일치 (`BusCongestion`)
- [ ] API 엔드포인트 동일 (`getStationByPos`, `getStationByUid`)
- [ ] 파라미터명 동일 (`tmX`, `tmY`, `arsId`, `resultType`)
- [ ] 에러 처리 동일 (`headerCd == "4"` → 서울 외 지역)
- [ ] 응답 형식 JSON
- [ ] 타임아웃 5초

---

## 🔗 참고 링크

- 서울 열린데이터 광장: https://data.seoul.go.kr/
- iOS 앱 코드:
  - `BusStopService.swift`
  - `BusArrivalService.swift`
  - `BusRouteType` enum
  - `BusCongestion` enum

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2026-03-08 | 1.0.0 | 초기 분석 완료 |
