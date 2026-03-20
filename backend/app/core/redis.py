"""
Redis 캐싱 관리

Redis 연결 및 캐싱 유틸리티 함수를 제공합니다.
"""

import json
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

# Redis 클라이언트 인스턴스
redis_client: redis.Redis | None = None


async def init_redis() -> None:
    """
    Redis 연결을 초기화합니다.

    애플리케이션 시작 시 호출됩니다.
    """
    global redis_client
    redis_client = redis.from_url(
        settings.redis_url_str,
        encoding="utf-8",
        decode_responses=True,
    )


async def close_redis() -> None:
    """
    Redis 연결을 종료합니다.

    애플리케이션 종료 시 호출됩니다.
    """
    global redis_client
    if redis_client:
        await redis_client.close()


async def get_redis() -> redis.Redis:
    """
    Redis 클라이언트를 반환합니다.

    FastAPI 의존성 주입에서 사용됩니다.

    Returns:
        redis.Redis: Redis 클라이언트 인스턴스

    Raises:
        RuntimeError: Redis가 초기화되지 않은 경우
    """
    if redis_client is None:
        raise RuntimeError("Redis client is not initialized")
    return redis_client


async def set_cache(
    key: str,
    value: Any,
    ttl: int | None = None,
) -> bool:
    """
    캐시에 값을 저장합니다.

    Args:
        key: 캐시 키
        value: 저장할 값 (dict, list 등은 JSON으로 자동 변환)
        ttl: 만료 시간(초). None이면 만료 없음

    Returns:
        bool: 저장 성공 여부

    Example:
        ```python
        await set_cache("bus:01234", {"arrivals": [...]}, ttl=60)
        ```
    """
    try:
        client = await get_redis()

        # 값을 JSON 문자열로 변환
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, ensure_ascii=False)
        else:
            value_str = str(value)

        # TTL과 함께 저장
        if ttl:
            await client.setex(key, ttl, value_str)
        else:
            await client.set(key, value_str)

        return True
    except Exception as e:
        print(f"Redis set error: {e}")
        return False


async def get_cache(key: str) -> Any | None:
    """
    캐시에서 값을 조회합니다.

    Args:
        key: 캐시 키

    Returns:
        Any | None: 저장된 값 (JSON이면 dict/list로 파싱), 없으면 None

    Example:
        ```python
        data = await get_cache("bus:01234")
        if data:
            print("Cache hit!")
        ```
    """
    try:
        client = await get_redis()
        value = await client.get(key)

        if value is None:
            return None

        # JSON 파싱 시도
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    except Exception as e:
        print(f"Redis get error: {e}")
        return None


async def delete_cache(key: str) -> bool:
    """
    캐시에서 값을 삭제합니다.

    Args:
        key: 캐시 키

    Returns:
        bool: 삭제 성공 여부
    """
    try:
        client = await get_redis()
        await client.delete(key)
        return True
    except Exception as e:
        print(f"Redis delete error: {e}")
        return False


async def clear_cache_pattern(pattern: str) -> int:
    """
    패턴과 일치하는 모든 캐시를 삭제합니다.

    Args:
        pattern: 삭제할 키 패턴 (예: "bus:*")

    Returns:
        int: 삭제된 키 개수

    Example:
        ```python
        # bus:로 시작하는 모든 캐시 삭제
        deleted_count = await clear_cache_pattern("bus:*")
        print(f"Deleted {deleted_count} keys")
        ```
    """
    try:
        client = await get_redis()
        keys = await client.keys(pattern)

        if not keys:
            return 0

        await client.delete(*keys)
        return len(keys)
    except Exception as e:
        print(f"Redis clear pattern error: {e}")
        return 0


async def check_redis_health() -> bool:
    """
    Redis 연결 상태를 확인합니다.

    Returns:
        bool: Redis 연결 정상 여부
    """
    try:
        client = await get_redis()
        await client.ping()
        return True
    except Exception:
        return False
