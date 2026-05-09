"""
헬스체크 API

서버 및 의존성 상태를 확인하는 엔드포인트
"""

from datetime import datetime, timezone

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.redis import check_redis_health, get_cache_stats
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
    except Exception:
        db_status = "disconnected"
        errors.append("Database connection failed")

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


@router.get(
    "/health/ready",
    summary="Readiness 체크 (K8s 용)",
    description=(
        "K8s readinessProbe 전용 — 외부 API(서울 TOPIS) 는 검사하지 않고 "
        "DB·Redis 만 확인한다. /api/v1/health 는 외부 API 까지 호출하므로 "
        "10초 주기 readiness probe 에 사용하면 일일 호출 한도가 빠르게 소진된다."
    ),
)
async def readiness_check():
    """K8s readinessProbe — DB·Redis 만 빠르게 확인. 서울 API 호출 없음."""
    db_ok = False
    redis_ok = False

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    redis_ok = await check_redis_health()

    if db_ok and redis_ok:
        return JSONResponse(content={"status": "ready"}, status_code=status.HTTP_200_OK)

    return JSONResponse(
        content={"status": "not_ready", "db": db_ok, "redis": redis_ok},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@router.get(
    "/health/cache",
    summary="캐시 상태 조회",
    description="Redis 캐시 키 분류별 통계를 조회합니다.",
)
async def cache_health():
    """
    Redis 캐시 통계 엔드포인트

    Returns:
        dict: 캐시 키 개수, 메모리 사용량 등
    """
    stats = await get_cache_stats()
    return JSONResponse(content=stats)
