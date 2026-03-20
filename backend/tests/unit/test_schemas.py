"""
Pydantic 스키마 단위 테스트

스키마 검증 로직을 테스트합니다.
"""

import pytest
from uuid import uuid4
from pydantic import ValidationError
from app.schemas.boarding import BoardingRecordRequest
from app.schemas.statistics import UserStatisticsResponse


class TestBoardingRecordRequest:
    """BoardingRecordRequest 스키마 테스트"""

    def test_valid_boarding_record(self):
        """유효한 탑승 기록 데이터"""
        data = {
            "route_name": "721",
            "sound_enabled": True,
            "notification_status": "success",
        }
        record = BoardingRecordRequest(**data)
        assert record.route_name == "721"
        assert record.sound_enabled is True
        assert record.notification_status == "success"

    def test_boarding_record_with_all_fields(self):
        """모든 필드 포함"""
        data = {
            "device_id": str(uuid4()),
            "route_name": "721",
            "route_type": "간선",
            "bus_device_id": "BF_DREAM_721",
            "station_name": "신설동역",
            "ars_id": "01234",
            "latitude": 37.575000,
            "longitude": 127.025000,
            "sound_enabled": True,
            "notification_status": "success",
        }
        record = BoardingRecordRequest(**data)
        assert record.device_id is not None
        assert record.route_name == "721"

    def test_invalid_notification_status(self):
        """잘못된 notification_status"""
        data = {
            "route_name": "721",
            "sound_enabled": True,
            "notification_status": "invalid",  # 잘못된 값
        }
        with pytest.raises(ValidationError):
            BoardingRecordRequest(**data)

    def test_invalid_latitude_too_high(self):
        """위도 값이 너무 큰 경우"""
        data = {
            "route_name": "721",
            "sound_enabled": True,
            "notification_status": "success",
            "latitude": 95.0,  # > 90
        }
        with pytest.raises(ValidationError):
            BoardingRecordRequest(**data)

    def test_invalid_latitude_too_low(self):
        """위도 값이 너무 작은 경우"""
        data = {
            "route_name": "721",
            "sound_enabled": True,
            "notification_status": "success",
            "latitude": -95.0,  # < -90
        }
        with pytest.raises(ValidationError):
            BoardingRecordRequest(**data)

    def test_invalid_longitude_too_high(self):
        """경도 값이 너무 큰 경우"""
        data = {
            "route_name": "721",
            "sound_enabled": True,
            "notification_status": "success",
            "longitude": 200.0,  # > 180
        }
        with pytest.raises(ValidationError):
            BoardingRecordRequest(**data)

    def test_invalid_longitude_too_low(self):
        """경도 값이 너무 작은 경우"""
        data = {
            "route_name": "721",
            "sound_enabled": True,
            "notification_status": "success",
            "longitude": -200.0,  # < -180
        }
        with pytest.raises(ValidationError):
            BoardingRecordRequest(**data)

    def test_route_name_validation(self):
        """route_name 검증 - 빈 문자열"""
        data = {
            "route_name": "   ",  # 공백만
            "sound_enabled": True,
            "notification_status": "success",
        }
        with pytest.raises(ValidationError):
            BoardingRecordRequest(**data)

    def test_missing_required_field(self):
        """필수 필드 누락"""
        data = {
            "sound_enabled": True,
            # route_name 누락
            # notification_status 누락
        }
        with pytest.raises(ValidationError):
            BoardingRecordRequest(**data)


class TestSchemaValidation:
    """스키마 검증 테스트"""

    def test_notification_status_allowed_values(self):
        """notification_status 허용 값 테스트"""
        allowed_statuses = ["success", "device_not_found", "failure"]

        for status in allowed_statuses:
            data = {
                "route_name": "721",
                "sound_enabled": True,
                "notification_status": status,
            }
            record = BoardingRecordRequest(**data)
            assert record.notification_status == status

    def test_notification_status_disallowed_value(self):
        """notification_status 비허용 값 테스트"""
        disallowed_statuses = ["pending", "error", "timeout", ""]

        for status in disallowed_statuses:
            data = {
                "route_name": "721",
                "sound_enabled": True,
                "notification_status": status,
            }
            with pytest.raises(ValidationError):
                BoardingRecordRequest(**data)
