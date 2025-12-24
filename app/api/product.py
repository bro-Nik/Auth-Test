from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import PermissionChecker
from app import crud, dependencies, models


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
    product = await crud.product.get(db, product_id)
    if not product:
        raise NotFoundException(detail="Товар не найден")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'products', 'read', product)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на чтение этого товара')

    return product


@router.post("/{product_id}")
async def create_product(
    form_data: dict,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'products', 'create')
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на изменение этого товара')

    # Логика создания
    product = await crud.product.create(db, user_id=current_user.id, product_data=form_data)

    return product


@router.put("/{product_id}")
async def update_product(
    product_id:int,
    form_data: dict,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    product = await crud.product.get(db, product_id)
    if not product:
        raise NotFoundException(detail="Товар не найден")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'products', 'update', product)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на изменение этого товара')

    # Логика обновления
    product = await crud.product.update(db, product_id=product_id, update_data=form_data)

    return product


@router.delete("/{product_id}")
async def delete_product(
    product_id:int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    product = await crud.product.get(db, product_id)
    if not product:
        raise NotFoundException(detail="Товар не найден")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'products', 'delete', product)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на удаление этого товара')

    # Логика удаления
    await crud.product.delete(db, product_id=product_id)

    return {'message': 'Товар удален'}
