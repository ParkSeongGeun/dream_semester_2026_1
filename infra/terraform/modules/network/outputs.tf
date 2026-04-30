output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "퍼블릭 서브넷 ID 목록"
  value       = [for s in aws_subnet.public : s.id]
}

output "private_subnet_ids" {
  description = "프라이빗 서브넷 ID 목록"
  value       = [for s in aws_subnet.private : s.id]
}

output "public_subnet_map" {
  description = "AZ → 퍼블릭 서브넷 ID 매핑"
  value       = { for az, s in aws_subnet.public : az => s.id }
}

output "private_subnet_map" {
  description = "AZ → 프라이빗 서브넷 ID 매핑"
  value       = { for az, s in aws_subnet.private : az => s.id }
}
