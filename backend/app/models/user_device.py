"""
UserDevice 모델

iOS 기기 정보를 저장하는 테이블 (users_devices)
- 기기 고유 ID(UUID)로 익명 사용자 식별
- 향후 임산부 인증, 알림 설정 등 확장 가능
"""

import uuid
from datetime import datetime, timezone, date

from sqlalchemy import Boolean, CheckConstraint, Date, String, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserDevice(Base):
    __tablename__ = "users_devices"

    # Primary Key
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="기기 고유 ID",
    )

    # Device Information
    device_token: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        comment="iOS 기기 식별자 (선택)",
    )
    device_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="기기 이름 (예: iPhone 14 Pro)",
    )
    os_version: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="iOS 버전 (예: iOS 17.2)",
    )
    app_version: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="앱 버전 (예: 1.2.1)",
    )

    # User Profile
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="임산부 인증 여부",
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="출산 예정일 (임신 기간 추적용)",
    )

    # Settings
    sound_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="알림음 설정",
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        comment="기기 등록 시간",
    )
    last_active_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="마지막 활동 시간",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            r"app_version ~ '^\d+\.\d+\.\d+$'",
            name="chk_app_version",
        ),
    )

    # Relationships
    boarding_records: Mapped[list["BoardingRecord"]] = relationship(
        "BoardingRecord",
        back_populates="device",
        cascade="save-update, merge",
    )

    def __repr__(self) -> str:
        return (
            f"UserDevice(device_id={self.device_id!r}, "
            f"device_name={self.device_name!r}, "
            f"app_version={self.app_version!r})"
        )
