root@ubuntu:~/dream_semester# vim setup.sh 
root@ubuntu:~/dream_semester# cat setup.sh 
#!/bin/bash

echo "Comfortable Move Server setup starts..."

# 1. package list update
echo "[1/5] package update ..."
apt update -y && apt upgrade -y

# 2. Install Python
echo "[2/5] install python..."
apt install python3 python3-pip -y
python3 --version

# 3. Install docker
echo "[3/5] install docker..."
apt install curl -y
curl -fsSL https://get.docker.com | sh
docker --version

# 4. Create Directories
echo "[4/5] create directories..."
mkdir -p /app/backend
mkdir -p /app/logs
mkdir -p /app/data
echo "directory setting ends"
ls /app

# 5. Firewall Setup
echo "[5/5] setup firewall..."."
echo "컨테이너 환경 → 방화벽 설정 스킵"
echo "실제 EC2 서버에서 아래 명령어를 실행할 것"
echo "  ufw allow 22"
echo "  ufw allow 80"
echo "  ufw allow 443"
echo "  ufw allow 8000"
echo "  ufw --force enable"

echo "Comfortable Mover Server setup ends!!"s