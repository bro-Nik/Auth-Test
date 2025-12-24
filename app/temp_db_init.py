from app.models.resource import Order, Product
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import engine, Base
from app.models import Permission, Role, User, Resource, RolePermissionResource
from app.core import security


# ToDo работа с таблицами (временно)
async def init_tables():
    """Функция для пересоздания всех таблиц"""
    async with engine.begin() as conn:
        # Удаляем все таблицы
        # Получаем все таблицы в правильном порядке для удаления
        tables = Base.metadata.sorted_tables
        for table in reversed(tables):
            try:
                await conn.execute(text(f'DROP TABLE IF EXISTS "{table.name}" CASCADE'))
            except Exception as e:
                print(f"Ошибка удаления таблицы {table.name}: {e}")

        # Создаем все таблицы
        await conn.run_sync(Base.metadata.create_all)

    print('Все таблицы пересозданы успешно!')

    # Заполняем начальными данными
    await populate_initial_data()


async def populate_initial_data():
    """Заполнение БД начальными данными: роли, разрешения, тестовый администратор"""
    async with AsyncSession(engine) as session:

        # Создаем ресурсы
        resources_data = [
            {"code": "users", "name": "Пользователи системы"},
            {"code": "orders", "name": "Заказы"},
            {"code": "products", "name": "Товары"},
            {"code": "roles", "name": "Роли пользователей"},
            {"code": "permissions", "name": "Разрешения"},
            {"code": "resources", "name": "Ресурсы системы"},
        ]

        resources = {}
        for resource_data in resources_data:
            resource = Resource(**resource_data)
            session.add(resource)

            resources[resource_data["code"]] = resource

        await session.flush()

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
            session.add(permission)

            # Для привязки в ролях
            permissions[f'{perm_data["code"]}_{perm_data["scope"]}'] = permission

        await session.flush()

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
            session.add(role)
            await session.flush()

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
                session.add(role_perm)

            # Для привязки в пользователях
            roles[role_data["code"]] = role

        await session.flush()

        # Создаем тестовых пользователей
        users_data = [
            {
                "email": "admin@example.com",
                "password": "123",
                "role_code": "admin"
            },
            {
                "email": "manager@example.com",
                "password": "123",
                "role_code": "manager"
            },
            {
                "email": "user@example.com",
                "password": "123",
                "role_code": "user"
            },
            {
                "email": "guest@example.com",
                "password": "123",
                "role_code": "guest"
            }
        ]

        users = {}
        for user_data in users_data:
            user = User(
                email=user_data["email"],
                hashed_password=security.get_password_hash(user_data["password"]),
                is_active=True,
                role_id=roles[user_data["role_code"]].id
            )
            session.add(user)

            # Для привязки в товарах
            users[user_data['role_code']] = user

        await session.flush()

        # Создаем товары
        products_data = [
            {
                "owner_id": users['user'].id,
                "name": "Product A"
            },
            {
                "owner_id": users['user'].id,
                "name": "Product B"
            },
            {
                "owner_id": users['manager'].id,
                "name": "Product C"
            },
            {
                "owner_id": users['manager'].id,
                "name": "Product D"
            },
        ]
        for product_data in products_data:
            product = Product(
                owner_id=product_data["owner_id"],
                name=product_data["name"],
            )
            session.add(product)

        # Создаем заказы
        orders_data = [
            {
                "owner_id": users['user'].id,
                "status": "pending"
            },
            {
                "owner_id": users['user'].id,
                "status": "completed"
            },
            {
                "owner_id": users['manager'].id,
                "status": "completed"
            },
            {
                "owner_id": users['manager'].id,
                "status": "pending"
            },
        ]
        for order_data in orders_data:
            order = Order(
                owner_id=order_data["owner_id"],
                status=order_data["status"],
            )
            session.add(order)


        await session.commit()
        print('Начальные данные добавлены успешно!')
        print('Тестовые пользователи:')
        for user_data in users_data:
            print(f"  {user_data['email']} / {user_data['password']} ({user_data['role_code']})")
