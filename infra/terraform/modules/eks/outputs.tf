output "cluster_name" {
  description = "EKS 클러스터 이름"
  value       = aws_eks_cluster.this.name
}

output "cluster_endpoint" {
  description = "EKS API 서버 엔드포인트"
  value       = aws_eks_cluster.this.endpoint
}

output "cluster_ca_certificate" {
  description = "EKS 클러스터 CA 인증서 (base64)"
  value       = aws_eks_cluster.this.certificate_authority[0].data
  sensitive   = true
}

output "node_group_role_arn" {
  description = "노드 그룹 IAM 역할 ARN"
  value       = aws_iam_role.node_group.arn
}
