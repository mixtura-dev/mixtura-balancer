from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Конфигурация приложения"""

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None

    # TTL для хранения балансов (в секундах)
    balance_ttl: int = 86400  # 24 часа

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    rabbitmq_balance_completed_queue: str = "balance.completed"
    rabbitmq_balance_failed_queue: str = "balance.failed"

    # Balance settings
    max_balance_results: int = 1000
    default_page_size: int = 50
    max_page_size: int = 100

    # Math defaults
    default_alpha: float = 1.0
    default_beta: float = 1.0
    default_gamma: float = 1.0
    default_p: float = 2.0
    default_q: float = 2.0

    class Config:
        env_file = ".env"
        env_prefix = "BALANCE_"


@lru_cache
def get_settings() -> Settings:
    return Settings()
