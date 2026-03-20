"""
데이터베이스 세션 관리

SQLAlchemy 비동기 엔진 및 세션을 설정합니다.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings

# PostgreSQL 비동기 엔진 생성
# postgresql:// -> postgresql+asyncpg:// 로 변환
database_url = settings.database_url_str.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# 개발 환경에서는 NullPool 사용 (pool_size, max_overflow 미적용)
# 프로덕션에서는 기본 Pool 사용 (pool_size, max_overflow 적용)
if settings.environment == "development":
    engine = create_async_engine(
        database_url,
        echo=settings.db_echo,
        poolclass=NullPool,
    )
else:
    engine = create_async_engine(
        database_url,
        echo=settings.db_echo,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )

# 비동기 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    데이터베이스 세션을 생성하고 반환합니다.

    FastAPI 의존성 주입(Dependency Injection)에서 사용됩니다.

    Example:
        ```python
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
        ```

    Yields:
        AsyncSession: SQLAlchemy 비동기 세션
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    데이터베이스 초기화

    테이블 생성 (개발 환경에서만 사용)
    프로덕션에서는 Alembic 마이그레이션 사용
    """
    from app.models.base import Base

    async with engine.begin() as conn:
        # 개발 환경에서만 테이블 자동 생성
        if settings.debug:
            await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    데이터베이스 연결 종료

    애플리케이션 종료 시 호출됩니다.
    """
    await engine.dispose()
