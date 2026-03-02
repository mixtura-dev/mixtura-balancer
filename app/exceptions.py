from typing import Any


class BalanceServiceException(Exception):
    """Базовое исключение сервиса балансировки"""

    def __init__(self, message: str, code: int = 500, details: dict[str, Any] | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class NotEnoughPlayersException(BalanceServiceException):
    """Недостаточно игроков"""

    def __init__(self, required: int, actual: int):
        super().__init__(
            message=f"Not enough players. Required: {required}, actual: {actual}",
            code=400,
            details={"required": required, "actual": actual},
        )


class InvalidRoleConfigurationException(BalanceServiceException):
    """Некорректная конфигурация ролей"""

    def __init__(self, reason: str):
        super().__init__(message=f"Invalid role configuration: {reason}", code=400)


class NoValidBalanceException(BalanceServiceException):
    """Невозможно найти валидный баланс"""

    def __init__(self, reason: str = "Cannot find valid team balance"):
        super().__init__(message=reason, code=400)


class DraftNotFoundException(BalanceServiceException):
    """Драфт не найден"""

    def __init__(self, draft_id: str):
        super().__init__(
            message=f"Draft not found: {draft_id}", code=404, details={"draft_id": draft_id}
        )


class PlayerRoleMismatchException(BalanceServiceException):
    """Игрок не может играть назначенную роль"""

    def __init__(self, member_id: str, role_id: str):
        super().__init__(
            message=f"Player {member_id} cannot play role {role_id}",
            code=400,
            details={"member_id": member_id, "role_id": role_id},
        )


class RedisConnectionException(BalanceServiceException):
    """Ошибка подключения к Redis"""

    def __init__(self, reason: str):
        super().__init__(message=f"Redis connection error: {reason}", code=503)


class NotificationException(BalanceServiceException):
    """Ошибка отправки уведомления"""

    def __init__(self, reason: str):
        super().__init__(message=f"Notification error: {reason}", code=502)
