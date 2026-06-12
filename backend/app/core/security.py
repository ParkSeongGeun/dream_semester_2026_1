"""
개인정보 보호 유틸리티

기기 식별자(device_id)를 그대로 저장하지 않고 가명화(pseudonymization)한다.
"""

import hashlib
import hmac
import uuid

from app.core.config import settings


def pseudonymize_device_id(device_id: uuid.UUID) -> uuid.UUID:
    """
    device_id(UUID)를 HMAC-SHA256으로 결정적 가명화한다.

    - 같은 입력은 항상 같은 출력 → 사용자별 통계 집계는 그대로 유지된다.
    - 비밀키(secret_key)를 모르면 원본 UUID를 역산할 수 없어, DB·로그에는
      원본 device_id가 남지 않는다.
    - 결과를 다시 UUID 타입으로 반환하여 기존 스키마(UUID 컬럼)를 그대로 사용한다.
    """
    mac = hmac.new(
        settings.secret_key.encode(),
        str(device_id).encode(),
        hashlib.sha256,
    ).digest()
    return uuid.UUID(bytes=mac[:16])
