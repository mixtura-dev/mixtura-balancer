"""
Пример клиента для сервиса балансировки команд.

Демонстрирует отправку запроса на балансировку и получение результата
через RabbitMQ используя FastStream.
"""

import asyncio
import logging
import uuid
from datetime import datetime

from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitQueue

# Импортируем модели из сервиса
from balancer_service.app.schemas import ErrorResponse, ResponseMessage
from balancer_service.domain.models.balance import (
    Balance,
    DraftBalances,
    QualityMetrics,
    Team,
    TeamPlayer,
)
from balancer_service.domain.models.balance_request import (
    BalanceRequest,
    BalanceSettings,
    MathSettings,
    Player,
    PlayerRole,
    RoleSettings,
)
from balancer_service.env_config import env

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class BalanceClient:
    """Клиент для взаимодействия с сервисом балансировки команд."""

    def __init__(self, broker_url: str):
        """
        Инициализация клиента.

        Args:
            broker_url: URL RabbitMQ брокера
        """
        self.broker = RabbitBroker(broker_url)
        self.response_received = asyncio.Event()
        self.response_data: ResponseMessage[DraftBalances  | ErrorResponse] | None = None

    async def start(self):
        """Запустить клиент и подписаться на ответы."""
        await self.broker.connect()
        await self.broker.declare_queue(RabbitQueue(name="balance_response"))  # Объявляем очередь для ответов
        # Подписываемся на очередь ответов
        @self.broker.subscriber("balance_response")
        async def handle_response(message: ResponseMessage[DraftBalances | ErrorResponse]):
            logger.info(f"Получен ответ")
            self.response_data = message
            self.response_received.set()
        self.app = FastStream(self.broker)
        await self.app.start()

    async def stop(self):
        """Остановить клиент."""
        await self.broker.stop()

    async def send_balance_request(self, request: BalanceRequest) -> ResponseMessage[DraftBalances | ErrorResponse]:
        """
        Отправить запрос на балансировку.

        Args:
            request: Запрос на балансировку

        Returns:
            Ответ с результатами балансировки
        """
        logger.info(f"Отправка запроса балансировки для draft_id={request.draft_id}")

        # Отправляем запрос
        await self.broker.publish(
            request,
            routing_key="mix_balance_service.balance",
            reply_to="balance_response",
        )

        # Ждём ответ с таймаутом
        try:
            await asyncio.wait_for(self.response_received.wait(), timeout=30.0)
            self.response_received.clear()
            await self.app.stop()  # Останавливаем приложение после получения ответа
            if self.response_data is None:
                logger.error("Ответ не получен")
                raise Exception("Ответ не получен")
            return self.response_data
        except asyncio.TimeoutError:
            logger.error("Таймаут при ожидании ответа от сервиса")
            raise


async def create_example_balance_request() -> BalanceRequest:
    """
    Создать пример запроса на балансировку.

    Returns:
        Пример BalanceRequest с тестовыми данными
    """
    # Создаем UUIDs для ролей
    role_carry_id = uuid.uuid4()
    role_midlane_id = uuid.uuid4()
    role_support_id = uuid.uuid4()

    # Настройки для ролей
    role_settings = {
        role_carry_id: RoleSettings(
            original_game_role=role_carry_id,
            max_in_team=2,
            min_in_team=1,
        ),
        role_midlane_id: RoleSettings(
            original_game_role=role_midlane_id,
            max_in_team=2,
            min_in_team=1,
        ),
        role_support_id: RoleSettings(
            original_game_role=role_support_id,
            max_in_team=2,
            min_in_team=1,
        ),
    }

    # Математические настройки для качества баланса
    math_settings = MathSettings(
        fairness_coef=3.0,
        role_fairness_coef=1.0,
        role_priority_coef=80.0,
        role_priority_imbalance_coef=0.2,
        fairness_power_coef=2.0,
        uniformity_power_coef=2.0,
    )

    # Общие настройки баланса
    balance_settings = BalanceSettings(
        max_in_team=3,
        roles=role_settings,
        math=math_settings,
        balance_limit=1000.0,
    )

    # Создаем список игроков
    players = []
    player_configs = [
        # (rating_carry, priority_carry, rating_mid, priority_mid, rating_support, priority_support)
        (2800, 1, 2600, 3, 2400, 2),  # Strong carry player
        (2700, 2, 2800, 1, 2500, 3),  # Strong midlaner
        (2600, 3, 2500, 2, 2800, 1),  # Strong support
        (2400, 1, 2600, 2, 2700, 3),
        (2500, 2, 2400, 3, 2600, 1),
        (2300, 3, 2500, 1, 2400, 2),
    ]

    for i, (r_carry, p_carry, r_mid, p_mid, r_sup, p_sup) in enumerate(player_configs):
        player = Player(
            member_id=uuid.uuid4(),
            roles={
                role_carry_id: PlayerRole(priority=p_carry, rating=r_carry),
                role_midlane_id: PlayerRole(priority=p_mid, rating=r_mid),
                role_support_id: PlayerRole(priority=p_sup, rating=r_sup),
            },
        )
        players.append(player)
        logger.info(
            f"Игрок {i + 1}: Carry({r_carry}, priority={p_carry}), "
            f"Mid({r_mid}, priority={p_mid}), Support({r_sup}, priority={p_sup})"
        )

    # Создаем запрос баланса
    balance_request = BalanceRequest(
        draft_id=uuid.uuid4(),
        players=players,
        balance_settings=balance_settings,
    )

    return balance_request


async def print_balance_results(result: ResponseMessage[DraftBalances | ErrorResponse]):
    """
    Вывести результаты балансировки в читаемом формате.

    Args:
        result: Результат балансировки
    """
    if result.status != 200:
        logger.error(f"Ошибка: статус {result.status}")
        return

    if isinstance(result.message, ErrorResponse):
        logger.error(f"Ошибка от сервиса: {result.message.message}")
        return

    draft = result.message
    logger.info("=" * 80)
    logger.info(f"ID черновика: {draft.draft_id}")
    logger.info(f"Время создания: {draft.created_at}")
    logger.info(f"Всего вариантов баланса: {len(draft.balances)}")
    logger.info("=" * 80)

    for balance_idx, balance in enumerate(draft.balances[:5], 1):
        logger.info(f"--- Вариант баланса #{balance_idx} (ID: {balance.id}) ---")
        logger.info(f"Качество баланса:")
        logger.info(f"  - Справедливость: {balance.quality.fairness:.2f}")
        logger.info(f"  - Справедливость по ролям: {balance.quality.role_fairness:.2f}")
        logger.info(f"  - Очки ролей: {balance.quality.role_points:.2f}")
        logger.info(f"  - Однородность: {balance.quality.uniformity:.2f}")

        for team_idx, team in enumerate(balance.teams, 1):
            logger.info(f"  Команда {team_idx} (ID: {team.id}):")
            total_rating = 0
            for player in team.players:
                logger.info(f"    - Player {player.member_id}: Role={player.game_role_id}, Rating={player.rating}")
                total_rating += player.rating
            logger.info(f"  Общий рейтинг команды: {total_rating}")


async def main():
    """Основная функция примера."""
    logger.info("Запуск примера клиента балансировки команд")

    # Инициализируем клиент
    client = BalanceClient(env.rabbit.url)

    try:
        # Запускаем клиент
        await client.start()
        logger.info("Клиент подключен к RabbitMQ")

        # Создаем пример запроса
        logger.info("Создание примера запроса на балансировку...")
        balance_request = await create_example_balance_request()
        logger.info(f"Создан запрос для {len(balance_request.players)} игроков")

        # Отправляем запрос и получаем результат
        logger.info("Отправка запроса на сервис...")
        result = await client.send_balance_request(balance_request)

        # Выводим результаты
        await print_balance_results(result)

    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
    finally:
        await client.stop()
        logger.info("Клиент отключен")


if __name__ == "__main__":
    asyncio.run(main())
