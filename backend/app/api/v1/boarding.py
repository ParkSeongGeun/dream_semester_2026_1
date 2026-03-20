"""
탑승 기록 API

배려석 알림 전송 기록을 저장하는 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.boarding_record import BoardingRecord
from app.schemas.boarding import BoardingRecordRequest, BoardingRecordResponse

router = APIRouter(prefix="/boarding", tags=["Boarding"])


@router.post(
    "/record",
    response_model=BoardingRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="탑승 기록 저장",
    description="사용자의 배려석 알림 전송 기록을 저장합니다.",
    responses={
        400: {"description": "유효성 검증 실패"},
    },
)
async def create_boarding_record(
    request: BoardingRecordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    탑승 기록 저장

    Args:
        request: 탑승 기록 요청 데이터
        db: 데이터베이스 세션

    Returns:
        BoardingRecordResponse: 저장된 기록 정보

    Raises:
        HTTPException 400: 유효성 검증 실패
    """
    try:
        # BoardingRecord 모델 인스턴스 생성
        boarding_record = BoardingRecord(
            device_id=request.device_id,
            route_name=request.route_name,
            route_type=request.route_type,
            bus_device_id=request.bus_device_id,
            station_id=request.station_id,
            station_name=request.station_name,
            ars_id=request.ars_id,
            latitude=request.latitude,
            longitude=request.longitude,
            sound_enabled=request.sound_enabled,
            notification_status=request.notification_status,
        )

        # 데이터베이스에 저장
        db.add(boarding_record)
        await db.commit()
        await db.refresh(boarding_record)

        # 응답 반환
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
