"""
Async Python wrapper for C++ balance engine.
Provides awaitable interface for balance calculation without blocking the event loop.
"""

import datetime
import logging
from uuid import UUID, uuid4

import balance_engine

from ..app.exceptions import DomainException

from .models.balance import Balance, DraftBalances, QualityMetrics, Team, TeamPlayer
from .models.balance_request import BalanceRequest, BalanceSettings, Player

logger = logging.getLogger(__name__)


class AsyncBalanceEngine:
    async def find_balances_async(self, balance_request: BalanceRequest) -> DraftBalances:
        try:
            players = balance_request.players
            settings = balance_request.balance_settings
            # Set quality settings in C++ engine
            quality_settings = balance_engine.QualitySettings()
            quality_settings.fairness_coef = settings.math.fairness_coef
            quality_settings.role_fairness_coef = settings.math.role_fairness_coef
            quality_settings.role_priority_coef = settings.math.role_priority_coef
            quality_settings.imbalance_role_priority_coef = (
                settings.math.role_priority_imbalance_coef
            )
            quality_settings.fairness_power = settings.math.fairness_power_coef
            quality_settings.uniformity_power = settings.math.uniformity_power_coef
            quality_settings.role_fairness_power = settings.math.fairness_power_coef
            quality_settings.max_priority = 3  # Default max priority

            # Convert Python objects to C++ structures (UUID conversion is automatic)
            players_for_engine = self._convert_players_to_cpp(players)
            role_ids = list(settings.roles.keys())
            role_constraints = self._convert_constraints_to_cpp(settings)

            # Call C++ engine with wrapped API (handles UUID automatically)
            result = await balance_engine.BalanceEngine.async_quick_find_balances(
                players_for_engine,
                role_ids,
                role_constraints,
                settings.max_in_team,
                settings.balance_limit,
                quality_settings=quality_settings,
            )

            if result.result_code != 200:
                logger.error(f"Balance engine error: {result.status}")
                raise DomainException(result.result_code, result.status)

            # Convert wrapper result to Python BalanceResult (UUID already handled)
            balance_result = [self._convert_result_to_python(r) for r in result]

            return DraftBalances(
                draft_id=balance_request.draft_id,
                balances=balance_result,
                created_at=datetime.datetime.now(),
            )

        except Exception as e:
            logger.error(f"Error in C++ balance engine: {e}")
            raise

    @staticmethod
    def _convert_players_to_cpp(players: list[Player]) -> list[balance_engine.PlayerInfo]:
        wrapped_players: list[balance_engine.PlayerInfo] = []

        for player in players:
            # Create wrapped roles (UUID conversion is automatic)
            roles = []
            for role_id, role_info in player.roles.items():
                role = balance_engine.PlayerRoleInfo(
                    role_id=role_id,  # Python UUID, wrapper handles conversion
                    priority=role_info.priority,
                    rating=role_info.rating,
                )
                roles.append(role)

            # Create wrapped PlayerInfo
            wrapped_player = balance_engine.PlayerInfo(member_id=player.member_id, roles=roles)
            wrapped_players.append(wrapped_player)

        return wrapped_players

    @staticmethod
    def _convert_constraints_to_cpp(
        settings: BalanceSettings,
    ) -> dict[UUID, balance_engine.RoleConstraint]:
        constraints = {}

        for id, role_settings in settings.roles.items():
            constraint = balance_engine.RoleConstraint(
                min_in_team=role_settings.min_in_team, max_in_team=role_settings.max_in_team
            )
            constraints[id] = constraint

        return constraints

    @staticmethod
    def _convert_result_to_python(result: balance_engine.BalanceResultData) -> Balance:
        teams = []

        for wrapped_team in result.teams:
            team_players = []
            for wrapped_player in wrapped_team.players:
                # wrapped_player.game_role_id is already a Python UUID
                team_player = TeamPlayer(
                    member_id=wrapped_player.member_id,
                    game_role_id=wrapped_player.game_role_id,
                    rating=wrapped_player.rating,
                )
                team_players.append(team_player)

            team = Team(id=wrapped_team.team_id, players=team_players)
            teams.append(team)

        quality = QualityMetrics(
            uniformity=result.quality.uniformity,
            fairness=result.quality.fairness,
            role_fairness=result.quality.role_fairness,
            role_points=result.quality.role_points,
        )

        return Balance(quality=quality, teams=teams, id=uuid4())


# Singleton instance for convenience
_async_engine: AsyncBalanceEngine | None = None


def get_async_engine() -> AsyncBalanceEngine:
    """Get or create the global async engine instance"""
    global _async_engine
    if _async_engine is None:
        _async_engine = AsyncBalanceEngine()
    return _async_engine
