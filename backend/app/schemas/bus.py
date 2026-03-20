"""
버스 도착 정보 스키마

서울시 버스 API 데이터를 위한 스키마
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BusArrivalInfo(BaseModel):
    """단일 버스 도착 정보"""

    route_name: str = Field(..., description="버스 노선명", examples=["721"])
    route_type: str = Field(..., description="노선 유형", examples=["간선"])
    arrival_message: str = Field(
        ..., description="도착 메시지", examples=["2분후[2번째 전]"]
    )
    direction: str | None = Field(
        default=None, description="방향(종점)", examples=["신설동"]
    )
    congestion: Literal["empty", "normal", "crowded", "unknown"] = Field(
        ..., description="혼잡도"
    )
    is_full: bool = Field(..., description="만차 여부")
    is_last_bus: bool = Field(..., description="막차 여부")
    bus_type: str = Field(..., description="버스 유형", examples=["gangseon"])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "route_name": "721",
                    "route_type": "간선",
                    "arrival_message": "2분후[2번째 전]",
                    "direction": "신설동",
                    "congestion": "empty",
                    "is_full": False,
                    "is_last_bus": False,
                    "bus_type": "gangseon",
                }
            ]
        }
    }


class BusArrivalResponse(BaseModel):
    """버스 도착 정보 응답"""

    ars_id: str = Field(..., description="정류장 고유번호", examples=["01234"])
    station_name: str = Field(..., description="정류장 이름", examples=["신설동역"])
    arrivals: list[BusArrivalInfo] = Field(..., description="버스 도착 정보 목록")
    cached: bool = Field(..., description="캐시 데이터 여부")
    cached_at: datetime | None = Field(default=None, description="캐시 저장 시간")
    expires_at: datetime | None = Field(default=None, description="캐시 만료 시간")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ars_id": "01234",
                    "station_name": "신설동역",
                    "arrivals": [
                        {
                            "route_name": "721",
                            "route_type": "간선",
                            "arrival_message": "2분후[2번째 전]",
                            "direction": "신설동",
                            "congestion": "empty",
                            "is_full": False,
                            "is_last_bus": False,
                            "bus_type": "gangseon",
                        }
                    ],
                    "cached": True,
                    "cached_at": "2026-03-18T10:29:30Z",
                    "expires_at": "2026-03-18T10:30:30Z",
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """에러 응답"""

    detail: str = Field(..., description="에러 메시지")
    error_code: str = Field(..., description="에러 코드")
    timestamp: datetime | None = Field(default=None, description="에러 발생 시간")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "detail": "No bus information found for this station",
                    "error_code": "NO_BUS_INFO",
                    "timestamp": "2026-03-18T10:30:00Z",
                }
            ]
        }
    }
