"""
Bus Arrivals API 통합 테스트

버스 도착 정보 조회 API를 테스트합니다.
Seoul Bus API와 Redis를 mock하여 외부 의존성 없이 테스트합니다.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


@pytest.mark.integration
@pytest.mark.asyncio
class TestBusArrivalsAPI:
    """버스 도착 정보 API 테스트"""

    async def test_get_bus_arrivals_success(self, client: AsyncClient, mock_seoul_api_success):
        """버스 도착 정보 조회 - 성공 (캐시 미스 → API 호출)"""
        with patch("app.api.v1.bus.get_cache", new_callable=AsyncMock, return_value=None), \
             patch("app.api.v1.bus.set_cache", new_callable=AsyncMock, return_value=True), \
             patch("app.api.v1.bus.seoul_bus_service") as mock_service:

            mock_service.get_station_arrival_info = AsyncMock(return_value=mock_seoul_api_success)
            mock_service.parse_arrival_info.return_value = [
                {
                    "route_name": "721",
                    "route_type": "간선",
                    "arrival_message": "2분후[2번째 전]",
                    "direction": "신설동",
                    "congestion": "empty",
                    "is_full": False,
                    "is_last_bus": False,
                    "bus_type": "3",
                },
            ]

            response = await client.get("/api/v1/bus/arrivals?ars_id=01234")

            assert response.status_code == 200
            data = response.json()
            assert data["ars_id"] == "01234"
            assert data["cached"] is False
            assert len(data["arrivals"]) == 1
            assert data["arrivals"][0]["route_name"] == "721"

    async def test_get_bus_arrivals_cache_hit(self, client: AsyncClient):
        """버스 도착 정보 조회 - 캐시 히트"""
        cached_data = {
            "station_name": "신설동역",
            "arrivals": [
                {
                    "route_name": "721",
                    "route_type": "간선",
                    "arrival_message": "3분후",
                    "direction": "신설동",
                    "congestion": "normal",
                    "is_full": False,
                    "is_last_bus": False,
                    "bus_type": "3",
                },
            ],
            "cached_at": "2026-03-25T10:00:00+00:00",
            "expires_at": "2026-03-25T10:01:00+00:00",
        }

        with patch("app.api.v1.bus.get_cache", new_callable=AsyncMock, return_value=cached_data):
            response = await client.get("/api/v1/bus/arrivals?ars_id=01234")

            assert response.status_code == 200
            data = response.json()
            assert data["cached"] is True
            assert data["station_name"] == "신설동역"

    async def test_get_bus_arrivals_no_data(self, client: AsyncClient):
        """버스 도착 정보 조회 - 데이터 없음 (headerCd != 0)"""
        no_data_response = {
            "msgHeader": {"headerCd": "4", "itemCount": 0},
            "msgBody": None,
        }

        with patch("app.api.v1.bus.get_cache", new_callable=AsyncMock, return_value=None), \
             patch("app.api.v1.bus.seoul_bus_service") as mock_service:

            mock_service.get_station_arrival_info = AsyncMock(return_value=no_data_response)

            response = await client.get("/api/v1/bus/arrivals?ars_id=01234")

            assert response.status_code == 404
            data = response.json()
            assert data["detail"]["error_code"] == "NO_BUS_INFO"

    async def test_get_bus_arrivals_api_error(self, client: AsyncClient):
        """버스 도착 정보 조회 - Seoul Bus API 장애"""
        with patch("app.api.v1.bus.get_cache", new_callable=AsyncMock, return_value=None), \
             patch("app.api.v1.bus.seoul_bus_service") as mock_service:

            mock_service.get_station_arrival_info = AsyncMock(
                side_effect=Exception("API connection failed")
            )

            response = await client.get("/api/v1/bus/arrivals?ars_id=01234")

            assert response.status_code == 503
            data = response.json()
            assert data["detail"]["error_code"] == "EXTERNAL_API_ERROR"

    async def test_get_bus_arrivals_invalid_ars_id(self, client: AsyncClient):
        """버스 도착 정보 조회 - 잘못된 ars_id (길이 불일치)"""
        response = await client.get("/api/v1/bus/arrivals?ars_id=123")
        assert response.status_code == 422

    async def test_get_bus_arrivals_missing_ars_id(self, client: AsyncClient):
        """버스 도착 정보 조회 - ars_id 누락"""
        response = await client.get("/api/v1/bus/arrivals")
        assert response.status_code == 422
