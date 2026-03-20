"""
헬스체크 API

서버 및 의존성 상태를 확인하는 엔드포인트
"""

from datetime import datetime, timezone

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.redis import check_redis_health
from app.db.session import AsyncSessionLocal
from app.schemas.health import HealthCheckResponse, ServiceStatus
from app.services.seoul_bus_api import seoul_bus_service

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="헬스체크",
    description="서버 및 의존성(DB, Redis, Seoul API) 상태를 확인합니다.",
)
async def health_check():
    """
    헬스체크 엔드포인트

    - PostgreSQL 연결 상태
    - Redis 연결 상태
    - 서울시 버스 API 연결 상태

    Returns:
        HealthCheckResponse: 서비스 상태 정보
    """
    errors = []

    # PostgreSQL 연결 확인
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = "disconnected"
        errors.append(f"Database connection failed: {str(e)}")

    # Redis 연결 확인
    redis_status = "connected" if await check_redis_health() else "disconnected"
    if redis_status == "disconnected":
        errors.append("Redis connection failed")

    # Seoul Bus API 연결 확인
    seoul_api_status = (
        "reachable" if await seoul_bus_service.check_api_health() else "unreachable"
    )
    if seoul_api_status == "unreachable":
        errors.append("Seoul Bus API is unreachable")

    # 전체 상태 판단
    overall_status = (
        "healthy"
        if db_status == "connected"
        and redis_status == "connected"
        and seoul_api_status == "reachable"
        else "unhealthy"
    )

    # 응답 생성
    response_data = HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc),
        version=settings.app_version,
        services=ServiceStatus(
            database=db_status,
            redis=redis_status,
            seoul_bus_api=seoul_api_status,
        ),
        errors=errors if errors else None,
    )

    # 상태에 따른 HTTP 상태 코드
    status_code = status.HTTP_200_OK if overall_status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        content=response_data.model_dump(mode="json"),
        status_code=status_code,
    )
