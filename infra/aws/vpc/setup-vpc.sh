#!/bin/bash
# =============================================================
# ComfortableMove VPC 구축 스크립트 (AWS CLI)
#
# 아키텍처:
#   - VPC: 10.0.0.0/16
#   - 가용영역 2개 (ap-northeast-2a, ap-northeast-2c)
#   - 퍼블릭 서브넷 2개 (10.0.1.0/24, 10.0.2.0/24)
#   - 프라이빗 서브넷 2개 (10.0.11.0/24, 10.0.12.0/24)
#   - 인터넷 게이트웨이 1개
#   - NAT 게이트웨이 1개 (AZ-a, Elastic IP 사용)
#   - 퍼블릭/프라이빗 라우팅 테이블 각 1개
#
# 사용법: bash setup-vpc.sh
# 사전 조건: aws configure --profile comfortablemove 완료
# =============================================================

set -euo pipefail

REGION="ap-northeast-2"
PROJECT="comfortablemove"
PROFILE="${PROJECT}"
VPC_CIDR="10.0.0.0/16"

# 서브넷 CIDR
PUBLIC_SUBNET_A_CIDR="10.0.1.0/24"
PUBLIC_SUBNET_C_CIDR="10.0.2.0/24"
PRIVATE_SUBNET_A_CIDR="10.0.11.0/24"
PRIVATE_SUBNET_C_CIDR="10.0.12.0/24"

AZ_A="${REGION}a"
AZ_C="${REGION}c"

tag() {
    aws ec2 create-tags \
        --region "${REGION}" \
        --profile "${PROFILE}" \
        --resources "$1" \
        --tags "Key=Name,Value=${PROJECT}-$2" "Key=Project,Value=${PROJECT}"
}

echo "========================================"
echo " ComfortableMove VPC 구축"
echo " 리전: ${REGION}"
echo "========================================"

# ---------------------------------------------------------
# Step 1: VPC 생성
# ---------------------------------------------------------
echo ""
echo "[Step 1] VPC 생성 (${VPC_CIDR})"
VPC_ID=$(aws ec2 create-vpc \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --cidr-block "${VPC_CIDR}" \
    --query 'Vpc.VpcId' --output text)
tag "${VPC_ID}" "vpc"

# DNS 호스트네임 활성화 (EC2 인스턴스에 퍼블릭 DNS 부여)
aws ec2 modify-vpc-attribute \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --vpc-id "${VPC_ID}" \
    --enable-dns-hostnames '{"Value":true}'

echo "  -> VPC 생성 완료: ${VPC_ID}"

# ---------------------------------------------------------
# Step 2: 서브넷 생성 (퍼블릭 2개 + 프라이빗 2개)
# ---------------------------------------------------------
echo ""
echo "[Step 2] 서브넷 생성 (4개)"

# 퍼블릭 서브넷 A
PUB_SUB_A=$(aws ec2 create-subnet \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --vpc-id "${VPC_ID}" \
    --cidr-block "${PUBLIC_SUBNET_A_CIDR}" \
    --availability-zone "${AZ_A}" \
    --query 'Subnet.SubnetId' --output text)
tag "${PUB_SUB_A}" "public-subnet-a"
# 퍼블릭 서브넷에서 인스턴스 생성 시 자동으로 퍼블릭 IP 할당
aws ec2 modify-subnet-attribute \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --subnet-id "${PUB_SUB_A}" \
    --map-public-ip-on-launch
echo "  -> 퍼블릭 서브넷 A: ${PUB_SUB_A} (${AZ_A}, ${PUBLIC_SUBNET_A_CIDR})"

# 퍼블릭 서브넷 C
PUB_SUB_C=$(aws ec2 create-subnet \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --vpc-id "${VPC_ID}" \
    --cidr-block "${PUBLIC_SUBNET_C_CIDR}" \
    --availability-zone "${AZ_C}" \
    --query 'Subnet.SubnetId' --output text)
tag "${PUB_SUB_C}" "public-subnet-c"
aws ec2 modify-subnet-attribute \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --subnet-id "${PUB_SUB_C}" \
    --map-public-ip-on-launch
echo "  -> 퍼블릭 서브넷 C: ${PUB_SUB_C} (${AZ_C}, ${PUBLIC_SUBNET_C_CIDR})"

# 프라이빗 서브넷 A
PRIV_SUB_A=$(aws ec2 create-subnet \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --vpc-id "${VPC_ID}" \
    --cidr-block "${PRIVATE_SUBNET_A_CIDR}" \
    --availability-zone "${AZ_A}" \
    --query 'Subnet.SubnetId' --output text)
tag "${PRIV_SUB_A}" "private-subnet-a"
echo "  -> 프라이빗 서브넷 A: ${PRIV_SUB_A} (${AZ_A}, ${PRIVATE_SUBNET_A_CIDR})"

# 프라이빗 서브넷 C
PRIV_SUB_C=$(aws ec2 create-subnet \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --vpc-id "${VPC_ID}" \
    --cidr-block "${PRIVATE_SUBNET_C_CIDR}" \
    --availability-zone "${AZ_C}" \
    --query 'Subnet.SubnetId' --output text)
tag "${PRIV_SUB_C}" "private-subnet-c"
echo "  -> 프라이빗 서브넷 C: ${PRIV_SUB_C} (${AZ_C}, ${PRIVATE_SUBNET_C_CIDR})"

# ---------------------------------------------------------
# Step 3: 인터넷 게이트웨이 생성 및 VPC 연결
# ---------------------------------------------------------
echo ""
echo "[Step 3] 인터넷 게이트웨이 생성"
IGW_ID=$(aws ec2 create-internet-gateway \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --query 'InternetGateway.InternetGatewayId' --output text)
tag "${IGW_ID}" "igw"

aws ec2 attach-internet-gateway \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --internet-gateway-id "${IGW_ID}" \
    --vpc-id "${VPC_ID}"
echo "  -> 인터넷 게이트웨이: ${IGW_ID} (VPC에 연결 완료)"

# ---------------------------------------------------------
# Step 4: NAT 게이트웨이 생성 (퍼블릭 서브넷 A에 배치)
# ---------------------------------------------------------
echo ""
echo "[Step 4] NAT 게이트웨이 생성 (Elastic IP 할당)"
EIP_ALLOC=$(aws ec2 allocate-address \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --domain vpc \
    --query 'AllocationId' --output text)
echo "  -> Elastic IP 할당: ${EIP_ALLOC}"

NAT_GW_ID=$(aws ec2 create-nat-gateway \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --subnet-id "${PUB_SUB_A}" \
    --allocation-id "${EIP_ALLOC}" \
    --query 'NatGateway.NatGatewayId' --output text)
tag "${NAT_GW_ID}" "nat-gw"
echo "  -> NAT 게이트웨이: ${NAT_GW_ID} (생성 중...)"

# NAT 게이트웨이가 available 상태가 될 때까지 대기
echo "  -> NAT 게이트웨이 활성화 대기 중..."
aws ec2 wait nat-gateway-available \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --nat-gateway-ids "${NAT_GW_ID}"
echo "  -> NAT 게이트웨이 활성화 완료"

# ---------------------------------------------------------
# Step 5: 퍼블릭 라우팅 테이블 설정
# ---------------------------------------------------------
echo ""
echo "[Step 5] 퍼블릭 라우팅 테이블 설정"
PUB_RT_ID=$(aws ec2 create-route-table \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --vpc-id "${VPC_ID}" \
    --query 'RouteTable.RouteTableId' --output text)
tag "${PUB_RT_ID}" "public-rt"

# 0.0.0.0/0 → 인터넷 게이트웨이 (인터넷 아웃바운드)
aws ec2 create-route \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --route-table-id "${PUB_RT_ID}" \
    --destination-cidr-block "0.0.0.0/0" \
    --gateway-id "${IGW_ID}" > /dev/null

# 퍼블릭 서브넷 연결
aws ec2 associate-route-table \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --route-table-id "${PUB_RT_ID}" \
    --subnet-id "${PUB_SUB_A}" > /dev/null
aws ec2 associate-route-table \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --route-table-id "${PUB_RT_ID}" \
    --subnet-id "${PUB_SUB_C}" > /dev/null
echo "  -> 퍼블릭 RT: ${PUB_RT_ID} (0.0.0.0/0 → IGW)"

# ---------------------------------------------------------
# Step 6: 프라이빗 라우팅 테이블 설정
# ---------------------------------------------------------
echo ""
echo "[Step 6] 프라이빗 라우팅 테이블 설정"
PRIV_RT_ID=$(aws ec2 create-route-table \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --vpc-id "${VPC_ID}" \
    --query 'RouteTable.RouteTableId' --output text)
tag "${PRIV_RT_ID}" "private-rt"

# 0.0.0.0/0 → NAT 게이트웨이 (프라이빗에서 인터넷 접근)
aws ec2 create-route \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --route-table-id "${PRIV_RT_ID}" \
    --destination-cidr-block "0.0.0.0/0" \
    --nat-gateway-id "${NAT_GW_ID}" > /dev/null

# 프라이빗 서브넷 연결
aws ec2 associate-route-table \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --route-table-id "${PRIV_RT_ID}" \
    --subnet-id "${PRIV_SUB_A}" > /dev/null
aws ec2 associate-route-table \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --route-table-id "${PRIV_RT_ID}" \
    --subnet-id "${PRIV_SUB_C}" > /dev/null
echo "  -> 프라이빗 RT: ${PRIV_RT_ID} (0.0.0.0/0 → NAT GW)"

# ---------------------------------------------------------
# 완료 요약
# ---------------------------------------------------------
echo ""
echo "========================================"
echo " VPC 구축 완료!"
echo "========================================"
echo " VPC:              ${VPC_ID} (${VPC_CIDR})"
echo " 퍼블릭 서브넷 A:  ${PUB_SUB_A} (${AZ_A})"
echo " 퍼블릭 서브넷 C:  ${PUB_SUB_C} (${AZ_C})"
echo " 프라이빗 서브넷 A: ${PRIV_SUB_A} (${AZ_A})"
echo " 프라이빗 서브넷 C: ${PRIV_SUB_C} (${AZ_C})"
echo " 인터넷 게이트웨이: ${IGW_ID}"
echo " NAT 게이트웨이:    ${NAT_GW_ID}"
echo " 퍼블릭 RT:         ${PUB_RT_ID}"
echo " 프라이빗 RT:       ${PRIV_RT_ID}"
echo " Elastic IP:        ${EIP_ALLOC}"
echo "========================================"
echo ""
echo " 다음 단계: bash ../ec2/setup-ec2.sh 를 실행하세요."

# ---------------------------------------------------------
# 리소스 ID를 파일로 저장 (후속 스크립트에서 참조)
# ---------------------------------------------------------
OUTPUT_FILE="$(dirname "$0")/vpc-outputs.env"
cat > "${OUTPUT_FILE}" <<EOF
# ComfortableMove VPC 리소스 ID (자동 생성)
# 생성일: $(date '+%Y-%m-%d %H:%M:%S')
VPC_ID=${VPC_ID}
PUB_SUB_A=${PUB_SUB_A}
PUB_SUB_C=${PUB_SUB_C}
PRIV_SUB_A=${PRIV_SUB_A}
PRIV_SUB_C=${PRIV_SUB_C}
IGW_ID=${IGW_ID}
NAT_GW_ID=${NAT_GW_ID}
EIP_ALLOC=${EIP_ALLOC}
PUB_RT_ID=${PUB_RT_ID}
PRIV_RT_ID=${PRIV_RT_ID}
EOF
echo " 리소스 ID 저장: ${OUTPUT_FILE}"
