"""
Pytest Configuration and Fixtures

이 파일은 pytest의 전역 설정 및 공통 fixture를 정의합니다.
"""

import os
import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import get_db
from app.models.base import Base


# ============================================
# SQLite - PostgreSQL 타입 호환성 설정
# ============================================

from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP as PG_TIMESTAMP
from sqlalchemy.ext.compiler import compiles

# SQLite에서 PostgreSQL UUID → CHAR(36) 으로 렌더링
compiles(PG_UUID, "sqlite")(lambda type_, compiler, **kw: "CHAR(36)")

# SQLite에서 PostgreSQL TIMESTAMP → TIMESTAMP 으로 렌더링
compiles(PG_TIMESTAMP, "sqlite")(lambda type_, compiler, **kw: "TIMESTAMP")


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
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def _create_tables_for_sqlite(conn):
    """SQLite에서 PostgreSQL 전용 CHECK 제약조건을 제거 후 테이블 생성"""
    from sqlalchemy import CheckConstraint as CC

    for table in Base.metadata.sorted_tables:
        # PostgreSQL regex(~) 연산자를 사용하는 제약조건 필터링
        original_constraints = list(table.constraints)
        pg_only = [
            c for c in table.constraints
            if isinstance(c, CC) and c.sqltext is not None and "~" in str(c.sqltext)
        ]
        for c in pg_only:
            table.constraints.discard(c)

    Base.metadata.create_all(conn)

    # 제거했던 제약조건 복원
    for table in Base.metadata.sorted_tables:
        for c in pg_only:
            if c.parent is table:
                table.constraints.add(c)


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """테스트용 데이터베이스 세션"""
    # 테이블 생성 (SQLite 호환)
    async with test_engine.begin() as conn:
        await conn.run_sync(_create_tables_for_sqlite)

    session = TestSessionLocal()
    try:
        yield session
    finally:
        await session.close()
        # 테이블 삭제
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
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
# Seoul Bus API Test Fixtures
# ============================================

@pytest.fixture
def seoul_api_test_locations():
    """Seoul Bus API 테스트용 위치 데이터"""
    return {
        "seoul_station": {
            "latitude": 37.5547125,
            "longitude": 126.9707878,
            "ars_id": "01234",
        },
        "gangnam_station": {
            "latitude": 37.4979461,
            "longitude": 127.0276188,
            "ars_id": "23288",
        },
        "busan": {
            "latitude": 35.1795543,
            "longitude": 129.0756416,
        },
    }


@pytest.fixture
def bus_type_test_cases():
    """버스 유형 분류 테스트 케이스"""
    return [
        ("3", "간선"),
        ("4", "지선"),
        ("6", "광역"),
        ("1", "공항"),
        ("2", "마을"),
        ("5", "순환"),
        ("7", "인천"),
        ("99", "기타"),
    ]


@pytest.fixture
def congestion_test_cases():
    """혼잡도 파싱 테스트 케이스"""
    return [
        ("3", "empty"),
        ("4", "normal"),
        ("5", "crowded"),
        (None, "unknown"),
        ("", "unknown"),
        ("0", "unknown"),
        ("99", "unknown"),
    ]


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
