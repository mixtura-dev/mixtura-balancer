# _core.pyi
"""
Balance Engine - optimized team balancing module.

This module provides fast C++ implementation for team balancing
with role constraints and quality metrics.
"""

from typing import Dict, List, Tuple, Iterator, Optional, overload

class RoleRating:
    """Player's rating and priority for a specific role."""
    
    role_id: int
    rating: int
    priority: int
    
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, role_id: int, rating: int, priority: int) -> None: ...
    
    def __repr__(self) -> str: ...


class PlayerInfo:
    """Information about a player including their roles and ratings."""
    
    member_id: int
    roles: List[RoleRating]
    
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(
        self, 
        member_id: int, 
        roles: List[RoleRating]
    ) -> None: ...
    
    def can_play_role(self, role_id: int) -> bool:
        """Check if player can play the specified role."""
        ...
    
    def get_rating_for_role(self, role_id: int) -> int:
        """Get player's rating for the specified role."""
        ...
    
    def get_priority_for_role(self, role_id: int) -> int:
        """Get player's priority for the specified role (higher = more preferred)."""
        ...
    
    def __repr__(self) -> str: ...


class RoleConstraint:
    """Constraints for role distribution in a team."""
    
    min_in_team: int
    max_in_team: int
    
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, min_in_team: int, max_in_team: int) -> None: ...
    
    def __repr__(self) -> str: ...


class QualitySettings:
    """Settings for balance quality calculations."""
    
    alpha: float
    """Weight for fairness metric."""
    
    beta: float
    """Weight for role fairness metric."""
    
    gamma: float
    """Weight for role priority metric."""

    xi: float
    """Weight for role priority imbalance penalty."""
    
    p: float
    """Power for fairness norm calculation."""
    
    q: float
    """Power for uniformity norm calculation."""
    
    g: float
    """Power for role fairness norm calculation."""
    
    max_priority: int
    """Maximum role priority value."""
    
    role_weights: Dict[int, float]
    """Weight multipliers for each role (role_id -> weight)."""
    
    def __init__(self) -> None: ...
    def __repr__(self) -> str: ...


class QualityMetrics:
    """Quality metrics for a balance result."""
    
    fairness: float
    """Team skill fairness score."""
    
    role_fairness: float
    """Role-based fairness score."""
    
    role_points: float
    """Role priority satisfaction score."""
    
    uniformity: float
    """Skill distribution uniformity score."""
    
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(
        self, 
        fairness: float, 
        role_fairness: float, 
        role_points: float, 
        uniformity: float
    ) -> None: ...
    
    def total(self) -> float:
        """Calculate total quality score (lower is better)."""
        ...
    
    @property
    def total_score(self) -> float:
        """Alias for total() for backwards compatibility."""
        ...
    
    def __repr__(self) -> str: ...


class TeamPlayerResult:
    """Result of player assignment to a team and role."""
    
    member_id: int
    role_id: int
    rating: int
    
    game_role_id: int
    """Alias for role_id (backwards compatibility)."""
    
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, member_id: int, role_id: int, rating: int) -> None: ...
    
    def __repr__(self) -> str: ...


class TeamResult:
    """Result containing team composition."""
    
    name: str
    players: List[TeamPlayerResult]
    
    team_id: str
    """Alias for name (backwards compatibility)."""
    
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, name: str, players: List[TeamPlayerResult]) -> None: ...
    
    def __repr__(self) -> str: ...


class BalanceResultData:
    """Single balance result with quality metrics and team compositions."""
    
    quality: QualityMetrics
    teams: List[TeamResult]
    team_mask: str
    role_mask1: str
    role_mask2: str
    
    def __init__(self) -> None: ...
    
    def to_dict(self) -> Dict[str, object]:
        """Convert to dictionary format."""
        ...
    
    def __repr__(self) -> str: ...


class BalanceResponse:
    """Response from balance search containing all valid balances."""
    
    result_code: int
    status: str
    balances: List[BalanceResultData]
    
    @property
    def ok(self) -> bool:
        """Check if response is successful."""
        ...
    
    def __init__(self) -> None: ...
    
    def to_dict(self) -> Dict[str, object]:
        """
        Convert to dictionary format matching Python version output.
        
        Returns:
            Dict with keys: 'result', 'status', 'active'
        """
        ...
    
    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> BalanceResultData: ...
    def __iter__(self) -> Iterator[BalanceResultData]: ...
    def __bool__(self) -> bool: ...
    def __repr__(self) -> str: ...


class BalanceEngine:
    """
    Main engine for finding team balances.
    
    Create an instance with settings and constraints, then call
    find_balances() to search for valid team compositions.
    """
    
    def __init__(
        self,
        settings: QualitySettings,
        role_ids: List[int],
        role_constraints: Dict[int, RoleConstraint]
    ) -> None:
        """
        Create a new BalanceEngine instance.
        
        Args:
            settings: QualitySettings for balance calculations
            role_ids: List of role IDs (e.g., [0, 1, 2] for Tank, DPS, Healer)
            role_constraints: Dict mapping role_id to RoleConstraint
        """
        ...
    
    def find_balances(
        self,
        players: List[PlayerInfo],
        team_size: int,
        balance_limit: float,
        max_results: int = 1000
    ) -> BalanceResponse:
        """
        Find all valid team balances.
        
        Args:
            players: List of PlayerInfo objects (must be exactly team_size * 2)
            team_size: Number of players per team
            balance_limit: Maximum allowed balance score (lower = stricter)
            max_results: Maximum number of results to return (default: 1000)
        
        Returns:
            BalanceResponse with sorted balance results (best first)
        """
        ...
    
    def __repr__(self) -> str: ...


# ==================== Module-level functions ====================

def find_balances(
    players: List[PlayerInfo],
    role_ids: List[int],
    role_constraints: Dict[int, RoleConstraint],
    team_size: int,
    balance_limit: float,
    settings: QualitySettings = ...,
    max_results: int = 1000
) -> BalanceResponse:
    """
    Find team balances (convenience function).
    
    Creates a temporary BalanceEngine and finds balances.
    For repeated calls with same settings, prefer creating 
    a BalanceEngine instance directly.
    
    GIL is released during computation for better concurrency.
    
    Args:
        players: List of PlayerInfo objects
        role_ids: List of role IDs
        role_constraints: Dict mapping role_id to RoleConstraint
        team_size: Number of players per team
        balance_limit: Maximum allowed balance score
        settings: QualitySettings (optional, uses defaults if not provided)
        max_results: Maximum number of results to return
    
    Returns:
        BalanceResponse with sorted balance results
    """
    ...


def async_find_balances(
    players: List[PlayerInfo],
    role_ids: List[int],
    role_constraints: Dict[int, RoleConstraint],
    team_size: int,
    balance_limit: float,
    settings: QualitySettings = ...,
    max_results: int = 1000
) -> BalanceResponse:
    """
    Alias for find_balances with GIL release (for backwards compatibility).
    
    Identical to find_balances() - both release the GIL during computation.
    """
    ...


def create_player(
    member_id: int,
    roles: List[Tuple[int, int, int]]
) -> PlayerInfo:
    """
    Create a PlayerInfo from tuple data.
    
    Args:
        member_id: Player's unique ID
        roles: List of (role_id, rating, priority) tuples
    
    Returns:
        PlayerInfo instance
    
    Example:
        >>> player = create_player(1, [(0, 2500, 3), (1, 2400, 2)], False)
        >>> player.member_id
        1
        >>> player.can_play_role(0)
        True
    """
    ...


def create_settings(
    alpha: float = 1.0,
    beta: float = 1.0,
    gamma: float = 1.0,
    p: float = 1.0,
    q: float = 1.0,
    g: float = 1.0,
    max_priority: int = 3,
    role_weights: Dict[int, float] = ...
) -> QualitySettings:
    """
    Create QualitySettings with all parameters.
    
    Args:
        alpha: Weight for fairness metric (default: 1.0)
        beta: Weight for role fairness metric (default: 1.0)
        gamma: Weight for role priority metric (default: 1.0)
        p: Power for fairness norm calculation (default: 1.0)
        q: Power for uniformity norm calculation (default: 1.0)
        g: Power for role fairness norm calculation (default: 1.0)
        max_priority: Maximum role priority value (default: 3)
        role_weights: Weight multipliers for each role (default: empty)
    
    Returns:
        QualitySettings instance
    
    Example:
        >>> settings = create_settings(
        ...     alpha=1.0,
        ...     beta=0.5,
        ...     gamma=0.3,
        ...     role_weights={0: 1.2, 1: 1.0, 2: 1.1}
        ... )
    """
    ...


# ==================== Type aliases for convenience ====================

# Common type patterns
PlayerRoles = List[Tuple[int, int, int]]
"""Type alias: List of (role_id, rating, priority) tuples."""

RoleConstraints = Dict[int, RoleConstraint]
"""Type alias: Dict mapping role_id to RoleConstraint."""

RoleWeights = Dict[int, float]
"""Type alias: Dict mapping role_id to weight multiplier."""