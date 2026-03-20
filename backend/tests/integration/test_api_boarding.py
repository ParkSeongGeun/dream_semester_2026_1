"""
Boarding API 통합 테스트

탑승 기록 저장 API를 테스트합니다.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestBoardingAPI:
    """탑승 기록 API 테스트"""

    async def test_create_boarding_record_success(
        self, client: AsyncClient, sample_boarding_data
    ):
        """탑승 기록 저장 - 성공"""
        response = await client.post(
            "/api/v1/boarding/record",
            json=sample_boarding_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert "record_id" in data
        assert data["message"] == "Boarding record saved successfully"
        assert "boarded_at" in data

    async def test_create_boarding_record_minimal_data(
        self, client: AsyncClient
    ):
        """탑승 기록 저장 - 최소 필수 데이터만"""
        minimal_data = {
            "route_name": "721",
            "sound_enabled": True,
            "notification_status": "success",
        }

        response = await client.post(
            "/api/v1/boarding/record",
            json=minimal_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert "record_id" in data

    async def test_create_boarding_record_invalid_status(
        self, client: AsyncClient
    ):
        """탑승 기록 저장 - 잘못된 notification_status"""
        invalid_data = {
            "route_name": "721",
            "sound_enabled": True,
            "notification_status": "invalid_status",  # 잘못된 값
        }

        response = await client.post(
            "/api/v1/boarding/record",
            json=invalid_data,
        )

        assert response.status_code == 422  # Validation Error

    async def test_create_boarding_record_missing_required_field(
        self, client: AsyncClient
    ):
        """탑승 기록 저장 - 필수 필드 누락"""
        incomplete_data = {
            "sound_enabled": True,
            # route_name 누락
            # notification_status 누락
        }

        response = await client.post(
            "/api/v1/boarding/record",
            json=incomplete_data,
        )

        assert response.status_code == 422  # Validation Error

    async def test_create_boarding_record_invalid_latitude(
        self, client: AsyncClient
    ):
        """탑승 기록 저장 - 잘못된 위도 값"""
        invalid_data = {
            "route_name": "721",
            "sound_enabled": True,
            "notification_status": "success",
            "latitude": 95.0,  # 범위 초과 (90 이상)
        }

        response = await client.post(
            "/api/v1/boarding/record",
            json=invalid_data,
        )

        assert response.status_code == 422  # Validation Error

    async def test_create_boarding_record_invalid_longitude(
        self, client: AsyncClient
    ):
        """탑승 기록 저장 - 잘못된 경도 값"""
        invalid_data = {
            "route_name": "721",
            "sound_enabled": True,
            "notification_status": "success",
            "longitude": 200.0,  # 범위 초과 (180 이상)
        }

        response = await client.post(
            "/api/v1/boarding/record",
            json=invalid_data,
        )

        assert response.status_code == 422  # Validation Error

    async def test_create_boarding_record_with_device_id(
        self, client: AsyncClient, test_db
    ):
        """탑승 기록 저장 - device_id 포함"""
        from app.models.user_device import UserDevice

        # 테스트용 기기 생성
        device = UserDevice(
            device_name="Test Device",
            app_version="1.0.0",
        )
        test_db.add(device)
        await test_db.commit()
        await test_db.refresh(device)

        boarding_data = {
            "device_id": str(device.device_id),
            "route_name": "721",
            "sound_enabled": True,
            "notification_status": "success",
        }

        response = await client.post(
            "/api/v1/boarding/record",
            json=boarding_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert "record_id" in data


@pytest.mark.integration
@pytest.mark.asyncio
class TestBoardingAPIValidation:
    """탑승 기록 API 입력 검증 테스트"""

    async def test_route_name_too_long(self, client: AsyncClient):
        """route_name이 너무 긴 경우"""
        data = {
            "route_name": "A" * 30,  # 20자 초과
            "sound_enabled": True,
            "notification_status": "success",
        }

        response = await client.post(
            "/api/v1/boarding/record",
            json=data,
        )

        assert response.status_code == 422

    async def test_route_name_empty(self, client: AsyncClient):
        """route_name이 빈 문자열인 경우"""
        data = {
            "route_name": "",
            "sound_enabled": True,
            "notification_status": "success",
        }

        response = await client.post(
            "/api/v1/boarding/record",
            json=data,
        )

        assert response.status_code == 422
