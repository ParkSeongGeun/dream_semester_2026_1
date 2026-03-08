"""
Seoul Bus API Integration Tests

서울시 버스 정보 API 통합 테스트

실제 Seoul Bus API를 호출하여 응답을 검증합니다.
Week 3 구현 시 주석을 해제하고 사용하세요.
"""

import pytest
import httpx
import asyncio

# Week 3: 실제 서비스 import
# from app.services.seoul_bus_api import (
#     SeoulBusAPIService,
#     classify_bus_type,
#     parse_congestion,
# )


# ============================================
# Seoul Bus API Service Tests
# ============================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_station_by_position_seoul_station(seoul_api_test_locations):
    """
    Test 1: 서울역 근처 정류장 조회

    서울역 좌표로 정류장을 조회하고 결과를 검증합니다.
    """
    # Week 3: 구현 예시
    """
    service = SeoulBusAPIService()
    location = seoul_api_test_locations["seoul_station"]

    response = await service.get_stations_by_position(
        latitude=location["latitude"],
        longitude=location["longitude"],
        radius=100
    )

    # 검증
    assert response["msgHeader"]["headerCd"] == "0"
    assert response["msgHeader"]["itemCount"] > 0
    assert len(response["msgBody"]["itemList"]) > 0

    # 첫 번째 정류장 데이터 검증
    first_station = response["msgBody"]["itemList"][0]
    assert "stationNm" in first_station
    assert "arsId" in first_station
    assert "gpsX" in first_station
    assert "gpsY" in first_station

    print(f"✅ 서울역 근처 정류장 {len(response['msgBody']['itemList'])}개 발견")
    """
    # 임시 pass (Week 3에서 구현)
    pass


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_station_by_position_gangnam_station(seoul_api_test_locations):
    """
    Test 2: 강남역 근처 정류장 조회

    강남역 좌표로 정류장을 조회하고 결과를 검증합니다.
    """
    # Week 3: 구현 예시
    """
    service = SeoulBusAPIService()
    location = seoul_api_test_locations["gangnam_station"]

    response = await service.get_stations_by_position(
        latitude=location["latitude"],
        longitude=location["longitude"],
        radius=100
    )

    assert response["msgHeader"]["headerCd"] == "0"
    assert response["msgHeader"]["itemCount"] > 0

    # 강남역이 정류장 이름에 포함되어야 함
    station_names = [item["stationNm"] for item in response["msgBody"]["itemList"]]
    assert any("강남" in name for name in station_names)

    print(f"✅ 강남역 근처 정류장: {station_names[:3]}")
    """
    pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_station_by_position_out_of_seoul(seoul_api_test_locations):
    """
    Test 3: 서울 외 지역 조회 (부산)

    서울이 아닌 지역 좌표로 조회 시 headerCd "4" 반환 검증
    """
    # Week 3: 구현 예시
    """
    service = SeoulBusAPIService()
    location = seoul_api_test_locations["busan"]

    response = await service.get_stations_by_position(
        latitude=location["latitude"],
        longitude=location["longitude"],
        radius=100
    )

    # 부산은 서울 외 지역이므로 데이터 없음
    assert response["msgHeader"]["headerCd"] == "4"
    assert response["msgBody"] is None or response["msgBody"]["itemList"] == []

    print("✅ 서울 외 지역 에러 처리 확인")
    """
    pass


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_arrivals_by_station_gangnam(seoul_api_test_locations):
    """
    Test 4: 강남역 버스 도착 정보 조회

    실제 강남역 정류장(ARS ID: 23288)의 버스 도착 정보를 조회합니다.
    """
    # Week 3: 구현 예시
    """
    service = SeoulBusAPIService()
    ars_id = seoul_api_test_locations["gangnam_station"]["ars_id"]

    response = await service.get_arrivals_by_station(ars_id)

    # 검증
    assert response["msgHeader"]["headerCd"] == "0"

    if response["msgBody"]["itemList"]:
        first_bus = response["msgBody"]["itemList"][0]

        # 필수 필드 존재 확인
        assert "rtNm" in first_bus  # 노선명
        assert "routeType" in first_bus  # 노선 유형
        assert "arrmsg1" in first_bus or "arrmsg2" in first_bus  # 도착 메시지

        print(f"✅ 강남역 첫 번째 버스: {first_bus.get('rtNm')} - {first_bus.get('arrmsg1')}")
    else:
        print("⚠️  강남역에 현재 도착 예정 버스 없음 (심야 시간대일 수 있음)")
    """
    pass


# ============================================
# Bus Type Classification Tests
# ============================================

@pytest.mark.unit
def test_bus_type_classification_all_types(bus_type_test_cases):
    """
    Test 5: 버스 유형 분류 (7가지 + unknown)

    iOS BusRouteType.from() 로직과 동일하게 동작하는지 검증
    """
    # Week 3: 구현 예시
    """
    for bus_number, expected_type in bus_type_test_cases:
        result = classify_bus_type(bus_number)
        assert result == expected_type, f"Failed for {bus_number}: expected {expected_type}, got {result}"

    print(f"✅ 버스 유형 분류 테스트 {len(bus_type_test_cases)}개 통과")
    """
    pass


@pytest.mark.unit
def test_bus_type_classification_gangseon():
    """Test 6: 간선버스 분류 (3자리)"""
    # Week 3: 구현 예시
    """
    test_cases = ["100", "721", "999"]
    for bus_number in test_cases:
        assert classify_bus_type(bus_number) == "gangseon"

    print("✅ 간선버스 분류 정상")
    """
    pass


@pytest.mark.unit
def test_bus_type_classification_jiseon():
    """Test 7: 지선버스 분류 (4자리, 6/9로 시작 안 함)"""
    # Week 3: 구현 예시
    """
    test_cases = ["2012", "1234", "5000"]
    for bus_number in test_cases:
        assert classify_bus_type(bus_number) == "jiseon"

    print("✅ 지선버스 분류 정상")
    """
    pass


@pytest.mark.unit
def test_bus_type_classification_gwangyeok():
    """Test 8: 광역버스 분류 (9로 시작하는 4자리)"""
    # Week 3: 구현 예시
    """
    test_cases = ["9403", "9000", "9999"]
    for bus_number in test_cases:
        assert classify_bus_type(bus_number) == "gwangyeok"

    print("✅ 광역버스 분류 정상")
    """
    pass


@pytest.mark.unit
def test_bus_type_classification_gongHang():
    """Test 9: 공항버스 분류 (6으로 시작하는 4자리)"""
    # Week 3: 구현 예시
    """
    test_cases = ["6705", "6000", "6999"]
    for bus_number in test_cases:
        assert classify_bus_type(bus_number) == "gongHang"

    print("✅ 공항버스 분류 정상")
    """
    pass


@pytest.mark.unit
def test_bus_type_classification_sunhwan():
    """Test 10: 순환버스 분류 (2자리)"""
    # Week 3: 구현 예시
    """
    test_cases = ["01", "02", "99"]
    for bus_number in test_cases:
        assert classify_bus_type(bus_number) == "sunhwan"

    print("✅ 순환버스 분류 정상")
    """
    pass


@pytest.mark.unit
def test_bus_type_classification_simya():
    """Test 11: 심야버스 분류 (N으로 시작)"""
    # Week 3: 구현 예시
    """
    test_cases = ["N16", "N37", "N99"]
    for bus_number in test_cases:
        assert classify_bus_type(bus_number) == "simya"

    print("✅ 심야버스 분류 정상")
    """
    pass


@pytest.mark.unit
def test_bus_type_classification_maeul():
    """Test 12: 마을버스 분류 (한글 포함)"""
    # Week 3: 구현 예시
    """
    test_cases = ["강동01", "강남01", "종로01"]
    for bus_number in test_cases:
        assert classify_bus_type(bus_number) == "maeul"

    print("✅ 마을버스 분류 정상")
    """
    pass


# ============================================
# Congestion Parsing Tests
# ============================================

@pytest.mark.unit
def test_congestion_parsing_all_cases(congestion_test_cases):
    """
    Test 13: 혼잡도 파싱 (모든 케이스)

    iOS BusCongestion enum과 동일하게 동작하는지 검증
    """
    # Week 3: 구현 예시
    """
    for code, expected_result in congestion_test_cases:
        result = parse_congestion(code)
        assert result == expected_result, f"Failed for code '{code}': expected {expected_result}, got {result}"

    print(f"✅ 혼잡도 파싱 테스트 {len(congestion_test_cases)}개 통과")
    """
    pass


@pytest.mark.unit
def test_congestion_parsing_empty():
    """Test 14: 여유 혼잡도 (0, 3)"""
    # Week 3: 구현 예시
    """
    assert parse_congestion("0") == "empty"
    assert parse_congestion("3") == "empty"
    print("✅ 여유 혼잡도 파싱 정상")
    """
    pass


@pytest.mark.unit
def test_congestion_parsing_normal():
    """Test 15: 보통 혼잡도 (4)"""
    # Week 3: 구현 예시
    """
    assert parse_congestion("4") == "normal"
    print("✅ 보통 혼잡도 파싱 정상")
    """
    pass


@pytest.mark.unit
def test_congestion_parsing_crowded():
    """Test 16: 혼잡 (5, 6)"""
    # Week 3: 구현 예시
    """
    assert parse_congestion("5") == "crowded"
    assert parse_congestion("6") == "crowded"
    print("✅ 혼잡 혼잡도 파싱 정상")
    """
    pass


@pytest.mark.unit
def test_congestion_parsing_unknown():
    """Test 17: 알 수 없음 (None, 빈 문자열)"""
    # Week 3: 구현 예시
    """
    assert parse_congestion(None) == "unknown"
    assert parse_congestion("") == "unknown"
    print("✅ 알 수 없음 혼잡도 파싱 정상")
    """
    pass


# ============================================
# Error Handling Tests
# ============================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_seoul_api_timeout_handling():
    """
    Test 18: Seoul Bus API 타임아웃 처리

    5초 타임아웃 설정 확인
    """
    # Week 3: 구현 예시
    """
    service = SeoulBusAPIService()

    # 매우 느린 응답을 시뮬레이션하기는 어려우므로,
    # 실제 API 호출이 5초 안에 완료되는지 확인
    start_time = asyncio.get_event_loop().time()

    try:
        await service.get_stations_by_position(
            latitude=37.5547125,
            longitude=126.9707878,
            radius=100
        )
        elapsed = asyncio.get_event_loop().time() - start_time
        assert elapsed < 5.0, f"API call took {elapsed}s, should be < 5s"
        print(f"✅ API 응답 시간: {elapsed:.2f}초")
    except httpx.TimeoutException:
        print("⚠️  Seoul Bus API 타임아웃 발생 (정상 동작)")
    """
    pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_seoul_api_retry_logic():
    """
    Test 19: Seoul Bus API 재시도 로직

    네트워크 오류 시 최대 3회 재시도 확인
    """
    # Week 3: 구현 시 mock을 사용하여 테스트
    """
    # httpx.TimeoutException을 발생시키는 mock 사용
    # 재시도 로직이 정상 동작하는지 확인
    """
    pass


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
    # Week 3: 구현 예시
    """
    service = SeoulBusAPIService()

    response = await service.get_stations_by_position(
        latitude=37.5547125,
        longitude=126.9707878,
        radius=100
    )

    # msgHeader 검증
    assert "msgHeader" in response
    assert "headerCd" in response["msgHeader"]
    assert "headerMsg" in response["msgHeader"]
    assert "itemCount" in response["msgHeader"]

    # msgBody 검증 (성공 시)
    if response["msgHeader"]["headerCd"] == "0":
        assert "msgBody" in response
        assert "itemList" in response["msgBody"]
        assert isinstance(response["msgBody"]["itemList"], list)

        if response["msgBody"]["itemList"]:
            station = response["msgBody"]["itemList"][0]
            required_fields = ["stationId", "stationNm", "arsId", "gpsX", "gpsY"]
            for field in required_fields:
                assert field in station, f"Missing field: {field}"

    print("✅ 정류장 응답 구조 검증 완료")
    """
    pass


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_arrivals_response_structure():
    """
    Test 21: 버스 도착 정보 응답 구조 검증

    Seoul Bus API 버스 도착 응답이 예상 구조를 따르는지 확인
    """
    # Week 3: 구현 예시
    """
    service = SeoulBusAPIService()

    response = await service.get_arrivals_by_station("23288")  # 강남역

    # msgHeader 검증
    assert "msgHeader" in response
    assert "headerCd" in response["msgHeader"]

    # msgBody 검증 (성공 시)
    if response["msgHeader"]["headerCd"] == "0" and response["msgBody"]["itemList"]:
        bus = response["msgBody"]["itemList"][0]
        required_fields = ["rtNm", "routeType"]
        for field in required_fields:
            assert field in bus, f"Missing field: {field}"

    print("✅ 버스 도착 응답 구조 검증 완료")
    """
    pass


# ============================================
# Performance Tests (Optional)
# ============================================

@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_api_calls():
    """
    Test 22: 동시 API 호출 성능 테스트

    여러 정류장을 동시에 조회할 때 성능 확인
    """
    # Week 3: 구현 예시
    """
    service = SeoulBusAPIService()

    # 여러 정류장 동시 조회
    tasks = [
        service.get_arrivals_by_station("23288"),  # 강남역
        service.get_arrivals_by_station("01234"),  # 신설동역
        service.get_arrivals_by_station("12345"),  # 기타
    ]

    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    elapsed = asyncio.get_event_loop().time() - start_time

    print(f"✅ 3개 정류장 동시 조회 소요 시간: {elapsed:.2f}초")
    print(f"   - 평균: {elapsed/3:.2f}초/정류장")

    # 동시 호출이 순차 호출보다 빨라야 함
    # (순차: ~1.5초, 동시: ~0.5초 예상)
    assert elapsed < 2.0
    """
    pass


# ============================================
# Helper Functions for Manual Testing
# ============================================

async def manual_test_seoul_api():
    """
    수동 테스트용 함수

    pytest 없이 직접 실행 가능:
    python -m asyncio tests/integration/test_seoul_bus_api.py
    """
    # Week 3: 구현 예시
    """
    service = SeoulBusAPIService()

    print("=" * 50)
    print("Seoul Bus API 수동 테스트")
    print("=" * 50)

    # 1. 정류장 조회
    print("\n1. 서울역 근처 정류장 조회...")
    stations = await service.get_stations_by_position(37.5547125, 126.9707878, 100)
    print(f"   결과: {stations['msgHeader']['itemCount']}개 정류장 발견")

    # 2. 버스 도착 정보 조회
    print("\n2. 강남역 버스 도착 정보 조회...")
    arrivals = await service.get_arrivals_by_station("23288")
    if arrivals["msgBody"]["itemList"]:
        print(f"   결과: {len(arrivals['msgBody']['itemList'])}개 버스 도착 예정")

    # 3. 버스 유형 분류
    print("\n3. 버스 유형 분류 테스트...")
    test_buses = ["721", "2012", "9403", "N16", "강동01"]
    for bus in test_buses:
        bus_type = classify_bus_type(bus)
        print(f"   {bus} → {bus_type}")

    print("\n" + "=" * 50)
    print("테스트 완료")
    """
    pass


if __name__ == "__main__":
    # 수동 테스트 실행
    # asyncio.run(manual_test_seoul_api())
    print("Week 3에서 주석을 해제하고 실행하세요.")
