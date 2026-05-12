variable "project_name" {
  description = "프로젝트 이름 (prefix)"
  type        = string
}

variable "kubernetes_version" {
  description = "EKS Kubernetes 버전"
  type        = string
  default     = "1.29"
}

variable "private_subnet_ids" {
  description = "EKS 노드 그룹 배치용 프라이빗 서브넷 ID 목록"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "EKS 컨트롤 플레인 + LB 배치용 퍼블릭 서브넷 ID 목록"
  type        = list(string)
}

variable "node_instance_types" {
  description = "노드 그룹 인스턴스 타입"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  description = "노드 그룹 기본 수"
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "노드 그룹 최소 수"
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "노드 그룹 최대 수"
  type        = number
  default     = 3
}
