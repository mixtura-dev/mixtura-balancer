from pydantic import BaseModel, Field, computed_field
from uuid import UUID
import uuid as uuid_lib


class QualityMetrics(BaseModel):
    """Метрики качества баланса"""

    evaluation: float = Field(ge=0, description="Общая оценка")
    uniformity: float = Field(ge=0, description="Равномерность распределения")
    fairness: float = Field(ge=0, description="Честность баланса")
    role_points: float = Field(ge=0, description="Очки ролей")

    @computed_field
    @property
    def total_score(self) -> float:
        """Итоговый балл (меньше = лучше)"""
        return self.evaluation + self.uniformity + self.fairness + self.role_points


class TeamPlayer(BaseModel):
    """Игрок в команде"""

    member_id: str = Field(description="ID участника")
    game_role_id: UUID = Field(description="ID назначенной роли")
    rating: int = Field(ge=0, description="Рейтинг на роли")


class Team(BaseModel):
    """Команда"""

    team_id: str = Field(description="ID команды")
    players: list[TeamPlayer] = Field(default_factory=list)

    @property
    def total_rating(self) -> int:
        return sum(p.rating for p in self.players)

    @property
    def average_rating(self) -> float:
        if not self.players:
            return 0.0
        return self.total_rating / len(self.players)

    def get_ratings_by_role(self) -> dict[UUID, list[int]]:
        """Получение рейтингов по ролям"""
        result: dict[UUID, list[int]] = {}
        for player in self.players:
            if player.game_role_id not in result:
                result[player.game_role_id] = []
            result[player.game_role_id].append(player.rating)
        return result


class BalanceResult(BaseModel):
    """Результат балансировки"""

    quality: QualityMetrics
    teams: list[Team]

    @classmethod
    def create_teams(cls, num_teams: int = 2) -> list[Team]:
        return [Team(team_id=f"team_{i + 1}", players=[]) for i in range(num_teams)]


class BalanceResultWithMeta(BaseModel):
    """Результат балансировки с метаданными"""

    balance_id: str = Field(
        default_factory=lambda: str(uuid_lib.uuid4()), description="Уникальный ID баланса"
    )
    draft_id: str = Field(description="ID драфта")
    result: BalanceResult
    created_at: float = Field(description="Timestamp создания")
