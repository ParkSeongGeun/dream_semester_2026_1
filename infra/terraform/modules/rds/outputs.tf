output "endpoint" {
  description = "RDS 엔드포인트"
  value       = aws_db_instance.main.endpoint
}

output "db_name" {
  description = "데이터베이스 이름"
  value       = aws_db_instance.main.db_name
}

output "db_instance_id" {
  description = "RDS 인스턴스 식별자"
  value       = aws_db_instance.main.identifier
}
