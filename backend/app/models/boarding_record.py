"""
BoardingRecord 모델

배려석 알림 전송 기록을 저장하는 테이블 (boarding_records)
- 통계 분석 (인기 노선/정류장, 성공률)
- device_id는 NULL 허용 (익명 사용자 지원)
- 기기 삭제 시 device_id → NULL (ON DELETE SET NULL)
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class BoardingRecord(Base):
    __tablename__ = "boarding_records"

    # Primary Key
    record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="기록 고유 ID",
    )

    # Foreign Key (nullable: 익명 사용자 지원)
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users_devices.device_id", ondelete="SET NULL"),
        nullable=True,
        comment="기기 ID (FK, 익명 사용자는 NULL)",
    )

    # Bus Information
    route_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="버스 노선명 (예: 721, 강동01)",
    )
    route_type: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="노선 유형 (간선, 지선, 마을 등)",
    )
    bus_device_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="BLE 기기 ID (예: BF_DREAM_721)",
    )

    # Station Information
    station_id: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="정류장 ID (서울시 API 기준)",
    )
    station_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="정류장 이름 (예: 신설동역)",
    )
    ars_id: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="정류장 고유번호 (ARS ID)",
    )

    # Location
    latitude: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
        comment="탑승 위치 위도",
    )
    longitude: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
        comment="탑승 위치 경도",
    )

    # Notification Details
    sound_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="알림음 사용 여부",
    )
    notification_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="전송 결과 (success, device_not_found, failure)",
    )

    # Timestamp
    boarded_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        comment="탑승 시간",
    )

    # Constraints & Indexes
    __table_args__ = (
        CheckConstraint(
            "notification_status IN ('success', 'device_not_found', 'failure')",
            name="chk_notification_status",
        ),
        CheckConstraint(
            "latitude BETWEEN -90 AND 90",
            name="chk_latitude",
        ),
        CheckConstraint(
            "longitude BETWEEN -180 AND 180",
            name="chk_longitude",
        ),
        # 통계 쿼리 최적화 인덱스
        Index("idx_boarding_records_device", "device_id"),
        Index("idx_boarding_records_route", "route_name"),
        Index("idx_boarding_records_boarded_at", "boarded_at"),
        Index("idx_boarding_records_station", "station_id"),
        Index("idx_boarding_records_status", "notification_status"),
        # 복합 인덱스: 사용자별 최근 탑승 기록 조회
        Index("idx_boarding_records_device_date", "device_id", "boarded_at"),
    )

    # Relationships
    device: Mapped["UserDevice | None"] = relationship(
        "UserDevice",
        back_populates="boarding_records",
    )

    def __repr__(self) -> str:
        return (
            f"BoardingRecord(record_id={self.record_id!r}, "
            f"route_name={self.route_name!r}, "
            f"notification_status={self.notification_status!r})"
        )
