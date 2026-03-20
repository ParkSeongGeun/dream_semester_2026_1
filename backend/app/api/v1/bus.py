"""
버스 도착 정보 API

서울시 버스 API를 프록시하여 실시간 도착 정보를 제공합니다.
Redis 캐싱을 통해 응답 속도를 개선합니다.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import settings
from app.core.redis import get_cache, set_cache
from app.schemas.bus import BusArrivalResponse, ErrorResponse
from app.services.seoul_bus_api import seoul_bus_service

router = APIRouter(prefix="/bus", tags=["Bus"])


@router.get(
    "/arrivals",
    response_model=BusArrivalResponse,
    summary="버스 도착 정보 조회",
    description="특정 정류장의 실시간 버스 도착 정보를 조회합니다. Redis 캐싱 적용 (TTL: 60초)",
    responses={
        404: {"model": ErrorResponse, "description": "버스 정보 없음"},
        503: {"model": ErrorResponse, "description": "Seoul Bus API 장애"},
    },
)
async def get_bus_arrivals(
    ars_id: str = Query(
        ...,
        description="정류장 고유번호",
        example="01234",
        min_length=5,
        max_length=5,
    )
):
    """
    버스 도착 정보 조회

    Args:
        ars_id: 정류장 고유번호 (5자리)

    Returns:
        BusArrivalResponse: 버스 도착 정보

    Raises:
        HTTPException 404: 버스 정보 없음
        HTTPException 503: Seoul Bus API 장애
    """
    cache_key = f"arrivals:{ars_id}"
    now = datetime.now(timezone.utc)

    # 1. 캐시 확인
    cached_data = await get_cache(cache_key)
    if cached_data:
        # 캐시 히트
        return BusArrivalResponse(
            ars_id=ars_id,
            station_name=cached_data.get("station_name", ""),
            arrivals=cached_data.get("arrivals", []),
            cached=True,
            cached_at=datetime.fromisoformat(cached_data.get("cached_at")),
            expires_at=datetime.fromisoformat(cached_data.get("expires_at")),
        )

    # 2. 캐시 미스 - Seoul API 호출
    try:
        raw_data = await seoul_bus_service.get_station_arrival_info(ars_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "detail": "Seoul Bus API is currently unavailable",
                "error_code": "EXTERNAL_API_ERROR",
                "retry_after": 60,
            },
        )

    # 3. 응답 파싱
    msg_header = raw_data.get("msgHeader", {})
    header_code = msg_header.get("headerCd", "")

    if header_code != "0":
        # 데이터 없음
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "detail": "No bus information found for this station",
                "error_code": "NO_BUS_INFO",
                "ars_id": ars_id,
            },
        )

    # 4. 데이터 정제
    arrivals = seoul_bus_service.parse_arrival_info(raw_data)

    # 정류장 이름 추출
    station_name = ""
    if arrivals:
        station_name = arrivals[0].get("direction", "")

    # 5. Redis에 캐싱
    expires_at = now + timedelta(seconds=settings.redis_ttl_bus_arrival)
    cache_data = {
        "station_name": station_name,
        "arrivals": arrivals,
        "cached_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
    }
    await set_cache(cache_key, cache_data, ttl=settings.redis_ttl_bus_arrival)

    # 6. 응답 반환
    return BusArrivalResponse(
        ars_id=ars_id,
        station_name=station_name,
        arrivals=arrivals,
        cached=False,
        cached_at=now,
        expires_at=expires_at,
    )
