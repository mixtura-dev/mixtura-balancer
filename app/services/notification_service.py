import logging

from faststream.rabbit import RabbitBroker

from app.config import get_settings
from app.exceptions import NotificationException
from app.schemas.rabbitmq import BalanceCompletedMessage, BalanceFailedMessage

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для отправки уведомлений через RabbitMQ"""

    def __init__(self):
        self.settings = get_settings()
        self._broker: RabbitBroker | None = None

    async def connect(self) -> None:
        """Подключение к RabbitMQ"""
        try:
            self._broker = RabbitBroker(url=self.settings.rabbitmq_url)
            await self._broker.connect()
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise NotificationException(str(e))

    async def disconnect(self) -> None:
        """Отключение от RabbitMQ"""
        if self._broker:
            await self._broker.close()
            logger.info("Disconnected from RabbitMQ")

    async def notify_balance_completed(
        self, draft_id: str, total_results: int, best_score: float
    ) -> bool:
        """
        Уведомление о завершении балансировки.

        Args:
            draft_id: ID драфта
            total_results: Количество найденных балансов
            best_score: Лучший результат (оценка)

        Returns:
            True если уведомление отправлено успешно
        """
        if not self._broker:
            logger.warning("RabbitMQ broker not connected")
            return False

        message = BalanceCompletedMessage(
            draft_id=draft_id, total_results=total_results, best_score=best_score
        )

        try:
            await self._broker.publish(
                message.model_dump(), queue=self.settings.rabbitmq_balance_completed_queue
            )
            logger.info(f"Successfully published balance completed event for draft {draft_id}")
            return True
        except Exception as e:
            logger.error(f"Error publishing balance completed event: {e}")
            raise NotificationException(str(e))

    async def notify_balance_failed(self, draft_id: str, error_message: str) -> bool:
        """Уведомление об ошибке балансировки"""
        if not self._broker:
            logger.warning("RabbitMQ broker not connected")
            return False

        message = BalanceFailedMessage(draft_id=draft_id, error=error_message)

        try:
            await self._broker.publish(
                message.model_dump(), queue=self.settings.rabbitmq_balance_failed_queue
            )
            logger.info(f"Successfully published balance failed event for draft {draft_id}")
            return True
        except Exception as e:
            logger.error(f"Error publishing balance failed event: {e}")
            raise NotificationException(str(e))
