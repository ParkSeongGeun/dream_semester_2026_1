# Environments

dev / prod 환경 분리 디렉토리. 동일한 `modules/*` 를 재사용하되 환경별 변수 값으로 차별화.

## 빠른 시작

```bash
cd environments/dev   # 또는 environments/prod
cp terraform.tfvars.example terraform.tfvars
# terraform.tfvars 의 비밀값 채움
terraform init
terraform plan -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars
```

## 환경 비교

| 항목 | dev/ | prod/ |
|------|------|-------|
| 모듈 포함 | network, security, storage, compute, rds | + ingress, dns, monitoring |
| 인스턴스 | t3.micro / db.t3.micro | t3.small / db.t3.small |
| Multi-AZ | × | 옵션 |
| HTTPS/도메인 | × | ✓ |
| 모니터링 | × | ✓ (CloudWatch + Budget) |

## 시크릿 분리 원칙

- `*.tfvars` 는 일반 설정만 (git 관리)
- `terraform.tfvars` 는 시크릿 (gitignore)
- 또는 `TF_VAR_<name>` 환경변수로 주입
