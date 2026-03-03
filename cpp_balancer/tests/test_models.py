"""
Tests for balance_engine models and data classes.

Tests validation and functionality of PlayerInfo, RoleConstraint, QualitySettings, etc.
"""

import uuid
import pytest
from balance_engine.models import (
    PlayerRoleInfo,
    PlayerInfo,
    RoleConstraint,
    QualitySettings,
    EngineSettings,
    QualityMetrics,
    TeamPlayerResult,
    TeamResult,
    BalanceResultData,
    BalanceResponse,
)


class TestPlayerRoleInfo:
    """Test suite for PlayerRoleInfo model."""

    def test_player_role_info_creation(self):
        """Test creating a PlayerRoleInfo instance."""
        role_id = uuid.uuid4()
        role_info = PlayerRoleInfo(role_id=role_id, rating=2000, priority=1)

        assert role_info.role_id == role_id
        assert role_info.rating == 2000
        assert role_info.priority == 1

    def test_player_role_info_with_different_ratings(self):
        """Test PlayerRoleInfo with various rating values."""
        role_id = uuid.uuid4()

        for rating in [500, 1000, 2000, 3000]:
            role_info = PlayerRoleInfo(role_id=role_id, rating=rating, priority=1)
            assert role_info.rating == rating

    def test_player_role_info_with_different_priorities(self):
        """Test PlayerRoleInfo with various priority values."""
        role_id = uuid.uuid4()

        for priority in [1, 2, 3]:
            role_info = PlayerRoleInfo(role_id=role_id, rating=2000, priority=priority)
            assert role_info.priority == priority

    def test_player_role_info_zero_rating(self):
        """Test PlayerRoleInfo with zero rating."""
        role_id = uuid.uuid4()
        role_info = PlayerRoleInfo(role_id=role_id, rating=0, priority=1)

        assert role_info.rating == 0

    def test_player_role_info_high_rating(self):
        """Test PlayerRoleInfo with high rating."""
        role_id = uuid.uuid4()
        role_info = PlayerRoleInfo(role_id=role_id, rating=10000, priority=1)

        assert role_info.rating == 10000


class TestPlayerInfo:
    """Test suite for PlayerInfo model."""

    def test_player_info_creation(self):
        """Test creating a PlayerInfo instance."""
        member_id = uuid.uuid4()
        role_id = uuid.uuid4()
        role_info = PlayerRoleInfo(role_id=role_id, rating=2000, priority=1)

        player = PlayerInfo(member_id=member_id, roles=[role_info])

        assert player.member_id == member_id
        assert len(player.roles) == 1
        assert player.roles[0] == role_info

    def test_player_info_single_role(self):
        """Test PlayerInfo with single role."""
        member_id = uuid.uuid4()
        role_id = uuid.uuid4()
        role_info = PlayerRoleInfo(role_id=role_id, rating=2000, priority=1)

        player = PlayerInfo(member_id=member_id, roles=[role_info])

        assert len(player.roles) == 1

    def test_player_info_multiple_roles(self):
        """Test PlayerInfo with multiple roles."""
        member_id = uuid.uuid4()
        role1 = uuid.uuid4()
        role2 = uuid.uuid4()
        roles = [
            PlayerRoleInfo(role_id=role1, rating=2000, priority=1),
            PlayerRoleInfo(role_id=role2, rating=1900, priority=2),
        ]

        player = PlayerInfo(member_id=member_id, roles=roles)

        assert len(player.roles) == 2

    def test_player_info_flex_flag_default(self):
        """Test that is_flex defaults to False."""
        member_id = uuid.uuid4()
        role_id = uuid.uuid4()
        role_info = PlayerRoleInfo(role_id=role_id, rating=2000, priority=1)

        player = PlayerInfo(member_id=member_id, roles=[role_info])

        assert player.is_flex is False

    def test_player_info_flex_flag_true(self):
        """Test PlayerInfo with is_flex=True."""
        member_id = uuid.uuid4()
        role_id = uuid.uuid4()
        role_info = PlayerRoleInfo(role_id=role_id, rating=2000, priority=1)

        player = PlayerInfo(member_id=member_id, roles=[role_info], is_flex=True)

        assert player.is_flex is True


class TestRoleConstraint:
    """Test suite for RoleConstraint model."""

    def test_role_constraint_creation(self):
        """Test creating a RoleConstraint."""
        constraint = RoleConstraint(min_in_team=1, max_in_team=2)

        assert constraint.min_in_team == 1
        assert constraint.max_in_team == 2

    def test_role_constraint_zero_min(self):
        """Test RoleConstraint with min=0."""
        constraint = RoleConstraint(min_in_team=0, max_in_team=2)

        assert constraint.min_in_team == 0

    def test_role_constraint_equal_min_max(self):
        """Test RoleConstraint where min equals max."""
        constraint = RoleConstraint(min_in_team=2, max_in_team=2)

        assert constraint.min_in_team == constraint.max_in_team


class TestQualitySettings:
    """Test suite for QualitySettings model."""

    def test_quality_settings_default_creation(self):
        """Test creating QualitySettings with defaults."""
        settings = QualitySettings()

        assert settings.fairness_coef == 1.0
        assert settings.role_fairness_coef == 1.0
        assert settings.role_priority_coef == 1.0
        assert settings.imbalance_role_priority_coef == 0.2

    def test_quality_settings_custom_values(self):
        """Test creating QualitySettings with custom values."""
        settings = QualitySettings(
            fairness_coef=2.0,
            role_fairness_coef=1.5,
            role_priority_coef=3.0,
        )

        assert settings.fairness_coef == 2.0
        assert settings.role_fairness_coef == 1.5
        assert settings.role_priority_coef == 3.0

    def test_quality_settings_powers(self):
        """Test QualitySettings power parameters."""
        settings = QualitySettings(
            fairness_power=2.0,
            uniformity_power=1.5,
            role_fairness_power=2.5,
        )

        assert settings.fairness_power == 2.0
        assert settings.uniformity_power == 1.5
        assert settings.role_fairness_power == 2.5

    def test_quality_settings_max_priority(self):
        """Test QualitySettings max_priority."""
        settings = QualitySettings(max_priority=5)

        assert settings.max_priority == 5

    def test_quality_settings_role_weights(self):
        """Test QualitySettings with role weights."""
        role_id = uuid.uuid4()
        role_weights = {role_id: 1.5}

        settings = QualitySettings(role_weights=role_weights)

        assert settings.role_weights == role_weights

    def test_quality_settings_role_weights_multiple(self):
        """Test QualitySettings with multiple role weights."""
        role1 = uuid.uuid4()
        role2 = uuid.uuid4()
        role_weights = {role1: 1.5, role2: 2.0}

        settings = QualitySettings(role_weights=role_weights)

        assert settings.role_weights is not None
        assert len(settings.role_weights) == 2
        assert settings.role_weights[role1] == 1.5
        assert settings.role_weights[role2] == 2.0

    def test_quality_settings_role_weights_none(self):
        """Test QualitySettings with role_weights=None."""
        settings = QualitySettings(role_weights=None)

        assert settings.role_weights is None


class TestEngineSettings:
    """Test suite for EngineSettings model."""

    def test_engine_settings_default_creation(self):
        """Test creating EngineSettings with defaults."""
        settings = EngineSettings()

        assert settings.num_workers == 0
        assert settings.fallback_workers == 4
        assert settings.worker_result_buffer == 1000
        assert settings.max_players == 32

    def test_engine_settings_custom_workers(self):
        """Test EngineSettings with custom worker configuration."""
        settings = EngineSettings(
            num_workers=8,
            fallback_workers=6,
        )

        assert settings.num_workers == 8
        assert settings.fallback_workers == 6

    def test_engine_settings_memory_tuning(self):
        """Test EngineSettings with memory tuning parameters."""
        settings = EngineSettings(
            worker_result_buffer=2000,
            mask_reserve_limit=25,
        )

        assert settings.worker_result_buffer == 2000
        assert settings.mask_reserve_limit == 25

    def test_engine_settings_max_players(self):
        """Test EngineSettings max_players limit."""
        settings = EngineSettings(max_players=16)

        assert settings.max_players == 16


class TestQualityMetrics:
    """Test suite for QualityMetrics model."""

    def test_quality_metrics_creation(self):
        """Test creating QualityMetrics."""
        metrics = QualityMetrics(
            fairness=1.0,
            role_fairness=2.0,
            role_points=3.0,
            uniformity=4.0,
        )

        assert metrics.fairness == 1.0
        assert metrics.role_fairness == 2.0
        assert metrics.role_points == 3.0
        assert metrics.uniformity == 4.0

    def test_quality_metrics_total(self):
        """Test QualityMetrics.total property."""
        metrics = QualityMetrics(
            fairness=1.0,
            role_fairness=2.0,
            role_points=3.0,
            uniformity=4.0,
        )

        assert metrics.total == 10.0

    def test_quality_metrics_evaluation_alias(self):
        """Test that evaluation is an alias for total."""
        metrics = QualityMetrics(
            fairness=1.0,
            role_fairness=2.0,
            role_points=3.0,
            uniformity=4.0,
        )

        assert metrics.evaluation == metrics.total

    def test_quality_metrics_zero_values(self):
        """Test QualityMetrics with zero values."""
        metrics = QualityMetrics(
            fairness=0.0,
            role_fairness=0.0,
            role_points=0.0,
            uniformity=0.0,
        )

        assert metrics.total == 0.0

    def test_quality_metrics_high_values(self):
        """Test QualityMetrics with high values."""
        metrics = QualityMetrics(
            fairness=1000.0,
            role_fairness=2000.0,
            role_points=3000.0,
            uniformity=4000.0,
        )

        assert metrics.total == 10000.0


class TestTeamPlayerResult:
    """Test suite for TeamPlayerResult model."""

    def test_team_player_result_creation(self):
        """Test creating TeamPlayerResult."""
        member_id = uuid.uuid4()
        role_id = uuid.uuid4()

        result = TeamPlayerResult(
            member_id=member_id,
            game_role_id=role_id,
            rating=2000,
        )

        assert result.member_id == member_id
        assert result.game_role_id == role_id
        assert result.rating == 2000


class TestTeamResult:
    """Test suite for TeamResult model."""

    def test_team_result_creation(self):
        """Test creating TeamResult."""
        member_id = uuid.uuid4()
        role_id = uuid.uuid4()

        player = TeamPlayerResult(
            member_id=member_id,
            game_role_id=role_id,
            rating=2000,
        )

        team = TeamResult(team_id="Team1", players=[player])

        assert team.team_id == "Team1"
        assert len(team.players) == 1

    def test_team_result_multiple_players(self):
        """Test TeamResult with multiple players."""
        players = [
            TeamPlayerResult(
                member_id=uuid.uuid4(),
                game_role_id=uuid.uuid4(),
                rating=2000,
            )
            for _ in range(5)
        ]

        team = TeamResult(team_id="Team1", players=players)

        assert len(team.players) == 5


class TestBalanceResultData:
    """Test suite for BalanceResultData model."""

    def test_balance_result_data_creation(self):
        """Test creating BalanceResultData."""
        metrics = QualityMetrics(1.0, 2.0, 3.0, 4.0)
        team = TeamResult(team_id="Team1", players=[])

        result = BalanceResultData(quality=metrics, teams=[team])

        assert result.quality == metrics
        assert len(result.teams) == 1

    def test_balance_result_data_to_dict(self):
        """Test BalanceResultData.to_dict() method."""
        metrics = QualityMetrics(
            fairness=1.234,
            role_fairness=2.345,
            role_points=3.456,
            uniformity=4.567,
        )
        team = TeamResult(team_id="Team1", players=[])

        result = BalanceResultData(quality=metrics, teams=[team])
        result_dict = result.to_dict()

        assert "dpFairness" in result_dict
        assert "rgRolesFairness" in result_dict
        assert "teamRolePriority" in result_dict
        assert "vqUniformity" in result_dict
        assert "result" in result_dict


class TestBalanceResponse:
    """Test suite for BalanceResponse model."""

    def test_balance_response_successful(self):
        """Test creating successful BalanceResponse."""
        metrics = QualityMetrics(1.0, 2.0, 3.0, 4.0)
        team = TeamResult(team_id="Team1", players=[])
        balance = BalanceResultData(quality=metrics, teams=[team])

        response = BalanceResponse(
            result_code=200,
            status="OK",
            balances=[balance],
        )

        assert response.result_code == 200
        assert response.status == "OK"
        assert len(response.balances) == 1

    def test_balance_response_ok_property(self):
        """Test BalanceResponse.ok property."""
        response_ok = BalanceResponse(result_code=200, status="OK")
        response_error = BalanceResponse(result_code=400, status="ERROR")

        assert response_ok.ok is True
        assert response_error.ok is False

    def test_balance_response_bool(self):
        """Test BalanceResponse as boolean."""
        metrics = QualityMetrics(1.0, 2.0, 3.0, 4.0)
        team = TeamResult(team_id="Team1", players=[])
        balance = BalanceResultData(quality=metrics, teams=[team])

        response_with_results = BalanceResponse(
            result_code=200,
            status="OK",
            balances=[balance],
        )
        response_without_results = BalanceResponse(
            result_code=200,
            status="OK",
            balances=[],
        )

        assert bool(response_with_results) is True
        assert bool(response_without_results) is False

    def test_balance_response_len(self):
        """Test BalanceResponse.__len__()."""
        metrics = QualityMetrics(1.0, 2.0, 3.0, 4.0)
        balances = [
            BalanceResultData(quality=metrics, teams=[TeamResult("T1", [])]),
            BalanceResultData(quality=metrics, teams=[TeamResult("T2", [])]),
        ]

        response = BalanceResponse(
            result_code=200,
            status="OK",
            balances=balances,
        )

        assert len(response) == 2

    def test_balance_response_iteration(self):
        """Test iterating over BalanceResponse."""
        metrics = QualityMetrics(1.0, 2.0, 3.0, 4.0)
        balances = [
            BalanceResultData(quality=metrics, teams=[TeamResult("T1", [])]),
            BalanceResultData(quality=metrics, teams=[TeamResult("T2", [])]),
        ]

        response = BalanceResponse(
            result_code=200,
            status="OK",
            balances=balances,
        )

        collected = list(response)
        assert len(collected) == 2

    def test_balance_response_indexing(self):
        """Test indexing into BalanceResponse."""
        metrics = QualityMetrics(1.0, 2.0, 3.0, 4.0)
        balance1 = BalanceResultData(quality=metrics, teams=[TeamResult("T1", [])])
        balance2 = BalanceResultData(quality=metrics, teams=[TeamResult("T2", [])])

        response = BalanceResponse(
            result_code=200,
            status="OK",
            balances=[balance1, balance2],
        )

        assert response[0] == balance1
        assert response[1] == balance2

    def test_balance_response_to_dict(self):
        """Test BalanceResponse.to_dict() method."""
        metrics = QualityMetrics(1.5, 2.5, 3.5, 4.5)
        balance = BalanceResultData(quality=metrics, teams=[TeamResult("T1", [])])

        response = BalanceResponse(
            result_code=200,
            status="OK",
            balances=[balance],
        )

        result_dict = response.to_dict()

        assert "result" in result_dict
        assert "status" in result_dict
        assert "active" in result_dict
        assert result_dict["result"] == 200
        assert result_dict["status"] == "OK"
        assert len(result_dict["active"]) == 1
