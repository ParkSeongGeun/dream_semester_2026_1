# =============================================================
# ComfortableMove - Terraform Root Configuration
# =============================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# =============================================================
# Modules
# =============================================================

# --- 1. Network (VPC, Subnets, IGW, NAT GW) ---
module "network" {
  source = "./modules/network"

  project_name         = var.project_name
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  availability_zones   = var.availability_zones
  enable_nat_gateway   = var.enable_nat_gateway
}

# --- 2. Security (Security Groups) ---
module "security" {
  source = "./modules/security"

  project_name = var.project_name
  vpc_id       = module.network.vpc_id
  my_ip        = var.my_ip
}

# --- 3. Storage (S3) ---
module "storage" {
  source = "./modules/storage"

  s3_bucket_name = var.s3_bucket_name
}

# --- 4. Compute (EC2) ---
module "compute" {
  source = "./modules/compute"

  project_name        = var.project_name
  ec2_instance_type   = var.ec2_instance_type
  ssh_public_key_path = var.ssh_public_key_path
  public_subnet_ids   = module.network.public_subnet_ids
  ec2_sg_id           = module.security.ec2_sg_id
  s3_bucket_arn       = module.storage.bucket_arn
}

# --- 5. RDS (PostgreSQL) ---
module "rds" {
  source = "./modules/rds"

  project_name       = var.project_name
  db_instance_class  = var.db_instance_class
  db_name            = var.db_name
  db_username        = var.db_username
  db_password        = var.db_password
  db_multi_az        = var.db_multi_az
  private_subnet_ids = module.network.private_subnet_ids
  rds_sg_id          = module.security.rds_sg_id
}

# --- 6. Ingress (ALB) ---
module "ingress" {
  source = "./modules/ingress"

  project_name      = var.project_name
  vpc_id            = module.network.vpc_id
  public_subnet_ids = module.network.public_subnet_ids
  alb_sg_id         = module.security.alb_sg_id
  instance_id       = module.compute.instance_id
  certificate_arn   = module.dns.certificate_arn
}

# --- 7. DNS (Route53 + ACM) ---
module "dns" {
  source = "./modules/dns"

  project_name = var.project_name
  domain_name  = var.domain_name
  alb_dns_name = module.ingress.alb_dns_name
  alb_zone_id  = module.ingress.alb_zone_id
}

# --- 8. Monitoring (Budgets + CloudWatch) ---
module "monitoring" {
  source = "./modules/monitoring"

  project_name            = var.project_name
  aws_region              = var.aws_region
  budget_limit            = var.budget_limit
  notification_email      = var.notification_email
  instance_id             = module.compute.instance_id
  alb_arn_suffix          = module.ingress.alb_arn_suffix
  target_group_arn_suffix = module.ingress.target_group_arn_suffix
  db_instance_id          = module.rds.db_instance_id
}
