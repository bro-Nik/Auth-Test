from app.core.exceptions import BadRequestException, ForbiddenException, UnauthorizedException
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.core import security
from app.core.database import get_db


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=schemas.AccessToken)
async def register(
    form_data: schemas.UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # ToDo Что, если пользователь удалился и хочет восстановиться?
    try:
        # Создаем пользователя
        user = await crud.user.create(db, user_data=form_data)

        # Создаем токен
        access_token = security.create_access_token(user)

        return schemas.AccessToken(access_token=access_token)

    except ValueError as e:
        raise BadRequestException(detail=str(e))


@router.post("/login", response_model=schemas.AccessToken)
async def login(
    form_data: schemas.UserLogin,
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await crud.user.authenticate(
            db, email=form_data.email, password=form_data.password
        )
        if not user:
            raise UnauthorizedException(detail="Не корректный Email или пароль")
        if not user.is_active:
            raise BadRequestException(detail="Пользователь удален")

        # Создаем токен
        access_token = security.create_access_token(user)

        return schemas.AccessToken(access_token=access_token)

    except ValueError as e:
        raise BadRequestException(detail=str(e))


@router.post("/logout")
async def logout():
    """Выход пользователя"""
    # Выход реализуется на клиенте (удалить Access Token)
    return {'message': 'Выход из системы пройден успешно'}
