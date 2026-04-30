# =============================================================
# PROD Environment - Outputs
# =============================================================

output "environment" {
  description = "환경 이름"
  value       = local.environment
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.network.vpc_id
}

output "ec2_public_ip" {
  description = "EC2 퍼블릭 IP"
  value       = module.compute.public_ip
}

output "rds_endpoint" {
  description = "RDS 엔드포인트"
  value       = module.rds.endpoint
  sensitive   = true
}

output "s3_bucket_name" {
  description = "S3 버킷 이름"
  value       = module.storage.bucket_name
}

output "alb_dns_name" {
  description = "ALB DNS 이름"
  value       = module.ingress.alb_dns_name
}

output "nameservers" {
  description = "Route53 네임서버"
  value       = module.dns.nameservers
}

output "budget_name" {
  description = "Budget 이름"
  value       = module.monitoring.budget_name
}
