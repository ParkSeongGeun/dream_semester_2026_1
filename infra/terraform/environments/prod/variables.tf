# =============================================================
# PROD Environment - Variables
# =============================================================

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
  default     = "comfortablemove"
}

variable "aws_region" {
  description = "AWS 리전"
  type        = string
  default     = "ap-northeast-2"
}

variable "aws_access_key" {
  description = "AWS Access Key ID"
  type        = string
  sensitive   = true
}

variable "aws_secret_key" {
  description = "AWS Secret Access Key"
  type        = string
  sensitive   = true
}

# --- Network ---
variable "vpc_cidr" {
  description = "VPC CIDR"
  type        = string
  default     = "10.20.0.0/16" # prod 전용 대역
}

variable "public_subnet_cidrs" {
  description = "퍼블릭 서브넷 CIDR"
  type        = list(string)
  default     = ["10.20.1.0/24", "10.20.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "프라이빗 서브넷 CIDR"
  type        = list(string)
  default     = ["10.20.11.0/24", "10.20.12.0/24"]
}

variable "availability_zones" {
  description = "가용영역"
  type        = list(string)
  default     = ["ap-northeast-2a", "ap-northeast-2c"]
}

variable "enable_nat_gateway" {
  description = "NAT 게이트웨이 활성 여부 (prod 권장: true, 비용 고려시 false)"
  type        = bool
  default     = false
}

# --- EC2 ---
variable "ec2_instance_type" {
  description = "EC2 인스턴스 타입 (prod=t3.small)"
  type        = string
  default     = "t3.small"
}

variable "ssh_public_key_path" {
  description = "SSH 공개키 경로"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "my_ip" {
  description = "SSH 허용 IP CIDR"
  type        = string
}

# --- RDS ---
variable "db_instance_class" {
  description = "RDS 인스턴스 클래스 (prod=db.t3.small)"
  type        = string
  default     = "db.t3.small"
}

variable "db_name" {
  description = "DB 이름"
  type        = string
  default     = "comfortablemove"
}

variable "db_username" {
  description = "DB 마스터 사용자명"
  type        = string
  default     = "cmadmin"
}

variable "db_password" {
  description = "DB 마스터 비밀번호"
  type        = string
  sensitive   = true
}

variable "db_multi_az" {
  description = "Multi-AZ 배포 (prod 권장: true)"
  type        = bool
  default     = false
}

# --- S3 ---
variable "s3_bucket_name" {
  description = "S3 버킷 이름"
  type        = string
  default     = "comfortablemove-assets"
}

# --- Domain ---
variable "domain_name" {
  description = "도메인 이름"
  type        = string
  default     = "comfortablemove.com"
}

# --- Budget ---
variable "budget_limit" {
  description = "월간 예산 한도 (USD)"
  type        = string
  default     = "30.0"
}

variable "notification_email" {
  description = "비용/알람 수신 이메일"
  type        = string
}
