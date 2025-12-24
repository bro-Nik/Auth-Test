from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import PermissionChecker
from app import crud, dependencies, models


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
    orders = result.scalars().all()

    return orders


@router.get("/{order_id}")
async def get_order(
    order_id:int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    order = await crud.order.get(db, order_id)
    if not order:
        raise NotFoundException(detail="Заказ не найден")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'orders', 'read', order)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на чтение этого заказа')

    return order


@router.post("/{order_id}")
async def create_order(
    form_data: dict,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'orders', 'create')
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на изменение этого заказа')

    # Логика создания
    order = await crud.order.create(db, user_id=current_user.id, order_data=form_data)

    return order


@router.put("/{order_id}")
async def update_order(
    order_id:int,
    form_data: dict,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    order = await crud.order.get(db, order_id)
    if not order:
        raise NotFoundException(detail="Заказ не найден")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'orders', 'update', order)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на изменение этого заказа')

    # Логика обновления
    order = await crud.order.update(db, order_id=order_id, update_data=form_data)

    return order


@router.delete("/{order_id}")
async def delete_order(
    order_id:int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    order = await crud.order.get(db, order_id)
    if not order:
        raise NotFoundException(detail="Заказ не найден")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'orders', 'delete', order)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на удаление этого заказа')

    # Логика удаления
    await crud.order.delete(db, order_id=order_id)

    return {'message': 'Заказ удален'}
