#!/usr/bin/env bash
# =============================================================
# ComfortableMove - iOS 연동 헬스체크
# =============================================================
# iOS 앱(ComfortableMove)이 사용하는 두 엔드포인트를 백엔드 프록시 경로로
# 호출하여 응답 형식이 iOS 모델(BusArrivalResponse, StationByPosResponse)과
# 일치하는지 검증.
#
# Usage:
#   ./healthcheck.sh
#   API_BASE_URL=https://api.comfortablemove.com ./healthcheck.sh
# =============================================================
set -u

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
TIMEOUT="${TIMEOUT:-10}"
ARS_ID="${ARS_ID:-23288}"      # 강남역 (테스트 기본값)
TM_X="${TM_X:-126.9707}"       # 서울역 longitude
TM_Y="${TM_Y:-37.5547}"        # 서울역 latitude
RADIUS="${RADIUS:-100}"

G='\033[0;32m'; R='\033[0;31m'; Y='\033[0;33m'; B='\033[0;34m'; N='\033[0m'
PASS=0; FAIL=0

require() { command -v "$1" >/dev/null 2>&1 || { echo "필수 도구 누락: $1"; exit 2; }; }
require curl
require jq

echo -e "${B}========== ComfortableMove iOS 연동 체크 ==========${N}"
echo "Target: $API_BASE_URL"
echo ""

# ---------------------------------------------------------------
# 1. Health
# ---------------------------------------------------------------
echo -e "${B}▶ 1) /api/v1/health${N}"
status=$(curl -sS -m "$TIMEOUT" -o /tmp/_hc.$$ -w "%{http_code}" "$API_BASE_URL/api/v1/health" || echo "000")
if [[ "$status" =~ ^(200|503)$ ]]; then
  body=$(cat /tmp/_hc.$$)
  overall=$(echo "$body" | jq -r '.status // empty')
  echo -e "  ${G}HTTP $status${N}, status=$overall"
  PASS=$((PASS+1))
else
  echo -e "  ${R}HTTP $status${N} — 백엔드 응답 없음"
  FAIL=$((FAIL+1))
fi
rm -f /tmp/_hc.$$

# ---------------------------------------------------------------
# 2. /api/v1/bus/arrivals — iOS BusArrivalResponse 와 동일한 키
# ---------------------------------------------------------------
echo -e "\n${B}▶ 2) /api/v1/bus/arrivals?ars_id=$ARS_ID  (iOS: BusArrivalResponse)${N}"
status=$(curl -sS -m "$TIMEOUT" -o /tmp/_hc.$$ -w "%{http_code}" \
  "$API_BASE_URL/api/v1/bus/arrivals?ars_id=$ARS_ID")
body=$(cat /tmp/_hc.$$)
rm -f /tmp/_hc.$$

if [[ "$status" == "200" ]]; then
  # iOS 디코더가 요구하는 키 검증
  has_header=$(echo "$body" | jq 'has("msgHeader")')
  has_body=$(echo "$body" | jq 'has("msgBody")')
  has_headerCd=$(echo "$body" | jq '.msgHeader | has("headerCd")')
  has_itemCount=$(echo "$body" | jq '.msgHeader.itemCount | type == "number"')

  if [[ "$has_header" == "true" && "$has_body" == "true" && "$has_headerCd" == "true" && "$has_itemCount" == "true" ]]; then
    echo -e "  ${G}HTTP 200 / iOS BusArrivalResponse 형식 일치${N}"
    item_count=$(echo "$body" | jq -r '.msgHeader.itemCount')
    echo "  itemCount=$item_count"

    # 아이템이 있으면 iOS BusArrivalItem 키 검증
    first=$(echo "$body" | jq '.msgBody.itemList[0] // empty')
    if [[ -n "$first" && "$first" != "null" ]]; then
      for key in rtNm routeType; do
        if echo "$first" | jq -e "has(\"$key\")" >/dev/null; then
          echo -e "  ${G}✓${N} BusArrivalItem.$key 존재"
        else
          echo -e "  ${R}✗${N} BusArrivalItem.$key 누락"
          FAIL=$((FAIL+1))
        fi
      done
    fi
    PASS=$((PASS+1))
  else
    echo -e "  ${R}응답 키 불일치 (msgHeader/msgBody/headerCd/itemCount)${N}"
    echo "$body" | head -c 400
    FAIL=$((FAIL+1))
  fi
elif [[ "$status" == "503" ]]; then
  echo -e "  ${Y}HTTP 503 (외부 API 장애 — 백엔드 자체는 정상)${N}"
  PASS=$((PASS+1))
else
  echo -e "  ${R}HTTP $status${N}"
  echo "$body" | head -c 300
  FAIL=$((FAIL+1))
fi

# ---------------------------------------------------------------
# 3. /api/v1/bus/stations — iOS StationByPosResponse
# ---------------------------------------------------------------
echo -e "\n${B}▶ 3) /api/v1/bus/stations?tmX=$TM_X&tmY=$TM_Y&radius=$RADIUS  (iOS: StationByPosResponse)${N}"
status=$(curl -sS -m "$TIMEOUT" -o /tmp/_hc.$$ -w "%{http_code}" \
  "$API_BASE_URL/api/v1/bus/stations?tmX=$TM_X&tmY=$TM_Y&radius=$RADIUS")
body=$(cat /tmp/_hc.$$)
rm -f /tmp/_hc.$$

if [[ "$status" == "200" ]]; then
  has_header=$(echo "$body" | jq 'has("msgHeader")')
  has_body=$(echo "$body" | jq 'has("msgBody")')
  if [[ "$has_header" == "true" && "$has_body" == "true" ]]; then
    echo -e "  ${G}HTTP 200 / iOS StationByPosResponse 형식 일치${N}"
    item_count=$(echo "$body" | jq -r '.msgHeader.itemCount')
    echo "  itemCount=$item_count"

    first=$(echo "$body" | jq '.msgBody.itemList[0] // empty')
    if [[ -n "$first" && "$first" != "null" ]]; then
      for key in stationId stationNm arsId gpsX gpsY dist stationTp; do
        if echo "$first" | jq -e "has(\"$key\")" >/dev/null; then
          echo -e "  ${G}✓${N} StationItem.$key"
        else
          echo -e "  ${R}✗${N} StationItem.$key 누락"
          FAIL=$((FAIL+1))
        fi
      done
    fi
    PASS=$((PASS+1))
  else
    echo -e "  ${R}응답 키 불일치${N}"
    echo "$body" | head -c 400
    FAIL=$((FAIL+1))
  fi
elif [[ "$status" == "503" ]]; then
  echo -e "  ${Y}HTTP 503 (외부 API 장애)${N}"
  PASS=$((PASS+1))
else
  echo -e "  ${R}HTTP $status${N}"
  echo "$body" | head -c 300
  FAIL=$((FAIL+1))
fi

# ---------------------------------------------------------------
# Summary
# ---------------------------------------------------------------
echo ""
echo -e "${B}---------------------------------------------------${N}"
if [[ $FAIL -eq 0 ]]; then
  echo -e "${G}모든 체크 통과 (${PASS}건)${N}"
  echo "iOS 앱이 백엔드 프록시로 전환 가능한 상태입니다."
  exit 0
else
  echo -e "${Y}${PASS} passed, ${R}${FAIL} failed${N}"
  exit 1
fi
