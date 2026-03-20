"""
통계 API

사용자 및 전역 이용 통계를 제공하는 엔드포인트
"""

from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import get_cache, set_cache
from app.db.session import get_db
from app.models.boarding_record import BoardingRecord
from app.models.user_device import UserDevice
from app.schemas.statistics import (
    ActivityByDayOfWeek,
    GlobalStatisticsData,
    GlobalStatisticsResponse,
    RouteStatistics,
    StationStatistics,
    UserStatisticsData,
    UserStatisticsResponse,
)

router = APIRouter(prefix="/statistics", tags=["Statistics"])


def get_period_dates(period: str) -> tuple[datetime, datetime]:
    """
    기간 문자열을 시작/종료 datetime으로 변환

    Args:
        period: 기간 ("7d", "30d", "90d", "all")

    Returns:
        tuple[datetime, datetime]: (시작 시간, 종료 시간)
    """
    now = datetime.now(timezone.utc)
    end = now

    if period == "7d":
        start = now - timedelta(days=7)
    elif period == "30d":
        start = now - timedelta(days=30)
    elif period == "90d":
        start = now - timedelta(days=90)
    else:  # "all"
        start = datetime(2020, 1, 1, tzinfo=timezone.utc)

    return start, end


@router.get(
    "/user/{device_id}",
    response_model=UserStatisticsResponse,
    summary="사용자 통계 조회",
    description="특정 기기의 이용 통계를 조회합니다. Redis 캐싱 적용 (TTL: 300초)",
    responses={
        404: {"description": "기기를 찾을 수 없음"},
    },
)
async def get_user_statistics(
    device_id: UUID = Path(..., description="기기 고유 ID"),
    period: Literal["7d", "30d", "90d", "all"] = Query(
        default="30d", description="조회 기간"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    사용자 통계 조회

    Args:
        device_id: 기기 고유 ID
        period: 조회 기간 (7d, 30d, 90d, all)
        db: 데이터베이스 세션

    Returns:
        UserStatisticsResponse: 사용자 통계 데이터

    Raises:
        HTTPException 404: 기기를 찾을 수 없음
    """
    cache_key = f"stats:user:{device_id}:{period}"

    # 1. 캐시 확인
    cached_data = await get_cache(cache_key)
    if cached_data:
        return UserStatisticsResponse(**cached_data)

    # 2. 기기 존재 여부 확인
    device_result = await db.execute(
        select(UserDevice).where(UserDevice.device_id == device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "detail": "Device not found",
                "error_code": "DEVICE_NOT_FOUND",
                "device_id": str(device_id),
            },
        )

    # 3. 기간 설정
    period_start, period_end = get_period_dates(period)

    # 4. 통계 쿼리
    # 4.1. 총 알림 횟수 및 성공률
    stats_result = await db.execute(
        select(
            func.count(BoardingRecord.record_id).label("total"),
            func.count(
                BoardingRecord.record_id
            ).filter(BoardingRecord.notification_status == "success").label("success"),
            func.count(
                BoardingRecord.record_id
            ).filter(BoardingRecord.notification_status != "success").label("failed"),
        )
        .where(BoardingRecord.device_id == device_id)
        .where(BoardingRecord.boarded_at >= period_start)
        .where(BoardingRecord.boarded_at <= period_end)
    )
    stats = stats_result.one()

    total_notifications = stats.total or 0
    successful_notifications = stats.success or 0
    failed_notifications = stats.failed or 0
    success_rate = (
        round((successful_notifications / total_notifications) * 100, 2)
        if total_notifications > 0
        else 0.0
    )

    # 4.2. 자주 이용한 노선 Top 5
    routes_result = await db.execute(
        select(
            BoardingRecord.route_name,
            BoardingRecord.route_type,
            func.count(BoardingRecord.record_id).label("count"),
        )
        .where(BoardingRecord.device_id == device_id)
        .where(BoardingRecord.boarded_at >= period_start)
        .where(BoardingRecord.boarded_at <= period_end)
        .group_by(BoardingRecord.route_name, BoardingRecord.route_type)
        .order_by(func.count(BoardingRecord.record_id).desc())
        .limit(5)
    )
    most_used_routes = [
        RouteStatistics(
            route_name=row.route_name, route_type=row.route_type, count=row.count
        )
        for row in routes_result.all()
    ]

    # 4.3. 자주 이용한 정류장 Top 3
    stations_result = await db.execute(
        select(
            BoardingRecord.station_name,
            BoardingRecord.ars_id,
            func.count(BoardingRecord.record_id).label("count"),
        )
        .where(BoardingRecord.device_id == device_id)
        .where(BoardingRecord.boarded_at >= period_start)
        .where(BoardingRecord.boarded_at <= period_end)
        .where(BoardingRecord.station_name.isnot(None))
        .group_by(BoardingRecord.station_name, BoardingRecord.ars_id)
        .order_by(func.count(BoardingRecord.record_id).desc())
        .limit(3)
    )
    most_used_stations = [
        StationStatistics(
            station_name=row.station_name, ars_id=row.ars_id, count=row.count
        )
        for row in stations_result.all()
    ]

    # 4.4. 요일별 활동
    # PostgreSQL의 EXTRACT(DOW FROM ...) 사용 (0=일요일, 6=토요일)
    dow_result = await db.execute(
        select(
            func.extract("dow", BoardingRecord.boarded_at).label("day_of_week"),
            func.count(BoardingRecord.record_id).label("count"),
        )
        .where(BoardingRecord.device_id == device_id)
        .where(BoardingRecord.boarded_at >= period_start)
        .where(BoardingRecord.boarded_at <= period_end)
        .group_by("day_of_week")
    )

    # 요일별 집계 초기화
    activity_by_day = {
        "monday": 0,
        "tuesday": 0,
        "wednesday": 0,
        "thursday": 0,
        "friday": 0,
        "saturday": 0,
        "sunday": 0,
    }

    # PostgreSQL DOW: 0=일, 1=월, ..., 6=토
    day_map = {
        0: "sunday",
        1: "monday",
        2: "tuesday",
        3: "wednesday",
        4: "thursday",
        5: "friday",
        6: "saturday",
    }

    for row in dow_result.all():
        day_name = day_map.get(int(row.day_of_week))
        if day_name:
            activity_by_day[day_name] = row.count

    # 4.5. 마지막 이용 시간
    last_used_result = await db.execute(
        select(BoardingRecord.boarded_at)
        .where(BoardingRecord.device_id == device_id)
        .order_by(BoardingRecord.boarded_at.desc())
        .limit(1)
    )
    last_used = last_used_result.scalar_one_or_none()

    # 5. 응답 생성
    statistics_data = UserStatisticsData(
        total_notifications=total_notifications,
        successful_notifications=successful_notifications,
        failed_notifications=failed_notifications,
        success_rate=success_rate,
        most_used_routes=most_used_routes,
        most_used_stations=most_used_stations,
        activity_by_day_of_week=ActivityByDayOfWeek(**activity_by_day),
        last_used=last_used,
    )

    response = UserStatisticsResponse(
        device_id=device_id,
        period=period,
        period_start=period_start,
        period_end=period_end,
        statistics=statistics_data,
    )

    # 6. Redis에 캐싱
    await set_cache(
        cache_key, response.model_dump(mode="json"), ttl=settings.redis_ttl_statistics
    )

    return response


@router.get(
    "/global",
    response_model=GlobalStatisticsResponse,
    summary="전역 통계 조회",
    description="전체 서비스 통계를 조회합니다. Redis 캐싱 적용 (TTL: 600초)",
)
async def get_global_statistics(
    period: Literal["24h", "7d", "30d", "all"] = Query(
        default="7d", description="조회 기간"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    전역 통계 조회

    Args:
        period: 조회 기간 (24h, 7d, 30d, all)
        db: 데이터베이스 세션

    Returns:
        GlobalStatisticsResponse: 전역 통계 데이터
    """
    cache_key = f"stats:global:{period}"

    # 1. 캐시 확인
    cached_data = await get_cache(cache_key)
    if cached_data:
        return GlobalStatisticsResponse(**cached_data)

    # 2. 기간 설정
    if period == "24h":
        period_start = datetime.now(timezone.utc) - timedelta(hours=24)
    else:
        period_start, _ = get_period_dates(period)
    period_end = datetime.now(timezone.utc)

    # 3. 통계 쿼리
    # 3.1. 총 사용자 수
    total_users_result = await db.execute(select(func.count(UserDevice.device_id)))
    total_users = total_users_result.scalar_one() or 0

    # 3.2. 최근 7일 활성 사용자
    active_users_result = await db.execute(
        select(func.count(UserDevice.device_id)).where(
            UserDevice.last_active_at >= datetime.now(timezone.utc) - timedelta(days=7)
        )
    )
    active_users_7d = active_users_result.scalar_one() or 0

    # 3.3. 알림 횟수 및 성공률
    stats_result = await db.execute(
        select(
            func.count(BoardingRecord.record_id).label("total"),
            func.count(
                BoardingRecord.record_id
            ).filter(BoardingRecord.notification_status == "success").label("success"),
            func.count(
                BoardingRecord.record_id
            ).filter(BoardingRecord.notification_status != "success").label("failed"),
        )
        .where(BoardingRecord.boarded_at >= period_start)
        .where(BoardingRecord.boarded_at <= period_end)
    )
    stats = stats_result.one()

    total_notifications = stats.total or 0
    successful_notifications = stats.success or 0
    failed_notifications = stats.failed or 0
    success_rate = (
        round((successful_notifications / total_notifications) * 100, 2)
        if total_notifications > 0
        else 0.0
    )

    # 3.4. 인기 노선 Top 10
    top_routes_result = await db.execute(
        select(
            BoardingRecord.route_name,
            BoardingRecord.route_type,
            func.count(BoardingRecord.record_id).label("count"),
        )
        .where(BoardingRecord.boarded_at >= period_start)
        .where(BoardingRecord.boarded_at <= period_end)
        .group_by(BoardingRecord.route_name, BoardingRecord.route_type)
        .order_by(func.count(BoardingRecord.record_id).desc())
        .limit(10)
    )
    top_routes = [
        RouteStatistics(
            route_name=row.route_name, route_type=row.route_type, count=row.count
        )
        for row in top_routes_result.all()
    ]

    # 3.5. 인기 정류장 Top 10
    top_stations_result = await db.execute(
        select(
            BoardingRecord.station_name,
            BoardingRecord.ars_id,
            func.count(BoardingRecord.record_id).label("count"),
        )
        .where(BoardingRecord.boarded_at >= period_start)
        .where(BoardingRecord.boarded_at <= period_end)
        .where(BoardingRecord.station_name.isnot(None))
        .group_by(BoardingRecord.station_name, BoardingRecord.ars_id)
        .order_by(func.count(BoardingRecord.record_id).desc())
        .limit(10)
    )
    top_stations = [
        StationStatistics(
            station_name=row.station_name, ars_id=row.ars_id, count=row.count
        )
        for row in top_stations_result.all()
    ]

    # 4. 응답 생성
    statistics_data = GlobalStatisticsData(
        total_users=total_users,
        active_users_7d=active_users_7d,
        total_notifications=total_notifications,
        successful_notifications=successful_notifications,
        failed_notifications=failed_notifications,
        success_rate=success_rate,
        top_routes=top_routes,
        top_stations=top_stations,
    )

    response = GlobalStatisticsResponse(
        period=period,
        period_start=period_start,
        period_end=period_end,
        statistics=statistics_data,
    )

    # 5. Redis에 캐싱 (10분)
    await set_cache(cache_key, response.model_dump(mode="json"), ttl=600)

    return response
