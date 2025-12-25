from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.core.database import get_db
from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.core.permissions import PermissionChecker
from app import dependencies, models


router = APIRouter(prefix="/api/permission", tags=["permission"])


# Реализованна работа с правилами (связь роль-ресурс-разрешения).
# В дальнейшем возможно организовать управление для ролей, ресурсов и т.д.


@router.get("/rules", response_model=List[schemas.RuleResponse])
async def get_all_rules(
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    role_id: Optional[int] = None,
    permission_id: Optional[int] = None,
    resource_id: Optional[int] = None
) -> List[schemas.RuleResponse]:
    """Получить список всех правил доступа с возможностью фильтрации"""

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'permissions', 'read')
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на чтение правил доступа')

    # Получаем правила с фильтрами
    role_permissions = await crud.permission.get_rules(
        db,
        role_id=role_id,
        permission_id=permission_id,
        resource_id=resource_id,
        skip=skip,
        limit=limit,
        load_relations=True
    )

    return role_permissions


@router.get("/rules/{rule_id}", response_model=schemas.RuleResponse)
async def get_rule(
    rule_id: int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> schemas.RuleResponse:
    """Получить детальную информацию о правиле доступа"""
    # Получаем правило
    rule = await crud.permission.get_rule(db, id=rule_id, load_relations=True)
    if not rule:
        raise NotFoundException(detail=f'Правило с ID {rule_id} не найдено')

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'permissions', 'read', rule)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на чтение этого правила')

    return rule


@router.post("/rules", response_model=schemas.RuleResponse)
async def create_rule(
    form_data: schemas.RuleCreate,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> schemas.RuleResponse:
    """
    Создать новое правило доступа.
    
    - **role_id**: ID роли (обязательно)
    - **permission_id**: ID разрешения (обязательно)
    - **resource_id**: ID ресурса (опционально, если None - правило для всех ресурсов)
    - **conditions**: Условия доступа в формате JSON (опционально)
    """
    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'permissions', 'create')
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на создание правил доступа')

    try:
        # Создаем правило
        rule = await crud.permission.create_rule(db, rule_data=form_data)
    except ValueError as e:
        raise BadRequestException(detail=str(e))

    return rule


@router.put("/rules/{rule_id}", response_model=schemas.RuleResponse)
async def update_rule(
    rule_id: int,
    form_data: schemas.RuleUpdate,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> schemas.RuleResponse:
    """
    Обновить правило доступа.
    
    Можно обновлять только условия (conditions).
    Для изменения связей с ролями/разрешениями/ресурсами нужно удалить и создать новое правило.
    """
    # Получаем правило
    rule = await crud.permission.get_rule(db, id=rule_id, load_relations=True)

    if not rule:
        raise NotFoundException(detail=f"Правило с ID {rule_id} не найдено")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'permissions', 'update', rule)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на обновление этого правила')

    # Обновляем правило
    updated_rule = await crud.permission.update_rule(db, id=rule_id, rule_data=form_data)

    if not updated_rule:
        raise NotFoundException(detail=f"Правило с ID {rule_id} не найдено после обновления")

    return updated_rule


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить правило доступа"""
    # Получаем правило
    rule = await crud.permission.get_rule(db, id=rule_id, load_relations=False)
    if not rule:
        raise NotFoundException(detail=f"Правило с ID {rule_id} не найдено")

    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'permissions', 'delete', rule)
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на удаление этого правила')

    # Удаляем правило
    success = await crud.permission.delete_rule(db, id=rule_id)

    if not success:
        raise NotFoundException(detail=f"Ошибка при удалении правила с ID {rule_id}")

    return {"message": "Правило доступа удалено"}


@router.get("/roles/{role_id}/rules", response_model=List[schemas.RuleResponse])
async def get_role_permissions(
    role_id: int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> List[schemas.RuleResponse]:
    """Получить все правила доступа для конкретной роли"""
    # Проверка прав доступа
    checker = PermissionChecker(db, current_user, 'permissions', 'read')
    if not await checker.check_permission():
        raise ForbiddenException(detail='Нет разрешения на чтение правил роли')

    # Получаем правила для роли
    role_permissions = await crud.permission.get_rules(
        db,
        role_id=role_id,
        skip=skip,
        limit=limit,
        load_relations=True
    )

    return role_permissions
