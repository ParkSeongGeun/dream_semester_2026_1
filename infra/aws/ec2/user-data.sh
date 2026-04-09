#!/bin/bash
# =============================================================
# ComfortableMove EC2 User Data (부트스트랩 스크립트)
#
# EC2 인스턴스 최초 부팅 시 자동 실행됩니다.
# 설치 항목: Docker, Docker Compose, Git, 프로젝트 클론
#
# 로그 확인: /var/log/cloud-init-output.log
# =============================================================

set -euo pipefail

LOG_FILE="/var/log/comfortablemove-setup.log"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "========================================"
echo " ComfortableMove EC2 초기화 시작"
echo " 시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"

# ---------------------------------------------------------
# Step 1: 시스템 업데이트
# ---------------------------------------------------------
echo "[Step 1] 시스템 패키지 업데이트"
dnf update -y
echo "  -> 시스템 업데이트 완료"

# ---------------------------------------------------------
# Step 2: Docker 설치
# ---------------------------------------------------------
echo "[Step 2] Docker 설치"
dnf install -y docker
systemctl start docker
systemctl enable docker

# ec2-user를 docker 그룹에 추가 (sudo 없이 docker 사용)
usermod -aG docker ec2-user
echo "  -> Docker 설치 완료: $(docker --version)"

# ---------------------------------------------------------
# Step 3: Docker Compose 설치
# ---------------------------------------------------------
echo "[Step 3] Docker Compose 설치"
COMPOSE_VERSION="v2.27.0"
ARCH=$(uname -m)
if [[ "${ARCH}" == "x86_64" ]]; then
    ARCH="x86_64"
elif [[ "${ARCH}" == "aarch64" ]]; then
    ARCH="aarch64"
fi

curl -SL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-${ARCH}" \
    -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# docker compose (V2 plugin) 심볼릭 링크
mkdir -p /usr/local/lib/docker/cli-plugins
ln -sf /usr/local/bin/docker-compose /usr/local/lib/docker/cli-plugins/docker-compose
echo "  -> Docker Compose 설치 완료: $(docker-compose --version)"

# ---------------------------------------------------------
# Step 4: Git 설치 및 프로젝트 클론
# ---------------------------------------------------------
echo "[Step 4] Git 설치 및 프로젝트 클론"
dnf install -y git

PROJECT_DIR="/home/ec2-user/comfortablemove"
if [[ -d "${PROJECT_DIR}" ]]; then
    echo "  -> 프로젝트 디렉토리가 이미 존재합니다."
else
    # TODO: 실제 GitHub 리포지토리 URL로 변경
    # git clone https://github.com/<user>/dream_semester_2026_1.git "${PROJECT_DIR}"
    mkdir -p "${PROJECT_DIR}/backend"
    echo "  -> 프로젝트 디렉토리 생성 (Git 클론은 수동으로 실행하세요)"
fi
chown -R ec2-user:ec2-user "${PROJECT_DIR}"

# ---------------------------------------------------------
# Step 5: 환경변수 템플릿 생성
# ---------------------------------------------------------
echo "[Step 5] 환경변수 템플릿 생성"
ENV_FILE="${PROJECT_DIR}/backend/.env.docker"
if [[ ! -f "${ENV_FILE}" ]]; then
    cat > "${ENV_FILE}" <<'ENVEOF'
# ComfortableMove Production Environment
# ⚠️ 실제 값으로 변경하세요

# App
ENVIRONMENT=production
DEBUG=false
APP_NAME=ComfortableMove Backend
APP_VERSION=1.0.0

# Database (Docker 내부 서비스명)
DATABASE_URL=postgresql+asyncpg://comfortablemove:CHANGE_ME_DB_PASSWORD@postgres:5432/comfortablemove
DB_ECHO=false

# Redis (Docker 내부 서비스명)
REDIS_URL=redis://redis:6379/0

# Seoul Bus API
SEOUL_BUS_API_KEY=YOUR_API_KEY_HERE

# Security
SECRET_KEY=CHANGE_ME_RANDOM_SECRET_KEY
ENVEOF
    chown ec2-user:ec2-user "${ENV_FILE}"
    chmod 600 "${ENV_FILE}"
    echo "  -> 환경변수 템플릿 생성: ${ENV_FILE}"
    echo "  ⚠️  반드시 실제 값으로 수정하세요!"
else
    echo "  -> 환경변수 파일이 이미 존재합니다."
fi

# ---------------------------------------------------------
# Step 6: 시스템 보안 설정
# ---------------------------------------------------------
echo "[Step 6] 시스템 보안 설정"

# SSH 비밀번호 인증 비활성화 (키 기반만 허용)
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart sshd
echo "  -> SSH 비밀번호 인증 비활성화, root 로그인 차단"

# 불필요한 포트 방화벽 (보안 그룹과 이중 방어)
# Amazon Linux 2023은 기본적으로 firewalld가 비활성화 상태
echo "  -> 방화벽: AWS 보안 그룹에 위임 (최소 포트만 오픈)"

# ---------------------------------------------------------
# 완료
# ---------------------------------------------------------
echo ""
echo "========================================"
echo " EC2 초기화 완료!"
echo " 시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""
echo " 다음 단계:"
echo " 1. ssh 접속 후 프로젝트 디렉토리로 이동"
echo "    cd ${PROJECT_DIR}/backend"
echo " 2. .env.docker 파일 수정 (DB 비밀번호, API 키 등)"
echo "    vi .env.docker"
echo " 3. Docker Compose 실행"
echo "    docker compose up -d"
echo " 4. 상태 확인"
echo "    docker compose ps"
echo "    curl http://localhost:8000/api/v1/health"
