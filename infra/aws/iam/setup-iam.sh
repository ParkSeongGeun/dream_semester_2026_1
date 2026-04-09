#!/bin/bash
# =============================================================
# ComfortableMove IAM 설정 스크립트
# 맘편한 이동 프로젝트용 IAM 그룹, 사용자, 정책 생성
# =============================================================
# 사용법: bash setup-iam.sh
# 사전 조건: AWS CLI 설치 및 루트/관리자 계정으로 aws configure 완료
# =============================================================

set -euo pipefail

REGION="ap-northeast-2"
PROJECT="comfortablemove"
GROUP_NAME="${PROJECT}-developers"
USER_NAME="${PROJECT}-deploy"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo " ComfortableMove IAM 설정"
echo "========================================"

# ---------------------------------------------------------
# Step 1: IAM 그룹 생성
# ---------------------------------------------------------
echo "[Step 1] IAM 그룹 생성: ${GROUP_NAME}"
if aws iam get-group --group-name "${GROUP_NAME}" &>/dev/null; then
    echo "  -> 그룹이 이미 존재합니다. 건너뜁니다."
else
    aws iam create-group --group-name "${GROUP_NAME}"
    echo "  -> 그룹 생성 완료"
fi

# ---------------------------------------------------------
# Step 2: IAM 정책 생성 및 그룹에 연결
# ---------------------------------------------------------
echo "[Step 2] IAM 정책 생성 및 그룹 연결"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# EC2/VPC 관리 정책
EC2_POLICY_NAME="${PROJECT}-ec2-policy"
EC2_POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${EC2_POLICY_NAME}"

if aws iam get-policy --policy-arn "${EC2_POLICY_ARN}" &>/dev/null; then
    echo "  -> EC2 정책이 이미 존재합니다."
else
    EC2_POLICY_ARN=$(aws iam create-policy \
        --policy-name "${EC2_POLICY_NAME}" \
        --policy-document "file://${SCRIPT_DIR}/comfortablemove-ec2-policy.json" \
        --description "ComfortableMove EC2/VPC 관리 권한" \
        --query 'Policy.Arn' --output text)
    echo "  -> EC2 정책 생성: ${EC2_POLICY_ARN}"
fi
aws iam attach-group-policy --group-name "${GROUP_NAME}" --policy-arn "${EC2_POLICY_ARN}"
echo "  -> EC2 정책 그룹 연결 완료"

# 비용 조회 정책
BILLING_POLICY_NAME="${PROJECT}-billing-policy"
BILLING_POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${BILLING_POLICY_NAME}"

if aws iam get-policy --policy-arn "${BILLING_POLICY_ARN}" &>/dev/null; then
    echo "  -> Billing 정책이 이미 존재합니다."
else
    BILLING_POLICY_ARN=$(aws iam create-policy \
        --policy-name "${BILLING_POLICY_NAME}" \
        --policy-document "file://${SCRIPT_DIR}/comfortablemove-billing-policy.json" \
        --description "ComfortableMove 비용 조회 권한" \
        --query 'Policy.Arn' --output text)
    echo "  -> Billing 정책 생성: ${BILLING_POLICY_ARN}"
fi
aws iam attach-group-policy --group-name "${GROUP_NAME}" --policy-arn "${BILLING_POLICY_ARN}"
echo "  -> Billing 정책 그룹 연결 완료"

# ---------------------------------------------------------
# Step 3: IAM 사용자 생성 및 그룹 추가
# ---------------------------------------------------------
echo "[Step 3] IAM 사용자 생성: ${USER_NAME}"
if aws iam get-user --user-name "${USER_NAME}" &>/dev/null; then
    echo "  -> 사용자가 이미 존재합니다."
else
    aws iam create-user --user-name "${USER_NAME}"
    echo "  -> 사용자 생성 완료"
fi

aws iam add-user-to-group --user-name "${USER_NAME}" --group-name "${GROUP_NAME}"
echo "  -> 그룹에 사용자 추가 완료"

# ---------------------------------------------------------
# Step 4: Access Key 생성 (프로그래밍 방식 접근용)
# ---------------------------------------------------------
echo "[Step 4] Access Key 생성"
echo "  ⚠️  주의: Access Key는 생성 시 한 번만 표시됩니다."
echo "  ⚠️  절대 Git에 커밋하거나 코드에 하드코딩하지 마세요."
echo ""

read -p "  Access Key를 생성하시겠습니까? (y/N): " CREATE_KEY
if [[ "${CREATE_KEY}" == "y" || "${CREATE_KEY}" == "Y" ]]; then
    KEY_OUTPUT=$(aws iam create-access-key --user-name "${USER_NAME}" --output json)
    ACCESS_KEY=$(echo "${KEY_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['AccessKey']['AccessKeyId'])")
    SECRET_KEY=$(echo "${KEY_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['AccessKey']['SecretAccessKey'])")

    echo ""
    echo "  =========================================="
    echo "  Access Key ID:     ${ACCESS_KEY}"
    echo "  Secret Access Key: ${SECRET_KEY}"
    echo "  =========================================="
    echo ""
    echo "  이 정보를 안전한 곳에 저장하세요."
    echo "  aws configure --profile ${PROJECT} 로 프로필을 설정하세요."
else
    echo "  -> Access Key 생성을 건너뜁니다."
fi

# ---------------------------------------------------------
# Step 5: MFA 설정 안내
# ---------------------------------------------------------
echo ""
echo "[Step 5] MFA 설정 안내"
echo "  루트 계정 및 IAM 사용자에 MFA를 반드시 설정하세요."
echo "  AWS 콘솔 > IAM > Users > ${USER_NAME} > Security credentials > MFA"
echo "  Google Authenticator 또는 Authy 앱을 사용하세요."

echo ""
echo "========================================"
echo " IAM 설정 완료!"
echo "========================================"
echo " 그룹: ${GROUP_NAME}"
echo " 사용자: ${USER_NAME}"
echo " 정책: ${EC2_POLICY_NAME}, ${BILLING_POLICY_NAME}"
echo " 리전: ${REGION}"
echo "========================================"
