# Модель команд сервиса балансировки

## Обзор

Сервис использует архитектуру на основе **RabbitMQ** и **FastStream** для асинхронной обработки запросов на балансировку команд. Коммуникация происходит через публикацию сообщений в очередь RabbitMQ.

## Архитектура коммуникации

```
┌─────────────────┐     RabbitMQ              ┌──────────────────┐
│   Balance       │  ───────────────────────> │  Balancer        │
│   Client        │                           │  Service         │
│                 │                           │                  │
│                 │  <─────────────────────── │                  │
└─────────────────┘     (ответ)               └──────────────────┘
     balance_response                          mix_balance_service.balance
```

## Команды (Commands)

### 1. BalanceRequest

**Назначение:** Запрос на расчёт баланса команд

**Routing Key:** `mix_balance_service.balance`

**Структура:**

```python
class BalanceRequest:
    draft_id: UUID                    # Уникальный идентификатор черновика/матча
    players: list[Player]             # Список игроков для балансировки
    balance_settings: BalanceSettings # Настройки балансировки
```

#### Player

```python
class Player:
    member_id: UUID                   # ID игрока
    roles: dict[UUID, PlayerRole]     # Роли игрока с приоритетами и рейтингами
```

#### PlayerRole

```python
class PlayerRole:
    priority: int  # Приоритет роли (0 = минимальный)
    rating: int    # Рейтинг игрока на данной роли
```

#### BalanceSettings

```python
class BalanceSettings:
    max_in_team: int                  # Максимум игроков в одной команде
    roles: dict[UUID, RoleSettings]   # Настройки для каждой роли
    math: MathSettings                # Математические параметры алгоритма
    balance_limit: float              # Лимит дисбаланса (по умолчанию 1000.0)
```

#### RoleSettings

```python
class RoleSettings:
    original_game_role: UUID    # Оригинальный ID роли в игре
    max_in_team: int            # Максимум игроков этой роли в команде
    min_in_team: int            # Минимум игроков этой роли в команде
```

#### MathSettings

| Параметр | Тип | Описание | По умолчанию |
|----------|-----|----------|--------------|
| `fairness_coef` | float | Вес справедливости | 3.0 |
| `role_fairness_coef` | float | Вес справедливости по ролям | 1.0 |
| `role_priority_coef` | float | Вес приоритета роли | 80.0 |
| `role_priority_imbalance_coef` | float | Штраф за дисбаланс приоритетов | 0.2 |
| `fairness_power_coef` | float | Степень для fairness | 2.0 |
| `uniformity_power_coef` | float | Степень для uniformity | 2.0 |

## Ответы (Responses)

### ResponseMessage

**Формат:** Универсальная обёртка для всех ответов

```python
class ResponseMessage[T]:
    status: int       # HTTP-подобный код статуса (200 = успех)
    message: T        # Полезная нагрузка (DraftBalances или ErrorResponse)
```

### DraftBalances (успешный ответ)

```python
class DraftBalances:
    draft_id: UUID              # ID черновика (из запроса)
    balances: list[Balance]     # Список вариантов баланса
    created_at: datetime        # Время создания ответа
```

#### Balance

```python
class Balance:
    id: UUID                    # Уникальный ID варианта баланса
    quality: QualityMetrics     # Метрики качества баланса
    teams: list[Team]           # Сформированные команды
```

#### QualityMetrics

| Поле | Тип | Описание |
|------|-----|----------|
| `uniformity` | float | Однородность распределения |
| `fairness` | float | Общая справедливость |
| `role_fairness` | float | Справедливость по ролям |
| `role_points` | float | Очки ролей |

#### Team

```python
class Team:
    id: UUID              # ID команды
    players: list[TeamPlayer]  # Игроки в команде
```

#### TeamPlayer

```python
class TeamPlayer:
    member_id: UUID     # ID игрока
    game_role_id: UUID  # ID роли в игре
    rating: int         # Рейтинг игрока
```

### ErrorResponse (ошибка)

```python
class ErrorResponse:
    message: str    # Описание ошибки
```

## Валидация

BalanceRequest проходит следующую валидацию:

1. **Роли игроков:** Все роли игроков должны быть определены в `balance_settings.roles`
2. **Количество игроков:** `len(players) <= max_in_team * 2`
3. **RoleSettings:** `min_in_team <= max_in_team`
4. **Сумма минимумов:** `sum(min_in_team) <= max_in_team`

## Пример использования

```python
from balancer_service.domain.models.balance_request import (
    BalanceRequest, BalanceSettings, MathSettings, Player, PlayerRole, RoleSettings
)
import uuid

# Создание запроса
role_id = uuid.uuid4()
request = BalanceRequest(
    draft_id=uuid.uuid4(),
    players=[
        Player(
            member_id=uuid.uuid4(),
            roles={
                role_id: PlayerRole(priority=1, rating=2500)
            }
        )
    ],
    balance_settings=BalanceSettings(
        max_in_team=3,
        roles={
            role_id: RoleSettings(
                original_game_role=role_id,
                min_in_team=1,
                max_in_team=2
            )
        },
        math=MathSettings()
    )
)
```

## Обработка ошибок

Сервис использует `ExceptionMiddleware` для обработки ошибок:

- `DomainException` → `ErrorResponse` с кодом статуса
- Любая другая ошибка → логирование и возврат ошибки
