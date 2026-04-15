variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "domain_name" {
  description = "도메인 이름"
  type        = string
}

variable "alb_dns_name" {
  description = "ALB DNS 이름"
  type        = string
}

variable "alb_zone_id" {
  description = "ALB 호스팅 영역 ID"
  type        = string
}
