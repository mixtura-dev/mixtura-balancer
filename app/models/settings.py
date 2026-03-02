from pydantic import BaseModel, Field, model_validator
from uuid import UUID


class RoleSettings(BaseModel):
    """Настройки роли в команде"""

    original_game_role: UUID = Field(description="Оригинальная роль в игре")
    max_in_team: int = Field(ge=0, description="Максимум игроков этой роли в команде")
    min_in_team: int = Field(ge=0, description="Минимум игроков этой роли в команде")

    @model_validator(mode="after")
    def validate_min_max(self) -> "RoleSettings":
        if self.min_in_team > self.max_in_team:
            raise ValueError(
                f"min_in_team ({self.min_in_team}) cannot be greater than "
                f"max_in_team ({self.max_in_team})"
            )
        return self


class MathSettings(BaseModel):
    """Математические настройки расчёта баланса"""

    alpha: float = Field(default=1.0, ge=0, description="Вес fairness")
    beta: float = Field(default=1.0, ge=0, description="Вес role fairness")
    gamma: float = Field(default=1.0, ge=0, description="Вес role priority")
    p: float = Field(default=2.0, ge=1, description="Степень для fairness")
    q: float = Field(default=2.0, ge=1, description="Степень для uniformity")


class BalanceSettings(BaseModel):
    """Настройки балансировки"""

    max_in_team: int = Field(ge=1, description="Максимум игроков в команде")
    roles: dict[UUID, RoleSettings] = Field(description="Настойки ролей: UUID роли -> настройки")
    math: MathSettings = Field(default_factory=MathSettings, description="Математические настройки")
    balance_limit: float = Field(default=1000.0, ge=0, description="Лимит дисбаланса")

    @property
    def min_players_per_team(self) -> int:
        """Минимальное количество игроков в команде"""
        return sum(role.min_in_team for role in self.roles.values())

    @property
    def max_players_per_team(self) -> int:
        """Максимальное количество игроков в команде"""
        return min(self.max_in_team, sum(role.max_in_team for role in self.roles.values()))

    def get_role_ids_ordered(self) -> list[UUID]:
        """Получение списка ID ролей в порядке"""
        return list(self.roles.keys())

    @model_validator(mode="after")
    def validate_settings(self) -> "BalanceSettings":
        total_min = sum(r.min_in_team for r in self.roles.values())
        if total_min > self.max_in_team:
            raise ValueError(
                f"Sum of min_in_team ({total_min}) exceeds max_in_team ({self.max_in_team})"
            )
        return self
