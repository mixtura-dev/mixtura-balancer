from uuid import UUID

from pydantic import BaseModel, Field


class PlayerRole(BaseModel):
    """Роль игрока с приоритетом и рейтингом"""

    priority: int = Field(ge=1, description="Приоритет роли")
    rating: int = Field(ge=0, description="Рейтинг на этой роли")


class Player(BaseModel):
    """Модель игрока"""

    member_id: UUID = Field(description="ID участника")
    roles: dict[UUID, PlayerRole] = Field(description="Роли игрока: UUID роли -> данные роли")

    def can_play_role(self, role_id: UUID) -> bool:
        """Проверка, может ли игрок играть указанную роль"""
        return role_id in self.roles

    def get_rating_for_role(self, role_id: UUID) -> int | None:
        """Получение рейтинга для роли"""
        if role_id in self.roles:
            return self.roles[role_id].rating
        return None

    def get_priority_for_role(self, role_id: UUID) -> int | None:
        """Получение приоритета для роли"""
        if role_id in self.roles:
            return self.roles[role_id].priority
        return None

    def get_best_role(self) -> UUID | None:
        """Получение роли с наивысшим приоритетом"""
        if not self.roles:
            return None
        return min(self.roles.keys(), key=lambda r: self.roles[r].priority)

    def get_role_priority_points(self, role_id: UUID, max_roles: int = 5) -> int:
        """
        Расчёт очков приоритета для роли.
        Больше очков = лучше соответствие
        """
        if role_id not in self.roles:
            return 0

        priority = self.roles[role_id].priority
        return max(0, max_roles - priority + 1)
