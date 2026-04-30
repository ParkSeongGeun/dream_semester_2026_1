# =============================================================
# Network Module - VPC, Subnets, IGW, NAT GW, Route Tables
# =============================================================
# locals: 공통 태그/이름 계산
# for_each: 가용영역 키로 서브넷 생성 (인덱스 변경에 안전)
# =============================================================

locals {
  # 가용영역을 키로 하는 서브넷 매핑
  public_subnets = {
    for i, az in var.availability_zones : az => {
      cidr = var.public_subnet_cidrs[i]
      name = "${var.project_name}-public-${az}"
    }
  }

  private_subnets = {
    for i, az in var.availability_zones : az => {
      cidr = var.private_subnet_cidrs[i]
      name = "${var.project_name}-private-${az}"
    }
  }
}

# --- VPC ---
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${var.project_name}-vpc" }
}

# --- Internet Gateway ---
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = { Name = "${var.project_name}-igw" }
}

# --- Public Subnets (for_each) ---
resource "aws_subnet" "public" {
  for_each = local.public_subnets

  vpc_id                  = aws_vpc.main.id
  cidr_block              = each.value.cidr
  availability_zone       = each.key
  map_public_ip_on_launch = true

  tags = { Name = each.value.name }
}

# --- Private Subnets (for_each) ---
resource "aws_subnet" "private" {
  for_each = local.private_subnets

  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value.cidr
  availability_zone = each.key

  tags = { Name = each.value.name }
}

# --- Public Route Table ---
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "${var.project_name}-public-rt" }
}

resource "aws_route_table_association" "public" {
  for_each = aws_subnet.public

  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

# --- NAT Gateway (선택적) ---
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? 1 : 0
  domain = "vpc"

  tags = { Name = "${var.project_name}-nat-eip" }
}

resource "aws_nat_gateway" "main" {
  count         = var.enable_nat_gateway ? 1 : 0
  allocation_id = aws_eip.nat[0].id
  subnet_id     = values(aws_subnet.public)[0].id

  tags = { Name = "${var.project_name}-nat-gw" }
}

# --- Private Route Table ---
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = { Name = "${var.project_name}-private-rt" }
}

resource "aws_route" "private_nat" {
  count                  = var.enable_nat_gateway ? 1 : 0
  route_table_id         = aws_route_table.private.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main[0].id
}

resource "aws_route_table_association" "private" {
  for_each = aws_subnet.private

  subnet_id      = each.value.id
  route_table_id = aws_route_table.private.id
}
