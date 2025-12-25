from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models import RolePermissionResource, Role, Permission, Resource
from app.schemas.permission import RuleCreate, RuleUpdate


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


async def get_rule(
    db: AsyncSession,
    *,
    id: Optional[int] = None,
    role_id: Optional[int] = None,
    permission_id: Optional[int] = None,
    resource_id: Optional[int] = None,
    load_relations: bool = True
) -> Optional[RolePermissionResource]:
    """Получить одно правило по различным критериям"""
    query = select(RolePermissionResource)

    if load_relations:
        query = query.options(
            selectinload(RolePermissionResource.role),
            selectinload(RolePermissionResource.permission),
            selectinload(RolePermissionResource.resource)
        )

    if id:
        query = query.where(RolePermissionResource.id == id)
    elif role_id and permission_id:
        if resource_id is not None:
            query = query.where(
                and_(
                    RolePermissionResource.role_id == role_id,
                    RolePermissionResource.permission_id == permission_id,
                    RolePermissionResource.resource_id == resource_id
                )
            )
        else:
            query = query.where(
                and_(
                    RolePermissionResource.role_id == role_id,
                    RolePermissionResource.permission_id == permission_id,
                    RolePermissionResource.resource_id.is_(None)
                )
            )

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_rules(
    db: AsyncSession,
    *,
    role_id: Optional[int] = None,
    permission_id: Optional[int] = None,
    resource_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    load_relations: bool = True
) -> List[RolePermissionResource]:
    """Получить список правил с фильтрацией"""
    query = select(RolePermissionResource)

    if load_relations:
        query = query.options(
            selectinload(RolePermissionResource.role),
            selectinload(RolePermissionResource.permission),
            selectinload(RolePermissionResource.resource)
        )

    # Применяем фильтры
    filters = []
    if role_id:
        filters.append(RolePermissionResource.role_id == role_id)
    if permission_id:
        filters.append(RolePermissionResource.permission_id == permission_id)
    if resource_id is not None:
        if resource_id == -1:  # Специальное значение для получения записей без ресурса
            filters.append(RolePermissionResource.resource_id.is_(None))
        else:
            filters.append(RolePermissionResource.resource_id == resource_id)

    if filters:
        query = query.where(and_(*filters))

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


async def create_rule(
    db: AsyncSession,
    *,
    rule_data: RuleCreate
) -> RolePermissionResource:
    """Создать новое правило"""
    # Проверяем, существует ли уже такое правило
    existing = await get_rule(
        db,
        role_id=rule_data.role_id,
        permission_id=rule_data.permission_id,
        resource_id=rule_data.resource_id,
        load_relations=False
    )

    if existing:
        raise ValueError('Такое правило уже существует')

    # Проверяем существование связанных объектов
    role = await db.get(Role, rule_data.role_id)
    if not role:
        raise ValueError(f"Роль с id={rule_data.role_id} не найдена")

    permission = await db.get(Permission, rule_data.permission_id)
    if not permission:
        raise ValueError(f"Разрешение с id={rule_data.permission_id} не найдена")

    if rule_data.resource_id:
        resource = await db.get(Resource, rule_data.resource_id)
        if not resource:
            raise ValueError(f"Ресурс с id={rule_data.resource_id} не найден")

    # Создаем новое правило
    rule = RolePermissionResource(
        role_id=rule_data.role_id,
        permission_id=rule_data.permission_id,
        resource_id=rule_data.resource_id,
        conditions=rule_data.conditions
    )

    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    # Загружаем связанные объекты для возврата
    await db.refresh(rule, ['role', 'permission', 'resource'])

    return rule


async def update_rule(
    db: AsyncSession,
    *,
    id: int,
    rule_data: RuleUpdate
) -> Optional[RolePermissionResource]:
    """Обновить правило"""
    rule = await get_rule(db, id=id, load_relations=False)
    if not rule:
        return None

    # Обновляем только разрешенные поля
    update_data = rule_data.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(rule, field, value)

    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    # Загружаем связанные объекты для возврата
    await db.refresh(rule, ['role', 'permission', 'resource'])

    return rule


async def delete_rule(db: AsyncSession, *, id: int) -> bool:
    """Удалить правило"""
    rule = await get_rule(db, id=id, load_relations=False)
    if not rule:
        return False

    await db.delete(rule)
    await db.commit()

    return True
