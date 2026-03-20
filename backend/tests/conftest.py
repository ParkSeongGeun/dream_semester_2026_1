"""
Pytest Configuration and Fixtures

이 파일은 pytest의 전역 설정 및 공통 fixture를 정의합니다.
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.session import get_db
from app.models.base import Base


# ============================================
# Pytest Configuration
# ============================================

def pytest_configure(config):
    """Pytest 실행 전 설정"""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


# ============================================
# Test Database
# ============================================

# 테스트용 SQLite 인메모리 DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# event_loop fixture removed - use pytest-asyncio default


@pytest.fixture(scope="function")
async def test_db():
    """테스트용 데이터베이스 세션"""
    # 테이블 생성
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session = TestSessionLocal()
    try:
        yield session
    finally:
        await session.close()
        # 테이블 삭제
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(test_db: AsyncSession):
    """FastAPI 테스트 클라이언트"""

    async def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


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
        "station_name": "신설동역",
        "ars_id": "01234",
        "latitude": 37.575000,
        "longitude": 127.025000,
        "sound_enabled": True,
        "notification_status": "success",
    }


# ============================================
# Mock Seoul Bus API Response
# ============================================

@pytest.fixture
def mock_seoul_api_success():
    """Seoul Bus API 성공 응답"""
    return {
        "msgHeader": {
            "headerCd": "0",
            "itemCount": 2,
        },
        "msgBody": {
            "itemList": [
                {
                    "rtNm": "721",
                    "busRouteType": "3",
                    "arrmsg1": "2분후[2번째 전]",
                    "stNm": "신설동",
                    "congestion": "3",
                    "full1": "0",
                    "mkTm": "0",
                },
                {
                    "rtNm": "2012",
                    "busRouteType": "4",
                    "arrmsg1": "5분후[5번째 전]",
                    "stNm": "종암동",
                    "congestion": "4",
                    "full1": "0",
                    "mkTm": "0",
                },
            ]
        },
    }


@pytest.fixture
def mock_seoul_api_no_data():
    """Seoul Bus API 데이터 없음 응답"""
    return {
        "msgHeader": {
            "headerCd": "4",
            "itemCount": 0,
        },
        "msgBody": None,
    }


# ============================================
# Environment Variables
# ============================================

@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """테스트 환경 변수 설정"""
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    os.environ["DEBUG"] = "true"
    os.environ["ENVIRONMENT"] = "development"
    os.environ["SEOUL_BUS_API_KEY"] = "test_api_key"

    yield
