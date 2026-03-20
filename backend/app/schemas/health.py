"""
헬스체크 스키마

서버 상태 확인을 위한 스키마
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    """개별 서비스 상태"""

    database: Literal["connected", "disconnected"] = Field(
        ..., description="PostgreSQL 연결 상태"
    )
    redis: Literal["connected", "disconnected"] = Field(
        ..., description="Redis 연결 상태"
    )
    seoul_bus_api: Literal["reachable", "unreachable"] = Field(
        ..., description="서울시 버스 API 연결 상태"
    )


class HealthCheckResponse(BaseModel):
    """헬스체크 응답"""

    status: Literal["healthy", "unhealthy"] = Field(..., description="전체 서비스 상태")
    timestamp: datetime = Field(..., description="체크 시간")
    version: str = Field(..., description="API 버전")
    services: ServiceStatus = Field(..., description="개별 서비스 상태")
    errors: list[str] | None = Field(default=None, description="에러 목록")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "timestamp": "2026-03-18T10:30:00Z",
                    "version": "1.0.0",
                    "services": {
                        "database": "connected",
                        "redis": "connected",
                        "seoul_bus_api": "reachable",
                    },
                    "errors": None,
                }
            ]
        }
    }
