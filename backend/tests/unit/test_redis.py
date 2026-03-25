"""
Redis 유틸리티 단위 테스트

Redis 캐싱 함수들을 mock으로 테스트합니다.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.redis import (
    init_redis,
    close_redis,
    get_redis,
    set_cache,
    get_cache,
    delete_cache,
    clear_cache_pattern,
    check_redis_health,
)


@pytest.mark.asyncio
class TestRedisConnection:
    """Redis 연결 관리 테스트"""

    async def test_init_redis(self):
        """Redis 초기화"""
        with patch("app.core.redis.redis") as mock_redis_module:
            mock_client = AsyncMock()
            mock_redis_module.from_url.return_value = mock_client

            await init_redis()

            mock_redis_module.from_url.assert_called_once()

    async def test_close_redis_when_connected(self):
        """Redis 연결 종료 - 연결된 상태"""
        import app.core.redis as redis_module

        mock_client = AsyncMock()
        original = redis_module.redis_client
        redis_module.redis_client = mock_client

        await close_redis()
        mock_client.close.assert_called_once()

        redis_module.redis_client = original

    async def test_close_redis_when_not_connected(self):
        """Redis 연결 종료 - 미연결 상태"""
        import app.core.redis as redis_module

        original = redis_module.redis_client
        redis_module.redis_client = None

        await close_redis()  # 에러 없이 정상 종료

        redis_module.redis_client = original

    async def test_get_redis_not_initialized(self):
        """Redis 미초기화 시 RuntimeError"""
        import app.core.redis as redis_module

        original = redis_module.redis_client
        redis_module.redis_client = None

        with pytest.raises(RuntimeError, match="Redis client is not initialized"):
            await get_redis()

        redis_module.redis_client = original

    async def test_get_redis_initialized(self):
        """Redis 초기화 후 클라이언트 반환"""
        import app.core.redis as redis_module

        mock_client = AsyncMock()
        original = redis_module.redis_client
        redis_module.redis_client = mock_client

        result = await get_redis()
        assert result is mock_client

        redis_module.redis_client = original


@pytest.mark.asyncio
class TestRedisCacheOperations:
    """Redis 캐시 CRUD 테스트"""

    async def test_set_cache_dict_with_ttl(self):
        """캐시 저장 - dict 값 + TTL"""
        import app.core.redis as redis_module

        mock_client = AsyncMock()
        original = redis_module.redis_client
        redis_module.redis_client = mock_client

        result = await set_cache("test:key", {"data": "value"}, ttl=60)

        assert result is True
        mock_client.setex.assert_called_once()

        redis_module.redis_client = original

    async def test_set_cache_without_ttl(self):
        """캐시 저장 - TTL 없이"""
        import app.core.redis as redis_module

        mock_client = AsyncMock()
        original = redis_module.redis_client
        redis_module.redis_client = mock_client

        result = await set_cache("test:key", {"data": "value"})

        assert result is True
        mock_client.set.assert_called_once()

        redis_module.redis_client = original

    async def test_set_cache_string_value(self):
        """캐시 저장 - 문자열 값"""
        import app.core.redis as redis_module

        mock_client = AsyncMock()
        original = redis_module.redis_client
        redis_module.redis_client = mock_client

        result = await set_cache("test:key", "simple_string", ttl=30)

        assert result is True
        mock_client.setex.assert_called_once()
        args = mock_client.setex.call_args[0]
        assert args[2] == "simple_string"

        redis_module.redis_client = original

    async def test_set_cache_error_handling(self):
        """캐시 저장 - 에러 시 False 반환"""
        import app.core.redis as redis_module

        original = redis_module.redis_client
        redis_module.redis_client = None

        result = await set_cache("test:key", "value", ttl=60)
        assert result is False

        redis_module.redis_client = original

    async def test_get_cache_json_value(self):
        """캐시 조회 - JSON 값"""
        import app.core.redis as redis_module

        mock_client = AsyncMock()
        mock_client.get.return_value = '{"data": "value"}'
        original = redis_module.redis_client
        redis_module.redis_client = mock_client

        result = await get_cache("test:key")

        assert result == {"data": "value"}

        redis_module.redis_client = original

    async def test_get_cache_none(self):
        """캐시 조회 - 키 없음"""
        import app.core.redis as redis_module

        mock_client = AsyncMock()
        mock_client.get.return_value = None
        original = redis_module.redis_client
        redis_module.redis_client = mock_client

        result = await get_cache("nonexistent:key")

        assert result is None

        redis_module.redis_client = original

    async def test_get_cache_non_json_value(self):
        """캐시 조회 - JSON이 아닌 문자열"""
        import app.core.redis as redis_module

        mock_client = AsyncMock()
        mock_client.get.return_value = "plain_string"
        original = redis_module.redis_client
        redis_module.redis_client = mock_client

        result = await get_cache("test:key")

        assert result == "plain_string"

        redis_module.redis_client = original

    async def test_get_cache_error_handling(self):
        """캐시 조회 - 에러 시 None 반환"""
        import app.core.redis as redis_module

        original = redis_module.redis_client
        redis_module.redis_client = None

        result = await get_cache("test:key")
        assert result is None

        redis_module.redis_client = original

    async def test_delete_cache_success(self):
        """캐시 삭제 - 성공"""
        import app.core.redis as redis_module

        mock_client = AsyncMock()
        original = redis_module.redis_client
        redis_module.redis_client = mock_client

        result = await delete_cache("test:key")

        assert result is True
        mock_client.delete.assert_called_once_with("test:key")

        redis_module.redis_client = original

    async def test_delete_cache_error(self):
        """캐시 삭제 - 에러 시 False 반환"""
        import app.core.redis as redis_module

        original = redis_module.redis_client
        redis_module.redis_client = None

        result = await delete_cache("test:key")
        assert result is False

        redis_module.redis_client = original

    async def test_clear_cache_pattern_success(self):
        """패턴 캐시 삭제 - 성공"""
        import app.core.redis as redis_module

        mock_client = AsyncMock()
        mock_client.keys.return_value = ["bus:01234", "bus:56789"]
        original = redis_module.redis_client
        redis_module.redis_client = mock_client

        result = await clear_cache_pattern("bus:*")

        assert result == 2
        mock_client.delete.assert_called_once_with("bus:01234", "bus:56789")

        redis_module.redis_client = original

    async def test_clear_cache_pattern_no_keys(self):
        """패턴 캐시 삭제 - 일치하는 키 없음"""
        import app.core.redis as redis_module

        mock_client = AsyncMock()
        mock_client.keys.return_value = []
        original = redis_module.redis_client
        redis_module.redis_client = mock_client

        result = await clear_cache_pattern("nonexistent:*")

        assert result == 0

        redis_module.redis_client = original

    async def test_clear_cache_pattern_error(self):
        """패턴 캐시 삭제 - 에러 시 0 반환"""
        import app.core.redis as redis_module

        original = redis_module.redis_client
        redis_module.redis_client = None

        result = await clear_cache_pattern("bus:*")
        assert result == 0

        redis_module.redis_client = original


@pytest.mark.asyncio
class TestRedisHealth:
    """Redis 헬스체크 테스트"""

    async def test_check_redis_health_connected(self):
        """Redis 연결 정상"""
        import app.core.redis as redis_module

        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        original = redis_module.redis_client
        redis_module.redis_client = mock_client

        result = await check_redis_health()

        assert result is True

        redis_module.redis_client = original

    async def test_check_redis_health_disconnected(self):
        """Redis 연결 실패"""
        import app.core.redis as redis_module

        original = redis_module.redis_client
        redis_module.redis_client = None

        result = await check_redis_health()

        assert result is False

        redis_module.redis_client = original
