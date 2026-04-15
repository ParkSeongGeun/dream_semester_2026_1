variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "aws_region" {
  description = "AWS 리전"
  type        = string
}

variable "budget_limit" {
  description = "월간 예산 한도 (USD)"
  type        = string
}

variable "notification_email" {
  description = "비용 알림 수신 이메일"
  type        = string
}

variable "instance_id" {
  description = "EC2 인스턴스 ID"
  type        = string
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix (CloudWatch 차원용)"
  type        = string
}

variable "target_group_arn_suffix" {
  description = "Target Group ARN suffix"
  type        = string
}

variable "db_instance_id" {
  description = "RDS 인스턴스 식별자"
  type        = string
}
