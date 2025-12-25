import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, Product, Order
from app.core.permissions import PermissionChecker
from tests.conftest import client, db_session as db


class TestPermissionChecker:
    """Тесты класса PermissionChecker"""

    @pytest.mark.anyio
    async def test_admin_has_all_permissions(self, db: AsyncSession):
        """Администратор имеет разрешение на все действия"""
        # Получаем пользователя-администратора
        result = await db.execute(select(User).where(User.email == "admin@example.com"))
        admin = result.scalar_one()

        # Проверяем различные разрешения
        test_cases = [
            ("users", "read"),
            ("users", "create"),
            ("users", "update"),
            ("users", "delete"),
            ("products", "read"),
            ("products", "create"),
            ("orders", "read"),
            ("permissions", "read"),
        ]

        for resource, action in test_cases:
            checker = PermissionChecker(db, admin, resource, action)
            has_permission = await checker.check_permission()
            assert has_permission

    @pytest.mark.anyio
    async def test_user_own_scope(self, db: AsyncSession):
        """Проверка scope=own для обычного пользователя"""
        # Получаем обычного пользователя
        result = await db.execute(select(User).where(User.email == "user@example.com"))
        user = result.scalar_one()

        # Получаем продукт, принадлежащий этому пользователю
        result = await db.execute(select(Product).where(Product.owner_id == user.id).limit(1))
        own_product = result.scalar_one()

        # Получаем продукт, не принадлежащий пользователю
        result = await db.execute(select(Product).where(Product.owner_id != user.id).limit(1))
        other_product = result.scalar_one()

        # Пользователь должен иметь доступ
        checker = PermissionChecker(db, user, "products", "read", own_product)
        has_permission = await checker.check_permission()
        assert has_permission

        checker = PermissionChecker(db, user, "products", "read", other_product)
        has_permission = await checker.check_permission()
        # Пользователь должен иметь доступ
        assert has_permission

        # Получаем заказ, принадлежащий этому пользователю
        result = await db.execute(select(Order).where(Order.owner_id == user.id).limit(1))
        own_order = result.scalar_one()

        # Получаем заказ, не принадлежащий пользователю
        result = await db.execute(select(Order).where(Order.owner_id != user.id).limit(1))
        other_order = result.scalar_one()

        # Пользователь должен иметь доступ к своему
        checker = PermissionChecker(db, user, "orders", "read", own_order)
        has_permission = await checker.check_permission()
        assert has_permission

        checker = PermissionChecker(db, user, "orders", "read", other_order)
        has_permission = await checker.check_permission()
        # Пользователь не должен иметь доступ к другим заказам
        assert not has_permission

    @pytest.mark.anyio
    async def test_guest_limited_permissions(self, db: AsyncSession):
        """Гость имеет очень ограниченные разрешения"""
        result = await db.execute(select(User).where(User.email == "guest@example.com"))
        guest = result.scalar_one()

        # Гость может читать продукты
        checker = PermissionChecker(db, guest, "products", "read")
        has_permission = await checker.check_permission()
        assert has_permission

        # Гость НЕ может создавать продукты
        checker = PermissionChecker(db, guest, "products", "create")
        has_permission = await checker.check_permission()
        assert not has_permission

        # Гость НЕ может читать пользователей
        checker = PermissionChecker(db, guest, "users", "read")
        has_permission = await checker.check_permission()
        assert not has_permission

    @pytest.mark.anyio
    async def test_apply_scope_filter(self, db: AsyncSession):
        """Тест применения фильтров scope к запросам"""
        # Тестируем для обычного пользователя
        result = await db.execute(select(User).where(User.email == "user@example.com"))
        user = result.scalar_one()

        # Для заказов у пользователя scope=own
        checker = PermissionChecker(db, user, "orders", "read")
        stmt = await checker.apply_scope_filter(Order)

        # Выполняем запрос
        result = await db.execute(stmt)
        user_orders = result.scalars().all()

        # Должны быть только заказы этого пользователя
        for order in user_orders:
            assert order.owner_id == user.id

        # Тестируем для менеджера
        result = await db.execute(select(User).where(User.email == "manager@example.com"))
        manager = result.scalar_one()

        checker = PermissionChecker(db, manager, "orders", "read")
        stmt = await checker.apply_scope_filter(Order)

        result = await db.execute(stmt)
        manager_orders = result.scalars().all()

        # Менеджер должен видеть все заказы (scope=all)
        assert len(manager_orders) == 4  # В тестовых данных 4 заказа
