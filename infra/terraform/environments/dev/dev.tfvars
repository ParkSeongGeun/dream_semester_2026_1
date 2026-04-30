# =============================================================
# DEV Environment - 환경별 기본 설정 값
# =============================================================
# 사용법: terraform plan -var-file=dev.tfvars
# 비밀값(aws_*, db_password, my_ip)은 별도 terraform.tfvars 또는
# 환경변수(TF_VAR_*) 로 주입할 것.
# =============================================================

project_name = "comfortablemove"
aws_region   = "ap-northeast-2"

# 인스턴스 타입: 최소 사양
ec2_instance_type = "t3.micro"
db_instance_class = "db.t3.micro"

# 네트워크: dev 전용 대역
vpc_cidr             = "10.10.0.0/16"
public_subnet_cidrs  = ["10.10.1.0/24", "10.10.2.0/24"]
private_subnet_cidrs = ["10.10.11.0/24", "10.10.12.0/24"]
availability_zones   = ["ap-northeast-2a", "ap-northeast-2c"]

# DB
db_name     = "comfortablemove_dev"
db_username = "cmadmin"

# S3 (전역 고유, 환경 접미사는 main.tf 에서 자동 부여)
s3_bucket_name = "comfortablemove-assets"
