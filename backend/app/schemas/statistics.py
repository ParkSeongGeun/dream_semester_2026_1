"""
통계 스키마

사용자 및 전역 통계를 위한 스키마
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class RouteStatistics(BaseModel):
    """노선별 통계"""

    route_name: str = Field(..., description="버스 노선명")
    count: int = Field(..., description="이용 횟수")
    route_type: str | None = Field(default=None, description="노선 유형")


class StationStatistics(BaseModel):
    """정류장별 통계"""

    station_name: str = Field(..., description="정류장 이름")
    ars_id: str | None = Field(default=None, description="정류장 고유번호")
    count: int = Field(..., description="이용 횟수")


class ActivityByDayOfWeek(BaseModel):
    """요일별 활동 통계"""

    monday: int = Field(default=0, description="월요일")
    tuesday: int = Field(default=0, description="화요일")
    wednesday: int = Field(default=0, description="수요일")
    thursday: int = Field(default=0, description="목요일")
    friday: int = Field(default=0, description="금요일")
    saturday: int = Field(default=0, description="토요일")
    sunday: int = Field(default=0, description="일요일")


class UserStatisticsData(BaseModel):
    """사용자 통계 데이터"""

    total_notifications: int = Field(..., description="총 알림 횟수")
    successful_notifications: int = Field(..., description="성공한 알림 횟수")
    failed_notifications: int = Field(..., description="실패한 알림 횟수")
    success_rate: float = Field(..., description="성공률 (%)")
    most_used_routes: list[RouteStatistics] = Field(..., description="자주 이용한 노선")
    most_used_stations: list[StationStatistics] = Field(
        ..., description="자주 이용한 정류장"
    )
    activity_by_day_of_week: ActivityByDayOfWeek = Field(..., description="요일별 활동")
    last_used: datetime | None = Field(default=None, description="마지막 이용 시간")


class UserStatisticsResponse(BaseModel):
    """사용자 통계 응답"""

    device_id: UUID = Field(..., description="기기 고유 ID")
    period: Literal["7d", "30d", "90d", "all"] = Field(..., description="조회 기간")
    period_start: datetime = Field(..., description="기간 시작")
    period_end: datetime = Field(..., description="기간 종료")
    statistics: UserStatisticsData = Field(..., description="통계 데이터")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "device_id": "550e8400-e29b-41d4-a716-446655440000",
                    "period": "30d",
                    "period_start": "2026-02-16T00:00:00Z",
                    "period_end": "2026-03-18T23:59:59Z",
                    "statistics": {
                        "total_notifications": 42,
                        "successful_notifications": 38,
                        "failed_notifications": 4,
                        "success_rate": 90.48,
                        "most_used_routes": [
                            {"route_name": "721", "count": 15, "route_type": "간선"}
                        ],
                        "most_used_stations": [
                            {"station_name": "신설동역", "ars_id": "01234", "count": 15}
                        ],
                        "activity_by_day_of_week": {
                            "monday": 8,
                            "tuesday": 7,
                            "wednesday": 6,
                            "thursday": 7,
                            "friday": 8,
                            "saturday": 3,
                            "sunday": 3,
                        },
                        "last_used": "2026-03-18T09:15:00Z",
                    },
                }
            ]
        }
    }


class GlobalStatisticsData(BaseModel):
    """전역 통계 데이터"""

    total_users: int = Field(..., description="총 사용자 수")
    active_users_7d: int = Field(..., description="최근 7일 활성 사용자")
    total_notifications: int = Field(..., description="총 알림 횟수")
    successful_notifications: int = Field(..., description="성공한 알림 횟수")
    failed_notifications: int = Field(..., description="실패한 알림 횟수")
    success_rate: float = Field(..., description="성공률 (%)")
    top_routes: list[RouteStatistics] = Field(..., description="인기 노선")
    top_stations: list[StationStatistics] = Field(..., description="인기 정류장")


class GlobalStatisticsResponse(BaseModel):
    """전역 통계 응답"""

    period: Literal["24h", "7d", "30d", "all"] = Field(..., description="조회 기간")
    period_start: datetime = Field(..., description="기간 시작")
    period_end: datetime = Field(..., description="기간 종료")
    statistics: GlobalStatisticsData = Field(..., description="통계 데이터")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "period": "7d",
                    "period_start": "2026-03-11T00:00:00Z",
                    "period_end": "2026-03-18T23:59:59Z",
                    "statistics": {
                        "total_users": 1247,
                        "active_users_7d": 523,
                        "total_notifications": 8932,
                        "successful_notifications": 8104,
                        "failed_notifications": 828,
                        "success_rate": 90.73,
                        "top_routes": [
                            {"route_name": "721", "count": 523, "route_type": "간선"}
                        ],
                        "top_stations": [
                            {"station_name": "신설동역", "ars_id": "01234", "count": 234}
                        ],
                    },
                }
            ]
        }
    }
