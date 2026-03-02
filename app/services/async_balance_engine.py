"""
Async Python wrapper for C++ balance engine.
Provides awaitable interface for balance calculation without blocking the event loop.
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from uuid import UUID

import balance_engine

from app.models.balance import BalanceResult, QualityMetrics, Team, TeamPlayer
from app.models.player import Player
from app.models.settings import BalanceSettings

logger = logging.getLogger(__name__)


class AsyncBalanceEngine:
    """Async wrapper for C++ balance engine"""

    def __init__(self, max_workers: int = 4):
        """
        Initialize async balance engine.

        Args:
            max_workers: Maximum number of worker threads for C++ computations
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def __del__(self):
        """Cleanup executor"""
        self.executor.shutdown(wait=True)

    async def find_balances_async(
        self, players: list[Player], settings: BalanceSettings
    ) -> list[BalanceResult]:
        """
        Synchronous wrapper for C++ balance engine.
        This runs in a thread pool executor.
        Uses high-level wrapper API with automatic UUID handling.
        """
        try:
            # Set quality settings in C++ engine
            quality_settings = balance_engine.QualitySettings()
            quality_settings.alpha = settings.math.alpha
            quality_settings.beta = settings.math.beta
            quality_settings.gamma = settings.math.gamma
            quality_settings.p = settings.math.p
            quality_settings.q = settings.math.q
            quality_settings.g = settings.math.p
            quality_settings.max_priority = 5  # Default max priority

            # Convert Python objects to C++ structures (UUID conversion is automatic)
            players_for_engine = self._convert_players_to_cpp(players)
            role_ids = settings.get_role_ids_ordered()
            role_constraints = self._convert_constraints_to_cpp(settings)

            # Call C++ engine with wrapped API (handles UUID automatically)
            result = await balance_engine.async_find_balances(
                players_for_engine,
                role_ids,
                role_constraints,
                settings.max_in_team,
                settings.balance_limit,
                settings=quality_settings
            )

            # Convert wrapper result to Python BalanceResult (UUID already handled)
            balance_result = [self._convert_result_to_python(r) for r in result]

            return balance_result

        except Exception as e:
            logger.error(f"Error in C++ balance engine: {e}")
            raise

    @staticmethod
    def _convert_players_to_cpp(players: list[Player]) -> list[balance_engine.PlayerInfo]:
        """
        Convert Python Player objects to wrapped PlayerInfo structures.
        UUID conversion happens automatically in the wrapper.
        """
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
        """Convert BalanceSettings role constraints to wrapped RoleConstraint"""
        constraints = {}

        for id, role_settings in settings.roles.items():
            constraint = balance_engine.RoleConstraint(
                min_in_team=role_settings.min_in_team, max_in_team=role_settings.max_in_team
            )
            constraints[id] = constraint

        return constraints

    @staticmethod
    def _convert_result_to_python(result: balance_engine.BalanceResultData) -> BalanceResult:
        """
        Convert wrapped BalanceResultData to Python BalanceResult.
        UUID values are already Python UUIDs from the wrapper properties.
        """
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

            team = Team(team_id=wrapped_team.team_id, players=team_players)
            teams.append(team)

        quality = QualityMetrics(
            evaluation=result.quality.evaluation,
            uniformity=result.quality.uniformity,
            fairness=result.quality.fairness,
            role_points=result.quality.role_points,
        )

        return BalanceResult(quality=quality, teams=teams)


# Singleton instance for convenience
_async_engine: AsyncBalanceEngine | None = None


def get_async_engine() -> AsyncBalanceEngine:
    """Get or create the global async engine instance"""
    global _async_engine
    if _async_engine is None:
        _async_engine = AsyncBalanceEngine()
    return _async_engine
