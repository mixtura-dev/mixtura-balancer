import datetime
from uuid import UUID

from pydantic import BaseModel


class QualityMetrics(BaseModel):
    uniformity: float
    fairness: float
    role_points: float
    role_fairness: float


class TeamPlayer(BaseModel):
    member_id: UUID
    game_role_id: UUID
    rating: int


class Team(BaseModel):
    id: UUID
    players: list[TeamPlayer]


class Balance(BaseModel):
    id: UUID
    quality: QualityMetrics
    teams: list[Team]


class DraftBalances(BaseModel):
    draft_id: UUID
    balances: list[Balance]
    created_at: datetime.datetime
