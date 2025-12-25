from typing import AsyncGenerator, Generator
import asyncio
import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core import security
from app.core.database import Base, get_db
from app.models import Resource, User, Order, Product, Permission, Role, RolePermissionResource


# Добавляем путь к проекту
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Настройка тестовой БД SQLite
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    # connect_args={"check_same_thread": False}
)

TestAsyncSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    # expire_on_commit=False
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Переопределенная зависимость для тестов"""
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Монтируем зависимость
app.dependency_overrides[get_db] = override_get_db

# Создаем TestClient
client = TestClient(app)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Фикстура для event loop"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Сессия БД для каждого теста"""
    async with TestAsyncSessionLocal() as session:
        yield session


@pytest.fixture
def admin_token():
    """Токен администратора для тестов"""
    login_data = {"email": "admin@example.com", "password": "123"}
    response = client.post("/api/auth/login", json=login_data)
    return response.json()["access_token"]


@pytest.fixture
def manager_token():
    """Токен менеджера для тестов"""
    login_data = {"email": "manager@example.com", "password": "123"}
    response = client.post("/api/auth/login", json=login_data)
    return response.json()["access_token"]


@pytest.fixture
def user_token():
    """Токен обычного пользователя для тестов"""
    login_data = {"email": "user@example.com", "password": "123"}
    response = client.post("/api/auth/login", json=login_data)
    return response.json()["access_token"]


@pytest.fixture
def guest_token():
    """Токен гостя для тестов"""
    login_data = {"email": "guest@example.com", "password": "123"}
    response = client.post("/api/auth/login", json=login_data)
    return response.json()["access_token"]


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Создание и заполнение тестовой БД перед каждым тестом"""
    # Создаем все таблицы
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Заполняем тестовыми данными
    async with TestAsyncSessionLocal() as session:
        await init_test_data(session)

    yield

    # Очистка после теста
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def init_test_data(db: AsyncSession):
    """Заполнение тестовой БД данными (аналогично temp_db_init.py)"""
    # Создаем ресурсы
    resources_data = [
        {"code": "users", "name": "Пользователи"},
        {"code": "orders", "name": "Заказы"},
        {"code": "products", "name": "Товары"},
        {"code": "permissions", "name": "Разрешения"},
        {"code": "resources", "name": "Ресурсы системы"},
    ]

    resources = {}
    for resource_data in resources_data:
        resource = Resource(**resource_data)
        db.add(resource)
        resources[resource_data["code"]] = resource

    await db.flush()

    # Создаем разрешения
    permissions_data = [
        {"code": "read", "name": "Чтение", "scope": "all"},
        {"code": "read", "name": "Чтение своих", "scope": "own"},
        {"code": "create", "name": "Создание", "scope": "all"},
        {"code": "update", "name": "Обновление", "scope": "all"},
        {"code": "update", "name": "Обновление своих", "scope": "own"},
        {"code": "delete", "name": "Удаление", "scope": "all"},
        {"code": "delete", "name": "Удаление своих", "scope": "own"},
    ]

    permissions = {}
    for perm_data in permissions_data:
        permission = Permission(**perm_data)
        db.add(permission)
        permissions[f'{perm_data["code"]}_{perm_data["scope"]}'] = permission

    await db.flush()

    # Создаем роли
    roles_data = [
        {
            "code": "admin",
            "name": "Администратор",
            "permissions": [
                # Полные права на все ресурсы
                ("read", None, "all", None),
                ("create", None, "all", None),
                ("update", None, "all", None),
                ("delete", None, "all", None),
            ]
        },
        {
            "code": "manager",
            "name": "Менеджер",
            "permissions": [
                # Пользователи
                ("read", "users", "all", None),
                # Заказы
                ("read", "orders", "all", None),
                ("create", "orders", "all", None),
                ("update", "orders", "all", None),
                # Товары
                ("read", "products", "all", None),
                ("create", "products", "all", None),
                ("update", "products", "all", None),
                # Роли (только чтение)
                ("read", "roles", "all", None),
            ]
        },
        {
            "code": "user",
            "name": "Обычный пользователь",
            "permissions": [
                # Свои данные
                ("read", "users", "own", None),
                ("update", "users", "own", None),
                ("delete", "users", "own", None),
                # Заказы (только свои)
                ("read", "orders", "own", None),
                ("create", "orders", "all", None),
                ("update", "orders", "own", None),
                # Товары (только чтение)
                ("read", "products", "all", None),
            ]
        },
        {
            "code": "guest",
            "name": "Гость",
            "permissions": [
                # Только публичные данные
                ("read", "products", "all", None),
            ]
        }
    ]

    roles = {}
    for role_data in roles_data:
        role = Role(
            code=role_data["code"],
            name=role_data["name"],
        )
        db.add(role)
        await db.flush()

        # Добавляем разрешения для роли
        for perm_code, resource_code, perm_scope, conditions in role_data["permissions"]:
            permission = permissions[f'{perm_code}_{perm_scope}']
            resource = resources.get(resource_code) if resource_code else None

            role_perm = RolePermissionResource(
                role_id=role.id,
                permission_id=permission.id,
                resource_id=resource.id if resource else None,
                conditions=conditions
            )
            db.add(role_perm)

        roles[role_data["code"]] = role

    await db.flush()

    # Добавляем тестовых пользователей
    users_data = [
        {
            "id": 1,
            "email": "admin@example.com",
            "password": "123",
            "role_code": "admin"
        },
        {
            "id": 2,
            "email": "manager@example.com",
            "password": "123",
            "role_code": "manager"
        },
        {
            "id": 3,
            "email": "user@example.com",
            "password": "123",
            "role_code": "user"
        },
        {
            "id": 4,
            "email": "guest@example.com",
            "password": "123",
            "role_code": "guest"
        }
    ]

    users = {}
    for user_data in users_data:
        user = User(
            id=user_data["id"],
            email=user_data["email"],
            hashed_password=security.get_password_hash(user_data["password"]),
            is_active=True,
            role_id=roles[user_data["role_code"]].id
        )
        db.add(user)
        # Для привязки в товарах
        users[user_data['role_code']] = user

    await db.flush()

    # Создаем товары
    products_data = [
        {"owner_id": users["user"].id, "name": "Product A"},
        {"owner_id": users["user"].id, "name": "Product B"},
        {"owner_id": users["manager"].id, "name": "Product C"},
        {"owner_id": users["manager"].id, "name": "Product D"},
    ]

    for product_data in products_data:
        product = Product(**product_data)
        db.add(product)

    # Создаем заказы
    orders_data = [
        {"owner_id": users["user"].id, "status": "pending"},
        {"owner_id": users["user"].id, "status": "completed"},
        {"owner_id": users["manager"].id, "status": "completed"},
        {"owner_id": users["manager"].id, "status": "pending"},
    ]

    for order_data in orders_data:
        order = Order(**order_data)
        db.add(order)


    await db.commit()
