from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from passlib.context import CryptContext
import jwt

from app.core.config import settings
from app.models.user import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(password_for_verification: str, hashed_password: str) -> bool:
    return pwd_context.verify(password_for_verification, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def access_token_expires() -> int:
    minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    return expires_timestamp(timedelta(minutes=minutes))


def expires_timestamp(delta: timedelta) -> int:
    date = datetime.now(timezone.utc) + delta
    return int(date.timestamp())


def create_access_token(user: User) -> str:
    token_payload: Dict[str, Any] = {
        "sub": str(user.id),
        "type": "access",
        "exp": access_token_expires()
    }

    access_token = jwt.encode(token_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return access_token


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        return {}
