"""
탑승 기록 API

배려석 알림 전송 기록을 저장하는 엔드포인트
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import pseudonymize_device_id
from app.db.session import get_db
from app.models.boarding_record import BoardingRecord
from app.models.user_device import UserDevice
from app.schemas.boarding import BoardingRecordRequest, BoardingRecordResponse

router = APIRouter(prefix="/boarding", tags=["Boarding"])


@router.post(
    "/record",
    response_model=BoardingRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="탑승 기록 저장",
    description=(
        "사용자의 배려석 알림 전송 기록을 저장합니다. "
        "iOS 가 보낸 device_id 가 users_devices 에 없으면 익명 기기로 자동 등록(upsert) 후 기록합니다 "
        "— FK(users_devices.device_id) 위반 방지."
    ),
    responses={
        400: {"description": "유효성 검증 실패"},
    },
)
async def create_boarding_record(
    request: BoardingRecordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    탑승 기록 저장 — iOS BluetoothTransferResult 와 1:1 매핑.

    Args:
        request: 탑승 기록 요청 데이터 (iOS BoardingRecordService.Payload 와 동일)
        db: 데이터베이스 세션

    Returns:
        BoardingRecordResponse: 저장된 기록 정보

    Raises:
        HTTPException 400: 유효성 검증 실패
    """
    try:
        # 개인정보 보호: 원본 device_id 를 그대로 저장하지 않고 가명화(HMAC)한다.
        # 같은 입력은 같은 결과라 통계 집계·FK 관계는 그대로 유지된다.
        device_id = (
            pseudonymize_device_id(request.device_id)
            if request.device_id is not None
            else None
        )

        # 1) device_id 가 있으면 users_devices 자동 upsert (FK 위반 방지).
        #    iOS DeviceIdentityManager 가 생성한 익명 UUID 가 처음 들어오면
        #    UserDevice 레코드를 즉시 만들어 둔다. 이후 통계 API 가 이 행을 기준 키로 사용.
        if device_id is not None:
            existing_q = await db.execute(
                select(UserDevice).where(UserDevice.device_id == device_id)
            )
            existing = existing_q.scalar_one_or_none()
            if existing is None:
                db.add(
                    UserDevice(
                        device_id=device_id,
                        sound_enabled=request.sound_enabled,
                    )
                )
                await db.flush()
            else:
                # 기존 기기는 활동 시간 갱신 (server-side onupdate 가 같은 트랜잭션에선
                # 변경 감지가 없을 수 있으므로 명시적으로 set)
                existing.last_active_at = datetime.now(timezone.utc)

        # 2) BoardingRecord insert
        boarding_record = BoardingRecord(
            device_id=device_id,
            route_name=request.route_name,
            route_type=request.route_type,
            bus_device_id=request.bus_device_id,
            station_id=request.station_id,
            station_name=request.station_name,
            ars_id=request.ars_id,
            # 개인정보 최소 수집: 정밀 위치 대신 약 100m 단위(소수점 3자리)로 절삭하여 저장
            latitude=round(request.latitude, 3) if request.latitude is not None else None,
            longitude=round(request.longitude, 3) if request.longitude is not None else None,
            sound_enabled=request.sound_enabled,
            notification_status=request.notification_status,
        )

        db.add(boarding_record)
        await db.commit()
        await db.refresh(boarding_record)

        return BoardingRecordResponse(
            record_id=boarding_record.record_id,
            message="Boarding record saved successfully",
            boarded_at=boarding_record.boarded_at,
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "detail": f"Failed to save boarding record: {str(e)}",
                "error_code": "VALIDATION_ERROR",
            },
        )
