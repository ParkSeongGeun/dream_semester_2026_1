#!/usr/bin/env bash
# ComfortableMove 풀스택 통합 검증
#   1) Backend (Docker) healthy
#   2) Backend → Seoul API live 호출
#   3) Terraform dev/prod validate
#   4) iOS build + simulator install (선택; SIM_ID 환경변수로 활성화)

set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
ARS_ID="${ARS_ID:-23288}"          # 강남역 8번출구
TM_X="${TM_X:-127.0276}"
TM_Y="${TM_Y:-37.4979}"
RADIUS="${RADIUS:-200}"

PASS=0; FAIL=0
ok()   { echo "  ✓ $1"; PASS=$((PASS+1)); }
fail() { echo "  ✗ $1"; FAIL=$((FAIL+1)); }

section() { echo ""; echo "── $1 ──"; }

section "1) Docker backend stack"
for c in comfortablemove_backend_dev comfortablemove_db_dev comfortablemove_redis_dev; do
  status="$(docker ps --filter "name=$c" --format '{{.Status}}' 2>/dev/null || true)"
  if echo "$status" | grep -q healthy; then ok "$c: $status"; else fail "$c: ${status:-not running}"; fi
done

section "2) Backend health"
HEALTH="$(curl -sS -m 5 "$BACKEND_URL/api/v1/health" 2>/dev/null || true)"
if echo "$HEALTH" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); assert d['status']=='healthy'" 2>/dev/null; then
  ok "/api/v1/health: healthy (db/redis/seoul_bus_api connected)"
else
  fail "health check failed: $HEALTH"
fi

section "3) Backend → Seoul API live"
ARR="$(curl -sS -m 10 "$BACKEND_URL/api/v1/bus/arrivals?ars_id=$ARS_ID" 2>/dev/null || true)"
COUNT="$(echo "$ARR" | python3 -c "import json,sys;print(len(json.loads(sys.stdin.read())['msgBody']['itemList']))" 2>/dev/null || echo 0)"
if [ "$COUNT" -gt 0 ]; then
  ok "/api/v1/bus/arrivals?ars_id=$ARS_ID → $COUNT routes"
  echo "$ARR" | python3 -c "
import json,sys
d=json.loads(sys.stdin.read()); item=d['msgBody']['itemList'][0]
required=['rtNm','arrmsg1','adirection','routeType','isFullFlag1','isLast1','congestion1']
miss=[k for k in required if k not in item]
print(f'    BusArrivalItem 필수 키 7개 누락: {miss if miss else \"없음\"}')"
else
  fail "arrivals returned 0 items"
fi

STA="$(curl -sS -m 10 "$BACKEND_URL/api/v1/bus/stations?tmX=$TM_X&tmY=$TM_Y&radius=$RADIUS" 2>/dev/null || true)"
SCOUNT="$(echo "$STA" | python3 -c "import json,sys;print(len(json.loads(sys.stdin.read())['msgBody']['itemList']))" 2>/dev/null || echo 0)"
if [ "$SCOUNT" -gt 0 ]; then
  ok "/api/v1/bus/stations?tmX=$TM_X&tmY=$TM_Y&radius=$RADIUS → $SCOUNT stops"
  echo "$STA" | python3 -c "
import json,sys
d=json.loads(sys.stdin.read()); item=d['msgBody']['itemList'][0]
required=['stationId','stationNm','arsId','gpsX','gpsY','dist','stationTp']
miss=[k for k in required if k not in item]
print(f'    StationItem 필수 키 7개 누락: {miss if miss else \"없음\"}')"
else
  fail "stations returned 0 items"
fi

section "4) Terraform validate"
for env in dev prod; do
  out="$(cd "$ROOT/infra/terraform/environments/$env" && terraform validate 2>&1 || true)"
  if echo "$out" | grep -q "Success"; then ok "$env: valid"; else fail "$env: $out"; fi
done

section "5) iOS simulator (optional)"
if [ -n "${SIM_ID:-}" ]; then
  if xcrun simctl list devices | grep -q "$SIM_ID.*Booted"; then
    ok "simulator booted: $SIM_ID"
    if xcrun simctl listapps "$SIM_ID" 2>/dev/null | grep -q "com.ParkSeongGeun.ComfortableMove"; then
      ok "ComfortableMove app installed"
    else
      fail "ComfortableMove app not installed"
    fi
  else
    fail "SIM_ID=$SIM_ID not booted"
  fi
else
  echo "  (skipped — set SIM_ID=<udid> to enable)"
fi

echo ""
echo "════════════════════════════════"
echo "  PASS=$PASS  FAIL=$FAIL"
echo "════════════════════════════════"
[ "$FAIL" -eq 0 ]
