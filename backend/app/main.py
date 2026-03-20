"""
ComfortableMove Backend API

임산부 배려석 알림 서비스 백엔드 API 메인 애플리케이션
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.redis import close_redis, init_redis
from app.db.session import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    애플리케이션 생명주기 관리

    시작 시: 데이터베이스 및 Redis 연결 초기화
    종료 시: 연결 정리
    """
    # 시작 시 실행
    print("🚀 Starting ComfortableMove Backend...")

    # 데이터베이스 초기화
    print("📊 Initializing database...")
    await init_db()

    # Redis 초기화
    print("🔴 Initializing Redis...")
    await init_redis()

    print("✅ Application started successfully!")

    yield

    # 종료 시 실행
    print("🛑 Shutting down...")

    # Redis 연결 종료
    await close_redis()

    # 데이터베이스 연결 종료
    await close_db()

    print("✅ Shutdown complete")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="임산부 배려석 알림 서비스 백엔드 API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# 루트 엔드포인트
@app.get("/", tags=["Root"])
async def root():
    """
    API 루트 엔드포인트

    기본 정보를 반환합니다.
    """
    return JSONResponse(
        content={
            "message": "ComfortableMove Backend API",
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
        }
    )


# API v1 라우터 등록
from app.api.v1 import router as api_v1_router

app.include_router(api_v1_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
