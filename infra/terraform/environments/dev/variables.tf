# =============================================================
# DEV Environment - Variables
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
  default     = "10.10.0.0/16" # dev 전용 대역
}

variable "public_subnet_cidrs" {
  description = "퍼블릭 서브넷 CIDR"
  type        = list(string)
  default     = ["10.10.1.0/24", "10.10.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "프라이빗 서브넷 CIDR"
  type        = list(string)
  default     = ["10.10.11.0/24", "10.10.12.0/24"]
}

variable "availability_zones" {
  description = "가용영역"
  type        = list(string)
  default     = ["ap-northeast-2a", "ap-northeast-2c"]
}

# --- EC2 ---
variable "ec2_instance_type" {
  description = "EC2 인스턴스 타입 (dev=t3.micro)"
  type        = string
  default     = "t3.micro"
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
  description = "RDS 인스턴스 클래스 (dev=db.t3.micro)"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "DB 이름"
  type        = string
  default     = "comfortablemove_dev"
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

# --- S3 ---
variable "s3_bucket_name" {
  description = "S3 버킷 이름 (전역 고유)"
  type        = string
  default     = "comfortablemove-assets"
}
