"""
탑승 기록 스키마

배려석 알림 전송 기록을 위한 스키마
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class BoardingRecordRequest(BaseModel):
    """탑승 기록 저장 요청"""

    device_id: UUID | None = Field(
        default=None, description="기기 고유 ID (선택)", examples=["550e8400-..."]
    )
    route_name: str = Field(
        ..., description="버스 노선명", min_length=1, max_length=20, examples=["721"]
    )
    route_type: str | None = Field(
        default=None,
        description="노선 유형",
        max_length=10,
        examples=["간선"],
    )
    bus_device_id: str | None = Field(
        default=None,
        description="BLE 기기 ID",
        max_length=50,
        examples=["BF_DREAM_721"],
    )
    station_id: str | None = Field(
        default=None,
        description="정류장 ID",
        max_length=20,
        examples=["123000001"],
    )
    station_name: str | None = Field(
        default=None,
        description="정류장 이름",
        max_length=100,
        examples=["신설동역"],
    )
    ars_id: str | None = Field(
        default=None,
        description="정류장 고유번호",
        max_length=20,
        examples=["01234"],
    )
    latitude: float | None = Field(
        default=None, description="탑승 위치 위도", ge=-90, le=90, examples=[37.575000]
    )
    longitude: float | None = Field(
        default=None,
        description="탑승 위치 경도",
        ge=-180,
        le=180,
        examples=[127.025000],
    )
    sound_enabled: bool = Field(..., description="알림음 사용 여부")
    notification_status: Literal["success", "device_not_found", "failure"] = Field(
        ..., description="알림 전송 결과"
    )

    @field_validator("route_name")
    @classmethod
    def validate_route_name(cls, v: str) -> str:
        """노선명 검증"""
        if not v.strip():
            raise ValueError("route_name cannot be empty")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "device_id": "550e8400-e29b-41d4-a716-446655440000",
                    "route_name": "721",
                    "route_type": "간선",
                    "bus_device_id": "BF_DREAM_721",
                    "station_id": "123000001",
                    "station_name": "신설동역",
                    "ars_id": "01234",
                    "latitude": 37.575000,
                    "longitude": 127.025000,
                    "sound_enabled": True,
                    "notification_status": "success",
                }
            ]
        }
    }


class BoardingRecordResponse(BaseModel):
    """탑승 기록 저장 응답"""

    record_id: UUID = Field(..., description="기록 고유 ID")
    message: str = Field(..., description="응답 메시지")
    boarded_at: datetime = Field(..., description="탑승 시간")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "record_id": "660e8400-e29b-41d4-a716-446655440001",
                    "message": "Boarding record saved successfully",
                    "boarded_at": "2026-03-18T10:30:00Z",
                }
            ]
        }
    }
