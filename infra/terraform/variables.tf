# =============================================================
# ComfortableMove - Variables
# =============================================================

# --- General ---
variable "project_name" {
  description = "프로젝트 이름"
  type        = string
  default     = "comfortablemove"
}

variable "environment" {
  description = "환경 (production, staging, development)"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS 리전"
  type        = string
  default     = "ap-northeast-2"
}

# --- AWS Credentials ---
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
  description = "VPC CIDR 블록"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "퍼블릭 서브넷 CIDR 목록"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "프라이빗 서브넷 CIDR 목록"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "availability_zones" {
  description = "가용영역 목록"
  type        = list(string)
  default     = ["ap-northeast-2a", "ap-northeast-2c"]
}

variable "enable_nat_gateway" {
  description = "NAT 게이트웨이 생성 여부 (프리티어 미포함, 시간당 $0.059)"
  type        = bool
  default     = false
}

# --- EC2 ---
variable "ec2_instance_type" {
  description = "EC2 인스턴스 타입"
  type        = string
  default     = "t2.micro"
}

variable "ssh_public_key_path" {
  description = "SSH 공개키 파일 경로"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "my_ip" {
  description = "SSH 접근 허용 IP (CIDR, 예: 1.2.3.4/32)"
  type        = string
}

# --- RDS ---
variable "db_instance_class" {
  description = "RDS 인스턴스 클래스"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "데이터베이스 이름"
  type        = string
  default     = "comfortablemove"
}

variable "db_username" {
  description = "데이터베이스 마스터 사용자명"
  type        = string
  default     = "cmadmin"
}

variable "db_password" {
  description = "데이터베이스 마스터 비밀번호 (최소 8자)"
  type        = string
  sensitive   = true
}

variable "db_multi_az" {
  description = "RDS Multi-AZ 배포 (프리티어는 Single-AZ만 무료)"
  type        = bool
  default     = false
}

# --- S3 ---
variable "s3_bucket_name" {
  description = "S3 버킷 이름 (전역 고유)"
  type        = string
  default     = "comfortablemove-assets"
}

# --- Budget ---
variable "budget_limit" {
  description = "월간 예산 한도 (USD)"
  type        = string
  default     = "10.0"
}

variable "notification_email" {
  description = "비용 알림 수신 이메일"
  type        = string
}

# --- Domain ---
variable "domain_name" {
  description = "도메인 이름"
  type        = string
  default     = "comfortablemove.com"
}
