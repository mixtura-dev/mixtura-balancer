"""
Balance Engine wrapper for C++ bindings.

This module provides a clean interface to the C++ balance engine.
It handles all UUID to int conversion internally (both role_id and member_id).

Users should only use BalanceEngine.find_balances() method.
All input and output uses plain Python dataclasses from models.py.
"""

from __future__ import annotations

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

from . import _core
from .models import (
    BalanceResponse,
    BalanceResultData,
    PlayerInfo,
    PlayerRoleInfo,
    QualityMetrics,
    QualitySettings,
    RoleConstraint,
    TeamPlayerResult,
    TeamResult,
)

if TYPE_CHECKING:
    pass


class UUIDMapper:
    """
    Bidirectional UUID <-> int mapping.
    
    Used internally to convert Python UUIDs to C++ int identifiers
    and back. Handles both role_id and member_id mappings.
    """
    
    __slots__ = ('_uuid_to_int', '_int_to_uuid', '_next_id')
    
    def __init__(self) -> None:
        self._uuid_to_int: dict[uuid.UUID, int] = {}
        self._int_to_uuid: dict[int, uuid.UUID] = {}
        self._next_id: int = 0
    
    def register(self, uid: uuid.UUID) -> int:
        """Register a UUID and return its int mapping."""
        if uid in self._uuid_to_int:
            return self._uuid_to_int[uid]
        
        int_id = self._next_id
        self._uuid_to_int[uid] = int_id
        self._int_to_uuid[int_id] = uid
        self._next_id += 1
        return int_id
    
    def to_int(self, uid: uuid.UUID) -> int:
        """Convert UUID to int. Must be registered first."""
        return self._uuid_to_int[uid]
    
    def to_uuid(self, int_id: int) -> uuid.UUID:
        """Convert int back to UUID."""
        return self._int_to_uuid[int_id]
    
    def register_all(self, uids: list[uuid.UUID]) -> list[int]:
        """Register multiple UUIDs and return their int mappings."""
        return [self.register(uid) for uid in uids]
    
    def clear(self) -> None:
        """Clear all mappings."""
        self._uuid_to_int.clear()
        self._int_to_uuid.clear()
        self._next_id = 0


class BalanceEngine:
    """
    High-level interface to the C++ balance engine.
    
    Handles UUID to int mapping automatically for both role_id and member_id.
    
    Usage:
        engine = BalanceEngine(settings, role_ids, role_constraints)
        response = engine.find_balances(players, team_size, balance_limit)
        
        # Or one-shot:
        response = BalanceEngine.quick_find(
            players, role_ids, role_constraints, 
            team_size, balance_limit, settings
        )
    """
    
    def __init__(
        self,
        settings: QualitySettings,
        role_ids: list[uuid.UUID],
        role_constraints: dict[uuid.UUID, RoleConstraint],
    ) -> None:
        """
        Create a new BalanceEngine instance.
        
        Args:
            settings: QualitySettings object with calculation parameters
            role_ids: List of all available role UUIDs
            role_constraints: Dict mapping role UUID to RoleConstraint
        """
        self._settings = settings
        self._role_ids = role_ids
        self._role_constraints = role_constraints
        
        # Create separate mappers for roles and members
        # Role mapper is persistent (roles don't change)
        self._role_mapper = UUIDMapper()
        
        # Register all role IDs
        self._cpp_role_ids = self._role_mapper.register_all(role_ids)
        
        # Ensure constraint roles are also registered
        for role_uuid in role_constraints.keys():
            self._role_mapper.register(role_uuid)
        
        # Create C++ settings
        cpp_settings = self._convert_settings(settings)
        
        # Create C++ constraints
        cpp_constraints = self._convert_constraints(role_constraints)
        
        # Create C++ engine instance
        self._cpp_engine = _core.BalanceEngine(
            cpp_settings,
            self._cpp_role_ids,
            cpp_constraints
        )
    
    def _convert_settings(self, settings: QualitySettings) -> _core.QualitySettings:
        """Convert Python QualitySettings to C++ format."""
        cpp_settings = _core.QualitySettings()
        cpp_settings.alpha = settings.alpha
        cpp_settings.beta = settings.beta
        cpp_settings.gamma = settings.gamma
        cpp_settings.xi = settings.xi
        cpp_settings.p = settings.p
        cpp_settings.q = settings.q
        cpp_settings.g = settings.g
        cpp_settings.max_priority = settings.max_priority
        
        # Convert role weights (UUID keys -> int keys)
        if settings.role_weights:
            cpp_settings.role_weights = {
                self._role_mapper.to_int(uid): weight
                for uid, weight in settings.role_weights.items()
            }
        
        return cpp_settings
    
    def _convert_constraints(
        self, 
        constraints: dict[uuid.UUID, RoleConstraint]
    ) -> dict[int, _core.RoleConstraint]:
        """Convert Python RoleConstraints to C++ format."""
        return {
            self._role_mapper.to_int(role_uuid): _core.RoleConstraint(
                constraint.min_in_team,
                constraint.max_in_team
            )
            for role_uuid, constraint in constraints.items()
        }
    
    def _convert_players(
        self, 
        players: list[PlayerInfo],
        member_mapper: UUIDMapper,
    ) -> list[_core.PlayerInfo]:
        """Convert Python PlayerInfo list to C++ format."""
        cpp_players = []
        
        for player in players:
            # Register and convert member_id UUID -> int
            member_int_id = member_mapper.register(player.member_id)
            
            cpp_roles = []
            for role_info in player.roles:
                role_int_id = self._role_mapper.to_int(role_info.role_id)
                cpp_role = _core.RoleRating(
                    role_int_id,
                    role_info.rating,
                    role_info.priority
                )
                cpp_roles.append(cpp_role)
            
            cpp_player = _core.PlayerInfo(
                member_int_id,  # Now using int instead of UUID
                cpp_roles
            )
            cpp_players.append(cpp_player)
        
        return cpp_players
    
    def _convert_results(
        self, 
        cpp_response: _core.BalanceResponse,
        member_mapper: UUIDMapper,
    ) -> BalanceResponse:
        """Convert C++ BalanceResponse to Python format."""
        python_results: list[BalanceResultData] = []
        
        for cpp_result in cpp_response.balances:
            # Convert quality metrics
            quality = QualityMetrics(
                fairness=cpp_result.quality.fairness,
                role_fairness=cpp_result.quality.role_fairness,
                role_points=cpp_result.quality.role_points,
                uniformity=cpp_result.quality.uniformity,
            )
            
            # Convert teams
            teams: list[TeamResult] = []
            for cpp_team in cpp_result.teams:
                python_players: list[TeamPlayerResult] = []
                
                for cpp_player in cpp_team.players:
                    # Convert back: int -> UUID for both member_id and role_id
                    member_uuid = member_mapper.to_uuid(cpp_player.member_id)
                    role_uuid = self._role_mapper.to_uuid(cpp_player.role_id)
                    
                    python_player = TeamPlayerResult(
                        member_id=member_uuid,
                        game_role_id=role_uuid,
                        rating=cpp_player.rating
                    )
                    python_players.append(python_player)
                
                team = TeamResult(
                    team_id=cpp_team.name,
                    players=python_players
                )
                teams.append(team)
            
            result = BalanceResultData(
                quality=quality,
                teams=teams,
                team_mask=cpp_result.team_mask,
                role_mask1=cpp_result.role_mask1,
                role_mask2=cpp_result.role_mask2,
            )
            python_results.append(result)
        
        return BalanceResponse(
            result_code=cpp_response.result_code,
            status=cpp_response.status,
            balances=python_results
        )
    
    def find_balances(
        self,
        players: list[PlayerInfo],
        team_size: int,
        balance_limit: float,
        max_results: int = 1000,
    ) -> BalanceResponse:
        """
        Find optimal team balances.
        
        Args:
            players: List of PlayerInfo objects with Python UUID member_id and role_ids
            team_size: Size of each team
            balance_limit: Maximum quality score threshold
            max_results: Maximum number of results to return
            
        Returns:
            BalanceResponse with result code, status, and list of BalanceResultData
        """
        # Create fresh member mapper for this call
        # (members can change between calls)
        member_mapper = UUIDMapper()
        
        # Convert players to C++ format
        cpp_players = self._convert_players(players, member_mapper)
        
        # Call C++ engine
        cpp_response = self._cpp_engine.find_balances(
            cpp_players,
            team_size,
            balance_limit,
            max_results
        )
        
        # Convert results back to Python format
        return self._convert_results(cpp_response, member_mapper)
    
    @staticmethod
    def quick_find(
        players: list[PlayerInfo],
        role_ids: list[uuid.UUID],
        role_constraints: dict[uuid.UUID, RoleConstraint],
        team_size: int,
        balance_limit: float,
        settings: QualitySettings | None = None,
        max_results: int = 1000,
    ) -> BalanceResponse:
        """
        One-shot balance finding (convenience method).
        
        Creates a temporary engine and finds balances.
        For repeated calls with same settings, prefer creating
        a BalanceEngine instance.
        
        Args:
            players: List of PlayerInfo objects
            role_ids: List of all available role UUIDs
            role_constraints: Dict mapping role UUID to RoleConstraint
            team_size: Size of each team
            balance_limit: Maximum quality score threshold
            settings: QualitySettings (uses defaults if None)
            max_results: Maximum number of results to return
            
        Returns:
            BalanceResponse with results
        """
        if settings is None:
            settings = QualitySettings()
        
        engine = BalanceEngine(settings, role_ids, role_constraints)
        return engine.find_balances(players, team_size, balance_limit, max_results)
    
    # Legacy static method for backwards compatibility
    @staticmethod
    def find_balances_static(
        players: list[PlayerInfo],
        role_ids: list[uuid.UUID],
        role_constraints: dict[uuid.UUID, RoleConstraint],
        team_size: int,
        balance_limit: float,
        settings: QualitySettings | None = None,
    ) -> list[BalanceResultData]:
        """
        Legacy static method for backwards compatibility.
        
        Deprecated: Use BalanceEngine instance or quick_find() instead.
        """
        response = BalanceEngine.quick_find(
            players, role_ids, role_constraints,
            team_size, balance_limit, settings
        )
        return response.balances


# Thread pool for async operations
_executor = ThreadPoolExecutor(max_workers=4)


async def async_find_balances(
    players: list[PlayerInfo],
    role_ids: list[uuid.UUID],
    role_constraints: dict[uuid.UUID, RoleConstraint],
    team_size: int,
    balance_limit: float,
    settings: QualitySettings | None = None,
    max_results: int = 1000,
) -> BalanceResponse:
    """
    Asynchronous version of find_balances using asyncio.
    
    This function runs the C++ engine in a separate thread
    to avoid blocking the event loop.
    
    Args:
        players: List of PlayerInfo objects with Python UUID member_id and role_ids
        role_ids: List of all available role UUIDs
        role_constraints: Dict mapping role UUID to RoleConstraint
        team_size: Size of each team
        balance_limit: Maximum quality score threshold
        settings: QualitySettings (uses defaults if None)
        max_results: Maximum number of results to return
        
    Returns:
        BalanceResponse with results
    """
    if settings is None:
        settings = QualitySettings()
    
    # Create mappers
    role_mapper = UUIDMapper()
    member_mapper = UUIDMapper()
    
    cpp_role_ids = role_mapper.register_all(role_ids)
    
    # Register constraint role IDs
    for role_uuid in role_constraints.keys():
        role_mapper.register(role_uuid)
    
    # Convert settings
    cpp_settings = _core.QualitySettings()
    cpp_settings.alpha = settings.alpha
    cpp_settings.beta = settings.beta
    cpp_settings.gamma = settings.gamma
    cpp_settings.xi = settings.xi
    cpp_settings.p = settings.p
    cpp_settings.q = settings.q
    cpp_settings.g = settings.g
    cpp_settings.max_priority = settings.max_priority
    
    if settings.role_weights:
        cpp_settings.role_weights = {
            role_mapper.to_int(uid): weight
            for uid, weight in settings.role_weights.items()
        }
    
    # Convert players (register member_ids and convert)
    cpp_players = []
    for player in players:
        member_int_id = member_mapper.register(player.member_id)
        
        cpp_roles = []
        for role_info in player.roles:
            role_int_id = role_mapper.to_int(role_info.role_id)
            cpp_role = _core.RoleRating(
                role_int_id,
                role_info.rating,
                role_info.priority
            )
            cpp_roles.append(cpp_role)
        
        cpp_player = _core.PlayerInfo(
            member_int_id,
            cpp_roles
        )
        cpp_players.append(cpp_player)
    
    # Convert constraints
    cpp_constraints = {
        role_mapper.to_int(role_uuid): _core.RoleConstraint(
            constraint.min_in_team,
            constraint.max_in_team
        )
        for role_uuid, constraint in role_constraints.items()
    }
    
    # Run C++ engine in thread pool
    loop = asyncio.get_running_loop()
    
    cpp_response = await loop.run_in_executor(
        _executor,
        lambda: _core.find_balances(
            cpp_players,
            cpp_role_ids,
            cpp_constraints,
            team_size,
            balance_limit,
            cpp_settings,
            max_results
        )
    )
    
    # Convert results back to Python format
    python_results: list[BalanceResultData] = []
    
    for cpp_result in cpp_response.balances:
        quality = QualityMetrics(
            fairness=cpp_result.quality.fairness,
            role_fairness=cpp_result.quality.role_fairness,
            role_points=cpp_result.quality.role_points,
            uniformity=cpp_result.quality.uniformity,
        )
        
        teams: list[TeamResult] = []
        for cpp_team in cpp_result.teams:
            python_players: list[TeamPlayerResult] = []
            
            for cpp_player in cpp_team.players:
                # Convert both member_id and role_id back to UUID
                member_uuid = member_mapper.to_uuid(cpp_player.member_id)
                role_uuid = role_mapper.to_uuid(cpp_player.role_id)
                
                python_player = TeamPlayerResult(
                    member_id=member_uuid,
                    game_role_id=role_uuid,
                    rating=cpp_player.rating
                )
                python_players.append(python_player)
            
            team = TeamResult(
                team_id=cpp_team.name,
                players=python_players
            )
            teams.append(team)
        
        result = BalanceResultData(
            quality=quality,
            teams=teams,
            team_mask=cpp_result.team_mask,
            role_mask1=cpp_result.role_mask1,
            role_mask2=cpp_result.role_mask2,
        )
        python_results.append(result)
    
    return BalanceResponse(
        result_code=cpp_response.result_code,
        status=cpp_response.status,
        balances=python_results
    )


async def async_find_balances_with_engine(
    engine: BalanceEngine,
    players: list[PlayerInfo],
    team_size: int,
    balance_limit: float,
    max_results: int = 1000,
) -> BalanceResponse:
    """
    Async version using existing BalanceEngine instance.
    
    More efficient for repeated calls with same settings.
    
    Args:
        engine: Pre-configured BalanceEngine instance
        players: List of PlayerInfo objects with UUID member_id
        team_size: Size of each team
        balance_limit: Maximum quality score threshold
        max_results: Maximum number of results to return
        
    Returns:
        BalanceResponse with results
    """
    loop = asyncio.get_running_loop()
    
    return await loop.run_in_executor(
        _executor,
        lambda: engine.find_balances(players, team_size, balance_limit, max_results)
    )


__all__ = [
    # Main classes
    "BalanceEngine",
    "UUIDMapper",
    
    # Async functions
    "async_find_balances",
    "async_find_balances_with_engine",
    
    # Re-export models for convenience
    "PlayerRoleInfo",
    "PlayerInfo", 
    "RoleConstraint",
    "TeamPlayerResult",
    "TeamResult",
    "QualityMetrics",
    "BalanceResultData",
    "BalanceResponse",
    "QualitySettings",
]