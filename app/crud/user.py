from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core import security
from app.models import User
from app.schemas import UserCreate, UserUpdate
from app.crud.permission import get_default_user_role_id


async def get(
    db: AsyncSession,
    *,
    email: Optional[str] = None,
    user_id: Optional[int] = None
) -> Optional[User]:
    if email:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    if user_id:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


async def create(db: AsyncSession, *, user_data: UserCreate) -> User:
    hashed_password = security.get_password_hash(user_data.password)
    role_id = await get_default_user_role_id(db)

    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        middle_name=user_data.middle_name,
        last_name=user_data.last_name,
        is_active=True,
        role_id=role_id
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update(
    db: AsyncSession,
    *,
    user_id: int,
    update_data: UserUpdate
) -> Optional[User]:
    user = await get(db, user_id=user_id)
    if not user:
        return None

    update_data = update_data.model_dump(exclude_unset=True)

    # Обновление хэша пароля
    if update_data.get('password'):
        hashed_password = security.get_password_hash(update_data['password'])
        update_data["hashed_password"] = hashed_password

    # Удаление полей пороля
    update_data.pop("password", None)
    update_data.pop("password_confirm", None)

    # Обновление
    for field in update_data:
        if hasattr(user, field) and field != 'id':
            setattr(user, field, update_data[field])

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate(
    db: AsyncSession,
    *,
    email: str,
    password: str
) -> Optional[User]:
    user = await get(db, email=email)
    if not user:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user


async def soft_delete(db: AsyncSession, *, user_id: int) -> User:
    user = await get(db, user_id=user_id)
    if user:
        user.is_active = False
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def get_all(db, skip: int = 0, limit: Optional[int] = None) -> List[User]:
    query = select(User)
    if skip:
        query = query.offset(skip)
    if limit:
        query = query.limit(limit)

    result = await db.execute(query)
    return result.scalars().all()
