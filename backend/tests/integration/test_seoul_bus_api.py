"""
Seoul Bus API Integration Tests

서울시 버스 정보 API 통합 테스트

- 실제 API 호출 테스트: @pytest.mark.slow (네트워크 필요)
- Mock 기반 테스트: 빠르고 안정적 (항상 실행)
"""

import pytest
import httpx
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.seoul_bus_api import SeoulBusAPIService


# ============================================
# Seoul Bus API Service Tests (실제 API 호출)
# ============================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_station_by_position_seoul_station(seoul_api_test_locations):
    """
    Test 1: 서울역 근처 정류장 조회

    서울역 좌표로 정류장을 조회하고 결과를 검증합니다.
    """
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
        assert "stationNm" in first_station
        assert "arsId" in first_station


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_station_by_position_gangnam_station(seoul_api_test_locations):
    """
    Test 2: 강남역 근처 정류장 조회

    강남역 좌표로 정류장을 조회하고 결과를 검증합니다.
    """
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
    """
    Test 3: 서울 외 지역 조회 (부산)

    서울이 아닌 지역 좌표로 조회 시 데이터 없음 응답 검증
    """
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
    # 부산은 서울 외 지역이므로 데이터 없음(headerCd != "0") 이거나 빈 리스트
    header_cd = response["msgHeader"]["headerCd"]
    if header_cd == "0":
        items = response.get("msgBody", {}).get("itemList", [])
        if isinstance(items, dict):
            items = [items]
        # 부산 근처에 서울 버스 정류장이 있을 수 없음
        assert len(items) == 0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_arrivals_by_station_gangnam(seoul_api_test_locations):
    """
    Test 4: 강남역 버스 도착 정보 조회

    실제 강남역 정류장(ARS ID: 23288)의 버스 도착 정보를 조회합니다.
    """
    service = SeoulBusAPIService()
    ars_id = seoul_api_test_locations["gangnam_station"]["ars_id"]

    try:
        response = await service.get_station_arrival_info(ars_id)
    except httpx.HTTPError:
        pytest.skip("Seoul Bus API unreachable")

    assert "msgHeader" in response
    assert "headerCd" in response["msgHeader"]

    if response["msgHeader"]["headerCd"] == "0":
        msg_body = response.get("msgBody", {})
        if msg_body and msg_body.get("itemList"):
            first_bus = msg_body["itemList"]
            if isinstance(first_bus, list):
                first_bus = first_bus[0]
            assert "rtNm" in first_bus


# ============================================
# Bus Type Classification Tests
# ============================================

@pytest.mark.unit
def test_bus_type_classification_all_types(bus_type_test_cases):
    """
    Test 5: 버스 유형 분류 (7가지 + unknown)

    parse_bus_route_type의 모든 코드 매핑을 검증
    """
    for code, expected_type in bus_type_test_cases:
        result = SeoulBusAPIService.parse_bus_route_type(code)
        assert result == expected_type, (
            f"Failed for code '{code}': expected {expected_type}, got {result}"
        )


@pytest.mark.unit
def test_bus_type_classification_gangseon():
    """Test 6: 간선버스 분류 (코드 3)"""
    assert SeoulBusAPIService.parse_bus_route_type("3") == "간선"


@pytest.mark.unit
def test_bus_type_classification_jiseon():
    """Test 7: 지선버스 분류 (코드 4)"""
    assert SeoulBusAPIService.parse_bus_route_type("4") == "지선"


@pytest.mark.unit
def test_bus_type_classification_gwangyeok():
    """Test 8: 광역버스 분류 (코드 6)"""
    assert SeoulBusAPIService.parse_bus_route_type("6") == "광역"


@pytest.mark.unit
def test_bus_type_classification_gongHang():
    """Test 9: 공항버스 분류 (코드 1)"""
    assert SeoulBusAPIService.parse_bus_route_type("1") == "공항"


@pytest.mark.unit
def test_bus_type_classification_sunhwan():
    """Test 10: 순환버스 분류 (코드 5)"""
    assert SeoulBusAPIService.parse_bus_route_type("5") == "순환"


@pytest.mark.unit
def test_bus_type_classification_simya():
    """Test 11: 인천버스 분류 (코드 7)"""
    assert SeoulBusAPIService.parse_bus_route_type("7") == "인천"


@pytest.mark.unit
def test_bus_type_classification_maeul():
    """Test 12: 마을버스 분류 (코드 2)"""
    assert SeoulBusAPIService.parse_bus_route_type("2") == "마을"


# ============================================
# Congestion Parsing Tests
# ============================================

@pytest.mark.unit
def test_congestion_parsing_all_cases(congestion_test_cases):
    """
    Test 13: 혼잡도 파싱 (모든 케이스)

    parse_congestion의 모든 코드 매핑을 검증
    """
    for code, expected_result in congestion_test_cases:
        result = SeoulBusAPIService.parse_congestion(code)
        assert result == expected_result, (
            f"Failed for code '{code}': expected {expected_result}, got {result}"
        )


@pytest.mark.unit
def test_congestion_parsing_empty():
    """Test 14: 여유 혼잡도 (코드 3)"""
    assert SeoulBusAPIService.parse_congestion("3") == "empty"


@pytest.mark.unit
def test_congestion_parsing_normal():
    """Test 15: 보통 혼잡도 (코드 4)"""
    assert SeoulBusAPIService.parse_congestion("4") == "normal"


@pytest.mark.unit
def test_congestion_parsing_crowded():
    """Test 16: 혼잡 (코드 5)"""
    assert SeoulBusAPIService.parse_congestion("5") == "crowded"


@pytest.mark.unit
def test_congestion_parsing_unknown():
    """Test 17: 알 수 없음 (None, 빈 문자열, 매핑에 없는 값)"""
    assert SeoulBusAPIService.parse_congestion(None) == "unknown"
    assert SeoulBusAPIService.parse_congestion("") == "unknown"
    assert SeoulBusAPIService.parse_congestion("99") == "unknown"


# ============================================
# Error Handling Tests
# ============================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_seoul_api_timeout_handling():
    """
    Test 18: Seoul Bus API 타임아웃 처리

    httpx.TimeoutException 발생 시 재시도 후 최종 예외 발생 확인
    """
    service = SeoulBusAPIService()

    with patch("app.services.seoul_bus_api.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        with pytest.raises(httpx.TimeoutException):
            await service.get_station_arrival_info("01234")

        # max_retries(3)만큼 재시도했는지 확인
        assert mock_client.get.call_count == service.max_retries


@pytest.mark.integration
@pytest.mark.asyncio
async def test_seoul_api_retry_logic():
    """
    Test 19: Seoul Bus API 재시도 로직

    처음 2회 실패 후 3회째 성공하는 시나리오 검증
    """
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
        # 2회 실패 후 3회째 성공
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
# Response Structure Validation Tests
# ============================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_station_response_structure():
    """
    Test 20: 정류장 조회 응답 구조 검증

    Seoul Bus API 응답이 예상 구조를 따르는지 확인
    """
    service = SeoulBusAPIService()

    try:
        response = await service.get_stations_by_position(
            latitude=37.5547125,
            longitude=126.9707878,
            radius=100,
        )
    except httpx.HTTPError:
        pytest.skip("Seoul Bus API unreachable")

    # msgHeader 검증
    assert "msgHeader" in response
    assert "headerCd" in response["msgHeader"]

    # msgBody 검증 (성공 시)
    if response["msgHeader"]["headerCd"] == "0":
        assert "msgBody" in response
        msg_body = response["msgBody"]
        assert msg_body is not None
        assert "itemList" in msg_body


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_arrivals_response_structure():
    """
    Test 21: 버스 도착 정보 응답 구조 검증

    Seoul Bus API 버스 도착 응답이 예상 구조를 따르는지 확인
    """
    service = SeoulBusAPIService()

    try:
        response = await service.get_station_arrival_info("23288")  # 강남역
    except httpx.HTTPError:
        pytest.skip("Seoul Bus API unreachable")

    # msgHeader 검증
    assert "msgHeader" in response
    assert "headerCd" in response["msgHeader"]

    # msgBody 검증 (성공 시)
    if response["msgHeader"]["headerCd"] == "0":
        msg_body = response.get("msgBody", {})
        if msg_body and msg_body.get("itemList"):
            items = msg_body["itemList"]
            if isinstance(items, dict):
                items = [items]
            bus = items[0]
            assert "rtNm" in bus


# ============================================
# Performance Tests
# ============================================

@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_api_calls():
    """
    Test 22: 동시 API 호출 성능 테스트

    여러 정류장을 동시에 조회할 때 성능 확인
    """
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

    # 최소한 결과가 반환되어야 함 (에러든 성공이든)
    assert len(results) == 3
    # 동시 호출이므로 순차 호출보다 빨라야 함 (타임아웃 5초 * 3 = 15초 이내)
    assert elapsed < 15.0
