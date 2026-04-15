# 7주차 활동 보고서

**프로젝트**: ComfortableMove (맘편한 이동) 백엔드 개발
**기간**: 2026년 4월 8일 ~ 2026년 4월 14일
**주요 목표**: AWS 심화 (RDS, S3, ALB) 및 HTTPS 통신 보안 구성

---

## 📋 주차 목표

6주차에 구축한 VPC/EC2 기반 인프라 위에 관리형 데이터베이스(RDS), 객체 스토리지(S3), 로드밸런서(ALB)를 추가하여 맘편한 이동 인프라를 완성합니다. 지도교수 피드백("HTTPS 통신 보안을 살펴볼 필요가 있다")을 반영하여 도메인 구매, ACM 인증서 발급, HTTPS 리스너 구성까지 진행합니다. 보안 그룹 체인(ALB → EC2 → RDS)을 설계하여 각 계층의 접근을 최소화하고, Elastic IP를 할당하여 EC2의 고정 IP를 확보합니다.

---

## ✅ 완료한 작업

### 1. 보안 그룹 체인 설계 및 구성

6주차에는 EC2 보안 그룹만 사용했으나, ALB와 RDS 도입에 맞춰 3단계 보안 그룹 체인을 설계했습니다.

**AWS 콘솔 경로**: VPC → 보안 그룹 → 보안 그룹 생성

**ALB 보안 그룹** (`comfortablemove-alb-sg`):

| 방향 | 프로토콜 | 포트 | 소스/대상 | 용도 |
|------|----------|------|-----------|------|
| 인바운드 | TCP | 80 | 0.0.0.0/0 | HTTP (HTTPS 리다이렉트용) |
| 인바운드 | TCP | 443 | 0.0.0.0/0 | HTTPS |
| 아웃바운드 | 전체 | 전체 | 0.0.0.0/0 | 헬스체크 등 |

**EC2 보안 그룹** (`comfortablemove-ec2-sg`) - 6주차 대비 변경:

| 방향 | 프로토콜 | 포트 | 소스/대상 | 용도 | 변경사항 |
|------|----------|------|-----------|------|----------|
| 인바운드 | TCP | 22 | 내 IP/32 | SSH 접속 | 유지 |
| 인바운드 | TCP | 8000 | **ALB SG** | API 접근 | **변경**: 내 IP → ALB SG |
| 아웃바운드 | 전체 | 전체 | 0.0.0.0/0 | 인터넷 | 유지 |

**RDS 보안 그룹** (`comfortablemove-rds-sg`):

| 방향 | 프로토콜 | 포트 | 소스/대상 | 용도 |
|------|----------|------|-----------|------|
| 인바운드 | TCP | 5432 | **EC2 SG** | PostgreSQL 접근 |
| 아웃바운드 | 전체 | 전체 | 0.0.0.0/0 | - |

**보안 그룹 체인 구조**:
```
인터넷 → ALB SG (80, 443) → EC2 SG (8000) → RDS SG (5432)
```

이 구조에서 RDS는 EC2에서만, EC2의 API 포트는 ALB에서만 접근 가능합니다. 외부에서 RDS나 EC2 API에 직접 접근하는 것은 불가능합니다.

### 2. RDS PostgreSQL 인스턴스 생성

Docker 컨테이너 내부 PostgreSQL을 AWS 관리형 서비스인 RDS로 전환했습니다.

**AWS 콘솔 경로**: RDS → 데이터베이스 생성

**2-1. DB 서브넷 그룹 생성**

RDS를 프라이빗 서브넷에 배치하기 위해 서브넷 그룹을 먼저 생성했습니다.

**콘솔 경로**: RDS → 서브넷 그룹 → DB 서브넷 그룹 생성

| 항목 | 값 |
|------|-----|
| 이름 | `comfortablemove-db-subnet` |
| VPC | `comfortablemove-vpc` |
| 가용영역 | ap-northeast-2a, ap-northeast-2c |
| 서브넷 | 프라이빗 A (10.0.11.0/24), 프라이빗 C (10.0.12.0/24) |

**2-2. 파라미터 그룹 생성**

SQL 로깅을 활성화하기 위해 커스텀 파라미터 그룹을 생성했습니다.

**콘솔 경로**: RDS → 파라미터 그룹 → 파라미터 그룹 생성

| 파라미터 | 값 | 용도 |
|----------|-----|------|
| `log_statement` | `all` | 모든 SQL 쿼리 로깅 |
| `log_min_duration_statement` | `1000` | 1초 이상 슬로우 쿼리 로깅 |

**2-3. RDS 인스턴스 생성**

| 항목 | 값 | 비고 |
|------|-----|------|
| 엔진 | PostgreSQL 15 | 백엔드와 동일 버전 |
| 인스턴스 식별자 | `comfortablemove-db` | - |
| 인스턴스 클래스 | db.t3.micro | 프리티어 (750시간/월) |
| 스토리지 | 20GB gp3 | 최대 30GB 자동 확장 |
| 스토리지 암호화 | 활성화 | AWS 관리형 키 사용 |
| 마스터 사용자 | `cmadmin` | - |
| DB 이름 | `comfortablemove` | - |
| Multi-AZ | 비활성화 | 프리티어는 Single-AZ만 무료 |
| 서브넷 그룹 | `comfortablemove-db-subnet` | 프라이빗 서브넷 |
| 보안 그룹 | `comfortablemove-rds-sg` | EC2에서만 접근 |
| 자동 백업 | 7일 보존 | 매일 자동 스냅샷 |
| 파라미터 그룹 | `comfortablemove-pg15-params` | SQL 로깅 활성화 |

**RDS 보안 포인트**:
- 프라이빗 서브넷 배치 → 인터넷에서 직접 접근 불가
- 보안 그룹으로 EC2에서만 5432 포트 접근 허용
- 스토리지 암호화 활성화
- 퍼블릭 액세스: 비활성화

### 3. S3 버킷 생성

정적 파일(이미지, 문서 등) 저장을 위한 S3 버킷을 생성했습니다.

**AWS 콘솔 경로**: S3 → 버킷 만들기

| 항목 | 값 |
|------|-----|
| 버킷 이름 | `comfortablemove-assets` |
| 리전 | ap-northeast-2 (서울) |
| 버전 관리 | 활성화 |
| 기본 암호화 | AES-256 (SSE-S3) |

**퍼블릭 액세스 차단 설정**:

| 설정 | 값 |
|------|-----|
| 모든 퍼블릭 액세스 차단 | ✅ 활성화 |
| 새 퍼블릭 ACL 차단 | ✅ |
| 새 퍼블릭 버킷 정책 차단 | ✅ |
| 기존 퍼블릭 ACL 무시 | ✅ |
| 기존 퍼블릭 버킷 정책 제한 | ✅ |

**CORS 설정**:
```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedOrigins": ["*"],
    "MaxAgeSeconds": 3600
  }
]
```

**EC2에서 S3 접근을 위한 IAM 역할**:

EC2에 IAM 인스턴스 프로파일을 연결하여 Access Key 없이 S3에 접근할 수 있도록 설정했습니다.

**콘솔 경로**: IAM → 역할 → 역할 만들기

| 항목 | 값 |
|------|-----|
| 역할 이름 | `comfortablemove-ec2-role` |
| 신뢰 대상 | EC2 서비스 |
| 허용 액션 | `s3:GetObject`, `s3:PutObject`, `s3:ListBucket` |
| 리소스 제한 | `comfortablemove-assets` 버킷만 |

### 4. Application Load Balancer 구성

EC2를 직접 노출하지 않고 ALB를 통해 트래픽을 전달하도록 구성했습니다.

**AWS 콘솔 경로**: EC2 → 로드 밸런서 → 로드 밸런서 생성 → Application Load Balancer

**4-1. 타겟 그룹 생성**

**콘솔 경로**: EC2 → 대상 그룹 → 대상 그룹 생성

| 항목 | 값 |
|------|-----|
| 이름 | `comfortablemove-tg` |
| 프로토콜 | HTTP |
| 포트 | 8000 |
| VPC | `comfortablemove-vpc` |
| 대상 | EC2 인스턴스 등록 |

**헬스체크 설정**:

| 항목 | 값 |
|------|-----|
| 경로 | `/api/v1/health` |
| 프로토콜 | HTTP |
| 포트 | 8000 |
| 정상 임계값 | 연속 2회 성공 |
| 비정상 임계값 | 연속 3회 실패 |
| 타임아웃 | 5초 |
| 간격 | 30초 |
| 성공 코드 | 200 |

**4-2. ALB 생성**

| 항목 | 값 |
|------|-----|
| 이름 | `comfortablemove-alb` |
| 스키마 | 인터넷 경계 (Internet-facing) |
| IP 주소 유형 | IPv4 |
| VPC | `comfortablemove-vpc` |
| 서브넷 | 퍼블릭 A + 퍼블릭 C (2개 AZ 필수) |
| 보안 그룹 | `comfortablemove-alb-sg` |

**4-3. 리스너 구성**

| 리스너 | 포트 | 동작 |
|--------|------|------|
| HTTPS | 443 | 타겟 그룹으로 포워딩 |
| HTTP | 80 | HTTPS(443)로 301 리다이렉트 |

ALB DNS: `comfortablemove-alb-252716626.ap-northeast-2.elb.amazonaws.com`

### 5. Elastic IP 할당

EC2 인스턴스의 퍼블릭 IP가 재시작 시 변경되는 문제를 해결하기 위해 Elastic IP를 할당했습니다.

**AWS 콘솔 경로**: EC2 → 탄력적 IP → 탄력적 IP 주소 할당

| 항목 | 값 |
|------|-----|
| Elastic IP | `3.37.165.32` |
| 연결 대상 | `comfortablemove-server` EC2 인스턴스 |
| 비용 | 실행 중 인스턴스 연결 시 무료 |

> **참고**: Elastic IP는 실행 중인 인스턴스에 연결되어 있으면 무료이지만, 인스턴스를 중지하면 시간당 $0.005가 과금됩니다.

### 6. HTTPS 통신 보안 구성 (지도교수 피드백 반영)

지도교수 피드백 "HTTPS 통신 보안을 살펴볼 필요가 있다"를 반영하여, 도메인 구매부터 SSL 인증서 적용까지 전체 HTTPS 구성을 완료했습니다.

**6-1. 도메인 구매**

`comfortablemove.com` 도메인을 구매했습니다.

**6-2. Route53 호스팅 영역 생성**

**콘솔 경로**: Route53 → 호스팅 영역 → 호스팅 영역 생성

| 항목 | 값 |
|------|-----|
| 도메인 | `comfortablemove.com` |
| 유형 | 퍼블릭 호스팅 영역 |

생성 후 Route53에서 제공하는 네임서버(NS) 4개를 도메인 등록기관의 네임서버 설정에 입력하여 DNS를 위임했습니다.

**6-3. ACM SSL 인증서 발급**

**콘솔 경로**: Certificate Manager → 인증서 요청

| 항목 | 값 |
|------|-----|
| 인증서 유형 | 퍼블릭 |
| 도메인 | `comfortablemove.com` |
| 추가 이름 | `*.comfortablemove.com` (와일드카드) |
| 검증 방법 | DNS 검증 |
| 비용 | **무료** (ACM 퍼블릭 인증서) |

DNS 검증을 위해 ACM이 제공하는 CNAME 레코드를 Route53에 추가했습니다. "Route53에서 레코드 생성" 버튼을 클릭하면 자동으로 검증 레코드가 추가됩니다.

**6-4. ALB에 HTTPS 리스너 추가**

**콘솔 경로**: EC2 → 로드 밸런서 → comfortablemove-alb → 리스너 추가

| 설정 | 값 |
|------|-----|
| 프로토콜 | HTTPS |
| 포트 | 443 |
| SSL 정책 | `ELBSecurityPolicy-TLS13-1-2-2021-06` |
| 인증서 | ACM에서 발급한 `comfortablemove.com` 인증서 |
| 기본 액션 | 타겟 그룹으로 포워딩 |

기존 HTTP(80) 리스너는 HTTPS(443)로 301 리다이렉트하도록 변경했습니다.

**6-5. Route53 A 레코드 생성 (도메인 → ALB)**

**콘솔 경로**: Route53 → comfortablemove.com → 레코드 생성

| 항목 | 값 |
|------|-----|
| 레코드 이름 | `comfortablemove.com` |
| 유형 | A (별칭) |
| 별칭 대상 | ALB (`comfortablemove-alb-xxx.elb.amazonaws.com`) |
| 라우팅 정책 | 단순 라우팅 |

**HTTPS 전체 흐름**:
```
사용자 → https://comfortablemove.com
  → Route53 (DNS → ALB IP)
    → ALB (HTTPS:443, SSL 종료)
      → EC2 (HTTP:8000, 내부 통신)
        → FastAPI 백엔드
```

**SSL/TLS 보안 포인트**:
- TLS 1.3/1.2만 허용 (1.0, 1.1 차단)
- ACM 인증서 자동 갱신 (만료 걱정 없음)
- HTTP → HTTPS 자동 리다이렉트로 비암호화 통신 방지
- SSL 종료는 ALB에서 처리, EC2 내부는 HTTP로 성능 확보

### 7. AWS Budgets 비용 알림

**AWS 콘솔 경로**: Billing → Budgets → 예산 생성

| 유형 | 임계값 | 금액 (월 $10 기준) | 설명 |
|------|--------|---------------------|------|
| 실제 비용 | 50% | $5.00 초과 시 | 조기 경고 |
| 실제 비용 | 80% | $8.00 초과 시 | 주의 경고 |
| 실제 비용 | 100% | $10.00 초과 시 | 한도 초과 |
| 예측 비용 | 100% | $10.00 초과 예측 시 | 사전 예방 |

알림 이메일을 등록하여 임계값 초과 시 자동으로 알림을 수신합니다.

### 8. CloudWatch 모니터링 구성

운영 가시성을 확보하기 위해 CloudWatch 대시보드와 알림을 구성했습니다.

**8-1. CloudWatch 대시보드**

**콘솔 경로**: CloudWatch → 대시보드 → 대시보드 생성

`comfortablemove-dashboard` 대시보드에 6개 위젯을 구성했습니다.

| 위젯 | 메트릭 | 서비스 |
|------|--------|--------|
| EC2 CPU Utilization | CPUUtilization | EC2 |
| ALB Request Count | RequestCount | ALB |
| RDS CPU Utilization | CPUUtilization | RDS |
| RDS Database Connections | DatabaseConnections | RDS |
| ALB Response Time | TargetResponseTime | ALB |
| RDS Free Storage Space | FreeStorageSpace | RDS |

**8-2. CloudWatch 알람**

SNS 토픽(`comfortablemove-alerts`)을 생성하고 이메일 구독을 설정하여, 알람 발생 시 이메일로 알림을 수신합니다.

| 알람 | 조건 | 설명 |
|------|------|------|
| EC2 CPU High | CPU > 80% (5분, 2회 연속) | 서버 과부하 감지 |
| ALB 5xx Errors | 5xx > 10회 (5분) | 서버 에러 급증 감지 |
| ALB Unhealthy Hosts | 비정상 호스트 > 0 (1분) | 헬스체크 실패 감지 |
| RDS CPU High | CPU > 80% (5분, 2회 연속) | DB 과부하 감지 |
| RDS Storage Low | 여유 공간 < 2GB | 디스크 부족 사전 경고 |

---

## 📊 전체 아키텍처

### 아키텍처 다이어그램 (7주차 완성)

```
                         인터넷
                           │
                    ┌──────┴──────┐
                    │  Route53    │  comfortablemove.com
                    │  (DNS)      │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │    ACM      │  SSL 인증서 (무료)
                    │  (HTTPS)    │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │   VPC (10.0.0.0/16)     │
              │                          │
              │  ┌─── 퍼블릭 서브넷 ───┐ │
              │  │                      │ │
              │  │  ┌──────────────┐   │ │
              │  │  │     ALB      │   │ │
              │  │  │  (80 → 443) │   │ │
              │  │  │  ALB SG      │   │ │
              │  │  └──────┬───────┘   │ │
              │  │         │           │ │
              │  │  ┌──────┴───────┐   │ │
              │  │  │     EC2      │   │ │
              │  │  │  t2.micro    │   │ │
              │  │  │  EIP: 3.37.  │   │ │
              │  │  │  EC2 SG      │   │ │
              │  │  │  :8000       │   │ │
              │  │  └──────┬───────┘   │ │
              │  └─────────│───────────┘ │
              │            │             │
              │  ┌─── 프라이빗 서브넷 ─┐ │
              │  │         │           │ │
              │  │  ┌──────┴───────┐   │ │
              │  │  │     RDS      │   │ │
              │  │  │ PostgreSQL15 │   │ │
              │  │  │  RDS SG      │   │ │
              │  │  │  :5432       │   │ │
              │  │  └──────────────┘   │ │
              │  └─────────────────────┘ │
              │                          │
              │  ┌─── S3 ────────────┐   │
              │  │ comfortablemove-  │   │
              │  │ assets (암호화)   │   │
              │  └──────────────────┘   │
              └──────────────────────────┘
```

### AWS 리소스 요약 (6주차 + 7주차)

| 구성 요소 | 리소스 | 주차 | 비용 |
|-----------|--------|------|------|
| VPC | `10.0.0.0/16` (서울) | 6주차 | 무료 |
| 퍼블릭 서브넷 | 2개 (AZ-a, AZ-c) | 6주차 | 무료 |
| 프라이빗 서브넷 | 2개 (AZ-a, AZ-c) | 6주차 | 무료 |
| 인터넷 게이트웨이 | 1개 | 6주차 | 무료 |
| EC2 | t2.micro, Amazon Linux 2023 | 6주차 | 프리티어 |
| Elastic IP | `3.37.165.32` | **7주차** | 무료 (연결 시) |
| 보안 그룹 | ALB SG + EC2 SG + RDS SG | **7주차** | 무료 |
| ALB | Application Load Balancer | **7주차** | ~$16/월 |
| 타겟 그룹 | EC2 등록, 헬스체크 설정 | **7주차** | 무료 |
| RDS | PostgreSQL 15, db.t3.micro | **7주차** | 프리티어 |
| S3 | `comfortablemove-assets` | **7주차** | 프리티어 |
| Route53 | `comfortablemove.com` 호스팅 영역 | **7주차** | $0.50/월 |
| ACM | SSL 인증서 (와일드카드) | **7주차** | 무료 |
| Budget | 월 $10, 4단계 알림 | 6주차 | 무료 |

---

## 🔧 기술 스택 (7주차 추가)

**Cloud (신규)**:
- RDS PostgreSQL 15 (관리형 DB)
- S3 (객체 스토리지, 암호화)
- ALB (Application Load Balancer)
- Route53 (DNS 관리)
- ACM (SSL/TLS 인증서)
- Elastic IP

**Security (강화)**:
- 3단계 보안 그룹 체인 (ALB → EC2 → RDS)
- HTTPS (TLS 1.3/1.2)
- S3 퍼블릭 액세스 완전 차단
- RDS 프라이빗 서브넷 배치 + 스토리지 암호화

---

## 💡 배운 점

### 1. RDS vs Docker 컨테이너 DB의 차이

6주차에는 Docker Compose 내부에 PostgreSQL 컨테이너를 띄웠습니다. RDS로 전환하면서 얻은 이점:

| 항목 | Docker 컨테이너 DB | RDS |
|------|-------------------|-----|
| 자동 백업 | 직접 cron 설정 필요 | 7일 자동 스냅샷 |
| 패치/업데이트 | 직접 이미지 업데이트 | AWS가 자동 관리 |
| 고가용성 | 직접 복제 구성 | Multi-AZ 옵션 |
| 스토리지 암호화 | 직접 구성 | 체크박스 하나 |
| 모니터링 | 직접 구성 | CloudWatch 자동 연동 |

### 2. ALB를 사용하는 이유

EC2에 직접 접속하면 되는데 왜 ALB를 앞에 두는가?

1. **SSL 종료**: ALB에서 HTTPS를 처리하므로 EC2는 HTTP만 처리
2. **EC2 직접 노출 방지**: 사용자는 ALB DNS/도메인만 알고 EC2 IP는 모름
3. **헬스체크**: 비정상 인스턴스 자동 제외
4. **확장성**: 향후 EC2를 추가하면 ALB가 자동 분산

### 3. HTTPS 구성의 전체 흐름 이해

처음에는 "인증서만 설치하면 되는 것 아닌가?"라고 생각했지만, 실제로는:

1. 도메인 구매 → 2. Route53 호스팅 영역 생성 → 3. 네임서버 변경 → 4. ACM 인증서 요청 → 5. DNS 검증 → 6. ALB HTTPS 리스너 연결 → 7. HTTP 리다이렉트 설정

이 모든 단계가 연결되어야 합니다. ACM은 도메인 소유를 DNS로 검증하기 때문에, Route53과 도메인 등록기관의 네임서버가 일치해야 인증서가 발급됩니다.

### 4. 보안 그룹 체인의 중요성

6주차에는 EC2 하나의 보안 그룹으로 모든 것을 관리했지만, 7주차에서 ALB, RDS가 추가되면서 각 계층별로 보안 그룹을 분리하는 것이 중요해졌습니다. 보안 그룹의 소스를 IP가 아닌 **다른 보안 그룹 ID**로 지정하면:

- IP가 변경되어도 규칙을 수정할 필요 없음
- 어떤 리소스가 어떤 리소스에 접근하는지 명확하게 표현
- 실수로 외부에 포트를 여는 것을 방지

### 5. Elastic IP의 필요성

EC2의 기본 퍼블릭 IP는 인스턴스 중지/시작 시 변경됩니다. Elastic IP를 할당하면:
- SSH 접속 시 매번 IP를 확인할 필요 없음
- GitHub Actions CD에서 배포 대상 IP가 고정
- DNS 레코드(직접 연결 시)가 안정적

단, 인스턴스에 연결하지 않은 Elastic IP는 과금되므로, 인스턴스 삭제 시 반드시 함께 해제해야 합니다.

---

## 🔄 다음 주 (8주차) 계획

### 1. 실제 서비스 연동 테스트
- FastAPI 백엔드의 DATABASE_URL을 RDS 엔드포인트로 전환
- `https://comfortablemove.com/api/v1/health`로 전체 연결 확인
- 신흥운수 협력 환경에서 실제 탑승 데이터 수집 초기 테스트

### 2. CloudWatch 모니터링
- EC2 CPU, 메모리, 네트워크 메트릭 대시보드 구성
- RDS 연결 수, 쿼리 성능 모니터링
- ALB 요청 수, 응답 시간, 5xx 에러 알림 설정

### 3. 인프라 코드화 (Terraform)
- 현재 콘솔로 구성한 인프라를 Terraform으로 코드화
- `terraform import`로 기존 리소스 가져오기
- 인프라 변경 이력 추적 및 재현 가능성 확보

---

## 📝 회고

### 잘한 점

1. **보안 그룹 체인 설계**: ALB → EC2 → RDS 3단계 보안 그룹으로 각 계층의 접근을 최소화했다. 보안 그룹 소스를 IP가 아닌 SG ID로 지정하여 유연성을 확보했다.
2. **HTTPS 완전 구성**: 도메인 구매부터 ACM 인증서, Route53 DNS, ALB HTTPS 리스너까지 전체 흐름을 완성했다. 지도교수 피드백을 적극 반영했다.
3. **RDS 프라이빗 서브넷 배치**: DB를 인터넷에서 직접 접근할 수 없는 프라이빗 서브넷에 배치하여 보안을 강화했다.
4. **S3 보안 설정**: 퍼블릭 액세스를 완전 차단하고, 서버 측 암호화를 적용하여 데이터 보안을 확보했다.
5. **비용 인식**: ALB가 프리티어에 포함되지 않는 점을 확인하고, 테스트 후 리소스 정리 계획을 수립했다.

### 아쉬운 점

1. **WAF 미적용**: ALB 앞단에 WAF(Web Application Firewall)를 추가하면 SQL Injection, XSS 등을 방어할 수 있지만, 비용 문제로 보류했다.
2. **Auto Scaling 미구성**: 현재 EC2 1대로 운영하고 있어 트래픽 급증 시 대응이 어렵다. 향후 Auto Scaling Group 도입을 검토할 예정이다.

### 개선 방향

1. Terraform으로 인프라 코드화 (재현 가능성 확보)
2. WAF 적용 검토 (보안 강화)
3. Auto Scaling Group 도입 검토
4. 실제 서비스 트래픽 기반 성능 테스트

---

## 🎯 총 투입 시간

**예상**: 주 30시간
**실제**: 약 30시간

**상세**:

- 보안 그룹 체인 설계 및 구성: 3시간
- RDS PostgreSQL 인스턴스 생성 및 설정: 4시간
- S3 버킷 생성 및 보안 설정: 2시간
- ALB 구성 (타겟 그룹, 리스너, 헬스체크): 4시간
- Elastic IP 할당: 0.5시간
- 도메인 구매 및 Route53 설정: 2시간
- ACM 인증서 발급 및 DNS 검증: 2시간
- ALB HTTPS 리스너 구성 및 테스트: 3시간
- RDS 연결 테스트 및 파라미터 튜닝: 3시간
- 전체 아키텍처 다이어그램 업데이트: 2시간
- 보고서 작성: 4.5시간

---

## 📌 참고 자료

- [AWS RDS 사용 설명서](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/)
- [AWS S3 보안 모범 사례](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [AWS ALB 사용 설명서](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/)
- [AWS ACM 사용 설명서](https://docs.aws.amazon.com/acm/latest/userguide/)
- [AWS Route53 사용 설명서](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/)
- [AWS 보안 그룹 모범 사례](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html)

---

**작성일**: 2026년 4월 14일
**작성자**: 박성근
