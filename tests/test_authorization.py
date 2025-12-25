import pytest
import jwt
from fastapi import status

from tests.conftest import client


class TestRoleBasedAccess:
    """Тесты контроля доступа на основе ролей"""

    @pytest.mark.anyio
    async def test_admin_full_access(self, admin_token):
        """Администратор имеет доступ ко всем endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Проверяем доступ к различным ресурсам
        endpoints = [
            "/api/user/",
            "/api/product/",
            "/api/order/",
            "/api/permission/rules",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=headers)
            # Админ должен иметь доступ
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.anyio
    async def test_manager_access(self, manager_token):
        """Менеджер имеет доступ к своим ресурсам"""
        headers = {"Authorization": f"Bearer {manager_token}"}

        # Менеджер может читать пользователей
        response = client.get("/api/user/", headers=headers)
        assert response.status_code == status.HTTP_200_OK

        # Менеджер может читать разрешения
        response = client.get("/api/permission/rules", headers=headers)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.anyio
    async def test_user_limited_access(self, user_token):
        """Обычный пользователь имеет ограниченный доступ"""
        headers = {"Authorization": f"Bearer {user_token}"}

        # Пользователь может читать себя
        response = client.get("/api/user/", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        users = response.json()
        assert len(users) == 1

        # Пользователь НЕ может читать разрешения
        response = client.get("/api/permission/rules", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Пользователь может читать товары
        response = client.get("/api/product/", headers=headers)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.anyio
    async def test_guest_minimal_access(self, guest_token):
        """Гость имеет минимальный доступ"""
        headers = {"Authorization": f"Bearer {guest_token}"}

        # Гость НЕ может читать пользователей
        response = client.get("/api/user/", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Гость НЕ может читать разрешения
        response = client.get("/api/permission/rules", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Гость может читать товары
        response = client.get("/api/product/", headers=headers)
        assert response.status_code == status.HTTP_200_OK


class TestUserResourceAuthorization:
    """Тесты авторизации для ресурса пользователей"""

    @pytest.mark.anyio
    async def test_admin_can_read_all_users(self, admin_token):
        """Администратор может читать всех пользователей"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/user/", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        users = response.json()
        assert len(users) == 4  # Все тестовые пользователи

    @pytest.mark.anyio
    async def test_user_can_read_own_profile(self, user_token):
        """Обычный пользователь может читать свой профиль"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/user/3", headers=headers)  # id пользователя

        assert response.status_code == status.HTTP_200_OK
        user_data = response.json()
        assert user_data["email"] == "user@example.com"

    @pytest.mark.anyio
    async def test_user_cannot_read_other_users(self, user_token):
        """Обычный пользователь не может читать чужие профили"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/user/1", headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Нет разрешения" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_user_can_update_own_profile(self, user_token):
        """Обычный пользователь может обновлять свой профиль"""
        update_data = {
            "id": 3,
            "first_name": "UpdatedName",
            "last_name": "UpdatedLastName"
        }

        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.put("/api/user/3", json=update_data, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        updated_user = response.json()
        assert updated_user["first_name"] == "UpdatedName"

    @pytest.mark.anyio
    async def test_user_cannot_update_other_profile(self, user_token):
        """Обычный пользователь не может обновлять чужой профиль"""
        update_data = {
            "id": 1,
            "first_name": "HackedName"
        }

        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.put("/api/user/1", json=update_data, headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestProductResourceAuthorization:
    """Тесты авторизации для ресурса товаров"""

    @pytest.mark.anyio
    async def test_all_roles_can_read_products(self, admin_token, manager_token, user_token, guest_token):
        """Все роли могут читать товары"""
        tokens = [admin_token, manager_token, user_token, guest_token]

        for token in tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/product/", headers=headers)
            assert response.status_code == status.HTTP_200_OK

            products = response.json()
            assert len(products) > 0

    @pytest.mark.anyio
    async def test_manager_can_create_product(self, manager_token):
        """Менеджер может создавать товары"""
        product_data = {"name": "New Product by Manager"}
        headers = {"Authorization": f"Bearer {manager_token}"}

        response = client.post("/api/product/", json=product_data, headers=headers)
        assert response.status_code != status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_user_cannot_create_product(self, user_token):
        """Обычный пользователь не может создавать товары"""
        product_data = {"name": "New Product by User"}
        headers = {"Authorization": f"Bearer {user_token}"}

        response = client.post("/api/product/", json=product_data, headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestOrderResourceAuthorization:
    """Тесты авторизации для ресурса заказов"""

    @pytest.mark.anyio
    async def test_user_sees_only_own_orders(self, user_token):
        """Обычный пользователь видит только свои заказы"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/order/", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        orders = response.json()
        assert len(orders) == 2  # В тестовых данных 2 заказа

    @pytest.mark.anyio
    async def test_manager_sees_all_orders(self, manager_token):
        """Менеджер видит все заказы"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        response = client.get("/api/order/", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        orders = response.json()
        assert len(orders) == 4  # В тестовых данных 4 заказа

    @pytest.mark.anyio
    async def test_user_can_create_orders(self, user_token):
        """Обычный пользователь может создавать заказы"""
        order_data = {"status": "pending"}
        headers = {"Authorization": f"Bearer {user_token}"}

        response = client.post("/api/order/", json=order_data, headers=headers)
        assert response.status_code != status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_guest_cannot_access_orders(self, guest_token):
        """Гость не может получать доступ к заказам"""
        headers = {"Authorization": f"Bearer {guest_token}"}
        response = client.get("/api/order/", headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestPermissionScope:
    """Тесты scope (all vs own) в разрешениях"""

    @pytest.mark.anyio
    async def test_user_own_scope_for_orders(self, user_token):
        """Проверка, что пользователь видит только свои заказы (scope=own)"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/order/", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        orders = response.json()

        assert len(orders) == 2
        for order in orders:
            assert order['owner_id'] == 3  # Только свои заказы

    @pytest.mark.anyio
    async def test_manager_all_scope_for_orders(self, manager_token):
        """Проверка, что менеджер видит все заказы (scope=all)"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        response = client.get("/api/order/", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        orders = response.json()

        # Менеджер должен видеть все заказы
        assert len(orders) == 4  # Все заказы в системе
