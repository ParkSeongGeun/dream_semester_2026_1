# 9주차 활동 보고서 — Terraform 심화 & iOS 연동

**기간**: 2026-04-24 ~ 2026-04-30  
**투입시간**: 30시간 (주간)  
**주제**: Terraform 모듈 재사용 구조화 / dev·prod 환경 분리 / iOS 앱 ↔ 백엔드 응답 호환

## 1. 주요 목표

| # | 목표 | 결과 |
|---|------|------|
| 1 | Terraform 모듈 재사용 구조화 | 8개 모듈 (network/security/storage/compute/rds/ingress/dns/monitoring) 정리 |
| 2 | dev/prod 환경 분리 | `environments/dev`, `environments/prod` 디렉토리로 진입점 분리 |
| 3 | locals/count/for_each 패턴 적용 | network 모듈에 `for_each` 도입, 환경별 `locals` 로 태그/이름 계산 |
| 4 | tfvars 파일로 환경별 설정 관리 | `dev.tfvars`, `prod.tfvars` + `terraform.tfvars.example` 분리 |
| 5 | 각 모듈 README 문서화 | 모든 모듈 + 루트 + environments README 작성 |
| 6 | terraform fmt/validate 검증 | dev/prod 모두 `Success! The configuration is valid.` |
| 7 | iOS 앱 연동 테스트 도구 | iOS 모델 기준으로 백엔드 응답 형식 정합 + 헬스체크 스크립트 |

## 2. Terraform 디렉토리 구조

```
infra/terraform/
├── modules/                    # 재사용 모듈
│   ├── network/                # VPC, Subnet, IGW, NAT, RouteTable
│   ├── security/               # ALB/EC2/RDS Security Group
│   ├── storage/                # S3 (버전관리, 암호화, CORS)
│   ├── compute/                # EC2 + IAM + Key Pair + EIP
│   ├── rds/                    # PostgreSQL 15
│   ├── ingress/                # ALB + HTTPS Listener
│   ├── dns/                    # Route53 + ACM
│   └── monitoring/             # CloudWatch + Budgets + SNS
├── environments/
│   ├── dev/                    # 개발: t3.micro, Single-AZ, NAT 비활성
│   └── prod/                   # 운영: t3.small, ALB+DNS+모니터링 포함
├── main.tf, variables.tf, ...  # legacy 단일환경 진입점 (호환 유지)
└── README.md
```

각 모듈은 `main.tf / variables.tf / outputs.tf / README.md` 구조로 통일.

## 3. 환경별 차이 (dev vs prod)

| 항목 | dev | prod |
|------|-----|------|
| EC2 | t3.micro | t3.small |
| RDS | db.t3.micro | db.t3.small |
| Multi-AZ | 비활성 | 옵션 (기본 false) |
| NAT Gateway | 비활성 | 옵션 (기본 false) |
| ALB / DNS / Monitoring | 미포함 | 포함 |
| VPC CIDR | 10.10.0.0/16 | 10.20.0.0/16 |
| Budget | – | $30/월 |

## 4. 적용한 Terraform 패턴

### 4.1 `locals` — 환경별 공통값 계산

```hcl
locals {
  environment = "dev"
  name_prefix = "${var.project_name}-${local.environment}"
  common_tags = {
    Project = var.project_name
    Environment = local.environment
    ManagedBy = "terraform"
    CostCenter = "development"
  }
}

provider "aws" {
  default_tags { tags = local.common_tags }
}
```

### 4.2 `for_each` — 인덱스 변경에 안전한 서브넷 생성

```hcl
locals {
  public_subnets = {
    for i, az in var.availability_zones : az => {
      cidr = var.public_subnet_cidrs[i]
      name = "${var.project_name}-public-${az}"
    }
  }
}

resource "aws_subnet" "public" {
  for_each          = local.public_subnets
  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value.cidr
  availability_zone = each.key
  ...
}
```

### 4.3 `count` — 조건부 리소스

```hcl
resource "aws_nat_gateway" "main" {
  count         = var.enable_nat_gateway ? 1 : 0
  ...
}
```

### 4.4 `tfvars` 분리

| 파일 | 용도 |
|------|------|
| `dev.tfvars`, `prod.tfvars` | 일반 환경값 (git 관리) |
| `terraform.tfvars` | 시크릿 (gitignore) |
| `terraform.tfvars.example` | 템플릿 |
| `TF_VAR_*` 환경변수 | CI/CD에서 시크릿 주입용 |

## 5. 검증 결과

```bash
$ cd environments/dev && terraform init -backend=false
Terraform has been successfully initialized!
$ terraform validate
Success! The configuration is valid.

$ cd ../prod && terraform init -backend=false
Terraform has been successfully initialized!
$ terraform validate
Success! The configuration is valid.

$ terraform fmt -recursive
(no changes)
```

## 6. iOS 앱 연동 작업

### 6.1 분석한 iOS 코드

`/Users/parkseonggeun/Desktop/개발프로젝트/bfdream/무제/ComfortableMove/ComfortableMove/`
의 다음 파일을 분석:

- `Core/Manager/BusArrivalService.swift` — `getStationByUid` 호출
- `Core/Manager/BusStopService.swift` — `getStationByPos` 호출
- `Core/Model/BusArrivalResponse.swift` — `BusArrivalItem` 모델
- `Core/Model/StationByPosResponse.swift` — `StationItem` 모델

**iOS 앱은 현재 백엔드를 호출하지 않고 서울시 공공데이터 API를 직접 호출**.
응답을 `JSONDecoder` 로 디코딩하여 `MsgHeader`, `MsgBody`, `BusArrivalItem`,
`StationItem` 등의 구조체로 변환하는 구조.

### 6.2 백엔드 수정 — iOS 모델을 기준으로 정합

**원칙**: iOS의 디코더가 동일하게 백엔드와 서울 API 양쪽을 처리할 수 있도록,
백엔드 응답의 키와 구조를 iOS 모델과 1:1 일치시킴.

| 변경 파일 | 요지 |
|-----------|------|
| `app/schemas/bus.py` | `BusArrivalResponse, MsgHeader, BusArrivalItem, StationByPosResponse, StationItem` 으로 재정의 (iOS 키 그대로 사용) |
| `app/services/seoul_bus_api.py` | `normalize_arrival_response`, `normalize_station_response` 추가. dict 단일항목 → list, `itemCount` 정수화. 한글/영문 변환 제거 |
| `app/api/v1/bus.py` | `GET /api/v1/bus/arrivals?ars_id=…`, `GET /api/v1/bus/stations?tmX=&tmY=&radius=` 두 엔드포인트 (iOS 호출 파라미터와 동일) |
| `app/schemas/__init__.py` | 신규 스키마 export |
| `tests/unit/test_seoul_bus_service.py` | 변환 테스트 → 정규화 테스트로 교체 |
| `tests/integration/test_seoul_bus_api.py` | 변환 메서드 테스트 제거, 정규화 검증 추가 |
| `tests/integration/test_api_bus.py` | 새 응답 형식 검증으로 교체 |

### 6.3 매핑 표

| iOS 모델 필드 | 백엔드 응답 필드 |
|---------------|------------------|
| `MsgHeader.headerCd` | `msgHeader.headerCd` |
| `MsgHeader.headerMsg` | `msgHeader.headerMsg` |
| `MsgHeader.itemCount` | `msgHeader.itemCount` (Int) |
| `BusArrivalItem.rtNm` | `msgBody.itemList[].rtNm` |
| `BusArrivalItem.arrmsg1` | `msgBody.itemList[].arrmsg1` |
| `BusArrivalItem.adirection` | `msgBody.itemList[].adirection` |
| `BusArrivalItem.routeType` | `msgBody.itemList[].routeType` |
| `BusArrivalItem.isFullFlag1` | `msgBody.itemList[].isFullFlag1` |
| `BusArrivalItem.isLast1` | `msgBody.itemList[].isLast1` |
| `BusArrivalItem.congestion1` | `msgBody.itemList[].congestion1` |
| `StationItem.stationId` | `msgBody.itemList[].stationId` |
| `StationItem.stationNm` | `msgBody.itemList[].stationNm` |
| `StationItem.arsId` | `msgBody.itemList[].arsId` |
| `StationItem.gpsX/gpsY/dist/stationTp` | 동일 키 |

### 6.4 헬스체크 도구 — `tools/ios-integration/healthcheck.sh`

3개 엔드포인트(헬스, arrivals, stations)를 호출하여 iOS 모델 키
(`msgHeader.headerCd, itemCount`, `BusArrivalItem.rtNm/routeType`, `StationItem.stationId/...`)
가 응답에 모두 존재하는지 검증.

```bash
$ tools/ios-integration/healthcheck.sh
========== ComfortableMove iOS 연동 체크 ==========
▶ 1) /api/v1/health
  HTTP 200, status=healthy
▶ 2) /api/v1/bus/arrivals?ars_id=23288  (iOS: BusArrivalResponse)
  HTTP 200 / iOS BusArrivalResponse 형식 일치
  itemCount=12
  ✓ BusArrivalItem.rtNm 존재
  ✓ BusArrivalItem.routeType 존재
▶ 3) /api/v1/bus/stations?tmX=126.9707&tmY=37.5547&radius=100
  HTTP 200 / iOS StationByPosResponse 형식 일치
  ...
```

### 6.5 iOS 앱 전환 가이드 (선택)

iOS 앱이 서울 API 직접 호출에서 백엔드 프록시로 전환할 때:

```swift
// 변경 전
let baseURL = "http://ws.bus.go.kr/api/rest/stationinfo/getStationByUid"
// queryItems: ServiceKey, arsId, resultType

// 변경 후
let baseURL = "\(BackendConfig.baseURL)/api/v1/bus/arrivals"
// queryItems: ars_id  (ServiceKey 불필요)
```

**JSONDecoder 디코딩 코드와 모델은 변경 불필요** (응답 구조 동일).

## 7. 산출물 (변경 파일)

```
infra/terraform/environments/dev/{main,variables,outputs,dev}.tfvars + tfvars.example
infra/terraform/environments/prod/{main,variables,outputs,prod}.tfvars + tfvars.example
infra/terraform/environments/README.md
infra/terraform/README.md
infra/terraform/modules/{network,security,storage,compute,rds,ingress,dns,monitoring}/README.md
infra/terraform/modules/network/{main,outputs}.tf  (for_each 패턴 적용)
.gitignore  (terraform 관련 항목 추가)

backend/app/schemas/bus.py            # iOS 모델과 1:1 일치
backend/app/schemas/__init__.py       # export 갱신
backend/app/services/seoul_bus_api.py # 정규화 로직
backend/app/api/v1/bus.py             # /arrivals + /stations
backend/tests/unit/test_seoul_bus_service.py
backend/tests/integration/test_seoul_bus_api.py
backend/tests/integration/test_api_bus.py

tools/ios-integration/healthcheck.sh
tools/ios-integration/README.md

docs/week9/week9_report.md
```

## 8. 시간 분배 (총 30시간)

| 활동 | 시간 |
|------|------|
| Terraform 모듈 분석 및 환경 분리 설계 | 6 |
| environments/dev, prod 작성 + locals/for_each 적용 | 7 |
| 모듈 README 문서화 | 4 |
| terraform fmt/validate 검증 및 troubleshooting | 2 |
| iOS 코드 분석 (BusArrivalService, BusStopService, 모델) | 3 |
| 백엔드 스키마 + 서비스 + 라우터를 iOS 형식으로 정합 | 5 |
| 테스트 코드 재작성 + 검증 | 2 |
| 헬스체크 스크립트 + 문서 작성 | 1 |

## 9. 풀스택 통합 검증 (2026-04-30 실시)

iOS / Backend / Infra 세 레이어가 함께 동작하는지 실기 검증.

### 9.1 검증 환경
- Backend: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`
  - `comfortablemove_backend_dev` (uvicorn, 코드 마운트, healthy)
  - `comfortablemove_db_dev` (Postgres 15, healthy)
  - `comfortablemove_redis_dev` (Redis 7, healthy)
- iOS: Xcode 26.2 / iPhone 16e 시뮬레이터 (UDID `7770F769-...`)
- 외부 API: 서울 TOPIS `ws.bus.go.kr/api/rest` (live)

### 9.2 iOS → Backend 전환 코드
- `App/Sources/AppConfig.swift` — `BackendConfig.useBackend = true`,
  `baseURL = http://localhost:8000` (Info.plist `BACKEND_BASE_URL` 로드)
- `Core/Manager/BusArrivalService.swift:62-74` — 백엔드 분기,
  legacy 서울 API 직접 호출은 폴백으로 보존
- `Core/Manager/BusStopService.swift:71-84` — 동일 패턴으로 분기
- `Info.plist` — `NSAppTransportSecurity.NSAllowsArbitraryLoads = true`
  (개발용 http 평문 허용; prod 에서는 ALB+ACM 후 https 만)

### 9.3 검증 스크립트 — `tools/ios-integration/fullstack_verify.sh`
1. Docker 컨테이너 healthy 3종 확인
2. `/api/v1/health` → status=healthy, db/redis/seoul_bus_api connected
3. `/api/v1/bus/arrivals?ars_id=23288` → 라이브 24개 노선,
   `BusArrivalItem` 7개 필수 키 누락 0
4. `/api/v1/bus/stations?tmX=127.0276&tmY=37.4979&radius=200` → 14개 정류소,
   `StationItem` 7개 필수 키 누락 0
5. `terraform validate` dev / prod 양쪽 통과
6. `xcrun simctl listapps` 로 시뮬레이터에 앱 설치 확인

### 9.4 결과

```
── 1) Docker backend stack ──
  ✓ comfortablemove_backend_dev: Up 28 minutes (healthy)
  ✓ comfortablemove_db_dev:      Up 28 minutes (healthy)
  ✓ comfortablemove_redis_dev:   Up 28 minutes (healthy)
── 2) Backend health ──
  ✓ /api/v1/health: healthy (db/redis/seoul_bus_api connected)
── 3) Backend → Seoul API live ──
  ✓ /api/v1/bus/arrivals?ars_id=23288 → 24 routes
    BusArrivalItem 필수 키 7개 누락: 없음
  ✓ /api/v1/bus/stations?tmX=127.0276&tmY=37.4979&radius=200 → 14 stops
    StationItem 필수 키 7개 누락: 없음
── 4) Terraform validate ──
  ✓ dev: valid
  ✓ prod: valid
── 5) iOS simulator ──
  ✓ simulator booted: 7770F769-...
  ✓ ComfortableMove app installed

PASS=10  FAIL=0
```

### 9.5 발견 및 조치
- **Postgres 패스워드 충돌**: 기존 볼륨이 다른 credential 로 초기화돼 있어
  `password authentication failed`. 해결: `docker compose down -v` 후
  `.env.dev` 의 `POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB` 를
  호스트 환경변수로 export 후 재기동.
- **Seoul API `itemCount=0` quirk**: 라이브 응답에서 `itemCount=0` 인데
  실제 `itemList` 는 24개. iOS 가 `itemCount` 로 분기하면 빈 결과로 오인됨.
  → `seoul_bus_api.py:_normalize_item_list` 가 `itemCount = len(item_list)`
  로 자동 보정.
- **API 키 위치**: data.go.kr 에서 발급된 새 키
  (`2a1d258c...`) 는 `api.odcloud.kr/api/15067528` 의 정적 정류장 데이터셋용
  으로 확인됨. 도착정보/위치기반 정류소는 서울 TOPIS API 만 제공하므로
  기존 키(`29b4ab63...`) 유지. 키는 `backend/.env*` 에 두고 iOS 는
  더 이상 직접 사용하지 않는 방향(server-side 전용)으로 정리 진행.

## 10. 다음 주(10주차) 계획

- iOS xcconfig 의 `API_KEY` 제거 (백엔드 프록시 전환 완료 후 클라이언트에서 키 노출 차단)
- 실제 dev 환경에 `terraform apply` 후 ALB + ACM + Route53 검증
- 시뮬레이터 UI 자동조작 (XCUITest 또는 fastlane snapshot) 으로 정류소 화면 진입까지 자동화
- `fullstack_verify.sh` 를 GitHub Actions 에 통합하여 매 PR 자동 검증
