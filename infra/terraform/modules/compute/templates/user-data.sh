#!/bin/bash
set -euo pipefail

# =============================================================
# EC2 User Data - Docker & Docker Compose 설치
# =============================================================

# --- 시스템 업데이트 ---
dnf update -y

# --- Docker 설치 ---
dnf install -y docker
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user

# --- Docker Compose 설치 ---
COMPOSE_VERSION="v2.29.1"
curl -L "https://github.com/docker/compose/releases/download/$${COMPOSE_VERSION}/docker-compose-linux-$(uname -m)" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# --- SSH 보안 강화 ---
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# --- 작업 디렉토리 생성 ---
mkdir -p /home/ec2-user/app
chown ec2-user:ec2-user /home/ec2-user/app

echo "=== User Data 완료 ==="
