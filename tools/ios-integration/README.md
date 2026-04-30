# iOS 연동 도구

iOS 프론트엔드(ComfortableMove)와 백엔드 API의 응답 호환성 검증 도구.

## 분석 결과: iOS 앱의 호출 구조

iOS 앱은 현재 **서울시 공공데이터 포털**(`ws.bus.go.kr`)을 직접 호출하며,
모델은 `Core/Model/*.swift` 에 정의된 형태로 디코딩합니다.

| iOS 호출 | 호출 메서드 | 응답 모델 |
|----------|-------------|-----------|
| `getStationByPos` | `BusStopService.getNearbyStations(location, radius)` | `StationByPosResponse` (msgHeader, msgBody.itemList[StationItem]) |
| `getStationByUid` | `BusArrivalService.getStationArrivalInfo(arsId)` | `BusArrivalResponse` (msgHeader, msgBody.itemList[BusArrivalItem]) |

## 백엔드 프록시 — iOS 모델과 1:1 일치

iOS 클라이언트가 동일한 디코더로 양쪽(서울 API / 백엔드)을 모두 디코딩할 수 있도록,
백엔드는 동일한 키와 응답 구조를 유지합니다.

| 백엔드 엔드포인트 | iOS 호출과 매핑 |
|---|---|
| `GET /api/v1/bus/arrivals?ars_id=XXXXX` | `getStationByUid` 대체 |
| `GET /api/v1/bus/stations?tmX=lon&tmY=lat&radius=N` | `getStationByPos` 대체 |

응답 구조는 iOS의 `BusArrivalResponse`, `StationByPosResponse` 와 1:1 동일합니다.

## 사용법

### 로컬 백엔드 헬스 체크

```bash
cd backend
docker compose -f docker-compose.dev.yml up -d
cd ../tools/ios-integration
./healthcheck.sh
```

### Dev/Prod 백엔드 대상

```bash
API_BASE_URL=https://api.comfortablemove.com ./healthcheck.sh
ARS_ID=23288 TM_X=127.0276 TM_Y=37.4979 ./healthcheck.sh   # 강남역
```

## iOS 앱을 백엔드 프록시로 전환할 때

기존 코드:
```swift
// BusArrivalService.swift
let baseURL = "http://ws.bus.go.kr/api/rest/stationinfo/getStationByUid"
components?.queryItems = [
  URLQueryItem(name: "ServiceKey", value: API_KEY),
  URLQueryItem(name: "arsId", value: arsId),
  URLQueryItem(name: "resultType", value: "json"),
]
```

전환 후:
```swift
let baseURL = "\(BackendConfig.baseURL)/api/v1/bus/arrivals"
components?.queryItems = [
  URLQueryItem(name: "ars_id", value: arsId),  // ServiceKey/resultType 불필요
]
```

`URLSession.shared.data(from:)` 와 `JSONDecoder` 호출은 **변경 불필요**.
응답 모델(`BusArrivalResponse`, `StationByPosResponse`)도 그대로 사용 가능합니다.

> 정류소 조회의 파라미터는 iOS 호출과 동일하게 `tmX=경도, tmY=위도, radius=m` 입니다.

## CI 연동 (선택)

```yaml
# .github/workflows/integration.yml
- name: iOS-backend healthcheck
  env:
    API_BASE_URL: ${{ secrets.API_BASE_URL }}
  run: tools/ios-integration/healthcheck.sh
```
