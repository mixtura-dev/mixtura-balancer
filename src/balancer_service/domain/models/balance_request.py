from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class PlayerRole(BaseModel):
    priority: int = Field(ge=0)
    rating: int = Field(ge=0)


class Player(BaseModel):
    member_id: UUID
    roles: dict[UUID, PlayerRole]


class RoleSettings(BaseModel):
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
    fairness_coef: float = Field(default=3.0, description="Вес fairness")
    role_fairness_coef: float = Field(default=1.0, description="Вес role fairness")
    role_priority_coef: float = Field(default=80.0, description="Вес role priority")
    role_priority_imbalance_coef: float = Field(
        default=0.2, ge=0, description="Вес штрафа за дисбаланс приоритетов"
    )
    fairness_power_coef: float = Field(default=2.0, ge=1, description="Степень для fairness")
    uniformity_power_coef: float = Field(default=2.0, ge=1, description="Степень для uniformity")


class BalanceSettings(BaseModel):
    max_in_team: int = Field(ge=1, description="Максимум игроков в команде")
    roles: dict[UUID, RoleSettings] = Field(
        default={}, description="Настойки ролей: UUID роли -> настройки"
    )
    math: MathSettings = Field(default_factory=MathSettings, description="Математические настройки")
    balance_limit: float = Field(default=1000.0, ge=0, description="Лимит дисбаланса")

    @model_validator(mode="after")
    def validate_settings(self) -> "BalanceSettings":
        total_min = sum(r.min_in_team for r in self.roles.values())
        if total_min > self.max_in_team:
            raise ValueError(
                f"Sum of min_in_team ({total_min}) exceeds max_in_team ({self.max_in_team})"
            )
        return self


class BalanceRequest(BaseModel):
    draft_id: UUID
    players: list[Player]
    balance_settings: BalanceSettings

    @model_validator(mode="after")
    def validate_players_roles(self) -> "BalanceRequest":
        role_ids = set(self.balance_settings.roles.keys())
        for player in self.players:
            for role_id in player.roles.keys():
                if role_id not in role_ids:
                    raise ValueError(f"Player {player.member_id} has undefined role {role_id}")
        return self

    @model_validator(mode="after")
    def validate_players_count(self) -> "BalanceRequest":
        if len(self.players) > self.balance_settings.max_in_team * 2:
            raise ValueError(
                f"Number of players ({len(self.players)}) exceeds maximum allowed "
                f"({self.balance_settings.max_in_team * 2})"
            )
        return self
