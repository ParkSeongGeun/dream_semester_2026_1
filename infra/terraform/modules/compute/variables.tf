variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "ec2_instance_type" {
  description = "EC2 인스턴스 타입"
  type        = string
}

variable "ssh_public_key_path" {
  description = "SSH 공개키 파일 경로"
  type        = string
}

variable "public_subnet_ids" {
  description = "퍼블릭 서브넷 ID 목록"
  type        = list(string)
}

variable "ec2_sg_id" {
  description = "EC2 보안 그룹 ID"
  type        = string
}

variable "s3_bucket_arn" {
  description = "S3 버킷 ARN (IAM 정책용)"
  type        = string
}
