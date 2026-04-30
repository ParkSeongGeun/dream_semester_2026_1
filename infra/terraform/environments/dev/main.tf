# =============================================================
# ComfortableMove - DEV Environment
# =============================================================
# 개발 환경: 최소 사양, 비용 최적화 (NAT 비활성, Single-AZ)
# =============================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # 원격 상태 저장소 (선택적, S3 백엔드 사용 시 주석 해제)
  # backend "s3" {
  #   bucket         = "comfortablemove-tfstate"
  #   key            = "dev/terraform.tfstate"
  #   region         = "ap-northeast-2"
  #   dynamodb_table = "comfortablemove-tflock"
  #   encrypt        = true
  # }
}

# =============================================================
# Locals - 환경별 공통 값 계산
# =============================================================
locals {
  environment = "dev"
  name_prefix = "${var.project_name}-${local.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = local.environment
    ManagedBy   = "terraform"
    Owner       = "dream-semester"
    CostCenter  = "development"
  }
}

provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key

  default_tags {
    tags = local.common_tags
  }
}

# =============================================================
# Modules - 모듈 호출 (modules/* 재사용)
# =============================================================

module "network" {
  source = "../../modules/network"

  project_name         = local.name_prefix
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  availability_zones   = var.availability_zones
  enable_nat_gateway   = false # dev: NAT 비활성 (비용 절감)
}

module "security" {
  source = "../../modules/security"

  project_name = local.name_prefix
  vpc_id       = module.network.vpc_id
  my_ip        = var.my_ip
}

module "storage" {
  source = "../../modules/storage"

  s3_bucket_name = "${var.s3_bucket_name}-${local.environment}"
}

module "compute" {
  source = "../../modules/compute"

  project_name        = local.name_prefix
  ec2_instance_type   = var.ec2_instance_type # dev: t3.micro
  ssh_public_key_path = var.ssh_public_key_path
  public_subnet_ids   = module.network.public_subnet_ids
  ec2_sg_id           = module.security.ec2_sg_id
  s3_bucket_arn       = module.storage.bucket_arn
}

module "rds" {
  source = "../../modules/rds"

  project_name       = local.name_prefix
  db_instance_class  = var.db_instance_class # dev: db.t3.micro
  db_name            = var.db_name
  db_username        = var.db_username
  db_password        = var.db_password
  db_multi_az        = false # dev: Single-AZ
  private_subnet_ids = module.network.private_subnet_ids
  rds_sg_id          = module.security.rds_sg_id
}
