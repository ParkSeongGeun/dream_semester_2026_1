output "instance_id" {
  description = "EC2 인스턴스 ID"
  value       = aws_instance.main.id
}

output "public_ip" {
  description = "EC2 퍼블릭 IP (Elastic IP)"
  value       = aws_eip.main.public_ip
}
