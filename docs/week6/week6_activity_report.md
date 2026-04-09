# 6주차 활동 보고서

**프로젝트**: ComfortableMove (맘편한 이동) 백엔드 개발
**기간**: 2026년 4월 1일 ~ 2026년 4월 7일
**주요 목표**: AWS 기초 (IAM, EC2, VPC) 인프라 구축

---

## 📋 주차 목표

AWS 클라우드의 핵심 서비스를 학습하고, 맘편한 이동 백엔드를 위한 기본 인프라를 구성합니다. IAM으로 최소 권한 원칙에 따라 프로젝트 전용 사용자를 생성하고, VPC를 설계하여 퍼블릭/프라이빗 서브넷을 2개 가용영역에 걸쳐 구성합니다. EC2 인스턴스에서 맘편한 이동 백엔드가 정상 동작하는 것을 확인하고, 비용 알림을 설정하여 예상치 못한 과금을 방지합니다. 5주차 지도교수 피드백("민감 정보 유출 방지 구조 설계")을 반영하여 자격증명 관리 체계를 수립합니다.

---

## ✅ 완료한 작업

### 1. AWS 계정 보안 설정

루트 계정에 MFA(Multi-Factor Authentication)를 설정하고, 일상 작업에는 루트 계정 대신 IAM 사용자를 사용하도록 구성했습니다.

**루트 계정 보안 체크리스트**:

| 항목                      | 상태 | 설명                               |
| ------------------------- | ---- | ---------------------------------- |
| MFA 활성화                | ✅   | Google Authenticator 기반 가상 MFA |
| Access Key 미생성         | ✅   | 루트 계정에는 Access Key 미생성    |
| 비밀번호 정책 설정        | ✅   | 최소 12자, 대소문자+숫자+특수문자  |
| 결제 정보 IAM 접근 활성화 | ✅   | IAM 사용자가 비용 정보 조회 가능   |

### 2. IAM 구성 (최소 권한 원칙)

프로젝트 전용 IAM 그룹, 사용자, 정책을 AWS CLI로 생성했습니다. 5주차 지도교수 피드백을 반영하여 민감 정보 관리 체계를 설계했습니다.

**2-1. IAM 정책 설계**

최소 권한 원칙(Principle of Least Privilege)에 따라 필요한 권한만 부여하는 커스텀 정책 2개를 작성했습니다.

```json
// comfortablemove-ec2-policy.json (핵심 부분)
{
  "Statement": [
    {
      "Sid": "EC2ManageInstances",
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:DescribeInstances"
        // ... EC2/VPC 관리에 필요한 최소 액션만 허용
      ],
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "ap-northeast-2"
        }
      }
    }
  ]
}
```

**정책 설계 원칙**:

- `Resource: "*"` 대신 리전 조건(`ap-northeast-2`)으로 범위 제한
- EC2 관리, VPC 네트워크, 비용 조회를 별도 정책으로 분리
- `iam:*`, `s3:*` 등 불필요한 서비스 권한 미부여

| 정책         | 파일                                  | 허용 액션                                |
| ------------ | ------------------------------------- | ---------------------------------------- |
| EC2/VPC 관리 | `comfortablemove-ec2-policy.json`     | EC2 인스턴스, 보안 그룹, VPC/서브넷 관리 |
| 비용 조회    | `comfortablemove-billing-policy.json` | Billing 조회, Budget 생성/조회           |

**2-2. IAM 그룹 및 사용자 생성**

AWS CLI로 그룹과 사용자를 생성하는 자동화 스크립트(`setup-iam.sh`)를 작성했습니다.

```bash
# IAM 그룹 생성
aws iam create-group --group-name comfortablemove-developers

# 커스텀 정책 생성 및 그룹 연결
aws iam create-policy \
    --policy-name comfortablemove-ec2-policy \
    --policy-document file://comfortablemove-ec2-policy.json
aws iam attach-group-policy \
    --group-name comfortablemove-developers \
    --policy-arn arn:aws:iam::ACCOUNT_ID:policy/comfortablemove-ec2-policy

# IAM 사용자 생성 및 그룹 추가
aws iam create-user --user-name comfortablemove-deploy
aws iam add-user-to-group \
    --user-name comfortablemove-deploy \
    --group-name comfortablemove-developers
```

**2-3. 자격증명 보안 관리 (지도교수 피드백 반영)**

5주차 피드백에서 지적된 "민감 정보 유출 방지"를 위해 다음 체계를 수립했습니다.

| 구분                  | 보안 조치      | 설명                                                  |
| --------------------- | -------------- | ----------------------------------------------------- |
| Access Key            | AWS CLI 프로필 | `aws configure --profile comfortablemove`로 로컬 저장 |
| Git 유출 방지         | `.gitignore`   | `*.pem`, `*-outputs.env`, `.env.*` 등록               |
| 코드 내 하드코딩 금지 | 환경변수 사용  | `.env.docker` 파일로 분리, `chmod 600`                |
| 향후 CI/CD            | GitHub Secrets | Access Key를 코드가 아닌 GitHub Secrets에 저장 예정   |

### 3. VPC 아키텍처 설계 및 구축

맘편한 이동 전용 VPC를 2개 가용영역에 걸쳐 설계하고 AWS CLI로 구축했습니다.

**3-1. VPC 네트워크 다이어그램**

![alt text](image.png)

**3-2. 서브넷 설계**

| 서브넷     | CIDR           | 가용영역        | 용도                  |
| ---------- | -------------- | --------------- | --------------------- |
| 퍼블릭 A   | `10.0.1.0/24`  | ap-northeast-2a | EC2 백엔드, NAT GW    |
| 퍼블릭 C   | `10.0.2.0/24`  | ap-northeast-2c | 확장용 예비 (ALB 등)  |
| 프라이빗 A | `10.0.11.0/24` | ap-northeast-2a | 향후 RDS, ElastiCache |
| 프라이빗 C | `10.0.12.0/24` | ap-northeast-2c | 향후 RDS Multi-AZ     |

**CIDR 설계 이유**:

- `/16` VPC: 65,536개 IP로 충분한 확장성 확보
- 퍼블릭은 `10.0.1-2.x`, 프라이빗은 `10.0.11-12.x`로 대역을 분리하여 직관적 관리
- 각 서브넷 `/24` (251개 가용 IP)로 소규모 프로젝트에 적합

**3-3. 라우팅 테이블**

| 라우팅 테이블 | 대상          | 타겟              | 연결 서브넷   |
| ------------- | ------------- | ----------------- | ------------- |
| 퍼블릭 RT     | `10.0.0.0/16` | local             | 퍼블릭 A, C   |
| 퍼블릭 RT     | `0.0.0.0/0`   | 인터넷 게이트웨이 | 퍼블릭 A, C   |
| 프라이빗 RT   | `10.0.0.0/16` | local             | 프라이빗 A, C |
| 프라이빗 RT   | `0.0.0.0/0`   | NAT 게이트웨이    | 프라이빗 A, C |

**3-4. VPC 구축 (AWS CLI)**

전체 VPC 인프라를 AWS CLI로 구축하는 자동화 스크립트(`setup-vpc.sh`)를 작성했습니다.

```bash
# VPC 생성 및 DNS 호스트네임 활성화
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query 'Vpc.VpcId' --output text)
aws ec2 modify-vpc-attribute --vpc-id ${VPC_ID} --enable-dns-hostnames '{"Value":true}'

# 퍼블릭 서브넷 생성 (자동 퍼블릭 IP 할당)
PUB_SUB_A=$(aws ec2 create-subnet --vpc-id ${VPC_ID} \
    --cidr-block 10.0.1.0/24 --availability-zone ap-northeast-2a \
    --query 'Subnet.SubnetId' --output text)
aws ec2 modify-subnet-attribute --subnet-id ${PUB_SUB_A} --map-public-ip-on-launch

# 인터넷 게이트웨이 → VPC 연결
IGW_ID=$(aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 attach-internet-gateway --internet-gateway-id ${IGW_ID} --vpc-id ${VPC_ID}

# NAT 게이트웨이 (Elastic IP 할당)
EIP_ALLOC=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
NAT_GW_ID=$(aws ec2 create-nat-gateway --subnet-id ${PUB_SUB_A} --allocation-id ${EIP_ALLOC} \
    --query 'NatGateway.NatGatewayId' --output text)

# 라우팅 테이블: 퍼블릭 → IGW, 프라이빗 → NAT GW
aws ec2 create-route --route-table-id ${PUB_RT_ID} \
    --destination-cidr-block 0.0.0.0/0 --gateway-id ${IGW_ID}
aws ec2 create-route --route-table-id ${PRIV_RT_ID} \
    --destination-cidr-block 0.0.0.0/0 --nat-gateway-id ${NAT_GW_ID}
```

스크립트 실행 완료 후 모든 리소스 ID를 `vpc-outputs.env`에 자동 저장하여 후속 스크립트(EC2 생성)에서 참조합니다.

### 4. EC2 인스턴스 생성 및 보안 그룹 설정

**4-1. 보안 그룹 (최소 포트 오픈)**

```bash
# 보안 그룹 생성
SG_ID=$(aws ec2 create-security-group \
    --group-name comfortablemove-backend-sg \
    --description "ComfortableMove Backend - SSH and API access only" \
    --vpc-id ${VPC_ID} --query 'GroupId' --output text)

# 현재 IP에서만 SSH, API 접근 허용
MY_IP=$(curl -s https://checkip.amazonaws.com)/32
aws ec2 authorize-security-group-ingress --group-id ${SG_ID} --protocol tcp --port 22 --cidr ${MY_IP}
aws ec2 authorize-security-group-ingress --group-id ${SG_ID} --protocol tcp --port 8000 --cidr ${MY_IP}
```

**보안 그룹 규칙**:

| 방향       | 프로토콜 | 포트 | 소스/대상 | 용도                    |
| ---------- | -------- | ---- | --------- | ----------------------- |
| 인바운드   | TCP      | 22   | 내 IP/32  | SSH 접속                |
| 인바운드   | TCP      | 8000 | 내 IP/32  | FastAPI 접근            |
| 아웃바운드 | 전체     | 전체 | 0.0.0.0/0 | 인터넷 (패키지 설치 등) |

**보안 강화 포인트**:

- `0.0.0.0/0`이 아닌 현재 IP(`/32`)로 인바운드 제한
- HTTP(80), HTTPS(443) 포트는 현재 미오픈 (추후 ALB 도입 시 설정)
- PostgreSQL(5432), Redis(6379) 포트는 외부 비노출 (Docker 내부 통신)

**4-2. EC2 인스턴스 생성**

```bash
# Amazon Linux 2023 최신 AMI 조회
AMI_ID=$(aws ec2 describe-images --owners amazon \
    --filters "Name=name,Values=al2023-ami-2023.*-x86_64" "Name=state,Values=available" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' --output text)

# EC2 인스턴스 생성 (t2.micro 프리티어)
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id ${AMI_ID} \
    --instance-type t2.micro \
    --key-name comfortablemove-key \
    --security-group-ids ${SG_ID} \
    --subnet-id ${PUB_SUB_A} \
    --user-data file://user-data.sh \
    --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' \
    --query 'Instances[0].InstanceId' --output text)
```

**인스턴스 사양**:

| 항목          | 값                         | 비고                  |
| ------------- | -------------------------- | --------------------- |
| 인스턴스 타입 | t2.micro                   | 프리티어 (750시간/월) |
| AMI           | Amazon Linux 2023          | 최신 보안 패치        |
| 스토리지      | 20GB gp3 EBS               | 프리티어 30GB 이내    |
| 서브넷        | 퍼블릭 서브넷 A            | 퍼블릭 IP 자동 할당   |
| User Data     | Docker + Compose 자동 설치 | 초기 부팅 시 실행     |

### 5. EC2 User Data (부트스트랩 스크립트)

EC2 인스턴스 최초 부팅 시 자동 실행되는 초기화 스크립트를 작성했습니다.

```bash
#!/bin/bash
# user-data.sh - EC2 부트스트랩

# 시스템 업데이트
dnf update -y

# Docker 설치 및 시작
dnf install -y docker
systemctl start docker && systemctl enable docker
usermod -aG docker ec2-user

# Docker Compose V2 설치
curl -SL "https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-linux-x86_64" \
    -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# SSH 보안 강화
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart sshd
```

**User Data 자동 설치 항목**:

| 항목           | 버전              | 용도                         |
| -------------- | ----------------- | ---------------------------- |
| Docker         | Amazon Linux 기본 | 컨테이너 런타임              |
| Docker Compose | v2.27.0           | 멀티 컨테이너 오케스트레이션 |
| Git            | Amazon Linux 기본 | 프로젝트 소스 클론           |

**보안 설정 (User Data 내)**:

- SSH 비밀번호 인증 비활성화 (키 기반만 허용)
- root 로그인 차단 (`PermitRootLogin no`)
- `.env.docker` 파일 퍼미션 `600` (소유자만 읽기/쓰기)

### 6. EC2에서 백엔드 동작 확인

SSH 접속 후 Docker Compose로 맘편한 이동 백엔드를 실행하고 정상 동작을 확인했습니다.

```bash
# SSH 접속
$ ssh -i comfortablemove-key.pem ec2-user@<PUBLIC_IP>

# 프로젝트 클론 및 환경 설정
$ git clone https://github.com/<user>/dream_semester_2026_1.git ~/comfortablemove
$ cd ~/comfortablemove/backend
$ vi .env.docker  # DB 비밀번호, API 키 설정

# Docker Compose 실행
$ docker compose up -d
 Network comfortablemove_network  Created
 Volume comfortablemove_postgres_data  Created
 Volume comfortablemove_redis_data  Created
 Container comfortablemove_redis  Started
 Container comfortablemove_db  Started
 Container comfortablemove_backend  Started

# 상태 확인
$ docker compose ps
NAME                      STATUS                    PORTS
comfortablemove_backend   Up 30 seconds (healthy)   0.0.0.0:8000->8000/tcp
comfortablemove_db        Up 41 seconds (healthy)   5432/tcp
comfortablemove_redis     Up 41 seconds (healthy)   6379/tcp
```

**헬스체크 API 확인**:

```bash
$ curl http://localhost:8000/api/v1/health
{
    "status": "healthy",
    "timestamp": "2026-04-07T09:15:22.123456Z",
    "version": "1.0.0",
    "services": {
        "database": "connected",
        "redis": "connected",
        "seoul_bus_api": "reachable"
    }
}
```

로컬(5주차)에서 구동했던 것과 동일하게 EC2 환경에서도 3개 서비스가 모두 healthy로 동작하는 것을 확인했습니다.

### 7. 비용 알림 설정

AWS Budgets를 사용하여 월간 비용 알림을 설정하는 스크립트를 작성했습니다.

```bash
$ bash setup-budget-alarm.sh your@email.com
```

**알림 임계값**:

| 유형      | 임계값 | 금액 (월 $10 기준)  | 설명      |
| --------- | ------ | ------------------- | --------- |
| 실제 비용 | 50%    | $5.00 초과 시       | 조기 경고 |
| 실제 비용 | 80%    | $8.00 초과 시       | 주의 경고 |
| 실제 비용 | 100%   | $10.00 초과 시      | 한도 초과 |
| 예측 비용 | 100%   | $10.00 초과 예측 시 | 사전 예방 |

**프리티어 사용량 모니터링**:

| 서비스       | 프리티어 한도      | 현재 사용    |
| ------------ | ------------------ | ------------ |
| EC2 t2.micro | 750시간/월         | 인스턴스 1개 |
| EBS gp3      | 30GB               | 20GB         |
| 데이터 전송  | 15GB/월            | 최소 사용    |
| NAT Gateway  | ⚠️ 프리티어 미포함 | $0.059/시간  |

> **⚠️ 비용 주의**: NAT 게이트웨이는 프리티어에 포함되지 않습니다. 테스트 후 불필요 시 삭제하거나, 프라이빗 서브넷 리소스 사용 시에만 생성하는 것을 권장합니다.

### 8. GitHub Actions CI/CD 파이프라인 구축

5주차 지도교수 피드백("민감 정보 유출 방지 구조 설계")을 반영하여, AWS 자격증명과 SSH 키를 GitHub Secrets로 관리하는 CI/CD 파이프라인을 구축했습니다.

**8-1. CI 파이프라인 (자동 테스트)**

PR 생성 및 main 브랜치 push 시 자동으로 테스트를 실행합니다.

```yaml
# .github/workflows/ci.yml (핵심 부분)
name: CI - Test & Lint

on:
  pull_request:
    branches: [main]
    paths: ['backend/**']

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: comfortablemove_test
      redis:
        image: redis:7

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql+asyncpg://test_user:test_password@localhost:5432/comfortablemove_test
          REDIS_URL: redis://localhost:6379/0
          SEOUL_BUS_API_KEY: test_key_for_ci  # 테스트용 더미 키
        run: pytest tests/ -v --cov=app --cov-report=term-missing

  docker-build:
    needs: test
    steps:
      - run: docker build -t comfortablemove-backend:${{ github.sha }} ./backend
```

**CI 파이프라인 특징**:
- GitHub Actions의 `services`로 PostgreSQL/Redis 컨테이너를 자동 기동
- `paths: ['backend/**']`로 백엔드 변경 시에만 실행 (불필요한 실행 방지)
- pip 캐싱으로 의존성 설치 시간 단축
- 테스트 통과 후 Docker 이미지 빌드 검증

**8-2. CD 파이프라인 (EC2 자동 배포)**

main 브랜치에 병합 시 EC2로 자동 배포합니다.

```yaml
# .github/workflows/cd.yml (핵심 부분)
name: CD - Deploy to EC2

on:
  push:
    branches: [main]
    paths: ['backend/**']

concurrency:
  group: deploy-production
  cancel-in-progress: false

jobs:
  deploy:
    steps:
      - name: Configure SSH
        env:
          SSH_PRIVATE_KEY: ${{ secrets.EC2_SSH_PRIVATE_KEY }}
          EC2_HOST: ${{ secrets.EC2_HOST }}
        run: |
          mkdir -p ~/.ssh
          echo "${SSH_PRIVATE_KEY}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key

      - name: Deploy to EC2
        run: |
          ssh -i ~/.ssh/deploy_key ec2-user@${{ secrets.EC2_HOST }} << 'DEPLOY_SCRIPT'
            cd /home/ec2-user/comfortablemove
            git pull origin main
            cd backend
            docker compose build --no-cache backend
            docker compose up -d
            # 헬스체크 (최대 60초 대기)
            for i in $(seq 1 30); do
              curl -sf http://localhost:8000/api/v1/health && exit 0
              sleep 2
            done
            exit 1
          DEPLOY_SCRIPT

      - name: Cleanup SSH
        if: always()
        run: rm -f ~/.ssh/deploy_key
```

**CD 파이프라인 특징**:
- `concurrency` 설정으로 동시 배포 방지
- SSH 키를 GitHub Secrets에 저장하여 코드와 자격증명 완전 분리
- 배포 후 헬스체크로 정상 동작 확인 (최대 60초 대기)
- `if: always()`로 SSH 키 파일 항상 정리

**8-3. GitHub Secrets 설정 (민감 정보 관리)**

지도교수 피드백을 반영하여 모든 민감 정보를 GitHub Secrets로 관리합니다.

| Secret 이름 | 용도 | 설정 방법 |
|---|---|---|
| `EC2_SSH_PRIVATE_KEY` | EC2 SSH 접속용 프라이빗 키 | `.pem` 파일 내용 전체 |
| `EC2_HOST` | EC2 퍼블릭 IP 또는 도메인 | `x.x.x.x` |

```bash
# GitHub CLI로 Secrets 등록 (권장)
gh secret set EC2_SSH_PRIVATE_KEY < comfortablemove-key.pem
gh secret set EC2_HOST --body "x.x.x.x"
```

**보안 설계 원칙**:
- SSH 키, EC2 IP 등 민감 정보는 **코드에 절대 포함하지 않음**
- GitHub Secrets는 워크플로우 로그에서 자동 마스킹됨 (`***`로 표시)
- 배포 후 SSH 키 파일을 즉시 삭제하여 Runner에 잔류하지 않음
- CI에서 사용하는 DB 비밀번호(`test_password`)는 테스트 전용이며 프로덕션과 무관

---

## 📊 주요 성과

### 인프라 산출물

| 산출물                                    | 상태    | 설명                                    |
| ----------------------------------------- | ------- | --------------------------------------- |
| `iam/comfortablemove-ec2-policy.json`     | ✅ 신규 | EC2/VPC 관리 IAM 정책 (리전 제한)       |
| `iam/comfortablemove-billing-policy.json` | ✅ 신규 | 비용 조회 IAM 정책                      |
| `iam/setup-iam.sh`                        | ✅ 신규 | IAM 그룹/사용자/정책 자동 생성 스크립트 |
| `vpc/setup-vpc.sh`                        | ✅ 신규 | VPC 전체 인프라 구축 스크립트           |
| `ec2/setup-ec2.sh`                        | ✅ 신규 | EC2 인스턴스 및 보안 그룹 생성 스크립트 |
| `ec2/user-data.sh`                        | ✅ 신규 | EC2 부트스트랩 (Docker, 보안 설정)      |
| `scripts/setup-budget-alarm.sh`           | ✅ 신규 | AWS Budgets 비용 알림 설정 스크립트     |
| `.github/workflows/ci.yml`               | ✅ 신규 | CI 파이프라인 (자동 테스트 + 빌드)      |
| `.github/workflows/cd.yml`               | ✅ 신규 | CD 파이프라인 (EC2 자동 배포)           |

### AWS 인프라 구축 요약

| 구성 요소         | 리소스                       | 상태 |
| ----------------- | ---------------------------- | ---- |
| IAM 그룹          | `comfortablemove-developers` | ✅   |
| IAM 사용자        | `comfortablemove-deploy`     | ✅   |
| IAM 정책          | EC2/VPC + Billing (2개)      | ✅   |
| VPC               | `10.0.0.0/16` (서울 리전)    | ✅   |
| 퍼블릭 서브넷     | 2개 (AZ-a, AZ-c)             | ✅   |
| 프라이빗 서브넷   | 2개 (AZ-a, AZ-c)             | ✅   |
| 인터넷 게이트웨이 | 1개                          | ✅   |
| NAT 게이트웨이    | 1개 (AZ-a)                   | ✅   |
| EC2 인스턴스      | t2.micro, Amazon Linux 2023  | ✅   |
| 보안 그룹         | SSH(22) + API(8000), 내 IP만 | ✅   |
| 비용 알림         | 월 $10 예산, 4단계 알림      | ✅   |
| CI 파이프라인     | PR 자동 테스트 + Docker 빌드 | ✅   |
| CD 파이프라인     | main 병합 시 EC2 자동 배포   | ✅   |
| GitHub Secrets    | SSH 키, EC2 IP 관리          | ✅   |

---

## 🔧 기술 스택

**Cloud**:

- AWS (서울 리전, ap-northeast-2)
- EC2 t2.micro (Amazon Linux 2023)
- VPC, 서브넷, IGW, NAT GW

**IAM & Security**:

- 커스텀 IAM 정책 (최소 권한)
- MFA (Google Authenticator)
- 보안 그룹 (IP 기반 접근 제어)

**CI/CD**:

- GitHub Actions (CI: 자동 테스트, CD: EC2 배포)
- GitHub Secrets (자격증명 관리)

**Automation**:

- AWS CLI v2
- Bash 스크립트 (인프라 자동화)
- User Data (EC2 부트스트랩)

**Backend (EC2에서 구동)**:

- FastAPI 0.109.0 + Python 3.12
- PostgreSQL 15 + Redis 7
- Docker Compose v2

---

## 📁 프로젝트 구조 (6주차 추가 파일)

```
infra/
└── aws/
    ├── iam/
    │   ├── comfortablemove-ec2-policy.json    # ✅ 신규 - EC2/VPC IAM 정책
    │   ├── comfortablemove-billing-policy.json # ✅ 신규 - 비용 조회 IAM 정책
    │   └── setup-iam.sh                       # ✅ 신규 - IAM 자동 설정 스크립트
    ├── vpc/
    │   ├── setup-vpc.sh                       # ✅ 신규 - VPC 구축 스크립트
    │   └── vpc-outputs.env                    # (자동 생성) VPC 리소스 ID
    ├── ec2/
    │   ├── setup-ec2.sh                       # ✅ 신규 - EC2 생성 스크립트
    │   ├── user-data.sh                       # ✅ 신규 - EC2 부트스트랩
    │   └── ec2-outputs.env                    # (자동 생성) EC2 리소스 ID
    └── scripts/
        └── setup-budget-alarm.sh              # ✅ 신규 - 비용 알림 스크립트

.github/
└── workflows/
    ├── ci.yml                                 # ✅ 신규 - CI (자동 테스트 + Docker 빌드)
    └── cd.yml                                 # ✅ 신규 - CD (EC2 자동 배포)

docs/
└── week6/
    └── week6_activity_report.md               # ✅ 신규 - 6주차 활동 보고서
```

---

## 💡 배운 점

### 1. IAM 최소 권한 원칙의 실제 적용

`AdministratorAccess`를 부여하면 편하지만, 실수로 리소스를 삭제하거나 Access Key 유출 시 피해가 커집니다. 커스텀 정책으로 필요한 액션만 허용하고, `Condition`으로 리전을 제한하면 실수의 범위를 최소화할 수 있습니다. 정책을 작성하면서 AWS의 IAM Policy Simulator로 권한을 검증하는 방법도 학습했습니다.

### 2. VPC 퍼블릭/프라이빗 서브넷의 차이

처음에는 "왜 프라이빗 서브넷이 필요한가?"를 이해하지 못했습니다. 핵심은 **인터넷에서 직접 접근 가능 여부**입니다:

- 퍼블릭 서브넷: 인터넷 게이트웨이를 통해 양방향 통신 가능 → EC2 백엔드 배치
- 프라이빗 서브넷: 외부에서 접근 불가, NAT GW를 통해 아웃바운드만 가능 → DB, 캐시 배치

데이터베이스를 프라이빗 서브넷에 두면 외부에서 직접 접속할 수 없으므로, 보안 그룹만으로 방어하는 것보다 한 단계 더 안전합니다.

### 3. NAT 게이트웨이의 역할과 비용

프라이빗 서브넷의 리소스가 인터넷에 접근해야 할 때(패키지 업데이트 등) NAT 게이트웨이가 필요합니다. 하지만 시간당 $0.059 + 데이터 처리 비용이 발생하므로, 프리티어 프로젝트에서는 비용 대비 효용을 따져야 합니다. 현재는 프라이빗 서브넷에 리소스가 없으므로, 학습 후 삭제하여 비용을 절감했습니다.

### 4. 보안 그룹과 NACL의 차이

| 항목      | 보안 그룹                 | NACL                          |
| --------- | ------------------------- | ----------------------------- |
| 적용 대상 | 인스턴스(ENI) 단위        | 서브넷 단위                   |
| 상태      | Stateful (응답 자동 허용) | Stateless (인/아웃 별도 규칙) |
| 기본 규칙 | 모든 인바운드 차단        | 모든 트래픽 허용              |
| 우선순위  | 모든 규칙 평가            | 번호순 평가                   |

이번 프로젝트에서는 보안 그룹만 사용했지만, 서브넷 레벨에서 추가 방어가 필요할 때 NACL을 활용할 수 있다는 것을 학습했습니다.

### 5. 자격증명 관리의 중요성 (지도교수 피드백 반영)

AWS Access Key가 GitHub에 커밋되면 수분 내에 악용될 수 있습니다. 이를 방지하기 위해:

- Access Key는 `aws configure --profile`로 로컬에만 저장
- `.pem` 키페어와 `*-outputs.env`를 `.gitignore`에 등록
- 향후 CI/CD에서는 GitHub Secrets를 사용하여 코드와 자격증명을 완전히 분리할 계획입니다

---

## 🔄 다음 주 (7주차) 계획

### 1. 인프라 고도화

- ALB(Application Load Balancer) 도입으로 EC2 직접 노출 제거
- HTTPS 인증서 (ACM) 적용으로 통신 암호화
- 프라이빗 서브넷에 RDS 배치하여 DB 보안 강화

### 2. Terraform 전환

- 현재 AWS CLI 스크립트를 Terraform으로 전환
- 인프라 상태 관리 및 변경 추적 자동화
- `terraform plan` / `terraform apply` 기반 워크플로우

### 3. 모니터링 구축

- CloudWatch 기반 EC2/컨테이너 메트릭 수집
- 로그 중앙화 (CloudWatch Logs)
- 알림 설정 (CPU, 메모리, 헬스체크 실패)

---

## 📝 회고

### 잘한 점

1. **AWS CLI 기반 자동화**: 콘솔 클릭 대신 모든 인프라를 AWS CLI 스크립트로 구축하여 재현 가능성을 확보했다. 스크립트를 Git으로 관리하면 인프라 변경 이력도 추적할 수 있다.
2. **최소 권한 원칙 적용**: `AdministratorAccess` 대신 커스텀 정책으로 필요한 권한만 부여하고, 리전 조건으로 범위를 제한했다.
3. **보안 그룹 최소 오픈**: SSH와 API 포트만 현재 IP에서 허용하여, 불필요한 포트 노출을 방지했다.
4. **비용 관리 체계 수립**: 4단계 Budget 알림으로 프리티어 초과를 사전에 감지할 수 있도록 설정했다.
5. **지도교수 피드백 반영**: 민감 정보 관리 체계를 수립하고, `.gitignore` 등록, 환경변수 분리, GitHub Secrets를 통한 자격증명 관리를 구현했다.
6. **CI/CD 파이프라인 구축**: PR 시 자동 테스트 + Docker 빌드 검증, main 병합 시 EC2 자동 배포까지 전체 파이프라인을 완성했다.

### 아쉬운 점

1. **NAT 게이트웨이 비용**: 학습 목적으로 생성했으나 프리티어에 미포함되어 과금 발생 가능성이 있다. 실습 후 즉시 삭제하는 습관이 필요하다.
2. **도메인 미연결**: EC2 퍼블릭 IP로 직접 접근하는 구조로, HTTPS나 도메인 연결은 아직 미설정이다.
3. **단일 AZ 구성**: EC2가 AZ-a에만 배치되어 있어 가용성 측면에서 개선이 필요하다. 향후 ALB + 다중 AZ 구성을 검토할 예정이다.

### 개선 방향

1. GitHub Actions CI/CD 파이프라인에서 AWS 배포 자동화
2. ALB + HTTPS 구성으로 프로덕션 수준 아키텍처 개선
3. 프라이빗 서브넷에 RDS를 배치하여 DB 보안 강화
4. Terraform으로 인프라를 코드화하여 관리 효율성 향상

---

## 🎯 총 투입 시간

**예상**: 주 25시간
**실제**: 약 28시간

**상세**:

- AWS 계정 생성 및 루트 보안 설정 (MFA): 2시간
- IAM 학습 및 정책 설계/스크립트 작성: 4시간
- VPC 개념 학습 (서브넷, 라우팅, IGW, NAT): 4시간
- VPC 아키텍처 설계 및 CLI 스크립트 작성: 4시간
- EC2 인스턴스 생성 및 보안 그룹 설정: 3시간
- User Data 부트스트랩 스크립트 작성: 2시간
- EC2에서 백엔드 Docker Compose 실행 검증: 2시간
- GitHub Actions CI/CD 파이프라인 구축: 3시간
- 비용 알림 설정 및 프리티어 분석: 1시간
- 보고서 작성: 3시간

---

## 📌 참고 자료

- [AWS IAM 모범 사례](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [AWS VPC 사용 설명서](https://docs.aws.amazon.com/vpc/latest/userguide/)
- [EC2 인스턴스 시작하기](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html)
- [AWS Budgets 사용 설명서](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)
- [AWS CLI v2 명령어 레퍼런스](https://docs.aws.amazon.com/cli/latest/reference/)
- [AWS 프리 티어](https://aws.amazon.com/free/)
- [GitHub Actions 공식 문서](https://docs.github.com/en/actions)
- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

---

**작성일**: 2026년 4월 7일
**작성자**: 박성근
