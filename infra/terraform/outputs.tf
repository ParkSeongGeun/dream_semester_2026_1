# =============================================================
# ComfortableMove - Root Outputs
# =============================================================

# --- Network ---
output "vpc_id" {
  description = "VPC ID"
  value       = module.network.vpc_id
}

# --- Compute ---
output "ec2_public_ip" {
  description = "EC2 퍼블릭 IP"
  value       = module.compute.public_ip
}

# --- RDS ---
output "rds_endpoint" {
  description = "RDS 엔드포인트"
  value       = module.rds.endpoint
}

# --- Ingress ---
output "alb_dns_name" {
  description = "ALB DNS 이름"
  value       = module.ingress.alb_dns_name
}

# --- Storage ---
output "s3_bucket_name" {
  description = "S3 버킷 이름"
  value       = module.storage.bucket_name
}

# --- DNS ---
output "nameservers" {
  description = "Route53 네임서버 (도메인 등록기관에 설정)"
  value       = module.dns.nameservers
}

# --- Monitoring ---
output "budget_name" {
  description = "Budget 이름"
  value       = module.monitoring.budget_name
}
