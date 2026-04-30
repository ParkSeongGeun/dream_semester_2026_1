# ComfortableMove - Terraform 인프라

AWS 인프라를 코드로 관리하기 위한 Terraform 구성. 모듈화된 구조와 dev/prod 환경 분리를 채택.

## 디렉토리 구조

```
infra/terraform/
├── modules/                  # 재사용 가능한 모듈 (역할별 분리)
│   ├── network/              # VPC, Subnet, IGW, NAT GW, Route Table
│   ├── security/             # ALB/EC2/RDS Security Group
│   ├── storage/              # S3 (versioning, encryption, CORS)
│   ├── compute/              # EC2 + IAM + Key Pair + EIP
│   ├── rds/                  # PostgreSQL 15
│   ├── ingress/              # Application Load Balancer + HTTPS Listener
│   ├── dns/                  # Route53 + ACM 인증서
│   └── monitoring/           # CloudWatch Alarms + Dashboard + Budgets
├── environments/             # 환경별 진입점
│   ├── dev/                  # 개발 환경 (t3.micro, Single-AZ, NAT 비활성)
│   └── prod/                 # 운영 환경 (t3.small, ALB+DNS+모니터링)
├── main.tf                   # (legacy) 단일 환경 루트 — 호환성 유지
├── variables.tf
├── outputs.tf
└── README.md
```

## 모듈 의존성

```
network ─┬─> security ─┬─> compute ──┐
         │             ├─> rds       │
         │             └─> ingress <─┤
         └─> ingress                 │
storage ─────────────────> compute   │
                                     │
ingress ──> dns ──> ingress (cert)   │
ingress ──┬──────────────────────────> monitoring
compute ──┤
rds ──────┘
```

## 환경별 차이

| 항목 | dev | prod |
|------|-----|------|
| EC2 인스턴스 | t3.micro | t3.small |
| RDS 인스턴스 | db.t3.micro | db.t3.small |
| Multi-AZ | 비활성 | 옵션 (기본 false) |
| NAT Gateway | 비활성 | 옵션 (기본 false) |
| ALB / DNS / 모니터링 | 미포함 | 포함 |
| VPC CIDR | 10.10.0.0/16 | 10.20.0.0/16 |
| 예산 | - | $30/월 |

## 사용법

### 1. 환경 선택 후 디렉토리 진입

```bash
# 개발
cd environments/dev

# 운영
cd environments/prod
```

### 2. 시크릿 값 설정

`terraform.tfvars.example` 를 `terraform.tfvars` 로 복사 후 시크릿 값 채움.
또는 환경변수 사용: `export TF_VAR_db_password=...`

### 3. 초기화 / 계획 / 적용

```bash
terraform init
terraform fmt -recursive ../..
terraform validate

# dev
terraform plan -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars

# prod
terraform plan -var-file=prod.tfvars
terraform apply -var-file=prod.tfvars
```

### 4. 출력 확인

```bash
terraform output
terraform output -raw rds_endpoint
```

## Terraform 패턴

- **locals**: 환경별 공통 태그(`common_tags`), 이름 prefix(`name_prefix`) 계산
- **for_each**: `network` 모듈의 서브넷 생성에 적용 — AZ 키 기반 안정적 식별
- **count**: NAT Gateway 등 조건부 리소스 (`enable_nat_gateway ? 1 : 0`)
- **default_tags**: provider 레벨에서 모든 리소스에 자동 태깅

## 모듈 추가/수정 가이드

1. `modules/<name>/main.tf, variables.tf, outputs.tf` 작성
2. `modules/<name>/README.md` 에 입력/출력/예시 명시
3. 각 환경(`environments/*/main.tf`)에서 `module "<name>" { source = "../../modules/<name>" }` 호출
