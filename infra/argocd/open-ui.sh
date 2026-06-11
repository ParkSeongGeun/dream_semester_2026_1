#!/bin/bash
# =============================================================
# ArgoCD UI 발표용 실행 스크립트
# 사용: ./open-ui.sh  → https://localhost:8080 으로 연결
# 종료: Ctrl+C
# =============================================================
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../terraform"

# AWS 자격증명 (kubectl 의 EKS 인증용) — tfvars 에서 로드
export AWS_ACCESS_KEY_ID=$(grep '^aws_access_key' terraform.tfvars | sed -E 's/^[^=]*=[[:space:]]*"?([^"]*)"?[[:space:]]*$/\1/')
export AWS_SECRET_ACCESS_KEY=$(grep '^aws_secret_key' terraform.tfvars | sed -E 's/^[^=]*=[[:space:]]*"?([^"]*)"?[[:space:]]*$/\1/')

# kubeconfig 보장
aws eks update-kubeconfig --name comfortablemove-cluster --region ap-northeast-2 >/dev/null 2>&1 || true

PW=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' 2>/dev/null | base64 -d)

echo "════════════════════════════════════════════"
echo "  ArgoCD UI  →  https://localhost:8080"
echo "  ID: admin"
echo "  PW: ${PW}"
echo ""
echo "  (브라우저 인증서 경고 시 → 고급 → 계속)"
echo "  종료하려면 Ctrl+C"
echo "════════════════════════════════════════════"

kubectl port-forward svc/argocd-server -n argocd 8080:443
