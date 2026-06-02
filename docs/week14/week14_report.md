# 14주차 활동 보고서

## 1. 프로젝트 주차 목표

14주차는 두 축으로 진행하였다. 첫째, Jenkins를 도입하여 13주차의 GitHub Actions와는 별개의 CI 파이프라인을 Pipeline as Code로 구축하고, 두 도구를 실증적으로 비교 분석한다. 둘째, 그동안 로컬 환경에서만 동작하던 백엔드를 AWS에 실제로 배포하고 iOS 앱을 클라우드 백엔드에 연동하여, iOS부터 임베디드(ESP32)·백엔드·데이터베이스까지 전 구간이 동작하는 실서비스 환경을 완성한다.

두 작업 모두 설정 파일이나 코드를 작성하는 데 그치지 않고, Jenkins를 실제로 기동하여 파이프라인이 SUCCESS로 완료되는 것, 그리고 AWS 인프라를 실제로 생성하여 도메인으로 서비스가 응답하는 것까지 직접 검증하는 것을 핵심 목표로 한다.


## 2. 프로젝트 주차 진행 내용

### 2-1. Jenkins CI 파이프라인 구축 (JCasC + Declarative)

Jenkins를 단순히 설치하는 대신 Pipeline as Code 정신에 맞춰 **JCasC(Jenkins Configuration as Code)** 로 서버 구성 전체를 코드화하였다. 이로써 Setup Wizard의 수동 작업(초기 비밀번호 입력, 플러그인 선택, 관리자 계정 생성) 없이 `docker compose up` 한 번으로 동일한 Jenkins 환경이 재현된다.

| 파일 | 역할 |
|------|------|
| Dockerfile | jenkins-lts + Python3 + Docker CLI + buildx + 플러그인 사전 설치 |
| plugins.txt | configuration-as-code, workflow-aggregator, job-dsl, docker-workflow 등 |
| casc.yaml | 관리자 계정·권한·파이프라인 Job(Job DSL)을 코드로 정의 |
| docker-compose.yml | docker.sock 공유로 DooD(Docker outside of Docker) 빌드 지원 |

루트에는 Declarative `Jenkinsfile`을 작성하여 13주차 GitHub Actions의 흐름(Checkout → Lint → Test → Docker Build → Push to ECR)을 그대로 옮겼다. flake8는 순수 파이썬이라 Jenkins 노드에서 직접 실행하고, 테스트는 `Dockerfile.test`(python:3.12-slim)를 빌드해 컨테이너 안에서 pytest를 수행한다. ECR 푸시는 `ECR_REGISTRY`가 있을 때만 실행되도록 `when` 조건을 두어 미설정 시 graceful skip 한다. 선언적/스크립트 중 가독성과 사전 오류 검증이 강한 **Declarative**를 채택하였다.

### 2-2. 파이프라인 실제 기동·검증 및 멀티브랜치·자동 트리거

Jenkins 컨테이너를 실제로 기동하고 REST API(crumb 인증)로 파이프라인을 트리거하며, SUCCESS가 나올 때까지 5회에 걸쳐 디버깅하였다. 최종적으로 **빌드 #5가 SUCCESS(49초)** 로 완료되었다.

| 단계 | 결과 | 소요 |
|------|------|------|
| Checkout | SUCCESS | 1s |
| Lint (flake8) | SUCCESS | 2s |
| Test (pytest) | SUCCESS (77 passed) | 8s |
| Docker Build | SUCCESS | 32s |
| Push to ECR | NOT_EXECUTED (graceful skip) | - |

멀티브랜치 파이프라인은 `multibranchPipelineJob`을 git source로 정의하여 `git ls-remote` 기반으로 GitHub API rate limit·토큰 없이 모든 브랜치를 발견한다. main과 테스트 브랜치(`ci/jenkins-multibranch-demo`)를 자동 발견하여 각각 빌드 SUCCESS함을 확인하였다. 자동 트리거는, 로컬 Jenkins(root + docker.sock + 기본 비밀번호)를 공개 인터넷에 노출하는 보안 위험을 피하기 위해 Webhook 대신 **SCM 폴링**(단일 Job `H/2`, 멀티브랜치 `periodicFolderTrigger(2m)`)을 채택하였고, 실제로 push 후 폴링으로 자동 빌드(`Started by an SCM change`)되는 것을 확인하였다.

### 2-3. GitHub Actions vs Jenkins 비교 분석

13주차(GitHub Actions)와 14주차(Jenkins)에 동일한 5단계 파이프라인을 구현한 경험을 바탕으로 비교 문서(`docs/week14/github_actions_vs_jenkins.md`)를 작성하였다. 호스팅 방식(SaaS vs self-hosted), 설정 언어(YAML vs Groovy), DB/캐시 의존성 처리, 설정 코드화 범위, 운영 부담, 비용 모델 등을 표로 정리하였다.

### 2-4. AWS 프로덕션 인프라 배포 (Terraform)

로컬에서만 동작하던 백엔드를 AWS에 배포하기 위해, Terraform으로 코드화된 풀스택 인프라(48개 리소스, 서울 리전)를 실제로 `apply` 하였다.

```
인터넷 → comfortablemove.com (Route53)
      → ALB (ACM 인증서, HTTP→HTTPS 301)        [public subnet]
      → EC2 t2.micro: backend(:8000) + redis     [public subnet]
      → RDS PostgreSQL db.t3.micro (asyncpg)      [private subnet, SG로 EC2만 허용]
```

| 모듈 | 리소스 | 비고 |
|------|--------|------|
| network | VPC, public/private 서브넷, IGW | NAT GW 미사용(비용 절감) |
| security | Security Group 3종(ALB/EC2/RDS) | RDS는 EC2 SG에서만 5432 허용 |
| compute | EC2 t2.micro | 루트 볼륨 30GB gp3(암호화) |
| rds | RDS PostgreSQL db.t3.micro | Single-AZ, private subnet |
| ingress | ALB, Target Group, Listener | HTTP→HTTPS 리다이렉트 |
| dns | ACM 인증서(DNS 검증), Route53 A레코드 | 와일드카드 SAN |
| storage / monitoring | S3, CloudWatch 알람, 월 예산 알림 | 예산 초과 시 이메일 |

### 2-5. 백엔드 배포 및 Alembic 마이그레이션 도입

EC2는 user-data로 Docker·docker-compose를 자동 설치하고, 저장소를 clone한 뒤 `.env.prod`(RDS endpoint·서울버스 키·SECRET_KEY 등)를 구성하여 `docker compose -f docker-compose.prod.yml up`으로 앱(backend + redis)을 기동한다. RDS는 외부 PostgreSQL로 연결한다.

기존 `init_db()`의 `create_all`은 development/testing 환경에서만 실행되어 production에서는 테이블이 생성되지 않았고 Alembic 마이그레이션도 부재하였다. 이를 정석대로 **Alembic(async)** 으로 전환하여 `users_devices`, `boarding_records` 테이블과 인덱스 6개를 초기 마이그레이션으로 정의하고, Dockerfile entrypoint에서 컨테이너 기동 시 `alembic upgrade head`가 자동 실행되도록 구성하였다.

### 2-6. iOS 클라우드 연동

iOS(별도 저장소 BFDream-iOS)의 백엔드 주소를 로컬 IP에서 클라우드 도메인으로 전환하고 개발용 더미를 제거하였다.

| 변경 | 파일 | 내용 |
|------|------|------|
| 백엔드 URL | Config.xcconfig | http://\<로컬IP>:8000 → https://comfortablemove.com |
| 더미 제거 | HomeView.swift | 도착정보에 항상 끼던 mock143 제거 → 실제 도착 버스만 표시 |
| BLE 송신값 | HomeView.swift | 고정 "143" → 화면 선택 노선(busName) |
| 기기 ID 일치 | HomeView.swift | busDeviceId 도 DistrictMapper 변환값 사용 |

BLE 노선명은 DistrictMapper(seoul_districts.csv)로 한글→영문 변환된다. 예: 화면 선택 "강동01" → "Gangdong01" → ESP32 기기명 `BF_DREAM_Gangdong01` 과 매칭(대소문자 무관). boarding 기록은 통계용으로 route_name은 한글("강동01"), bus_device_id는 영문("BF_DREAM_Gangdong01")으로 저장하여 통계 정확성과 기기 식별 일관성을 모두 확보하였다.


## 3. 프로젝트 주차 진행 결과

**Jenkins CI 완성 및 검증**: `docker compose up --build` 한 번으로 관리자 계정·플러그인·파이프라인 Job이 자동 구성되는 재현 가능한 CI 환경을 구축하였다. 빌드 #5가 전 단계 SUCCESS(pytest 77건 통과), 멀티브랜치가 두 브랜치를 자동 빌드, SCM 폴링이 push를 감지해 자동 빌드함을 확인하였다.

**AWS 프로덕션 배포 완성**: Terraform 48개 리소스를 실제 생성하여 `https://comfortablemove.com`이 HTTPS로 응답하는 프로덕션 환경을 구축하였다. 헬스체크에서 database·redis·서울버스 API가 모두 정상으로 확인되었다.

**End-to-End 검증**: iOS가 호출하는 엔드포인트를 클라우드 백엔드에 직접 호출하여 실데이터를 확인하였다.

| 검증 항목 | 요청 | 결과 |
|-----------|------|------|
| 헬스체크 | GET /api/v1/health | database/redis/seoul_bus_api 모두 정상 |
| HTTPS | https://comfortablemove.com | ACM 인증서 정상, HTTP→301 |
| 주변 정류장 | GET /api/v1/bus/stations | 정류장 35건(서울역 등) |
| 버스 도착 | GET /api/v1/bus/arrivals?ars_id=02003 | 실시간 도착정보(6001/1711/7016번) |
| 탑승 기록 | POST /api/v1/boarding/record | 201 Created → RDS 저장 |

최종적으로 실기기와 ESP32로 iOS(강동01 선택) → BLE 매칭(`BF_DREAM_Gangdong01`) → 알림 전송 success → RDS 저장까지 전 구간을 확인하였다. 기록은 route_name="강동01", bus_device_id="BF_DREAM_Gangdong01", notification_status="success"로 정확히 저장되었다.

GitHub(백엔드): https://github.com/ParkSeongGeun/dream_semester_2026_1
GitHub(iOS): https://github.com/BFDream-AutoEver/BFDream-iOS


## 4. 기타 (문제점, 해결방법, 자기평가)

### 4-1. 문제점 및 해결방법

Jenkins 파이프라인과 AWS 배포 과정에서 실제로 만나 해결한 문제들을 정리하면 다음과 같다.

| 영역 | 증상 | 원인 | 해결 |
|------|------|------|------|
| Jenkins | `timestamps()` 컴파일 실패 | timestamper 플러그인 미설치 | 옵션 제거 |
| Jenkins | ARM64 네이티브 컴파일 실패 | 노드에서 직접 pip install 시 asyncpg/pydantic-core wheel 부재 | 공식 python 이미지 기반 Docker 빌드로 전환 |
| Jenkins | `COPY tests/` 빌드 실패 | 운영 .dockerignore가 tests/ 제외 | BuildKit per-Dockerfile ignore로 분리 |
| Jenkins | "buildx is missing" | Jenkins 컨테이너에 buildx 컴포넌트 없음 | docker-buildx-plugin 추가 설치 |
| 배포 | EC2 생성 실패(InvalidBlockDeviceMapping) | AMI 스냅샷 30GB인데 루트 볼륨 20GB | volume_size 20→30GB |
| 배포 | `docker-compose: Not: command not found` | user-data가 file()로 읽혀 `$${VER}`가 PID로 깨짐 | `$${VERSION}` → `${VERSION}` |
| 배포 | boarding/record 400, 기록 안 됨 | production이라 create_all 스킵 + Alembic 부재 → 테이블 부재 | Alembic 마이그레이션 도입 |
| 배포 | entrypoint `alembic: not found` | requirements.prod.txt에 alembic 누락 | requirements.prod.txt에 추가 |
| iOS | 기록 bus_device_id가 한글 | BLE 검색은 변환값(영문)인데 기록은 변환 전 값 | busDeviceId도 변환값 사용 |

특히 배포의 docker-compose 설치 실패와 alembic 누락은 모두 dev/prod 의존성·설정 이중관리에서 비롯되었는데, 이는 12주차 prometheus 패키지 누락과 동일한 패턴으로 반복 학습이 되었다.

### 4-2. 자기평가

Jenkins에서는 JCasC로 서버 구성 전체를 코드화하고 실제로 기동하여 파이프라인을 SUCCESS까지 검증하였다. 5회의 빌드 실패를 콘솔 로그로 추적하며, CI 도구가 추상화해주던 부분(러너에 미리 깔린 docker/python, wheel 제공, 빌드 컨텍스트, buildx)을 self-hosted 환경에서는 직접 구성해야 함을 체감하였다. 13주차 GitHub Actions와 같은 파이프라인을 재구현하며 도구에 따라 구현 난이도와 책임 범위가 크게 달라짐도 비교 관점에서 학습하였다.

AWS 배포에서는 Terraform으로 코드화된 풀스택 인프라를 실제로 apply 하여 도메인 HTTPS까지 동작하는 프로덕션을 구축하였다. EC2 볼륨 크기, user-data의 템플릿 이스케이프, production 환경의 테이블 생성 경로 부재 등 로컬에서는 드러나지 않던 문제들을 실배포에서 직접 해결하며 인프라와 애플리케이션 경계의 이슈를 체감하였다. 또한 스키마 관리를 create_all 임시방편에서 Alembic 마이그레이션으로 정식화하고, iOS의 BLE 기기명 변환 규칙까지 일관되게 맞추어 클라이언트–서버–임베디드 전 구간의 데이터 정합성을 확보하였다. 무엇보다 CI/CD부터 실제 클라우드 배포, iOS 연동까지 한 주차에 통합하여, 코드가 사용자 단말에서 실서비스로 이어지는 전체 흐름을 직접 완성한 점이 의미 있었다.

아쉬운 점은 Jenkins의 GitHub Webhook 즉시 트리거와 Slack 실제 발송은 보안·자격증명 제약으로 SCM 폴링·설정 작성까지만 진행한 것이다. 또한 운영 비용을 고려하면 상시 가동보다 필요 시 `terraform apply/destroy`로 환경을 올리고 내리는 운영 전략이 필요함을 인지하였다.
