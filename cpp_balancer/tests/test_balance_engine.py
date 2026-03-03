"""
Integration tests for balance engine functionality.

Tests the actual balancing logic, correctness of results,
and edge cases in team distribution.
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


class TestBalanceEngineResultsCorrectness:
    """Test suite for correctness of balance results."""

    def test_results_have_valid_structure(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test that results have correct structure."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=100.0,
        )

        if len(response) > 0:
            for result in response:
                # Check quality metrics
                quality = result.quality
                assert quality.fairness >= 0
                assert quality.role_fairness >= 0
                assert quality.role_points >= 0
                assert quality.uniformity >= 0

    def test_results_quality_metrics_consistency(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test quality metrics are consistent."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=100.0,
        )

        if len(response) > 0:
            for result in response:
                # Total should equal sum of components
                expected_total = (
                    result.quality.fairness
                    + result.quality.role_fairness
                    + result.quality.role_points
                    + result.quality.uniformity
                )
                assert abs(result.quality.total - expected_total) < 0.01

    def test_results_have_two_teams(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test that each result has two teams."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=100.0,
        )

        if len(response) > 0:
            for result in response:
                # Should have 2 teams (team split)
                assert len(result.teams) == 2

    def test_team_size_matches_request(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test that team sizes match the requested size."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=100.0,
        )

        if len(response) > 0:
            for result in response:
                for team in result.teams:
                    assert len(team.players) == 5

    def test_no_player_duplication_in_result(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test that no player appears twice in one result."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=100.0,
        )

        if len(response) > 0:
            for result in response:
                all_members = []
                for team in result.teams:
                    for player in team.players:
                        all_members.append(player.member_id)

                # Check no duplicates within single result
                assert len(all_members) == len(set(all_members))

    def test_players_not_duplicated_across_teams(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test that players are not duplicated across teams in same result."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=100.0,
        )

        if len(response) > 0:
            for result in response:
                team1_members = {p.member_id for team in result.teams[:1] for p in team.players}
                team2_members = {p.member_id for team in result.teams[1:] for p in team.players}

                # No overlap between teams
                assert len(team1_members & team2_members) == 0

    def test_role_constraints_respected(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test that role constraints are respected in results."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=100.0,
        )

        if len(response) > 0:
            for result in response:
                for team in result.teams:
                    # Count roles in this team
                    role_counts = {}
                    for player in team.players:
                        role_id = player.game_role_id
                        role_counts[role_id] = role_counts.get(role_id, 0) + 1

                    # Check against constraints
                    for role_id, count in role_counts.items():
                        if role_id in role_constraints:
                            constraint = role_constraints[role_id]
                            assert count >= constraint.min_in_team
                            assert count <= constraint.max_in_team

    def test_results_are_balanced(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test that results show reasonable balance (fairness metric)."""
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
            # Get best result (first one should be best)
            best = response[0]
            # Total should be reasonably low (good balance)
            assert best.quality.total < 1000.0

    def test_multiple_results_sorted_by_quality(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test that multiple results are sorted by quality (lower is better)."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=1000.0,
            max_results=10,
        )

        if len(response) > 1:
            # Check if sorted by quality (total score)
            qualities = [result.quality.total for result in response]
            # Should be in ascending order (best first)
            # Note: may not be strictly sorted if close scores
            for i in range(len(qualities) - 1):
                assert qualities[i] <= qualities[i + 1] + 0.01  # Allow small tolerance


class TestBalanceEngineRoleDistribution:
    """Test suite for role distribution logic."""

    def test_each_player_has_role(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test that every player in result has a role assigned."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=100.0,
        )

        if len(response) > 0:
            for result in response:
                for team in result.teams:
                    for player in team.players:
                        assert player.game_role_id is not None

    def test_assigned_roles_are_valid(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test that assigned roles are in the engine's role list."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=100.0,
        )

        if len(response) > 0:
            for result in response:
                for team in result.teams:
                    for player in team.players:
                        assert player.game_role_id in role_list

    def test_player_can_play_assigned_role(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test that each player can play their assigned role."""
        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=100.0,
        )

        if len(response) > 0:
            # Create member lookup
            member_lookup = {p.member_id: p for p in sample_players}

            for result in response:
                for team in result.teams:
                    for player in team.players:
                        # Find original player
                        original = member_lookup[player.member_id]
                        # Check if they can play the assigned role
                        can_play = any(
                            r.role_id == player.game_role_id for r in original.roles
                        )
                        assert can_play or len(original.roles) == 0


class TestBalanceEngineEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_all_players_same_rating(self, sample_roles, role_list, role_constraints):
        """Test when all players have same rating."""
        players = [
            PlayerInfo(
                member_id=uuid.uuid4(),
                roles=[
                    PlayerRoleInfo(role_id=sample_roles["carry"], rating=2000, priority=1),
                ],
            )
            for _ in range(10)
        ]

        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=players,
            team_size=5,
            balance_limit=100.0,
        )

        assert response is not None

    def test_single_role_multiple_players(self, sample_roles, role_list):
        """Test players with only single role."""
        role_constraints = {
            sample_roles["carry"]: RoleConstraint(min_in_team=0, max_in_team=10),
        }

        players = [
            PlayerInfo(
                member_id=uuid.uuid4(),
                roles=[
                    PlayerRoleInfo(role_id=sample_roles["carry"], rating=2000 + i, priority=1),
                ],
            )
            for i in range(10)
        ]

        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=players,
            team_size=5,
            balance_limit=100.0,
        )

        assert response is not None

    def test_extreme_rating_differences(self, sample_roles, role_list, role_constraints):
        """Test with extreme rating differences between players."""
        players = [
            PlayerInfo(
                member_id=uuid.uuid4(),
                roles=[
                    PlayerRoleInfo(role_id=sample_roles["carry"], rating=100, priority=1),
                ],
            ),
            PlayerInfo(
                member_id=uuid.uuid4(),
                roles=[
                    PlayerRoleInfo(role_id=sample_roles["mid"], rating=5000, priority=1),
                ],
            ),
            PlayerInfo(
                member_id=uuid.uuid4(),
                roles=[
                    PlayerRoleInfo(role_id=sample_roles["support"], rating=1000, priority=1),
                ],
            ),
            PlayerInfo(
                member_id=uuid.uuid4(),
                roles=[
                    PlayerRoleInfo(role_id=sample_roles["tank"], rating=4500, priority=1),
                ],
            ),
            PlayerInfo(
                member_id=uuid.uuid4(),
                roles=[
                    PlayerRoleInfo(role_id=sample_roles["carry"], rating=50, priority=1),
                ],
            ),
        ]

        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=players,
            team_size=5,
            balance_limit=100.0,
        )

        assert response is not None

    def test_with_priority_weights(self, sample_roles, role_list, role_constraints, sample_players):
        """Test with role priority weights in quality settings."""
        weights = {
            sample_roles["carry"]: 2.0,
            sample_roles["support"]: 0.5,
        }
        quality_settings = QualitySettings(
            role_priority_coef=2.0,
            role_weights=weights,
        )

        engine = BalanceEngine(
            quality_settings=quality_settings,
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=100.0,
        )

        assert response is not None


class TestBalanceEnginePerformance:
    """Test suite for performance characteristics."""

    def test_find_balances_completes_reasonably(
        self, sample_roles, role_list, role_constraints, sample_players
    ):
        """Test that find_balances completes in reasonable time."""
        import time

        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        start = time.time()
        response = engine.find_balances(
            players=sample_players,
            team_size=5,
            balance_limit=100.0,
        )
        elapsed = time.time() - start

        # Should complete in less than 10 seconds for 10 players
        assert elapsed < 10.0
        assert response is not None

    def test_large_player_count(self, sample_roles, role_list, role_constraints):
        """Test with larger player count."""
        players = [
            PlayerInfo(
                member_id=uuid.uuid4(),
                roles=[
                    PlayerRoleInfo(
                        role_id=list(sample_roles.values())[i % len(sample_roles)],
                        rating=2000 + (i % 500),
                        priority=1 + (i % 3),
                    ),
                ],
            )
            for i in range(20)
        ]

        engine = BalanceEngine(
            quality_settings=QualitySettings(),
            role_ids=role_list,
            role_constraints=role_constraints,
        )

        response = engine.find_balances(
            players=players,
            team_size=5,
            balance_limit=200.0,
            max_results=50,
        )

        assert response is not None
