"""
Pytest Configuration and Fixtures

이 파일은 pytest의 전역 설정 및 공통 fixture를 정의합니다.
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Week 3에서 구현될 모듈들 (현재는 import 오류 발생 가능)
# from app.main import app
# from app.core.database import Base, get_db
# from app.models.user import UserDevice
# from app.models.boarding_record import BoardingRecord


# ============================================
# Pytest Configuration
# ============================================

def pytest_configure(config):
    """Pytest 실행 전 설정"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


# ============================================
# Database Fixtures (Week 3 구현 시 사용)
# ============================================

@pytest.fixture(scope="session")
def test_db_engine():
    """
    테스트용 인메모리 SQLite 데이터베이스 엔진 생성

    - 각 테스트 세션마다 새로운 DB 생성
    - 인메모리 DB이므로 빠르고 격리됨
    """
    # SQLite 인메모리 DB 사용
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Week 3: 테이블 생성
    # Base.metadata.create_all(bind=engine)

    yield engine

    # 정리
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """
    각 테스트 함수마다 새로운 DB 세션 제공

    - 트랜잭션 기반 격리
    - 테스트 종료 시 자동 롤백
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )

    session = TestingSessionLocal()

    yield session

    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def test_client(test_db_session):
    """
    FastAPI 테스트 클라이언트 제공

    - DB 세션을 테스트용 세션으로 오버라이드
    """
    # Week 3: 의존성 오버라이드
    # def override_get_db():
    #     try:
    #         yield test_db_session
    #     finally:
    #         pass

    # app.dependency_overrides[get_db] = override_get_db

    # with TestClient(app) as client:
    #     yield client

    # app.dependency_overrides.clear()

    # 임시 placeholder
    yield None


# ============================================
# Sample Data Fixtures
# ============================================

@pytest.fixture
def sample_device_data():
    """샘플 기기 데이터"""
    return {
        "device_token": "TEST_DEVICE_ABC123",
        "device_name": "iPhone 14 Pro",
        "os_version": "iOS 17.2",
        "app_version": "1.0.0",
        "sound_enabled": True,
    }


@pytest.fixture
def sample_boarding_data():
    """샘플 탑승 기록 데이터"""
    return {
        "route_name": "721",
        "route_type": "간선",
        "bus_device_id": "BF_DREAM_721",
        "station_id": "123000001",
        "station_name": "신설동역",
        "ars_id": "01234",
        "latitude": 37.575000,
        "longitude": 127.025000,
        "sound_enabled": True,
        "notification_status": "success",
    }


# ============================================
# Seoul Bus API Test Data
# ============================================

@pytest.fixture
def seoul_api_test_locations():
    """Seoul Bus API 테스트용 위치 데이터"""
    return {
        "seoul_station": {
            "name": "서울역",
            "latitude": 37.5547125,
            "longitude": 126.9707878,
            "expected_stations": True,  # 정류장 있을 것으로 예상
        },
        "gangnam_station": {
            "name": "강남역",
            "latitude": 37.497940,
            "longitude": 127.027610,
            "ars_id": "23288",  # 강남역 정류장 번호
        },
        "sindaebang_station": {
            "name": "신대방역",
            "latitude": 37.4863,
            "longitude": 126.9130,
        },
        "busan": {
            "name": "부산 (서울 외 지역)",
            "latitude": 35.1796,
            "longitude": 129.0756,
            "expected_stations": False,  # 서울 외 지역
        },
    }


@pytest.fixture
def bus_type_test_cases():
    """버스 유형 분류 테스트 케이스"""
    return [
        ("721", "gangseon"),       # 3자리 = 간선
        ("2012", "jiseon"),        # 4자리 = 지선
        ("9403", "gwangyeok"),     # 9xxx = 광역
        ("6705", "gongHang"),      # 6xxx = 공항
        ("01", "sunhwan"),         # 2자리 = 순환
        ("02", "sunhwan"),         # 2자리 = 순환
        ("N16", "simya"),          # N prefix = 심야
        ("N37", "simya"),          # N prefix = 심야
        ("강동01", "maeul"),       # 한글 = 마을
        ("M5107", "unknown"),      # 규칙 외 = unknown
    ]


@pytest.fixture
def congestion_test_cases():
    """혼잡도 파싱 테스트 케이스"""
    return [
        ("0", "empty"),      # 여유
        ("3", "empty"),      # 여유
        ("4", "normal"),     # 보통
        ("5", "crowded"),    # 혼잡
        ("6", "crowded"),    # 혼잡
        (None, "unknown"),   # 정보 없음
        ("", "unknown"),     # 정보 없음
    ]


# ============================================
# Async Fixtures
# ============================================

@pytest.fixture(scope="session")
def event_loop():
    """
    비동기 테스트를 위한 이벤트 루프

    - pytest-asyncio 사용 시 필요
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================
# Mock Fixtures (Week 3 구현 시 사용)
# ============================================

@pytest.fixture
def mock_seoul_api_response_success():
    """Seoul Bus API 성공 응답 모의 데이터"""
    return {
        "msgHeader": {
            "headerCd": "0",
            "headerMsg": "정상적으로처리되었습니다.",
            "itemCount": 2,
        },
        "msgBody": {
            "itemList": [
                {
                    "stationId": "123000001",
                    "stationNm": "신설동역",
                    "arsId": "01234",
                    "gpsX": "127.025000",
                    "gpsY": "37.575000",
                    "dist": "50",
                },
                {
                    "stationId": "123000002",
                    "stationNm": "신설동역.동묘앞역",
                    "arsId": "01235",
                    "gpsX": "127.026000",
                    "gpsY": "37.576000",
                    "dist": "85",
                },
            ]
        },
    }


@pytest.fixture
def mock_seoul_api_response_no_data():
    """Seoul Bus API 데이터 없음 응답 (서울 외 지역)"""
    return {
        "msgHeader": {
            "headerCd": "4",
            "headerMsg": "해당하는 데이터가 없습니다.",
            "itemCount": 0,
        },
        "msgBody": None,
    }


@pytest.fixture
def mock_bus_arrivals_response():
    """Seoul Bus API 버스 도착 정보 응답"""
    return {
        "msgHeader": {
            "headerCd": "0",
            "headerMsg": "정상적으로처리되었습니다.",
            "itemCount": 2,
        },
        "msgBody": {
            "itemList": [
                {
                    "rtNm": "721",
                    "routeType": "4",
                    "arrmsg1": "2분후[2번째 전]",
                    "adirection": "신설동",
                    "congestion1": "3",
                    "isFullFlag1": "0",
                    "isLast1": "0",
                },
                {
                    "rtNm": "2012",
                    "routeType": "5",
                    "arrmsg1": "5분후[5번째 전]",
                    "adirection": "종암동",
                    "congestion1": "4",
                    "isFullFlag1": "0",
                    "isLast1": "0",
                },
            ]
        },
    }


# ============================================
# Environment Variables for Testing
# ============================================

@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """
    테스트 환경 변수 설정

    - autouse=True: 모든 테스트에 자동 적용
    """
    import os

    # 테스트용 환경 변수 설정
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"  # 테스트용 DB 1번 사용
    os.environ["DEBUG"] = "true"
    os.environ["SEOUL_BUS_API_KEY"] = "29b4ab63713865b3f2cdf31264b27efa9dfac8019d464980fdccef522c46e39e"

    yield

    # 정리 (필요시)
    pass


# ============================================
# Cleanup Fixtures
# ============================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """
    각 테스트 후 정리 작업

    - autouse=True: 모든 테스트에 자동 적용
    """
    yield

    # 테스트 후 정리 작업
    # 예: 임시 파일 삭제, 캐시 초기화 등
    pass
