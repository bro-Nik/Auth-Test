from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.core.database import get_db
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import PermissionChecker
from app import dependencies, models


router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/", response_model=List[schemas.UserResponse])
async def get_all(
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> List[schemas.UserResponse]:
    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'users', 'read')
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на чтение пользователей')

    # Строим запрос с фильтрацией
    stmt = await checker.apply_scope_filter(models.User)
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    users = result.scalars().all()

    return users


@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_profile(
    user_id:int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> schemas.UserResponse:
    user = await crud.user.get(db, user_id=user_id)
    if not user:
        raise NotFoundException(detail="Пользователь не найден")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'users', 'read', user)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на чтение этого пользователя')

    return user


@router.put("/{user_id}", response_model=schemas.UserResponse)
async def update_profile(
    user_id:int,
    form_data: schemas.UserUpdate,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> schemas.UserResponse:
    user = await crud.user.get(db, user_id=user_id)
    if not user:
        raise NotFoundException(detail="Пользователь не найден")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'users', 'update', user)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на изменение этого пользователя')

    user = await crud.user.update(db, user_id=user_id, update_data=form_data)

    return user


@router.delete("/{user_id}")
async def delete_profile(
    user_id:int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await crud.user.get(db, user_id=user_id)
    if not user:
        raise NotFoundException(detail="Пользователь не найден")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'users', 'delete', user)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на удаление этого пользователя')

    await crud.user.soft_delete(db, user_id=user_id)

    return {'message': 'Пользователь удален'}
