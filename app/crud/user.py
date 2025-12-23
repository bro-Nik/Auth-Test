from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core import security
from app.models import User
from app.schemas import UserCreate, UserUpdate


async def get(
    db: AsyncSession,
    *,
    email: Optional[str] = None,
    id: Optional[int] = None
) -> Optional[User]:
    if email:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    if id:
        result = await db.execute(select(User).where(User.id == id))
        return result.scalar_one_or_none()


async def create(db: AsyncSession, *, user_data: UserCreate) -> User:
    hashed_password = security.get_password_hash(user_data.password)

    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        middle_name=user_data.middle_name,
        last_name=user_data.last_name,
        is_active=True,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update(
    db: AsyncSession,
    *,
    db_user: User,
    update_data: UserUpdate
) -> User:
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
        if hasattr(db_user, field) and field != 'id':
            setattr(db_user, field, update_data[field])

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


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
    user = await get(db, id=user_id)
    if user:
        user.is_active = False
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user
