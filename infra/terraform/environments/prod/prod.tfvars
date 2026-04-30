# =============================================================
# PROD Environment - 환경별 기본 설정 값
# =============================================================
# 사용법: terraform plan -var-file=prod.tfvars
# 비밀값(aws_*, db_password, my_ip, notification_email)은
# 별도 terraform.tfvars 또는 환경변수(TF_VAR_*) 로 주입할 것.
# =============================================================

project_name = "comfortablemove"
aws_region   = "ap-northeast-2"

# 인스턴스 타입: 운영 사양
ec2_instance_type = "t3.small"
db_instance_class = "db.t3.small"

# 가용성 (비용 고려시 false 유지)
db_multi_az        = false
enable_nat_gateway = false

# 네트워크: prod 전용 대역
vpc_cidr             = "10.20.0.0/16"
public_subnet_cidrs  = ["10.20.1.0/24", "10.20.2.0/24"]
private_subnet_cidrs = ["10.20.11.0/24", "10.20.12.0/24"]
availability_zones   = ["ap-northeast-2a", "ap-northeast-2c"]

# DB
db_name     = "comfortablemove"
db_username = "cmadmin"

# S3
s3_bucket_name = "comfortablemove-assets"

# Domain
domain_name = "comfortablemove.com"

# Budget
budget_limit = "30.0"
