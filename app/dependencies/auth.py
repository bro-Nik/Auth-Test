import jwt

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.models import User
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedException


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency для получения текущего пользователя по JWT токену"""
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException(detail='Недействительный токен')

        user = await crud.user.get(db, user_id=user_id)
        if not user:
            raise UnauthorizedException(detail='Пользователь не найден')

        return user

    except jwt.ExpiredSignatureError:
        raise UnauthorizedException(detail='Токен устарел')
    except jwt.InvalidTokenError:
        raise UnauthorizedException(detail='Недействительный токен')
