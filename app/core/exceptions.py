from fastapi import HTTPException, status


class UnauthorizedException(HTTPException):
    """401 - Не авторизован"""
    def __init__(self, detail: str = 'Необходима авторизация'):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={'WWW-Authenticate': 'Bearer'}
        )


class ForbiddenException(HTTPException):
    """403 - Нет разрешения"""
    def __init__(self, detail: str = 'Недостаточно прав'):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class NotFoundException(HTTPException):
    """404 - Не найдено"""
    def __init__(self, detail: str = 'Ресурс не найден'):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
