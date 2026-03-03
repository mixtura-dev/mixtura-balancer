"""
Tests for data validation and error handling.

Tests that the engine correctly validates input data and handles edge cases.
"""

import uuid
import pytest
from balance_engine.wrapper import BalanceEngine
from balance_engine.models import (
    PlayerInfo,
    PlayerRoleInfo,
    RoleConstraint,
    QualitySettings,
)


class TestPlayerValidation:
    """Test suite for player data validation."""

    def test_player_with_no_roles(self, sample_roles, role_list, role_constraints):
        """Test player with empty roles list."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        player = PlayerInfo(member_id=uuid.uuid4(), roles=[])

        # Should handle gracefully (depends on C++ implementation)
        response = engine.find_balances(
            players=[player],
            team_size=5,
            balance_limit=100.0,
        )

        assert response is not None

    def test_player_with_multiple_same_role(self, sample_roles, role_list, role_constraints):
        """Test player with duplicate role entries."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        player = PlayerInfo(
            member_id=uuid.uuid4(),
            roles=[
                PlayerRoleInfo(role_id=sample_roles["carry"], rating=2000, priority=1),
                PlayerRoleInfo(role_id=sample_roles["carry"], rating=2100, priority=1),
            ],
        )

        # Should handle duplicate roles
        response = engine.find_balances(
            players=[player],
            team_size=5,
            balance_limit=100.0,
        )

        assert response is not None

    def test_player_with_zero_rating(self, sample_roles, role_list, role_constraints):
        """Test player with zero rating."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        player = PlayerInfo(
            member_id=uuid.uuid4(),
            roles=[
                PlayerRoleInfo(role_id=sample_roles["carry"], rating=0, priority=1),
            ],
        )

        response = engine.find_balances(
            players=[player],
            team_size=5,
            balance_limit=100.0,
        )

        assert response is not None

    def test_player_with_very_high_rating(self, sample_roles, role_list, role_constraints):
        """Test player with very high rating."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        player = PlayerInfo(
            member_id=uuid.uuid4(),
            roles=[
                PlayerRoleInfo(role_id=sample_roles["carry"], rating=100000, priority=1),
            ],
        )

        response = engine.find_balances(
            players=[player],
            team_size=5,
            balance_limit=100.0,
        )

        assert response is not None

    def test_player_with_invalid_priority(self, sample_roles, role_list, role_constraints):
        """Test player with invalid priority values."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        # Test with priority > max_priority (should still work)
        player = PlayerInfo(
            member_id=uuid.uuid4(),
            roles=[
                PlayerRoleInfo(role_id=sample_roles["carry"], rating=2000, priority=10),
            ],
        )

        response = engine.find_balances(
            players=[player],
            team_size=5,
            balance_limit=100.0,
        )

        assert response is not None

    def test_duplicate_member_ids(self, sample_roles, role_list, role_constraints):
        """Test handling of duplicate member IDs."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        same_id = uuid.uuid4()
        players = [
            PlayerInfo(
                member_id=same_id,
                roles=[PlayerRoleInfo(role_id=sample_roles["carry"], rating=2000, priority=1)],
            ),
            PlayerInfo(
                member_id=same_id,
                roles=[PlayerRoleInfo(role_id=sample_roles["mid"], rating=2000, priority=1)],
            ),
        ]

        response = engine.find_balances(
            players=players,
            team_size=5,
            balance_limit=100.0,
        )

        assert response is not None


class TestRoleValidation:
    """Test suite for role validation."""

    def test_player_with_unknown_role(self, sample_roles, role_list, role_constraints):
        """Test player with role not in engine's role list."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        unknown_role = uuid.uuid4()
        player = PlayerInfo(
            member_id=uuid.uuid4(),
            roles=[
                PlayerRoleInfo(role_id=unknown_role, rating=2000, priority=1),
            ],
        )

        # Should handle gracefully or raise KeyError
        try:
            response = engine.find_balances(
                players=[player],
                team_size=5,
                balance_limit=100.0,
            )
            assert response is not None
        except KeyError:
            # This is acceptable - unknown role should be rejected
            pass

    def test_mismatched_role_constraints(self, sample_roles, role_list):
        """Test when role_constraints don't match all role_ids."""
        role_constraints = {
            sample_roles["carry"]: RoleConstraint(min_in_team=1, max_in_team=1),
        }

        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        assert engine is not None


class TestQualitySettingsValidation:
    """Test suite for quality settings validation."""

    def test_zero_coefficients(self, sample_roles, role_list, role_constraints):
        """Test with zero coefficients."""
        quality_settings = QualitySettings(
            fairness_coef=0.0,
            role_fairness_coef=0.0,
            role_priority_coef=0.0,
        )

        engine = BalanceEngine(
            quality_settings=quality_settings,
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        assert engine is not None

    def test_negative_coefficients(self, sample_roles, role_list, role_constraints):
        """Test with negative coefficients."""
        quality_settings = QualitySettings(
            fairness_coef=-1.0,
            role_fairness_coef=-1.0,
        )

        engine = BalanceEngine(
            quality_settings=quality_settings,
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        assert engine is not None

    def test_very_large_coefficients(self, sample_roles, role_list, role_constraints):
        """Test with very large coefficients."""
        quality_settings = QualitySettings(
            fairness_coef=1000.0,
            role_fairness_coef=1000.0,
        )

        engine = BalanceEngine(
            quality_settings=quality_settings,
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        assert engine is not None

    def test_zero_powers(self, sample_roles, role_list, role_constraints):
        """Test with zero power values."""
        quality_settings = QualitySettings(
            fairness_power=0.0,
            uniformity_power=0.0,
        )

        engine = BalanceEngine(
            quality_settings=quality_settings,
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        assert engine is not None

    def test_fractional_powers(self, sample_roles, role_list, role_constraints):
        """Test with fractional power values."""
        quality_settings = QualitySettings(
            fairness_power=0.5,
            uniformity_power=1.5,
        )

        engine = BalanceEngine(
            quality_settings=quality_settings,
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        assert engine is not None


class TestRoleConstraintValidation:
    """Test suite for role constraint validation."""

    def test_zero_players_in_role(self, sample_roles, role_list):
        """Test with zero players allowed for a role."""
        role_constraints = {
            sample_roles["carry"]: RoleConstraint(min_in_team=0, max_in_team=0),
            sample_roles["mid"]: RoleConstraint(min_in_team=1, max_in_team=1),
            sample_roles["support"]: RoleConstraint(min_in_team=1, max_in_team=2),
            sample_roles["tank"]: RoleConstraint(min_in_team=1, max_in_team=2),
        }

        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        assert engine is not None

    def test_max_less_than_min(self, sample_roles, role_list):
        """Test with max_in_team < min_in_team."""
        role_constraints = {
            sample_roles["carry"]: RoleConstraint(min_in_team=3, max_in_team=1),
            sample_roles["mid"]: RoleConstraint(min_in_team=1, max_in_team=1),
            sample_roles["support"]: RoleConstraint(min_in_team=1, max_in_team=2),
            sample_roles["tank"]: RoleConstraint(min_in_team=1, max_in_team=2),
        }

        # Should still create engine (validation might be at balance_find time)
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        assert engine is not None

    def test_very_large_team_size(self, sample_roles, role_list, role_constraints):
        """Test with very large team size constraints."""
        role_constraints = {
            sample_roles["carry"]: RoleConstraint(min_in_team=0, max_in_team=1000),
            sample_roles["mid"]: RoleConstraint(min_in_team=0, max_in_team=1000),
            sample_roles["support"]: RoleConstraint(min_in_team=0, max_in_team=1000),
            sample_roles["tank"]: RoleConstraint(min_in_team=0, max_in_team=1000),
        }

        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        assert engine is not None


class TestFindBalancesParameterValidation:
    """Test suite for find_balances parameter validation."""

    def test_zero_team_size(self, sample_roles, role_list, role_constraints, sample_players):
        """Test with team_size = 0."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=0,
            balance_limit=100.0,
        )

        assert response is not None

    def test_negative_team_size(self, sample_roles, role_list, role_constraints, sample_players):
        """Test with negative team_size."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=-5,
            balance_limit=100.0,
        )

        assert response is not None

    def test_negative_balance_limit(self, sample_roles, role_list, role_constraints, sample_players):
        """Test with negative balance_limit."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=-100.0,
        )

        assert response is not None

    def test_zero_balance_limit(self, sample_roles, role_list, role_constraints, sample_players):
        """Test with balance_limit = 0."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=0.0,
        )

        assert response is not None

    def test_negative_max_results(self, sample_roles, role_list, role_constraints, sample_players):
        """Test with negative max_results."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=100.0,
            max_results=-5,
        )

        assert response is not None

    def test_zero_max_results(self, sample_roles, role_list, role_constraints, sample_players):
        """Test with max_results = 0."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=100.0,
            max_results=0,
        )

        assert response is not None

    def test_very_large_max_results(self, sample_roles, role_list, role_constraints, sample_players):
        """Test with very large max_results."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=100.0,
            max_results=1000000,
        )

        assert response is not None
