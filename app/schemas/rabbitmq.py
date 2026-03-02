from pydantic import BaseModel, Field


class BalanceCompletedMessage(BaseModel):
    """Сообщение о завершении балансировки"""

    draft_id: str = Field(description="ID драфта")
    status: str = Field(default="completed", description="Статус")
    total_results: int = Field(ge=0, description="Количество найденных балансов")
    best_score: float = Field(ge=0, description="Лучший результат (оценка)")


class BalanceFailedMessage(BaseModel):
    """Сообщение об ошибке балансировки"""

    draft_id: str = Field(description="ID драфта")
    status: str = Field(default="failed", description="Статус")
    error: str = Field(description="Описание ошибки")
