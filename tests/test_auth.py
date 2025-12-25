import pytest
import jwt
import time
from fastapi import status

from tests.conftest import client


class TestAuthentication:
    """Тесты аутентификации"""

    @pytest.mark.anyio
    async def test_root_endpoint(self):
        """Тест доступности корневого эндпоинта"""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.anyio
    async def test_register_success(self):
        """Тест успешной регистрации нового пользователя"""
        user_data = {
            "email": "newuser@example.com",
            "password": "newpassword123",
            "password_confirm": "newpassword123",
            "first_name": "John",
            "last_name": "Doe"
        }

        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Проверяем, что токен валиден
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/user/", headers=headers)
        assert response.status_code != status.HTTP_401_UNAUTHORIZED

    @pytest.mark.anyio
    async def test_register_existing_user(self):
        """Тест регистрации существующего пользователя"""
        user_data = {
            "email": "admin@example.com",  # Существующий email
            "password": "password123",
            "password_confirm": "password123"
        }

        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "уже существует" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_register_password_mismatch(self):
        """Тест регистрации с несовпадающими паролями"""
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "password_confirm": "differentpassword"
        }

        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    @pytest.mark.anyio
    async def test_login_success(self):
        """Тест успешного входа для всех ролей"""
        test_users = [
            ("admin@example.com", "123"),
            ("manager@example.com", "123"),
            ("user@example.com", "123"),
            ("guest@example.com", "123")
        ]

        for email, password in test_users:
            login_data = {"email": email, "password": password}
            response = client.post("/api/auth/login", json=login_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    @pytest.mark.anyio
    async def test_login_wrong_password(self):
        """Тест входа с неправильным паролем"""
        login_data = {
            "email": "admin@example.com",
            "password": "wrongpassword"
        }

        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.anyio
    async def test_login_nonexistent_user(self):
        """Тест входа несуществующего пользователя"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }

        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.anyio
    async def test_logout_endpoint(self):
        """Тест выхода (просто проверяем, что endpoint работает)"""
        response = client.post("/api/auth/logout")
        assert response.status_code == status.HTTP_200_OK


class TestTokenValidation:
    """Тесты валидации JWT токенов"""

    @pytest.mark.anyio
    async def test_protected_endpoint_without_token(self):
        """Тест доступа к защищенному endpoint без токена"""
        response = client.get("/api/user/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.anyio
    async def test_protected_endpoint_with_malformed_token(self):
        """Тест доступа с неправильно сформированным токеном"""
        headers = {"Authorization": "Bearer invalid_token.123.456"}
        response = client.get("/api/user/", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.anyio
    async def test_protected_endpoint_with_wrong_scheme(self):
        """Тест доступа с неправильной схемой авторизации"""
        headers = {"Authorization": "Basic invalid_token"}
        response = client.get("/api/user/", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.anyio
    async def test_protected_endpoint_with_valid_token(self, admin_token):
        """Тест доступа с валидным токеном"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/user/", headers=headers)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.anyio
    async def test_token_contains_correct_payload(self, admin_token):
        """Тест, что JWT токен содержит правильные данные"""
        from app.core.config import settings

        payload = jwt.decode(
            admin_token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        assert "sub" in payload  # user_id
        assert "type" in payload and payload["type"] == "access"
        assert "exp" in payload  # expiration timestamp

        # Проверяем, что токен не истек
        assert payload["exp"] > time.time()
