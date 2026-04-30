"""
Seoul Bus API Integration Tests

iOS 프론트엔드(ComfortableMove) 호환 응답 구조 검증.

- 실제 API 호출 테스트: @pytest.mark.slow (네트워크 필요, 통합 환경에서만)
- Mock 기반 테스트: 빠르고 안정적 (항상 실행)
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.seoul_bus_api import SeoulBusAPIService


# ============================================
# 실제 Seoul Bus API 호출 테스트 (slow)
# ============================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_station_by_position_seoul_station(seoul_api_test_locations):
    """서울역 근처 정류장 조회 — iOS 호환 응답 구조 검증"""
    service = SeoulBusAPIService()
    location = seoul_api_test_locations["seoul_station"]

    try:
        response = await service.get_stations_by_position(
            latitude=location["latitude"],
            longitude=location["longitude"],
            radius=100,
        )
    except httpx.HTTPError:
        pytest.skip("Seoul Bus API unreachable")

    assert "msgHeader" in response
    assert "headerCd" in response["msgHeader"]

    if response["msgHeader"]["headerCd"] == "0":
        assert response["msgBody"] is not None
        items = response["msgBody"].get("itemList", [])
        if isinstance(items, dict):
            items = [items]
        assert len(items) > 0

        first_station = items[0]
        # iOS StationItem 필수 필드
        assert "stationNm" in first_station
        assert "arsId" in first_station


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_station_by_position_gangnam_station(seoul_api_test_locations):
    """강남역 근처 정류장 조회"""
    service = SeoulBusAPIService()
    location = seoul_api_test_locations["gangnam_station"]

    try:
        response = await service.get_stations_by_position(
            latitude=location["latitude"],
            longitude=location["longitude"],
            radius=100,
        )
    except httpx.HTTPError:
        pytest.skip("Seoul Bus API unreachable")

    assert "msgHeader" in response

    if response["msgHeader"]["headerCd"] == "0":
        items = response["msgBody"].get("itemList", [])
        if isinstance(items, dict):
            items = [items]
        station_names = [item.get("stationNm", "") for item in items]
        assert any("강남" in name for name in station_names)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_station_by_position_out_of_seoul(seoul_api_test_locations):
    """서울 외 지역 조회 (부산) — 데이터 없음 응답 검증"""
    service = SeoulBusAPIService()
    location = seoul_api_test_locations["busan"]

    try:
        response = await service.get_stations_by_position(
            latitude=location["latitude"],
            longitude=location["longitude"],
            radius=100,
        )
    except httpx.HTTPError:
        pytest.skip("Seoul Bus API unreachable")

    assert "msgHeader" in response
    header_cd = response["msgHeader"]["headerCd"]
    if header_cd == "0":
        items = response.get("msgBody", {}).get("itemList", [])
        if isinstance(items, dict):
            items = [items]
        assert len(items) == 0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_arrivals_by_station_gangnam(seoul_api_test_locations):
    """강남역 버스 도착 정보 — iOS BusArrivalItem.rtNm 필드 검증"""
    service = SeoulBusAPIService()
    ars_id = seoul_api_test_locations["gangnam_station"]["ars_id"]

    try:
        response = await service.get_station_arrival_info(ars_id)
    except httpx.HTTPError:
        pytest.skip("Seoul Bus API unreachable")

    assert "msgHeader" in response

    if response["msgHeader"]["headerCd"] == "0":
        msg_body = response.get("msgBody", {})
        if msg_body and msg_body.get("itemList"):
            first_bus = msg_body["itemList"]
            if isinstance(first_bus, list):
                first_bus = first_bus[0]
            assert "rtNm" in first_bus


# ============================================
# iOS 호환 정규화 — Mock 기반 통합 검증
# ============================================

@pytest.mark.integration
def test_normalize_arrival_response_full_passthrough():
    """서울 API 응답 → iOS BusArrivalResponse 와 동일 키만 노출"""
    raw = {
        "msgHeader": {"headerCd": "0", "headerMsg": "정상", "itemCount": "2"},
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
                    "extraField": "ignore_me",
                },
                {
                    "rtNm": "2012",
                    "arrmsg1": "5분후[5번째 전]",
                    "adirection": "강남",
                    "routeType": "4",
                    "isFullFlag1": "0",
                    "isLast1": "0",
                    "congestion1": "4",
                },
            ]
        },
    }
    out = SeoulBusAPIService.normalize_arrival_response(raw)
    assert out["msgHeader"]["itemCount"] == 2  # int 변환
    assert len(out["msgBody"]["itemList"]) == 2

    item_keys = set(out["msgBody"]["itemList"][0].keys())
    assert item_keys == {
        "rtNm", "arrmsg1", "adirection", "routeType",
        "isFullFlag1", "isLast1", "congestion1",
    }


@pytest.mark.integration
def test_normalize_station_response_full_passthrough():
    """서울 API 응답 → iOS StationByPosResponse 와 동일 키만 노출"""
    raw = {
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
                    "extraField": "ignore",
                }
            ]
        },
    }
    out = SeoulBusAPIService.normalize_station_response(raw)
    keys = set(out["msgBody"]["itemList"][0].keys())
    assert keys == {
        "stationId", "stationNm", "arsId", "gpsX", "gpsY", "dist", "stationTp",
    }


# ============================================
# 에러 처리 / 재시도 로직
# ============================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_seoul_api_timeout_handling():
    """Seoul Bus API 타임아웃 → 재시도 후 최종 예외 발생"""
    service = SeoulBusAPIService()

    with patch("app.services.seoul_bus_api.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        with pytest.raises(httpx.TimeoutException):
            await service.get_station_arrival_info("01234")

        assert mock_client.get.call_count == service.max_retries


@pytest.mark.integration
@pytest.mark.asyncio
async def test_seoul_api_retry_logic():
    """2회 실패 후 3회째 성공"""
    service = SeoulBusAPIService()
    success_response = MagicMock()
    success_response.status_code = 200
    success_response.raise_for_status = MagicMock()
    success_response.json.return_value = {
        "msgHeader": {"headerCd": "0", "itemCount": 1},
        "msgBody": {"itemList": [{"rtNm": "721"}]},
    }

    with patch("app.services.seoul_bus_api.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.side_effect = [
            httpx.HTTPStatusError("500", request=MagicMock(), response=MagicMock()),
            httpx.HTTPStatusError("500", request=MagicMock(), response=MagicMock()),
            success_response,
        ]
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        result = await service.get_station_arrival_info("01234")

        assert result["msgHeader"]["headerCd"] == "0"
        assert mock_client.get.call_count == 3


# ============================================
# 응답 구조 검증 (실제 API)
# ============================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_station_response_structure():
    """정류장 조회 응답 구조 검증"""
    service = SeoulBusAPIService()

    try:
        response = await service.get_stations_by_position(
            latitude=37.5547125,
            longitude=126.9707878,
            radius=100,
        )
    except httpx.HTTPError:
        pytest.skip("Seoul Bus API unreachable")

    assert "msgHeader" in response
    assert "headerCd" in response["msgHeader"]

    if response["msgHeader"]["headerCd"] == "0":
        assert "msgBody" in response
        msg_body = response["msgBody"]
        assert msg_body is not None
        assert "itemList" in msg_body


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_arrivals_response_structure():
    """버스 도착 정보 응답 구조 검증"""
    service = SeoulBusAPIService()

    try:
        response = await service.get_station_arrival_info("23288")  # 강남역
    except httpx.HTTPError:
        pytest.skip("Seoul Bus API unreachable")

    assert "msgHeader" in response
    assert "headerCd" in response["msgHeader"]

    if response["msgHeader"]["headerCd"] == "0":
        msg_body = response.get("msgBody", {})
        if msg_body and msg_body.get("itemList"):
            items = msg_body["itemList"]
            if isinstance(items, dict):
                items = [items]
            bus = items[0]
            assert "rtNm" in bus


# ============================================
# 동시 호출 성능 테스트
# ============================================

@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_api_calls():
    """여러 정류장을 동시에 조회할 때 성능 확인"""
    service = SeoulBusAPIService()

    tasks = [
        service.get_station_arrival_info("23288"),
        service.get_station_arrival_info("01234"),
        service.get_station_arrival_info("12345"),
    ]

    start_time = asyncio.get_event_loop().time()
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception:
        pytest.skip("Seoul Bus API unreachable")
    elapsed = asyncio.get_event_loop().time() - start_time

    assert len(results) == 3
    assert elapsed < 15.0
