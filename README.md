# Auth

Приложение системы контроля доступа на основе ролей (RBAC).

## Быстрый старт

### Клонирование репозитория
```bash
git clone https://github.com/bro-Nik/Auth-Test.git
cd Auth-Test
```
### Запуск приложения
```bash
docker-compose up
```
### Запуск тестов
```bash
docker-compose -f docker-compose.test.yml up
```

> Примечание: При каждом запуске приложение автоматически создает первичные данные в БД (необходимый минимум для работы)

## Архитектура системы

### Основные компоненты

1. Пользователи (Users)
    * Связаны с ролями

2. Роли (Roles)
    * Группируют наборы разрешений
    * Примеры: "Администратор", "Менеджер", "Пользователь", "Гость"

3. Ресурсы (Resources)
    * Объекты системы, к которым требуется контроль доступа
    * Примеры: "Пользователи", "Товары", "Заказы", "Правила доступа"

4. Разрешения (Permissions)
    * Операции, которые можно выполнять над ресурсами
    * Базовые CRUD операции: ```create```, ```read```, ```update```, ```delete```
    * Области видимости для ограничения доступа:
        * ```all``` - полный доступ ко всем ресурсам
        * ```own``` - доступ только к своим ресурсам (```owner_id``` ресурса = ```id``` пользователя)

5. Правила доступа (RolePermissionResource)
    * Связь между Ролью, Ресурсом и Разрешением
    * Определяет, может ли роль выполнить действие над ресурсом
    * Могут иметь условия (conditions) для динамической проверки доступа


## Использование PermissionChecker

```PermissionChecker``` - сервис для проверки прав доступа пользователя.
### Пример 1: Проверка доступа к конкретному ресурсу

```python
from app.core.permissions import PermissionChecker

# Проверка прав доступа
checker = PermissionChecker(db, current_user, 'users', 'read', resource_obj)
if not await checker.check_permission():
    raise ForbiddenException(detail='Нет разрешения на чтение этого ресурса')
```

#### Логика работы:
* Если пользователь имеет доступ к ресурсу ```users``` с операцией ```read```:
    * При области видимости ```all``` - доступ предоставляется
    * При области видимости ```own``` - доступ предоставляется, если ```resource_obj.owner_id == current_user.id``` (т.е. пользователь является владельцем ресурса)

### Пример 2: Проверка доступа к списку ресурсов
```python
from app.core.permissions import PermissionChecker

# Проверка общих прав доступа (без указания конкретного ресурса)
checker = PermissionChecker(db, current_user, 'users', 'read')
if not await checker.check_permission():
    raise ForbiddenException(detail='Нет разрешения на чтение этих ресурсов')

# Фильтрация запроса на основе области видимости
stmt = await checker.apply_scope_filter(models.User)
stmt = stmt.offset(skip).limit(limit)

result = await db.execute(stmt)
users = result.scalars().all()
return users
```

## Примеры API запросов

```bash
# Вход как user
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"123"}'

# Получить список заказов
curl -X GET http://localhost:8000/api/order/ \
  -H "Authorization: Bearer <YOUR_TOKEN>"

# Получить список пользователей
curl -X GET http://localhost:8000/api/user/ \
  -H "Authorization: Bearer <YOUR_TOKEN>"

# Получить профиль другого пользователя
curl -X GET http://localhost:8000/api/user/1 \
  -H "Authorization: Bearer <YOUR_TOKEN>"

# Получить список правил
curl -X GET http://localhost:8000/api/permission/rules \
  -H "Authorization: Bearer <YOUR_TOKEN>"

```
