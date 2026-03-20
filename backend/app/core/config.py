"""
애플리케이션 설정 관리

Pydantic Settings를 사용하여 환경 변수를 관리합니다.
.env 파일 또는 시스템 환경 변수에서 값을 자동으로 로드합니다.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App Settings
    app_name: str = Field(default="ComfortableMove Backend", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", alias="ENVIRONMENT"
    )

    # Server Settings
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Database Settings
    database_url: PostgresDsn = Field(
        default="postgresql://user:password@localhost:5432/comfortablemove",
        alias="DATABASE_URL",
    )
    db_echo: bool = Field(default=False, alias="DB_ECHO")
    db_pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")

    # Redis Settings
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL",
    )
    redis_ttl_bus_arrival: int = Field(default=60, alias="REDIS_TTL_BUS_ARRIVAL")
    redis_ttl_statistics: int = Field(default=300, alias="REDIS_TTL_STATISTICS")

    # Seoul Bus API Settings
    seoul_bus_api_key: str = Field(
        default="YOUR_API_KEY_HERE",
        alias="SEOUL_BUS_API_KEY",
    )
    seoul_bus_api_base_url: str = Field(
        default="http://ws.bus.go.kr/api/rest",
        alias="SEOUL_BUS_API_BASE_URL",
    )
    seoul_bus_api_timeout: int = Field(default=5, alias="SEOUL_BUS_API_TIMEOUT")
    seoul_bus_api_max_retries: int = Field(default=3, alias="SEOUL_BUS_API_MAX_RETRIES")

    # CORS Settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        alias="CORS_ORIGINS",
    )
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        alias="CORS_ALLOW_METHODS",
    )
    cors_allow_headers: list[str] = Field(
        default=["*"],
        alias="CORS_ALLOW_HEADERS",
    )

    # Security Settings
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        alias="SECRET_KEY",
    )

    # Logging Settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def database_url_str(self) -> str:
        """PostgreSQL URL을 문자열로 반환"""
        return str(self.database_url)

    @property
    def redis_url_str(self) -> str:
        """Redis URL을 문자열로 반환"""
        return str(self.redis_url)


@lru_cache
def get_settings() -> Settings:
    """
    설정 인스턴스를 반환합니다.

    @lru_cache 데코레이터로 캐싱되어 한 번만 생성됩니다.
    """
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()
