import itertools
import logging
import time
from uuid import UUID

from app.config import get_settings
from app.exceptions import (
    InvalidRoleConfigurationException,
    NotEnoughPlayersException,
    NoValidBalanceException,
)
from app.models.balance import BalanceResult
from app.models.player import Player
from app.models.settings import BalanceSettings
from app.services.async_balance_engine import AsyncBalanceEngine
from app.services.mask_service import MaskService
from app.services.notification_service import NotificationService
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)


class BalanceService:
    """Основной сервис балансировки"""

    def __init__(
        self,
        redis_service: RedisService,
        notification_service: NotificationService,
        mask_service: MaskService | None = None,
        async_engine: AsyncBalanceEngine | None = None,
    ):
        self.redis = redis_service
        self.notification = notification_service
        self.mask = mask_service or MaskService()
        self.async_engine = async_engine or AsyncBalanceEngine()
        self.settings = get_settings()

    async def create_balance(
        self, draft_id: str, players: list[Player], settings: BalanceSettings
    ) -> int:
        """
        Создание баланса для драфта.

        Args:
            draft_id: ID драфта
            players: Список игроков
            settings: Настройки балансировки

        Returns:
            Количество найденных балансов
        """
        start_time = time.time()
        try:
            # Валидация
            validate_start = time.time()
            self._validate_input(players, settings)
            validate_time = time.time() - validate_start
            logger.info(f"[{draft_id}] Validation: {validate_time:.4f}s")

            # Поиск балансов (асинхронно через C++ engine)
            find_start = time.time()
            balances = await self.async_engine.find_balances_async(
                players, settings
            )
            find_time = time.time() - find_start
            logger.info(f"[{draft_id}] Finding balances: {find_time:.4f}s ({len(balances)} found)")

            if not balances:
                raise NoValidBalanceException("No valid balance found with current constraints")

            # Сортировка по качеству
            sort_start = time.time()
            balances.sort(key=lambda b: b.quality.total_score)
            sort_time = time.time() - sort_start
            logger.info(f"[{draft_id}] Sorting: {sort_time:.4f}s")

            # Ограничение количества
            balances = balances[: self.settings.max_balance_results]

            # Сохранение в Redis
            redis_start = time.time()
            await self.redis.save_balances(draft_id, balances)
            redis_time = time.time() - redis_start
            logger.info(f"[{draft_id}] Redis save: {redis_time:.4f}s")

            # Уведомление
            notif_start = time.time()
            best_score = balances[0].quality.total_score if balances else 0
            await self.notification.notify_balance_completed(
                draft_id=draft_id, total_results=len(balances), best_score=best_score
            )
            notif_time = time.time() - notif_start
            logger.info(f"[{draft_id}] Notification: {notif_time:.4f}s")

            total_time = time.time() - start_time
            logger.info(
                f"[{draft_id}] TOTAL: {total_time:.4f}s (validation={validate_time:.4f}s, find={find_time:.4f}s, sort={sort_time:.4f}s, redis={redis_time:.4f}s, notif={notif_time:.4f}s)"
            )

            return len(balances)

        except Exception as e:
            logger.error(f"Balance creation failed for draft {draft_id}: {e}")
            await self.notification.notify_balance_failed(draft_id, str(e))
            raise

    def _validate_input(self, players: list[Player], settings: BalanceSettings) -> None:
        """Валидация входных данных"""
        required_players = settings.max_in_team * 2

        if len(players) < required_players:
            raise NotEnoughPlayersException(required=required_players, actual=len(players))

        # Проверка ролей
        total_min = sum(r.min_in_team for r in settings.roles.values())
        if total_min > settings.max_in_team:
            raise InvalidRoleConfigurationException(
                f"Sum of min_in_team ({total_min}) exceeds max_in_team ({settings.max_in_team})"
            )

        # Проверка, что игроки имеют хотя бы одну валидную роль
        valid_role_ids = set(settings.roles.keys())
        for player in players:
            player_roles = set(player.roles.keys())
            if not player_roles.intersection(valid_role_ids):
                logger.warning(
                    f"Player {player.member_id} has no valid roles for this configuration"
                )

    async def get_balances(
        self, draft_id: str, page: int, page_size: int
    ) -> tuple[list[BalanceResult], int]:
        """Получение балансов с пагинацией"""
        return await self.redis.get_balances_paginated(draft_id, page, page_size)
