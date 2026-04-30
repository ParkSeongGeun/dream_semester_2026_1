# =============================================================
# DEV Environment - Outputs
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
