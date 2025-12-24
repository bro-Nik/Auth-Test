from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Order


async def get(db: AsyncSession, order_id: int) -> Optional[Order]:
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, *, user_id: int, order_data: dict) -> Order:
    order = Order(owner_id=user_id, status='pending')

    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def update(db: AsyncSession, *, order_id: int, update_data: dict) -> Optional[Order]:
    order = await get(db, order_id)
    if not order:
        return None

    # Обновление
    for field in update_data:
        if hasattr(order, field) and field != 'id':
            setattr(order, field, update_data[field])

    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def delete(db: AsyncSession, *, order_id: int) -> None:
    order = await get(db, order_id)
    if order:
        db.delete(order)
        await db.commit()
