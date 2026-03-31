#!/bin/bash
# ============================================
# PostgreSQL 데이터 영속성 테스트 스크립트
# ============================================
# 목적: 컨테이너 재시작 후에도 PostgreSQL 데이터가 유지되는지 검증
#
# 사용법: bash scripts/test_persistence.sh
#
# 테스트 순서:
#   1. 컨테이너 기동 및 헬스체크 대기
#   2. 테스트 데이터 삽입
#   3. 데이터 존재 확인
#   4. 컨테이너 재시작
#   5. 재시작 후 데이터 존재 재확인
#   6. 테스트 데이터 정리
# ============================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

COMPOSE_FILE="docker-compose.yml"
DB_CONTAINER="comfortablemove_db"
DB_USER="${POSTGRES_USER:-user}"
DB_NAME="${POSTGRES_DB:-comfortablemove}"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW} PostgreSQL 데이터 영속성 테스트${NC}"
echo -e "${YELLOW}========================================${NC}"

# --- Step 1: 컨테이너 기동 확인 ---
echo -e "\n${YELLOW}[Step 1] 컨테이너 상태 확인...${NC}"
if ! docker compose -f "$COMPOSE_FILE" ps --status running | grep -q "$DB_CONTAINER"; then
    echo "PostgreSQL 컨테이너가 실행 중이지 않습니다. 기동합니다..."
    docker compose -f "$COMPOSE_FILE" up -d postgres
    echo "헬스체크 대기 중..."
    sleep 5
fi

# PostgreSQL 준비 대기
for i in $(seq 1 15); do
    if docker exec "$DB_CONTAINER" pg_isready -U "$DB_USER" > /dev/null 2>&1; then
        echo -e "${GREEN}PostgreSQL 준비 완료${NC}"
        break
    fi
    if [ "$i" -eq 15 ]; then
        echo -e "${RED}PostgreSQL 준비 시간 초과${NC}"
        exit 1
    fi
    echo "대기 중... ($i/15)"
    sleep 2
done

# --- Step 2: 테스트 테이블 및 데이터 삽입 ---
echo -e "\n${YELLOW}[Step 2] 테스트 데이터 삽입...${NC}"
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
CREATE TABLE IF NOT EXISTS persistence_test (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
INSERT INTO persistence_test (message) VALUES ('persistence_test_$(date +%s)');
"
echo -e "${GREEN}데이터 삽입 완료${NC}"

# --- Step 3: 데이터 존재 확인 ---
echo -e "\n${YELLOW}[Step 3] 재시작 전 데이터 확인...${NC}"
BEFORE_COUNT=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM persistence_test;" | tr -d ' ')
echo -e "현재 레코드 수: ${GREEN}${BEFORE_COUNT}${NC}"

if [ "$BEFORE_COUNT" -eq 0 ]; then
    echo -e "${RED}데이터 삽입 실패${NC}"
    exit 1
fi

# --- Step 4: 컨테이너 재시작 ---
echo -e "\n${YELLOW}[Step 4] PostgreSQL 컨테이너 재시작...${NC}"
docker compose -f "$COMPOSE_FILE" restart postgres
echo "헬스체크 대기 중..."

for i in $(seq 1 20); do
    if docker exec "$DB_CONTAINER" pg_isready -U "$DB_USER" > /dev/null 2>&1; then
        echo -e "${GREEN}PostgreSQL 재시작 완료${NC}"
        break
    fi
    if [ "$i" -eq 20 ]; then
        echo -e "${RED}재시작 후 PostgreSQL 준비 시간 초과${NC}"
        exit 1
    fi
    sleep 2
done

# --- Step 5: 재시작 후 데이터 확인 ---
echo -e "\n${YELLOW}[Step 5] 재시작 후 데이터 확인...${NC}"
AFTER_COUNT=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM persistence_test;" | tr -d ' ')
echo -e "재시작 후 레코드 수: ${GREEN}${AFTER_COUNT}${NC}"

if [ "$AFTER_COUNT" -eq "$BEFORE_COUNT" ]; then
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN} 영속성 테스트 통과!${NC}"
    echo -e "${GREEN} 재시작 전: ${BEFORE_COUNT}개 → 재시작 후: ${AFTER_COUNT}개${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "\n${RED}========================================${NC}"
    echo -e "${RED} 영속성 테스트 실패!${NC}"
    echo -e "${RED} 재시작 전: ${BEFORE_COUNT}개 → 재시작 후: ${AFTER_COUNT}개${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi

# --- Step 6: 테스트 데이터 정리 ---
echo -e "\n${YELLOW}[Step 6] 테스트 데이터 정리...${NC}"
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c \
    "DROP TABLE IF EXISTS persistence_test;"
echo -e "${GREEN}정리 완료${NC}"

echo -e "\n${GREEN}모든 테스트가 성공적으로 완료되었습니다.${NC}"
