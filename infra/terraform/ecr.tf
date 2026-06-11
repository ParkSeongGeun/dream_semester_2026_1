# =============================================================
# ECR - 백엔드 컨테이너 이미지 레지스트리
# CI(GitHub Actions) build-and-push job 의 푸시 대상
# =============================================================

data "aws_caller_identity" "current" {}

resource "aws_ecr_repository" "backend" {
  name                 = "comfortablemove-backend"
  image_tag_mutability = "MUTABLE"
  force_delete         = true # 학습용: destroy 시 이미지까지 정리

  image_scanning_configuration {
    scan_on_push = true
  }
}

# 오래된 이미지 자동 정리 (최근 10개만 유지)
resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

output "ecr_registry" {
  description = "ECR 레지스트리 URL (GitHub Secret ECR_REGISTRY 용)"
  value       = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com"
}

output "ecr_repository_url" {
  description = "ECR 리포지토리 URL"
  value       = aws_ecr_repository.backend.repository_url
}
