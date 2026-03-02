from pydantic import BaseModel, Field, computed_field
from typing import Generic, TypeVar, Any

from app.models.balance import BalanceResult, QualityMetrics, Team

T = TypeVar("T")


class BalanceResponse(BaseModel):
    """Ответ с балансом"""

    quality: QualityMetrics
    teams: list[Team]

    @classmethod
    def from_result(cls, result: BalanceResult) -> "BalanceResponse":
        return cls(quality=result.quality, teams=result.teams)


class PaginatedBalanceResponse(BaseModel):
    """Ответ с пагинацией балансов"""

    items: list[BalanceResponse]
    total: int = Field(description="Общее количество результатов")
    page: int = Field(description="Текущая страница")
    page_size: int = Field(description="Размер страницы")

    @computed_field
    @property
    def has_next(self) -> bool:
        """Есть ли следующая страница"""
        return (self.page + 1) * self.page_size < self.total

    @computed_field
    @property
    def total_pages(self) -> int:
        """Общее количество страниц"""
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""

    success: bool = False
    error: str
    code: int
    details: dict[str, Any] = Field(default_factory=dict)


class SuccessResponse(BaseModel, Generic[T]):
    """Успешный ответ"""

    success: bool = True
    data: T


class BalanceCreatedResponse(BaseModel):
    """Ответ на создание баланса"""

    success: bool = True
    draft_id: str
    message: str = "Balance calculation started"
    total_results: int = Field(description="Количество найденных балансов")


class HealthResponse(BaseModel):
    """Ответ проверки здоровья"""

    status: str = "healthy"
    redis: bool
    version: str = "1.0.0"
