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

output "eks_cluster_name" {
  description = "EKS 클러스터 이름"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS API 서버 엔드포인트"
  value       = module.eks.cluster_endpoint
}

output "eks_kubeconfig_command" {
  description = "kubeconfig 업데이트 명령어"
  value       = "aws eks update-kubeconfig --region ap-northeast-2 --name ${module.eks.cluster_name}"
}
