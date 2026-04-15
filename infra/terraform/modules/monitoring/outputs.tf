output "budget_name" {
  description = "Budget 이름"
  value       = aws_budgets_budget.monthly.name
}

output "dashboard_name" {
  description = "CloudWatch 대시보드 이름"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "sns_topic_arn" {
  description = "알림 SNS Topic ARN"
  value       = aws_sns_topic.alerts.arn
}
