"""
버스 도착 정보 / 정류소 조회 API

iOS 프론트엔드(ComfortableMove) 모델과 동일한 응답 구조로 서울시 버스 API 를
프록시. 응답은 `{msgHeader, msgBody.itemList[...]}` 형식.

Endpoints:
  - GET /api/v1/bus/arrivals?ars_id=XXXXX     (iOS getStationByUid 대체)
  - GET /api/v1/bus/stations?tmX=&tmY=&radius=  (iOS getStationByPos 대체)
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import settings
from app.core.redis import get_cache, set_cache
from app.schemas.bus import (
    BusArrivalResponse,
    ErrorResponse,
    StationByPosResponse,
)
from app.services.seoul_bus_api import seoul_bus_service

router = APIRouter(prefix="/bus", tags=["Bus"])


@router.get(
    "/arrivals",
    response_model=BusArrivalResponse,
    summary="버스 도착 정보 조회 (iOS 호환)",
    description=(
        "iOS BusArrivalResponse 와 동일한 `{msgHeader, msgBody.itemList[]}` 구조로 응답. "
        "Redis 캐시 TTL 적용."
    ),
    responses={503: {"model": ErrorResponse, "description": "Seoul Bus API 장애"}},
)
async def get_bus_arrivals(
    ars_id: str = Query(
        ...,
        description="정류장 고유번호 (서울 표준 5자리)",
        min_length=4,
        max_length=6,
        examples=["01234"],
    )
):
    """버스 도착 정보 조회 — iOS 모델과 1:1 호환"""
    cache_key = f"arrivals:{ars_id}"

    cached_data = await get_cache(cache_key)
    if cached_data:
        return BusArrivalResponse.model_validate(cached_data)

    try:
        raw_data = await seoul_bus_service.get_station_arrival_info(ars_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "detail": "Seoul Bus API is currently unavailable",
                "error_code": "EXTERNAL_API_ERROR",
                "retry_after": 60,
            },
        )

    normalized = seoul_bus_service.normalize_arrival_response(raw_data)

    # iOS는 headerCd != "0" 일 때 자체적으로 처리 (noBusInfo 등)
    # → 백엔드는 200 으로 그대로 통과시켜 클라이언트가 헤더로 분기 가능하게 함
    await set_cache(
        cache_key,
        normalized,
        ttl=settings.redis_ttl_bus_arrival,
    )

    return BusArrivalResponse.model_validate(normalized)


@router.get(
    "/stations",
    response_model=StationByPosResponse,
    summary="위치 기반 정류소 조회 (iOS 호환)",
    description=(
        "iOS StationByPosResponse 와 동일한 응답 구조. "
        "tmX=경도, tmY=위도, radius=반경(m) — iOS BusStopService 와 동일한 파라미터."
    ),
    responses={503: {"model": ErrorResponse, "description": "Seoul Bus API 장애"}},
)
async def get_nearby_stations(
    tmX: float = Query(..., description="경도 (longitude)", examples=[126.9707]),
    tmY: float = Query(..., description="위도 (latitude)", examples=[37.5547]),
    radius: int = Query(default=100, ge=1, le=2000, description="반경(m)"),
):
    """위치 기반 정류소 조회 — iOS StationByPosResponse 와 1:1 호환"""
    # 정류소 조회는 좌표가 키이므로 캐시 키도 좌표 기반
    cache_key = f"stations:{round(tmY, 5)}:{round(tmX, 5)}:{radius}"

    cached_data = await get_cache(cache_key)
    if cached_data:
        return StationByPosResponse.model_validate(cached_data)

    try:
        raw_data = await seoul_bus_service.get_stations_by_position(
            latitude=tmY, longitude=tmX, radius=radius
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "detail": "Seoul Bus API is currently unavailable",
                "error_code": "EXTERNAL_API_ERROR",
                "retry_after": 60,
            },
        )

    normalized = seoul_bus_service.normalize_station_response(raw_data)

    await set_cache(
        cache_key,
        normalized,
        ttl=settings.redis_ttl_bus_arrival,
    )

    return StationByPosResponse.model_validate(normalized)
