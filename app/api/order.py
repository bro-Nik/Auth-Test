from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import PermissionChecker
from app import dependencies, models


router = APIRouter(prefix="/api/order", tags=["order"])


@router.get("/")
async def get_all(
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'orders', 'read')
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на чтение заказов')

    # Строим запрос с фильтрацией
    stmt = await checker.apply_scope_filter(models.Order)
    result = await db.execute(stmt)
    products = result.scalars().all()

    return products


@router.get("/{order_id}")
async def get_order(
    order_id:int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Order).where(models.Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundException(detail="Заказ не найден")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'orders', 'read', order)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на чтение этого заказа')

    return order


@router.put("/{order_id}")
async def update_order(
    order_id:int,
    form_data: dict,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Order).where(models.Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundException(detail="Заказ не найден")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'orders', 'update', order)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на изменение этого заказа')

    # Логика обновления

    return order


@router.delete("/{order_id}")
async def delete_order(
    order_id:int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Order).where(models.Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundException(detail="Заказ не найден")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'orders', 'delete', order)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на удаление этого заказа')

    # Логика удаления

    return {'message': 'Заказ удален'}
