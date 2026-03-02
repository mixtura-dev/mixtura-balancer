from functools import lru_cache
from typing import AsyncGenerator

from app.services.redis_service import RedisService
from app.services.notification_service import NotificationService
from app.services.balance_service import BalanceService
from app.services.mask_service import MaskService


# Singleton сервисы
_redis_service: RedisService | None = None
_notification_service: NotificationService | None = None
_balance_service: BalanceService | None = None


async def get_redis_service() -> RedisService:
    """Получение Redis сервиса"""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
        await _redis_service.connect()
    return _redis_service


async def get_notification_service() -> NotificationService:
    """Получение сервиса уведомлений"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
        await _notification_service.connect()
    return _notification_service


async def get_balance_service() -> BalanceService:
    """Получение сервиса балансировки"""
    global _balance_service
    if _balance_service is None:
        redis = await get_redis_service()
        notification = await get_notification_service()
        _balance_service = BalanceService(
            redis_service=redis,
            notification_service=notification,
            mask_service=MaskService(),
        )
    return _balance_service


async def shutdown_services() -> None:
    """Завершение работы сервисов"""
    global _redis_service, _notification_service, _balance_service

    if _redis_service:
        await _redis_service.disconnect()
        _redis_service = None

    if _notification_service:
        await _notification_service.disconnect()
        _notification_service = None

    _balance_service = None
