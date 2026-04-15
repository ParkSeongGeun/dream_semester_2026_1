variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "퍼블릭 서브넷 ID 목록"
  type        = list(string)
}

variable "alb_sg_id" {
  description = "ALB 보안 그룹 ID"
  type        = string
}

variable "instance_id" {
  description = "EC2 인스턴스 ID"
  type        = string
}

variable "certificate_arn" {
  description = "ACM 인증서 ARN"
  type        = string
}
