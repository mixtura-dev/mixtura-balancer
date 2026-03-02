import logging
from typing import Optional
from datetime import datetime

import redis.asyncio as redis

from app.config import get_settings
from app.models.balance import BalanceResult, BalanceResultWithMeta
from app.exceptions import RedisConnectionException

logger = logging.getLogger(__name__)


class RedisService:
    """Сервис для работы с Redis"""

    def __init__(self):
        self.settings = get_settings()
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Подключение к Redis"""
        try:
            self._client = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                db=self.settings.redis_db,
                password=self.settings.redis_password,
                decode_responses=True,
            )
            await self._client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise RedisConnectionException(str(e))

    async def disconnect(self) -> None:
        """Отключение от Redis"""
        if self._client:
            await self._client.close()
            logger.info("Disconnected from Redis")

    async def health_check(self) -> bool:
        """Проверка соединения"""
        try:
            if self._client:
                await self._client.ping()
                return True
        except Exception:
            pass
        return False

    def _get_draft_key(self, draft_id: str) -> str:
        """Получение ключа для драфта"""
        return f"balance:draft:{draft_id}"

    def _get_balance_key(self, draft_id: str, balance_id: str) -> str:
        """Получение ключа для баланса"""
        return f"balance:draft:{draft_id}:result:{balance_id}"

    async def save_balances(self, draft_id: str, balances: list[BalanceResult]) -> int:
        """
        Сохранение балансов для драфта.
        Возвращает количество сохранённых балансов.
        """
        if not self._client:
            raise RedisConnectionException("Not connected to Redis")

        draft_key = self._get_draft_key(draft_id)
        ttl = self.settings.balance_ttl

        # Очищаем предыдущие результаты
        await self._delete_draft_balances(draft_id)

        # Сохраняем новые
        pipe = self._client.pipeline()

        balance_ids = []
        for i, balance in enumerate(balances):
            meta = BalanceResultWithMeta(
                draft_id=draft_id, result=balance, created_at=datetime.utcnow().timestamp()
            )

            balance_key = self._get_balance_key(draft_id, meta.balance_id)
            balance_ids.append(meta.balance_id)

            pipe.set(balance_key, meta.model_dump_json(), ex=ttl)

        # Сохраняем индекс балансов для драфта (sorted set по quality)
        for i, (balance, balance_id) in enumerate(zip(balances, balance_ids)):
            score = balance.quality.total_score
            pipe.zadd(draft_key, {balance_id: score})

        pipe.expire(draft_key, ttl)

        await pipe.execute()

        logger.info(f"Saved {len(balances)} balances for draft {draft_id}")
        return len(balances)

    async def _delete_draft_balances(self, draft_id: str) -> None:
        """Удаление всех балансов драфта"""
        if not self._client:
            return

        draft_key = self._get_draft_key(draft_id)

        # Получаем все balance_ids
        balance_ids = await self._client.zrange(draft_key, 0, -1)

        if balance_ids:
            pipe = self._client.pipeline()
            for balance_id in balance_ids:
                pipe.delete(self._get_balance_key(draft_id, balance_id))
            pipe.delete(draft_key)
            await pipe.execute()

    async def get_balances_paginated(
        self, draft_id: str, page: int, page_size: int
    ) -> tuple[list[BalanceResult], int]:
        """
        Получение балансов с пагинацией.
        Возвращает (список балансов, общее количество).
        """
        if not self._client:
            raise RedisConnectionException("Not connected to Redis")

        draft_key = self._get_draft_key(draft_id)

        # Общее количество
        total = await self._client.zcard(draft_key)

        if total == 0:
            return [], 0

        # Получаем ID балансов для страницы
        start = page * page_size
        end = start + page_size - 1

        balance_ids = await self._client.zrange(draft_key, start, end)

        if not balance_ids:
            return [], total

        # Получаем данные балансов
        pipe = self._client.pipeline()
        for balance_id in balance_ids:
            pipe.get(self._get_balance_key(draft_id, balance_id))

        results = await pipe.execute()

        balances = []
        for data in results:
            if data:
                meta = BalanceResultWithMeta.model_validate_json(data)
                balances.append(meta.result)

        return balances, total

    async def get_total_balances(self, draft_id: str) -> int:
        """Получение общего количества балансов для драфта"""
        if not self._client:
            raise RedisConnectionException("Not connected to Redis")

        draft_key = self._get_draft_key(draft_id)
        return await self._client.zcard(draft_key)

    async def draft_exists(self, draft_id: str) -> bool:
        """Проверка существования драфта"""
        if not self._client:
            return False

        draft_key = self._get_draft_key(draft_id)
        return await self._client.exists(draft_key) > 0
