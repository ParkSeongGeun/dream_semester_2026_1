"""
Pydantic 스키마 모듈

API 요청/응답 검증을 위한 스키마
"""

from app.schemas.boarding import BoardingRecordRequest, BoardingRecordResponse
from app.schemas.bus import BusArrivalInfo, BusArrivalResponse, ErrorResponse
from app.schemas.health import HealthCheckResponse, ServiceStatus
from app.schemas.statistics import (
    ActivityByDayOfWeek,
    GlobalStatisticsData,
    GlobalStatisticsResponse,
    RouteStatistics,
    StationStatistics,
    UserStatisticsData,
    UserStatisticsResponse,
)

__all__ = [
    # Health
    "HealthCheckResponse",
    "ServiceStatus",
    # Bus
    "BusArrivalInfo",
    "BusArrivalResponse",
    "ErrorResponse",
    # Boarding
    "BoardingRecordRequest",
    "BoardingRecordResponse",
    # Statistics
    "UserStatisticsData",
    "UserStatisticsResponse",
    "GlobalStatisticsData",
    "GlobalStatisticsResponse",
    "RouteStatistics",
    "StationStatistics",
    "ActivityByDayOfWeek",
]
