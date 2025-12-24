from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import PermissionChecker
from app import dependencies, models


router = APIRouter(prefix="/api/product", tags=["product"])


@router.get("/")
async def get_all(
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'products', 'read')
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на чтение товаров')

    # Строим запрос с фильтрацией
    stmt = await checker.apply_scope_filter(models.Product)
    result = await db.execute(stmt)
    products = result.scalars().all()

    return products


@router.get("/{product_id}")
async def get_product(
    product_id:int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Product).where(models.Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundException(detail="Товар не найден")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'products', 'read', product)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на чтение этого товара')

    return product


@router.put("/{product_id}")
async def update_product(
    product_id:int,
    form_data: dict,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Product).where(models.Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundException(detail="Товар не найден")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'products', 'update', product)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на изменение этого товара')

    # Логика обновления

    return product


@router.delete("/{product_id}")
async def delete_product(
    product_id:int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Product).where(models.Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundException(detail="Товар не найден")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'products', 'delete', product)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на удаление этого товара')

    # Логика удаления

    return {'message': 'Товар удален'}
