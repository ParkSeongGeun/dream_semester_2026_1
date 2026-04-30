"""
Bus API 통합 테스트

iOS 프론트엔드 호환 응답 구조(`{msgHeader, msgBody.itemList}`)를 검증.
Seoul Bus API와 Redis는 mock 처리.
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestBusArrivalsAPI:
    """GET /api/v1/bus/arrivals — iOS BusArrivalResponse 호환"""

    async def test_get_bus_arrivals_success(self, client: AsyncClient):
        """캐시 미스 → API 호출 → iOS 형식으로 응답"""
        seoul_raw = {
            "msgHeader": {"headerCd": "0", "headerMsg": "정상", "itemCount": 1},
            "msgBody": {
                "itemList": [
                    {
                        "rtNm": "721",
                        "arrmsg1": "2분후[2번째 전]",
                        "adirection": "신설동",
                        "routeType": "3",
                        "isFullFlag1": "0",
                        "isLast1": "0",
                        "congestion1": "3",
                    }
                ]
            },
        }

        with patch("app.api.v1.bus.get_cache", new_callable=AsyncMock, return_value=None), \
             patch("app.api.v1.bus.set_cache", new_callable=AsyncMock, return_value=True), \
             patch("app.api.v1.bus.seoul_bus_service") as mock_service:

            mock_service.get_station_arrival_info = AsyncMock(return_value=seoul_raw)
            mock_service.normalize_arrival_response.return_value = {
                "msgHeader": {"headerCd": "0", "headerMsg": "정상", "itemCount": 1},
                "msgBody": {
                    "itemList": [
                        {
                            "rtNm": "721",
                            "arrmsg1": "2분후[2번째 전]",
                            "adirection": "신설동",
                            "routeType": "3",
                            "isFullFlag1": "0",
                            "isLast1": "0",
                            "congestion1": "3",
                        }
                    ]
                },
            }

            response = await client.get("/api/v1/bus/arrivals?ars_id=01234")

            assert response.status_code == 200
            data = response.json()
            assert data["msgHeader"]["headerCd"] == "0"
            assert len(data["msgBody"]["itemList"]) == 1
            item = data["msgBody"]["itemList"][0]
            assert item["rtNm"] == "721"
            assert item["adirection"] == "신설동"
            assert item["congestion1"] == "3"

    async def test_get_bus_arrivals_cache_hit(self, client: AsyncClient):
        """캐시 히트 시 정규화된 형식 그대로 반환"""
        cached = {
            "msgHeader": {"headerCd": "0", "headerMsg": "정상", "itemCount": 1},
            "msgBody": {
                "itemList": [
                    {
                        "rtNm": "721",
                        "arrmsg1": "3분후",
                        "adirection": "신설동",
                        "routeType": "3",
                        "isFullFlag1": "0",
                        "isLast1": "0",
                        "congestion1": "4",
                    }
                ]
            },
        }
        with patch("app.api.v1.bus.get_cache", new_callable=AsyncMock, return_value=cached):
            response = await client.get("/api/v1/bus/arrivals?ars_id=01234")
            assert response.status_code == 200
            data = response.json()
            assert data["msgHeader"]["itemCount"] == 1
            assert data["msgBody"]["itemList"][0]["rtNm"] == "721"

    async def test_get_bus_arrivals_no_data_passthrough(self, client: AsyncClient):
        """결과 없음 (headerCd=4) — 200 으로 그대로 통과 (iOS가 헤더로 분기)"""
        no_data = {
            "msgHeader": {"headerCd": "4", "headerMsg": "결과가 없습니다.", "itemCount": 0},
            "msgBody": {"itemList": []},
        }
        with patch("app.api.v1.bus.get_cache", new_callable=AsyncMock, return_value=None), \
             patch("app.api.v1.bus.set_cache", new_callable=AsyncMock, return_value=True), \
             patch("app.api.v1.bus.seoul_bus_service") as mock_service:

            mock_service.get_station_arrival_info = AsyncMock(return_value={})
            mock_service.normalize_arrival_response.return_value = no_data

            response = await client.get("/api/v1/bus/arrivals?ars_id=01234")

            assert response.status_code == 200
            data = response.json()
            assert data["msgHeader"]["headerCd"] == "4"
            assert data["msgBody"]["itemList"] == []

    async def test_get_bus_arrivals_api_error(self, client: AsyncClient):
        """Seoul Bus API 장애 → 503"""
        with patch("app.api.v1.bus.get_cache", new_callable=AsyncMock, return_value=None), \
             patch("app.api.v1.bus.seoul_bus_service") as mock_service:

            mock_service.get_station_arrival_info = AsyncMock(
                side_effect=Exception("API connection failed")
            )

            response = await client.get("/api/v1/bus/arrivals?ars_id=01234")
            assert response.status_code == 503
            data = response.json()
            assert data["detail"]["error_code"] == "EXTERNAL_API_ERROR"

    async def test_get_bus_arrivals_invalid_ars_id_too_short(self, client: AsyncClient):
        """ars_id 길이 검증 (min 4)"""
        response = await client.get("/api/v1/bus/arrivals?ars_id=12")
        assert response.status_code == 422

    async def test_get_bus_arrivals_missing_ars_id(self, client: AsyncClient):
        response = await client.get("/api/v1/bus/arrivals")
        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
class TestNearbyStationsAPI:
    """GET /api/v1/bus/stations — iOS StationByPosResponse 호환"""

    async def test_get_nearby_stations_success(self, client: AsyncClient):
        """위치 기반 정류소 조회 성공"""
        normalized = {
            "msgHeader": {"headerCd": "0", "headerMsg": "정상", "itemCount": 1},
            "msgBody": {
                "itemList": [
                    {
                        "stationId": "100000001",
                        "stationNm": "서울역",
                        "arsId": "02001",
                        "gpsX": "126.9707",
                        "gpsY": "37.5547",
                        "dist": "42",
                        "stationTp": "0",
                    }
                ]
            },
        }

        with patch("app.api.v1.bus.get_cache", new_callable=AsyncMock, return_value=None), \
             patch("app.api.v1.bus.set_cache", new_callable=AsyncMock, return_value=True), \
             patch("app.api.v1.bus.seoul_bus_service") as mock_service:

            mock_service.get_stations_by_position = AsyncMock(return_value={})
            mock_service.normalize_station_response.return_value = normalized

            response = await client.get(
                "/api/v1/bus/stations?tmX=126.9707&tmY=37.5547&radius=100"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["msgHeader"]["headerCd"] == "0"
            station = data["msgBody"]["itemList"][0]
            assert station["stationNm"] == "서울역"
            assert station["arsId"] == "02001"
            assert station["gpsX"] == "126.9707"

    async def test_get_nearby_stations_radius_validation(self, client: AsyncClient):
        """radius 범위 외 (>2000)"""
        response = await client.get(
            "/api/v1/bus/stations?tmX=126.9707&tmY=37.5547&radius=5000"
        )
        assert response.status_code == 422

    async def test_get_nearby_stations_missing_params(self, client: AsyncClient):
        response = await client.get("/api/v1/bus/stations?tmX=126.9707")
        assert response.status_code == 422
