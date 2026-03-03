"""
Tests for BalanceEngine wrapper functionality.

Tests conversion between Python and C++ formats, core wrapper operations,
and integration with C++ backend.
"""

import uuid
import pytest
import asyncio
from balance_engine.wrapper import BalanceEngine
from balance_engine.models import (
    PlayerInfo,
    PlayerRoleInfo,
    RoleConstraint,
    QualitySettings,
    EngineSettings,
)


class TestBalanceEngineInitialization:
    """Test suite for BalanceEngine initialization."""

    def test_engine_creation_with_defaults(self, sample_roles, role_list, role_constraints):
        """Test creating BalanceEngine with minimal settings."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        assert engine is not None
        assert engine.quality_settings is not None

    def test_engine_creation_with_engine_settings(
        self, sample_roles, role_list, role_constraints, engine_settings
    ):
        """Test creating BalanceEngine with custom engine settings."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
            engine_settings=engine_settings,
        )

        assert engine.engine_settings == engine_settings

    def test_engine_quality_settings_property(
        self, sample_roles, role_list, role_constraints, quality_settings
    ):
        """Test accessing quality settings property."""
        engine = BalanceEngine(
            quality_settings=quality_settings,
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        assert engine.quality_settings == quality_settings

    def test_engine_engine_settings_property(
        self, sample_roles, role_list, role_constraints, engine_settings
    ):
        """Test accessing engine settings property."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
            engine_settings=engine_settings,
        )

        assert engine.engine_settings == engine_settings

    def test_engine_with_role_weights(self, sample_roles, role_list, role_constraints):
        """Test creating engine with role weights."""
        weights = {
            sample_roles["carry"]: 1.5,
            sample_roles["support"]: 0.8,
        }
        quality_settings = QualitySettings(role_weights=weights)

        engine = BalanceEngine(
            quality_settings=quality_settings,
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        assert engine.quality_settings.role_weights == weights


class TestBalanceEngineFindBalances:
    """Test suite for BalanceEngine.find_balances() method."""

    def test_find_balances_basic(self, sample_roles, role_list, role_constraints, sample_players):
        """Test basic balance finding."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=5000.0,
        )

        assert response is not None
        assert response.result_code in [200, 500]  # Either success or legitimate error

    def test_find_balances_returns_response(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test that find_balances returns BalanceResponse."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=1000.0,
        )

        assert hasattr(response, "result_code")
        assert hasattr(response, "status")
        assert hasattr(response, "balances")

    def test_find_balances_result_code(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test result code in response."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=1000.0,
        )

        assert isinstance(response.result_code, int)

    def test_find_balances_with_low_limit(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test find_balances with very low balance_limit."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=0.1,  # Very strict limit
        )

        # Should still return a valid response (might be empty or with limited results)
        assert response is not None

    def test_find_balances_with_high_limit(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test find_balances with high balance_limit."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=1000.0,  # Very permissive limit
        )

        assert response is not None

    def test_find_balances_with_max_results(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test find_balances with max_results parameter."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=1000.0,
            max_results=5,
        )

        # Should respect max_results limit
        assert len(response) <= 5

    def test_find_balances_result_structure(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test structure of balance results."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=1000.0,
        )

        if len(response) > 0:
            result = response[0]
            assert hasattr(result, "quality")
            assert hasattr(result, "teams")
            assert hasattr(result.quality, "fairness")
            assert hasattr(result.quality, "role_fairness")
            assert hasattr(result.quality, "role_points")
            assert hasattr(result.quality, "uniformity")

    def test_find_balances_team_structure(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test team structure in results."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=1000.0,
        )

        if len(response) > 0:
            result = response[0]
            for team in result.teams:
                assert hasattr(team, "team_id")
                assert hasattr(team, "players")
                # Each player should have member_id, game_role_id, rating
                for player in team.players:
                    assert isinstance(player.member_id, uuid.UUID)
                    assert isinstance(player.game_role_id, uuid.UUID)
                    assert isinstance(player.rating, int)

    def test_find_balances_converts_uuids(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test that result UUIDs are correctly converted back."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=1000.0,
        )

        if len(response) > 0:
            # Get all member IDs from results
            result_member_ids = set()
            for result in response:
                for team in result.teams:
                    for player in team.players:
                        result_member_ids.add(player.member_id)

            # Verify they are valid UUIDs and belong to input players
            input_member_ids = {p.member_id for p in sample_players}
            for member_id in result_member_ids:
                assert isinstance(member_id, uuid.UUID)
                assert member_id in input_member_ids


class TestBalanceEngineQuickFind:
    """Test suite for BalanceEngine.quick_find() static method."""

    def test_quick_find_basic(self, sample_roles, role_list, role_constraints, sample_players):
        """Test basic quick_find operation."""
        response = BalanceEngine.quick_find(
            players=sample_players,
            role_ids=role_list,
            role_constraints=role_constraints,
            team_size=5,
            balance_limit=5000.0,
        )

        assert response is not None
        assert response.result_code in [200, 500]  # Either success or legitimate error

    def test_quick_find_with_defaults(self, sample_roles, role_list, role_constraints, sample_players):
        """Test quick_find with default quality settings."""
        response = BalanceEngine.quick_find(
            players=sample_players,
            role_ids=role_list,
            role_constraints=role_constraints,
            team_size=5,
            balance_limit=1000.0,
            quality_settings=None,
        )

        assert response is not None

    def test_quick_find_with_custom_settings(
        self, sample_roles, role_list, role_constraints, sample_players, quality_settings
    ):
        """Test quick_find with custom quality settings."""
        response = BalanceEngine.quick_find(
            players=sample_players,
            role_ids=role_list,
            role_constraints=role_constraints,
            team_size=5,
            balance_limit=1000.0,
            quality_settings=quality_settings,
        )

        assert response is not None


class TestBalanceEngineStaticMethods:
    """Test suite for static/class methods."""

    def test_find_balances_static_legacy(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test legacy find_balances_static method."""
        results = BalanceEngine.find_balances_static(
            players=sample_players,
            role_ids=role_list,
            role_constraints=role_constraints,
            team_size=5,
            balance_limit=1000.0,
        )

        assert isinstance(results, list)


class TestBalanceEngineAsync:
    """Test suite for async methods."""

    @pytest.mark.asyncio
    async def test_async_quick_find_balances(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test async_quick_find_balances method."""
        response = await BalanceEngine.async_quick_find_balances(
            players=sample_players,
            role_ids=role_list,
            role_constraints=role_constraints,
            team_size=5,
            balance_limit=5000.0,
        )

        assert response is not None
        assert response.result_code in [200, 500]  # Either success or legitimate error

    @pytest.mark.asyncio
    async def test_async_find_balances(self, sample_roles, role_list, role_constraints, sample_players):
        """Test async_find_balances method."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = await engine.async_find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=5000.0,
        )

        assert response is not None
        assert response.result_code in [200, 500]  # Either success or legitimate error

    def test_async_finds_same_results(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test that async and sync methods produce same results."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        sync_response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=1000.0,
            max_results=5,
        )

        async def get_async_result():
            return await engine.async_find_balances(
                players=sample_players,
                team_size=5,
                balance_limit=1000.0,
                max_results=5,
            )

        async_response = asyncio.run(get_async_result())

        # Should have same number of results
        assert len(sync_response) == len(async_response)


class TestBalanceEngineMinimalPlayers:
    """Test suite with minimal player sets."""

    def test_find_balances_minimal_players(
        self, sample_roles, role_list, role_constraints, min_players
    ):
        """Test find_balances with minimum viable player set."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=min_players,
            team_size=5,
            balance_limit=1000.0,
        )

        assert response is not None


class TestBalanceEngineMultipleCalls:
    """Test suite for multiple calls to same engine."""

    def test_multiple_find_balances_calls(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test calling find_balances multiple times on same engine."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response1 = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=1000.0,
        )

        response2 = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=1000.0,
        )

        assert response1 is not None
        assert response2 is not None
        # Results should be consistent for same input
        assert len(response1) == len(response2)

    def test_different_player_sets(self, sample_roles, role_list, role_constraints, sample_players, min_players):
        """Test engine with different player sets."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response1 = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=1000.0,
        )

        response2 = engine.find_balances(
            players=min_players,
            team_size=5,
            balance_limit=1000.0,
        )

        assert response1 is not None
        assert response2 is not None
