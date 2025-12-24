from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Product


async def get(db: AsyncSession, product_id: int) -> Optional[Product]:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, *, user_id: int, product_data: dict) -> Product:
    product = Product(owner_id=user_id, name=product_data.get('name'))

    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def update(db: AsyncSession, *, product_id: int, update_data: dict) -> Optional[Product]:
    product = await get(db, product_id)
    if not product:
        return None

    # Обновление
    for field in update_data:
        if hasattr(product, field) and field != 'id':
            setattr(product, field, update_data[field])

    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def delete(db: AsyncSession, *, product_id: int) -> None:
    product = await get(db, product_id)
    if product:
        db.delete(product)
        await db.commit()
