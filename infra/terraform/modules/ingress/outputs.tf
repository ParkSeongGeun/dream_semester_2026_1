output "alb_dns_name" {
  description = "ALB DNS 이름"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "ALB 호스팅 영역 ID"
  value       = aws_lb.main.zone_id
}

output "alb_arn_suffix" {
  description = "ALB ARN suffix (CloudWatch용)"
  value       = aws_lb.main.arn_suffix
}

output "target_group_arn_suffix" {
  description = "Target Group ARN suffix (CloudWatch용)"
  value       = aws_lb_target_group.main.arn_suffix
}
