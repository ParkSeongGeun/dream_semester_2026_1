"""
Health Check API 통합 테스트

헬스체크 API를 테스트합니다.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestHealthAPI:
    """헬스체크 API 테스트"""

    async def test_health_check_success(self, client: AsyncClient):
        """헬스체크 - 성공"""
        response = await client.get("/api/v1/health")

        assert response.status_code in [200, 503]  # healthy or unhealthy
        data = response.json()

        # 필수 필드 확인
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "services" in data

        # services 필드 확인
        services = data["services"]
        assert "database" in services
        assert "redis" in services
        assert "seoul_bus_api" in services

    async def test_health_check_response_structure(self, client: AsyncClient):
        """헬스체크 응답 구조 검증"""
        response = await client.get("/api/v1/health")
        data = response.json()

        # status 값 확인
        assert data["status"] in ["healthy", "unhealthy"]

        # services 상태 확인
        services = data["services"]
        assert services["database"] in ["connected", "disconnected"]
        assert services["redis"] in ["connected", "disconnected"]
        assert services["seoul_bus_api"] in ["reachable", "unreachable"]

    async def test_root_endpoint(self, client: AsyncClient):
        """루트 엔드포인트 테스트"""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
