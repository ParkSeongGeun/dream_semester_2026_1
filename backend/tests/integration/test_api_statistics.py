"""
Statistics API 통합 테스트

사용자 및 전역 통계 API를 테스트합니다.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.models.user_device import UserDevice
from app.models.boarding_record import BoardingRecord


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserStatisticsAPI:
    """사용자 통계 API 테스트"""

    async def test_get_user_statistics_device_not_found(self, client: AsyncClient):
        """사용자 통계 조회 - 존재하지 않는 기기"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        with patch("app.api.v1.statistics.get_cache", new_callable=AsyncMock, return_value=None):
            response = await client.get(f"/api/v1/statistics/user/{fake_uuid}")

            assert response.status_code == 404
            data = response.json()
            assert data["detail"]["error_code"] == "DEVICE_NOT_FOUND"

    async def test_get_user_statistics_success(self, client: AsyncClient, test_db: AsyncSession):
        """사용자 통계 조회 - 성공 (기기 존재, 기록 없음)"""
        # 테스트용 기기 생성
        device = UserDevice(
            device_name="Test Device",
            app_version="1.0.0",
        )
        test_db.add(device)
        await test_db.commit()
        await test_db.refresh(device)

        with patch("app.api.v1.statistics.get_cache", new_callable=AsyncMock, return_value=None), \
             patch("app.api.v1.statistics.set_cache", new_callable=AsyncMock, return_value=True):
            response = await client.get(
                f"/api/v1/statistics/user/{device.device_id}?period=30d"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["device_id"] == str(device.device_id)
            assert data["period"] == "30d"
            assert data["statistics"]["total_notifications"] == 0
            assert data["statistics"]["success_rate"] == 0.0

    async def test_get_user_statistics_with_records(self, client: AsyncClient, test_db: AsyncSession):
        """사용자 통계 조회 - 탑승 기록이 있는 경우"""
        # 기기 생성
        device = UserDevice(
            device_name="Test Device",
            app_version="1.0.0",
        )
        test_db.add(device)
        await test_db.commit()
        await test_db.refresh(device)

        # 탑승 기록 생성
        for i in range(3):
            record = BoardingRecord(
                device_id=device.device_id,
                route_name="721",
                route_type="간선",
                station_name="신설동역",
                ars_id="01234",
                sound_enabled=True,
                notification_status="success",
            )
            test_db.add(record)

        record_fail = BoardingRecord(
            device_id=device.device_id,
            route_name="2012",
            sound_enabled=True,
            notification_status="failure",
        )
        test_db.add(record_fail)
        await test_db.commit()

        with patch("app.api.v1.statistics.get_cache", new_callable=AsyncMock, return_value=None), \
             patch("app.api.v1.statistics.set_cache", new_callable=AsyncMock, return_value=True):
            response = await client.get(
                f"/api/v1/statistics/user/{device.device_id}?period=all"
            )

            assert response.status_code == 200
            data = response.json()
            stats = data["statistics"]
            assert stats["total_notifications"] == 4
            assert stats["successful_notifications"] == 3
            assert stats["failed_notifications"] == 1
            assert stats["success_rate"] == 75.0

    async def test_get_user_statistics_cache_hit(self, client: AsyncClient):
        """사용자 통계 조회 - 캐시 히트"""
        fake_uuid = "11111111-1111-1111-1111-111111111111"
        cached = {
            "device_id": fake_uuid,
            "period": "7d",
            "period_start": "2026-03-18T00:00:00+00:00",
            "period_end": "2026-03-25T00:00:00+00:00",
            "statistics": {
                "total_notifications": 10,
                "successful_notifications": 9,
                "failed_notifications": 1,
                "success_rate": 90.0,
                "most_used_routes": [],
                "most_used_stations": [],
                "activity_by_day_of_week": {
                    "monday": 0, "tuesday": 0, "wednesday": 0,
                    "thursday": 0, "friday": 0, "saturday": 0, "sunday": 0,
                },
                "last_used": None,
            },
        }

        with patch("app.api.v1.statistics.get_cache", new_callable=AsyncMock, return_value=cached):
            response = await client.get(f"/api/v1/statistics/user/{fake_uuid}?period=7d")

            assert response.status_code == 200
            data = response.json()
            assert data["statistics"]["total_notifications"] == 10

    async def test_get_user_statistics_invalid_period(self, client: AsyncClient):
        """사용자 통계 조회 - 유효하지 않은 기간"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/v1/statistics/user/{fake_uuid}?period=1y")
        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
class TestGlobalStatisticsAPI:
    """전역 통계 API 테스트"""

    async def test_get_global_statistics_success(self, client: AsyncClient, test_db: AsyncSession):
        """전역 통계 조회 - 성공"""
        with patch("app.api.v1.statistics.get_cache", new_callable=AsyncMock, return_value=None), \
             patch("app.api.v1.statistics.set_cache", new_callable=AsyncMock, return_value=True):
            response = await client.get("/api/v1/statistics/global?period=7d")

            assert response.status_code == 200
            data = response.json()
            assert data["period"] == "7d"
            assert "statistics" in data
            stats = data["statistics"]
            assert "total_users" in stats
            assert "active_users_7d" in stats
            assert "total_notifications" in stats
            assert "success_rate" in stats

    async def test_get_global_statistics_24h_period(self, client: AsyncClient, test_db: AsyncSession):
        """전역 통계 조회 - 24시간 기간"""
        with patch("app.api.v1.statistics.get_cache", new_callable=AsyncMock, return_value=None), \
             patch("app.api.v1.statistics.set_cache", new_callable=AsyncMock, return_value=True):
            response = await client.get("/api/v1/statistics/global?period=24h")

            assert response.status_code == 200
            data = response.json()
            assert data["period"] == "24h"

    async def test_get_global_statistics_all_period(self, client: AsyncClient, test_db: AsyncSession):
        """전역 통계 조회 - 전체 기간"""
        with patch("app.api.v1.statistics.get_cache", new_callable=AsyncMock, return_value=None), \
             patch("app.api.v1.statistics.set_cache", new_callable=AsyncMock, return_value=True):
            response = await client.get("/api/v1/statistics/global?period=all")

            assert response.status_code == 200
            data = response.json()
            assert data["period"] == "all"

    async def test_get_global_statistics_cache_hit(self, client: AsyncClient):
        """전역 통계 조회 - 캐시 히트"""
        cached = {
            "period": "7d",
            "period_start": "2026-03-18T00:00:00+00:00",
            "period_end": "2026-03-25T00:00:00+00:00",
            "statistics": {
                "total_users": 100,
                "active_users_7d": 50,
                "total_notifications": 500,
                "successful_notifications": 450,
                "failed_notifications": 50,
                "success_rate": 90.0,
                "top_routes": [],
                "top_stations": [],
            },
        }

        with patch("app.api.v1.statistics.get_cache", new_callable=AsyncMock, return_value=cached):
            response = await client.get("/api/v1/statistics/global?period=7d")

            assert response.status_code == 200
            data = response.json()
            assert data["statistics"]["total_users"] == 100

    async def test_get_global_statistics_with_data(self, client: AsyncClient, test_db: AsyncSession):
        """전역 통계 조회 - 데이터가 있는 경우"""
        # 기기 및 기록 생성
        device = UserDevice(
            device_name="Stats Test",
            app_version="1.0.0",
        )
        test_db.add(device)
        await test_db.commit()
        await test_db.refresh(device)

        for _ in range(5):
            record = BoardingRecord(
                device_id=device.device_id,
                route_name="721",
                station_name="신설동역",
                sound_enabled=True,
                notification_status="success",
            )
            test_db.add(record)
        await test_db.commit()

        with patch("app.api.v1.statistics.get_cache", new_callable=AsyncMock, return_value=None), \
             patch("app.api.v1.statistics.set_cache", new_callable=AsyncMock, return_value=True):
            response = await client.get("/api/v1/statistics/global?period=all")

            assert response.status_code == 200
            data = response.json()
            assert data["statistics"]["total_users"] == 1
            assert data["statistics"]["total_notifications"] == 5
