"""
API v1 라우터 통합

모든 v1 엔드포인트를 통합하는 메인 라우터
"""

from fastapi import APIRouter

from app.api.v1 import boarding, bus, health, statistics

# v1 메인 라우터
router = APIRouter()

# 헬스체크 (루트 레벨)
router.include_router(health.router)

# 버스 정보
router.include_router(bus.router)

# 탑승 기록
router.include_router(boarding.router)

# 통계
router.include_router(statistics.router)
