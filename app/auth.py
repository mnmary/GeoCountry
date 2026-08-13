from datetime import datetime, timezone, timedelta

import jwt
from jwt import ExpiredSignatureError

from app.config import config

def create_access_token(user_id:int) -> str:
    """Генерирует короткоживущий Access токен."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)

def create_refresh_token(user_id:int) -> str:
    """долгоживущий токен"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": int(expire.timestamp())
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str, expected_type: str) -> int | None:
    """
    Декодирует токен, проверяет его валидность и тип (access или refresh).
    Возвращает user_id (int) в случае успеха или None при ошибке.
    """
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM], options={"verify_exp": True})
        print(payload)
        print(payload.get('type'))
        print(payload.get("sub"))
        print(config.ACCESS_TOKEN_EXPIRE_MINUTES)
        # Проверяем, что тип токена совпадает с ожидаемым (безопасность!)
        if payload.get("type") != expected_type:
            return None
        return int(payload.get("sub"))

    except (jwt.PyJWTError, ValueError):
        print("decode is error")
        return None

    except ExpiredSignatureError:
        # Вот эта магия сработает строго тогда, когда время 'exp' истекло!
        print("⚠️ [БЭКЕНД] Внимание: Срок действия Access-токена ИСТЕК (протух)!")
        return None