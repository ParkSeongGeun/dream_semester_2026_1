#!/bin/bash
# =============================================================
# ComfortableMove EC2 인스턴스 및 보안 그룹 생성 스크립트 (AWS CLI)
#
# 구성:
#   - 보안 그룹: SSH(22), HTTP(8000) 인바운드만 허용
#   - EC2: t2.micro (프리티어), Amazon Linux 2023, 퍼블릭 서브넷 A
#   - User Data: Docker + Docker Compose 자동 설치
#
# 사용법: bash setup-ec2.sh
# 사전 조건: setup-vpc.sh 실행 완료 (vpc-outputs.env 필요)
# =============================================================

set -euo pipefail

REGION="ap-northeast-2"
PROJECT="comfortablemove"
PROFILE="${PROJECT}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VPC_OUTPUT="${SCRIPT_DIR}/../vpc/vpc-outputs.env"

# ---------------------------------------------------------
# VPC 리소스 ID 로드
# ---------------------------------------------------------
if [[ ! -f "${VPC_OUTPUT}" ]]; then
    echo "❌ ${VPC_OUTPUT} 파일을 찾을 수 없습니다."
    echo "   먼저 setup-vpc.sh를 실행하세요."
    exit 1
fi
source "${VPC_OUTPUT}"

echo "========================================"
echo " ComfortableMove EC2 인스턴스 생성"
echo " 리전: ${REGION}"
echo " VPC:  ${VPC_ID}"
echo "========================================"

# ---------------------------------------------------------
# Step 1: SSH 키페어 생성
# ---------------------------------------------------------
echo ""
echo "[Step 1] SSH 키페어 생성"
KEY_NAME="${PROJECT}-key"
KEY_FILE="${SCRIPT_DIR}/${KEY_NAME}.pem"

if aws ec2 describe-key-pairs \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --key-names "${KEY_NAME}" &>/dev/null; then
    echo "  -> 키페어가 이미 존재합니다: ${KEY_NAME}"
else
    aws ec2 create-key-pair \
        --region "${REGION}" \
        --profile "${PROFILE}" \
        --key-name "${KEY_NAME}" \
        --query 'KeyMaterial' --output text > "${KEY_FILE}"
    chmod 400 "${KEY_FILE}"
    echo "  -> 키페어 생성 완료: ${KEY_FILE}"
    echo "  ⚠️  이 파일을 안전한 곳에 보관하세요. Git에 커밋하지 마세요!"
fi

# ---------------------------------------------------------
# Step 2: 보안 그룹 생성 (최소 권한 원칙)
# ---------------------------------------------------------
echo ""
echo "[Step 2] 보안 그룹 생성"
SG_NAME="${PROJECT}-backend-sg"

SG_ID=$(aws ec2 create-security-group \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --group-name "${SG_NAME}" \
    --description "ComfortableMove Backend - SSH and API access only" \
    --vpc-id "${VPC_ID}" \
    --query 'GroupId' --output text)

aws ec2 create-tags \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --resources "${SG_ID}" \
    --tags "Key=Name,Value=${SG_NAME}" "Key=Project,Value=${PROJECT}"

echo "  -> 보안 그룹 생성: ${SG_ID} (${SG_NAME})"

# 인바운드 규칙: SSH (포트 22) - 내 IP에서만 접근
echo ""
echo "[Step 2-1] 인바운드 규칙 설정"
MY_IP=$(curl -s https://checkip.amazonaws.com)/32
echo "  -> 현재 IP: ${MY_IP}"

aws ec2 authorize-security-group-ingress \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --group-id "${SG_ID}" \
    --protocol tcp \
    --port 22 \
    --cidr "${MY_IP}" > /dev/null
echo "  -> SSH (22): ${MY_IP} 에서만 허용"

# 인바운드 규칙: FastAPI (포트 8000) - 내 IP에서만 접근
aws ec2 authorize-security-group-ingress \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --group-id "${SG_ID}" \
    --protocol tcp \
    --port 8000 \
    --cidr "${MY_IP}" > /dev/null
echo "  -> API (8000): ${MY_IP} 에서만 허용"

# 아웃바운드: 기본적으로 모두 허용 (VPC 기본값 유지)
echo "  -> 아웃바운드: 전체 허용 (기본값)"

echo ""
echo "  보안 그룹 규칙 요약:"
echo "  ┌──────────┬──────────┬────────────────────┐"
echo "  │ 방향     │ 포트     │ 소스/대상          │"
echo "  ├──────────┼──────────┼────────────────────┤"
echo "  │ 인바운드 │ TCP 22   │ ${MY_IP} │"
echo "  │ 인바운드 │ TCP 8000 │ ${MY_IP} │"
echo "  │ 아웃바운드│ 전체     │ 0.0.0.0/0          │"
echo "  └──────────┴──────────┴────────────────────┘"

# ---------------------------------------------------------
# Step 3: 최신 Amazon Linux 2023 AMI 조회
# ---------------------------------------------------------
echo ""
echo "[Step 3] AMI 조회 (Amazon Linux 2023)"
AMI_ID=$(aws ec2 describe-images \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --owners amazon \
    --filters \
        "Name=name,Values=al2023-ami-2023.*-x86_64" \
        "Name=state,Values=available" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text)
echo "  -> AMI: ${AMI_ID}"

# ---------------------------------------------------------
# Step 4: EC2 인스턴스 생성
# ---------------------------------------------------------
echo ""
echo "[Step 4] EC2 인스턴스 생성 (t2.micro)"
INSTANCE_ID=$(aws ec2 run-instances \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --image-id "${AMI_ID}" \
    --instance-type "t2.micro" \
    --key-name "${KEY_NAME}" \
    --security-group-ids "${SG_ID}" \
    --subnet-id "${PUB_SUB_A}" \
    --user-data "file://${SCRIPT_DIR}/user-data.sh" \
    --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":20,"VolumeType":"gp3","DeleteOnTermination":true}}]' \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${PROJECT}-backend},{Key=Project,Value=${PROJECT}}]" \
    --query 'Instances[0].InstanceId' --output text)
echo "  -> 인스턴스 생성 중: ${INSTANCE_ID}"

# 인스턴스가 running 상태가 될 때까지 대기
echo "  -> 인스턴스 시작 대기 중..."
aws ec2 wait instance-running \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --instance-ids "${INSTANCE_ID}"

# 퍼블릭 IP 조회
PUBLIC_IP=$(aws ec2 describe-instances \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --instance-ids "${INSTANCE_ID}" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "  -> 인스턴스 실행 완료!"
echo "  -> 퍼블릭 IP: ${PUBLIC_IP}"

# ---------------------------------------------------------
# 완료 요약
# ---------------------------------------------------------
echo ""
echo "========================================"
echo " EC2 인스턴스 생성 완료!"
echo "========================================"
echo " 인스턴스 ID: ${INSTANCE_ID}"
echo " 퍼블릭 IP:   ${PUBLIC_IP}"
echo " AMI:         ${AMI_ID}"
echo " 타입:        t2.micro (프리티어)"
echo " 서브넷:      ${PUB_SUB_A} (퍼블릭 A)"
echo " 보안 그룹:   ${SG_ID}"
echo " 키페어:      ${KEY_NAME}"
echo "========================================"
echo ""
echo " SSH 접속:"
echo "   ssh -i ${KEY_FILE} ec2-user@${PUBLIC_IP}"
echo ""
echo " API 테스트 (Docker 초기화 완료 후 약 3-5분):"
echo "   curl http://${PUBLIC_IP}:8000/api/v1/health"
echo ""
echo " ⚠️  User Data 스크립트가 백그라운드에서 실행 중입니다."
echo " 로그 확인: ssh 접속 후 'sudo cat /var/log/cloud-init-output.log'"

# ---------------------------------------------------------
# 리소스 ID 저장
# ---------------------------------------------------------
OUTPUT_FILE="${SCRIPT_DIR}/ec2-outputs.env"
cat > "${OUTPUT_FILE}" <<EOF
# ComfortableMove EC2 리소스 ID (자동 생성)
# 생성일: $(date '+%Y-%m-%d %H:%M:%S')
INSTANCE_ID=${INSTANCE_ID}
PUBLIC_IP=${PUBLIC_IP}
SG_ID=${SG_ID}
AMI_ID=${AMI_ID}
KEY_NAME=${KEY_NAME}
EOF
echo " 리소스 ID 저장: ${OUTPUT_FILE}"
