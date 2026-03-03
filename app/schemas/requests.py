from pydantic import BaseModel, Field
from uuid import UUID

from app.models.player import PlayerRole


class PlayerRequest(BaseModel):
    """Запрос игрока"""

    member_id: str
    roles: dict[UUID, PlayerRole]


class RoleSettingsRequest(BaseModel):
    """Настройки роли"""

    original_game_role: UUID
    max_in_team: int = Field(ge=0)
    min_in_team: int = Field(ge=0)


class MathSettingsRequest(BaseModel):
    """Математические настройки"""

    fairness_coef: float = Field(default=1.0, ge=0)
    role_fairness_coef: float = Field(default=1.0, ge=0)
    role_priority_coef: float = Field(default=1.0, ge=0)
    fairness_power: float = Field(default=2.0, ge=1)
    uniformity_power: float = Field(default=2.0, ge=1)


class SettingsRequest(BaseModel):
    """Настройки балансировки"""

    max_in_team: int = Field(ge=1)
    roles: dict[UUID, RoleSettingsRequest]
    math: MathSettingsRequest = Field(default_factory=MathSettingsRequest)
    balance_limit: float = Field(default=1000.0, ge=0)


class BalanceRequest(BaseModel):
    """Запрос на балансировку"""

    draft_id: str = Field(description="ID драфта")
    players: list[PlayerRequest] = Field(description="Список игроков")
    settings: SettingsRequest = Field(description="Настройки балансировки")

    class Config:
        json_schema_extra = {
            "example": {
                "draft_id": "draft_12345",
                "players": [
                    {
                        "member_id": "player_001",
                        "roles": {
                            "550e8400-e29b-41d4-a716-446655440001": {"priority": 1, "rating": 2500}
                        },
                    }
                ],
                "settings": {
                    "max_in_team": 2,
                    "roles": {
                        "550e8400-e29b-41d4-a716-446655440001": {
                            "original_game_role": "00000000-0000-0000-0000-000000000000",
                            "max_in_team": 1,
                            "min_in_team": 1,
                        }
                    },
                },
            }
        }


class PaginationRequest(BaseModel):
    """Запрос с пагинацией"""

    draft: str = Field(alias="draft", description="ID драфта")
    page: int = Field(default=0, ge=0, description="Номер страницы")
    page_size: int = Field(default=50, ge=1, le=100, description="Размер страницы")

    class Config:
        populate_by_name = True
