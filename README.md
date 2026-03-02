# Team Balancing Service

Сервис API для балансировки команд в играх. Использует FastAPI, Redis, и сложные математические алгоритмы для поиска оптимальных распределений игроков по командам.

## Особенности

- **RESTful API** на базе FastAPI
- **Асинхронная обработка** запросов на балансировку
- **Redis** для хранения результатов с TTL
- **Гибкие математические модели** расчёта качества баланса
- **Поддержка ролей** с приоритетами и ограничениями
- **Пагинация** результатов
- **Docker Compose** для быстрого развёртывания

## Математический подход

Сервис использует многокритериальную оптимизацию для поиска лучших вариантов распределения:

- **Fairness (α)**: Честность между командами по общему рейтингу
- **Role Fairness (β)**: Честность распределения по ролям
- **Role Priority (γ)**: Предпочтения игроков по ролям
- **Uniformity (q)**: Равномерность распределения внутри команд

## Требования

- Python 3.11+
- Redis 7.0+
- Docker & Docker Compose (опционально)

## Установка

### Локально

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск Redis (отдельно)
redis-server

# Запуск сервиса
python -m uvicorn app.main:app --reload
```

### С Docker Compose

```bash
docker-compose up -d
```

Сервис будет доступен на `http://localhost:8000`

## API Endpoints

### POST /api/v1/balance
Асинхронное создание баланса (выполняется в фоне)

### POST /api/v1/balance/sync
Синхронное создание баланса (ожидает результата)

### POST /api/v1/balance/results
Получение результатов с пагинацией

### GET /api/v1/balance/{draft_id}/best
Получение лучшего баланса для драфта

### GET /api/v1/health
Проверка здоровья сервиса

## Пример использования

```bash
curl -X POST "http://localhost:8000/api/v1/balance/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "draft_123",
    "players": [
      {
        "member_id": "player_1",
        "roles": {
          "550e8400-e29b-41d4-a716-446655440001": {
            "priority": 1,
            "rating": 2500
          }
        }
      },
      {
        "member_id": "player_2",
        "roles": {
          "550e8400-e29b-41d4-a716-446655440002": {
            "priority": 1,
            "rating": 2400
          }
        }
      },
      {
        "member_id": "player_3",
        "roles": {
          "550e8400-e29b-41d4-a716-446655440001": {
            "priority": 2,
            "rating": 2300
          }
        }
      },
      {
        "member_id": "player_4",
        "roles": {
          "550e8400-e29b-41d4-a716-446655440002": {
            "priority": 1,
            "rating": 2200
          }
        }
      }
    ],
    "settings": {
      "max_in_team": 2,
      "roles": {
        "550e8400-e29b-41d4-a716-446655440001": {
          "original_game_role": "00000000-0000-0000-0000-000000000000",
          "max_in_team": 1,
          "min_in_team": 1
        },
        "550e8400-e29b-41d4-a716-446655440002": {
          "original_game_role": "00000000-0000-0000-0000-000000000000",
          "max_in_team": 1,
          "min_in_team": 1
        }
      },
      "balance_limit": 1000
    }
  }'
```

## Конфигурация

Переменные окружения (см. `.env`):

```
BALANCE_REDIS_HOST=localhost
BALANCE_REDIS_PORT=6379
BALANCE_REDIS_DB=0
BALANCE_REDIS_PASSWORD=
BALANCE_BALANCE_TTL=86400
BALANCE_EVENT_SERVICE_URL=http://localhost:8000
BALANCE_EVENT_SERVICE_TIMEOUT=30
BALANCE_MAX_BALANCE_RESULTS=1000
BALANCE_DEFAULT_PAGE_SIZE=50
BALANCE_MAX_PAGE_SIZE=100
BALANCE_DEFAULT_ALPHA=1.0
BALANCE_DEFAULT_BETA=1.0
BALANCE_DEFAULT_GAMMA=1.0
BALANCE_DEFAULT_P=2.0
BALANCE_DEFAULT_Q=2.0
```

## Структура проекта

```
app/
├── main.py              # Точка входа FastAPI приложения
├── config.py            # Конфигурация
├── exceptions.py        # Исключения
├── models/              # Pydantic модели
│   ├── player.py
│   ├── settings.py
│   └── balance.py
├── services/            # Бизнес-логика
│   ├── balance_service.py
│   ├── calculation_service.py
│   ├── mask_service.py
│   ├── redis_service.py
│   └── notification_service.py
├── api/                 # API маршруты
│   ├── routes.py
│   └── dependencies.py
└── schemas/             # Pydantic schemas для API
    ├── requests.py
    └── responses.py
```

## Развёртывание

### Production

```bash
# Используйте Gunicorn с uvicorn воркерами
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### С Docker

```bash
docker build -t balance-service .
docker run -p 8000:8000 --env-file .env balance-service
```

## Логирование

Логирование настроено в `app/main.py`. По умолчанию выводит в консоль с уровнем INFO.

## Тестирование

```bash
pytest tests/
```

## Лицензия

MIT
