variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "db_instance_class" {
  description = "RDS 인스턴스 클래스"
  type        = string
}

variable "db_name" {
  description = "데이터베이스 이름"
  type        = string
}

variable "db_username" {
  description = "마스터 사용자명"
  type        = string
}

variable "db_password" {
  description = "마스터 비밀번호"
  type        = string
  sensitive   = true
}

variable "db_multi_az" {
  description = "Multi-AZ 배포 여부"
  type        = bool
  default     = false
}

variable "private_subnet_ids" {
  description = "프라이빗 서브넷 ID 목록"
  type        = list(string)
}

variable "rds_sg_id" {
  description = "RDS 보안 그룹 ID"
  type        = string
}
