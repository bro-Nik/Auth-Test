from typing import List, Dict, Any, Optional, Type
import logging
import sys
from enum import Enum

from sqlalchemy import select
from sqlalchemy.sql import Select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Permission, Resource, Role, RolePermissionResource


logger = logging.getLogger(__name__)


def setup_logger():
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)


setup_logger()


class Scope(str, Enum):
    ALL = 'all'
    OWN = 'own'


class PermissionChecker:
    def __init__(
        self,
        db: AsyncSession,
        user: User,
        resource: str,
        action: str,
        resource_obj: Optional[Any] = None
    ):
        self.db = db
        self.user = user
        self.resource = resource
        self.action = action
        self.resource_obj = resource_obj

    async def get_permissions(self):
        if not hasattr(self, '_permissions'):
            self._permissions = await self.get_user_permissions()
        return self._permissions

    async def check_permission(self) -> bool:
        """Проверка прав с учетом scope"""
        permissions = await self.get_permissions()
        logger.info(
            f"Проверка прав: user_id={self.user.id}, email={self.user.email}, "
            f"resource={self.resource}, action={self.action}"
        )

        if not permissions:
            logger.info('Нет прав')
            return False

        # 1. Если пользователь имеет разрешение без привязки к ресурсу
        for p in permissions:
            if p.resource_id is None:
                logger.info('Есть разрешение без привязки к ресурсу')
                return True

        # 2. Если нет конкретного объекта - отдаем для фильтрации
        if self.resource_obj is None:
            logger.info('Нет конкретного ресурса, доступ есть')
            return True

        # 3. Проверяем доступ к конкретному объекту
        for perm in permissions:
            if await self._check_object_permission(perm):
                logger.info('_check_object_permission = доступ есть')
                return True

        return False

    async def get_user_permissions(self) -> List[RolePermissionResource]:
        """Получаем все разрешения пользователя"""

        # Поиск разрешения с привязкой к ресурсу
        stmt = (
            select(RolePermissionResource)
            .options(
                selectinload(RolePermissionResource.permission),  # Для scope
            )
            .join(RolePermissionResource.role)
            .join(RolePermissionResource.permission)
            .join(RolePermissionResource.resource)
            .where(Role.id == self.user.role_id)
            .where(Permission.code == self.action)
            .where(Resource.code == self.resource)
        )

        result = await self.db.execute(stmt)
        permissions = result.scalars().all()

        # Поиск разрешения без привязки к ресурсу
        if not permissions:
            stmt = (
                select(RolePermissionResource)
                .options(
                    selectinload(RolePermissionResource.permission),  # Для scope
                )
                .join(RolePermissionResource.role)
                .join(RolePermissionResource.permission)
                .where(Role.id == self.user.role_id)
                .where(Permission.code == self.action)
                .where(RolePermissionResource.resource_id.is_(None))
            )
            result = await self.db.execute(stmt)
            permissions = result.scalars().all()

        return permissions

    async def _check_object_permission(self, rule: RolePermissionResource) -> bool:
        """Проверка доступа к конкретному объекту на основе scope"""
        # Доступ ко всем
        if rule.permission.scope == Scope.ALL:
            return await self._check_conditions(rule.conditions)

        # Доступ к своим
        if rule.permission.scope == Scope.OWN:
            if self.user.id != self.resource_obj.owner_id:
                return False

            return await self._check_conditions(rule.conditions)

        return False

    async def _check_conditions(self, conditions: Optional[Dict]) -> bool:
        """Проверка дополнительных условий"""
        if not conditions:
            return True

        for key, value in conditions.items():
            if not hasattr(self.resource_obj, key):
                return False

            obj_value = getattr(self.resource_obj, key)

            if isinstance(value, list):
                if obj_value not in value:
                    return False
            else:
                if obj_value != value:
                    return False

        return True

    async def get_user_max_scope(self) -> str:
        """Определяет максимальный scope пользователя"""
        permissions = await self.get_permissions()
        scopes = [p.permission.scope for p in permissions]

        # Приоритет: all > own
        if Scope.ALL in scopes:
            logger.info('Область доступа пользователя: all')
            return Scope.ALL
        if Scope.OWN in scopes:
            logger.info('Область доступа пользователя: own')
            return Scope.OWN

        return "none"  # Нет доступа

    async def apply_scope_filter(
        self,
        resource_model: Type[Any],
        base_stmt: Select | None = None
    ) -> Select:
        """Применяет фильтры к запросу в зависимости от scope пользователя"""
        scope = await self.get_user_max_scope()

        if base_stmt is None:
            base_stmt = select(resource_model)

        if scope == Scope.ALL:
            logger.info('Фильтрация запроса в зависимости от scope: Без фильтров')
            return base_stmt  # Без фильтров

        if scope == Scope.OWN:
            # Фильтруем только свои объекты
            if hasattr(resource_model, 'owner_id'):
                logger.info('Фильтрация запроса в зависимости от scope: фильтр owner_id=user_id')
                return base_stmt.where(resource_model.owner_id == self.user.id)

        logger.info('Фильтрация запроса в зависимости от scope: Возвращаем "пустой" запрос')
        return base_stmt.where(False)  # Возвращаем "пустой" запрос
