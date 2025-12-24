from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Role


async def get_role(
    db: AsyncSession,
    *,
    id: Optional[int] = None,
    code: Optional[str] = None
) -> Optional[Role]:
    if code:
        result = await db.execute(select(Role).where(Role.code == code))
        return result.scalar_one_or_none()
    if id:
        result = await db.execute(select(Role).where(Role.id == id))
        return result.scalar_one_or_none()


async def get_default_user_role_id(db: AsyncSession) -> int:
    role = await get_role(db, code='user')
    return role.id
