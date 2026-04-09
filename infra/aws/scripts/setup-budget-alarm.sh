#!/bin/bash
# =============================================================
# ComfortableMove 비용 알림 설정 스크립트 (AWS CLI)
#
# AWS Budgets를 사용하여 월간 비용 알림을 설정합니다.
# 프리티어 범위를 초과하지 않도록 $5, $10 임계값에서 알림을 발송합니다.
#
# 사용법: bash setup-budget-alarm.sh <이메일주소>
# 예시:   bash setup-budget-alarm.sh parkseonggeun@example.com
# =============================================================

set -euo pipefail

PROFILE="comfortablemove"
BUDGET_NAME="comfortablemove-monthly-budget"
BUDGET_LIMIT="10.0"  # 월 $10 예산 한도
CURRENCY="USD"

# ---------------------------------------------------------
# 인자 확인
# ---------------------------------------------------------
if [[ $# -lt 1 ]]; then
    echo "사용법: bash setup-budget-alarm.sh <알림받을-이메일>"
    echo "예시:   bash setup-budget-alarm.sh your@email.com"
    exit 1
fi

NOTIFICATION_EMAIL="$1"
ACCOUNT_ID=$(aws sts get-caller-identity --profile "${PROFILE}" --query Account --output text)

echo "========================================"
echo " ComfortableMove 비용 알림 설정"
echo "========================================"
echo " 계정 ID: ${ACCOUNT_ID}"
echo " 월 예산: \$${BUDGET_LIMIT}"
echo " 알림 이메일: ${NOTIFICATION_EMAIL}"
echo ""

# ---------------------------------------------------------
# Step 1: 월간 예산 생성 ($5 경고, $10 위험)
# ---------------------------------------------------------
echo "[Step 1] 월간 예산 생성"

aws budgets create-budget \
    --profile "${PROFILE}" \
    --account-id "${ACCOUNT_ID}" \
    --budget "{
        \"BudgetName\": \"${BUDGET_NAME}\",
        \"BudgetLimit\": {
            \"Amount\": \"${BUDGET_LIMIT}\",
            \"Unit\": \"${CURRENCY}\"
        },
        \"BudgetType\": \"COST\",
        \"TimeUnit\": \"MONTHLY\",
        \"CostTypes\": {
            \"IncludeTax\": true,
            \"IncludeSubscription\": true,
            \"UseBlended\": false,
            \"IncludeRefund\": false,
            \"IncludeCredit\": false,
            \"IncludeUpfront\": true,
            \"IncludeRecurring\": true,
            \"IncludeOtherSubscription\": true,
            \"IncludeSupport\": true,
            \"IncludeDiscount\": true,
            \"UseAmortized\": false
        }
    }" \
    --notifications-with-subscribers "[
        {
            \"Notification\": {
                \"NotificationType\": \"ACTUAL\",
                \"ComparisonOperator\": \"GREATER_THAN\",
                \"Threshold\": 50,
                \"ThresholdType\": \"PERCENTAGE\"
            },
            \"Subscribers\": [{
                \"SubscriptionType\": \"EMAIL\",
                \"Address\": \"${NOTIFICATION_EMAIL}\"
            }]
        },
        {
            \"Notification\": {
                \"NotificationType\": \"ACTUAL\",
                \"ComparisonOperator\": \"GREATER_THAN\",
                \"Threshold\": 80,
                \"ThresholdType\": \"PERCENTAGE\"
            },
            \"Subscribers\": [{
                \"SubscriptionType\": \"EMAIL\",
                \"Address\": \"${NOTIFICATION_EMAIL}\"
            }]
        },
        {
            \"Notification\": {
                \"NotificationType\": \"ACTUAL\",
                \"ComparisonOperator\": \"GREATER_THAN\",
                \"Threshold\": 100,
                \"ThresholdType\": \"PERCENTAGE\"
            },
            \"Subscribers\": [{
                \"SubscriptionType\": \"EMAIL\",
                \"Address\": \"${NOTIFICATION_EMAIL}\"
            }]
        },
        {
            \"Notification\": {
                \"NotificationType\": \"FORECASTED\",
                \"ComparisonOperator\": \"GREATER_THAN\",
                \"Threshold\": 100,
                \"ThresholdType\": \"PERCENTAGE\"
            },
            \"Subscribers\": [{
                \"SubscriptionType\": \"EMAIL\",
                \"Address\": \"${NOTIFICATION_EMAIL}\"
            }]
        }
    ]"

echo "  -> 예산 생성 완료"

# ---------------------------------------------------------
# 완료 요약
# ---------------------------------------------------------
echo ""
echo "========================================"
echo " 비용 알림 설정 완료!"
echo "========================================"
echo ""
echo " 알림 임계값:"
echo " ┌────────────┬────────────┬──────────────────────────┐"
echo " │ 유형       │ 임계값     │ 금액 (월 \$${BUDGET_LIMIT} 기준)  │"
echo " ├────────────┼────────────┼──────────────────────────┤"
echo " │ 실제 비용  │  50%       │ \$5.00 초과 시 알림      │"
echo " │ 실제 비용  │  80%       │ \$8.00 초과 시 알림      │"
echo " │ 실제 비용  │ 100%       │ \$10.00 초과 시 알림     │"
echo " │ 예측 비용  │ 100%       │ \$10.00 초과 예측 시     │"
echo " └────────────┴────────────┴──────────────────────────┘"
echo ""
echo " 알림 이메일: ${NOTIFICATION_EMAIL}"
echo ""
echo " ⚠️  비용 절감 팁:"
echo "   - 사용하지 않는 EC2 인스턴스는 중지(Stop)하세요"
echo "   - NAT 게이트웨이는 시간당 과금됩니다 (\$0.059/hr)"
echo "   - Elastic IP는 미연결 시 과금됩니다"
echo "   - 프리티어: t2.micro 750시간/월, EBS 30GB, 데이터 전송 15GB"
