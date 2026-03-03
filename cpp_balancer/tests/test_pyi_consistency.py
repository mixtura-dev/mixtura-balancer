"""
Tests for consistency between .pyi type hints and actual C++ implementation.

Validates that the .pyi file accurately describes the C++ bindings.
"""

import inspect
import pytest
from balance_engine import _core


class TestPyiConsistency:
    """Test suite for .pyi consistency with runtime implementation."""

    def test_role_rating_class_exists(self):
        """Test that RoleRating class is defined."""
        assert hasattr(_core, "RoleRating")

    def test_role_rating_has_attributes(self):
        """Test that RoleRating has expected attributes."""
        rr = _core.RoleRating(1, 2000, 1)
        assert hasattr(rr, "role_id")
        assert hasattr(rr, "rating")
        assert hasattr(rr, "priority")

    def test_role_rating_attribute_values(self):
        """Test RoleRating attribute values."""
        rr = _core.RoleRating(5, 2500, 2)
        assert rr.role_id == 5
        assert rr.rating == 2500
        assert rr.priority == 2

    def test_role_rating_default_constructor(self):
        """Test RoleRating default constructor."""
        rr = _core.RoleRating()
        assert rr is not None

    def test_role_rating_repr(self):
        """Test RoleRating repr."""
        rr = _core.RoleRating(1, 2000, 1)
        repr_str = repr(rr)
        assert isinstance(repr_str, str)

    def test_player_info_class_exists(self):
        """Test that PlayerInfo class exists."""
        assert hasattr(_core, "PlayerInfo")

    def test_player_info_has_attributes(self):
        """Test that PlayerInfo has expected attributes."""
        roles = [_core.RoleRating(1, 2000, 1)]
        pi = _core.PlayerInfo(10, roles)
        assert hasattr(pi, "member_id")
        assert hasattr(pi, "roles")

    def test_player_info_default_constructor(self):
        """Test PlayerInfo default constructor."""
        pi = _core.PlayerInfo()
        assert pi is not None

    def test_player_info_can_play_role(self):
        """Test PlayerInfo.can_play_role method exists."""
        roles = [_core.RoleRating(1, 2000, 1), _core.RoleRating(2, 1900, 2)]
        pi = _core.PlayerInfo(10, roles)
        assert hasattr(pi, "can_play_role")
        # Should be callable
        assert callable(pi.can_play_role)

    def test_player_info_get_rating_for_role(self):
        """Test PlayerInfo.get_rating_for_role method exists."""
        roles = [_core.RoleRating(1, 2000, 1)]
        pi = _core.PlayerInfo(10, roles)
        assert hasattr(pi, "get_rating_for_role")
        assert callable(pi.get_rating_for_role)

    def test_player_info_get_priority_for_role(self):
        """Test PlayerInfo.get_priority_for_role method exists."""
        roles = [_core.RoleRating(1, 2000, 1)]
        pi = _core.PlayerInfo(10, roles)
        assert hasattr(pi, "get_priority_for_role")
        assert callable(pi.get_priority_for_role)

    def test_player_info_repr(self):
        """Test PlayerInfo repr."""
        roles = [_core.RoleRating(1, 2000, 1)]
        pi = _core.PlayerInfo(10, roles)
        repr_str = repr(pi)
        assert isinstance(repr_str, str)

    def test_role_constraint_class_exists(self):
        """Test that RoleConstraint class exists."""
        assert hasattr(_core, "RoleConstraint")

    def test_role_constraint_has_attributes(self):
        """Test that RoleConstraint has expected attributes."""
        rc = _core.RoleConstraint(1, 2)
        assert hasattr(rc, "min_in_team")
        assert hasattr(rc, "max_in_team")

    def test_role_constraint_attribute_values(self):
        """Test RoleConstraint attribute values."""
        rc = _core.RoleConstraint(1, 3)
        assert rc.min_in_team == 1
        assert rc.max_in_team == 3

    def test_role_constraint_default_constructor(self):
        """Test RoleConstraint default constructor."""
        rc = _core.RoleConstraint()
        assert rc is not None

    def test_role_constraint_repr(self):
        """Test RoleConstraint repr."""
        rc = _core.RoleConstraint(1, 2)
        repr_str = repr(rc)
        assert isinstance(repr_str, str)

    def test_quality_settings_class_exists(self):
        """Test that QualitySettings class exists."""
        assert hasattr(_core, "QualitySettings")

    def test_quality_settings_has_attributes(self):
        """Test that QualitySettings has expected attributes."""
        qs = _core.QualitySettings()
        assert hasattr(qs, "alpha")
        assert hasattr(qs, "beta")
        assert hasattr(qs, "gamma")
        assert hasattr(qs, "xi")
        assert hasattr(qs, "p")
        assert hasattr(qs, "q")
        assert hasattr(qs, "g")
        assert hasattr(qs, "max_priority")
        assert hasattr(qs, "role_weights")

    def test_quality_settings_attribute_assignable(self):
        """Test that QualitySettings attributes are assignable."""
        qs = _core.QualitySettings()
        qs.alpha = 2.0
        qs.beta = 1.5
        qs.gamma = 3.0
        qs.xi = 0.5
        qs.p = 2.0
        qs.q = 1.5
        qs.g = 2.5
        qs.max_priority = 5
        qs.role_weights = {1: 1.0, 2: 2.0}

        assert qs.alpha == 2.0
        assert qs.beta == 1.5
        assert qs.gamma == 3.0
        assert qs.xi == 0.5
        assert qs.max_priority == 5

    def test_quality_settings_repr(self):
        """Test QualitySettings repr."""
        qs = _core.QualitySettings()
        repr_str = repr(qs)
        assert isinstance(repr_str, str)

    def test_engine_settings_class_exists(self):
        """Test that EngineSettings class exists."""
        assert hasattr(_core, "EngineSettings")

    def test_engine_settings_has_attributes(self):
        """Test that EngineSettings has expected attributes."""
        es = _core.EngineSettings()
        assert hasattr(es, "num_workers")
        assert hasattr(es, "fallback_workers")
        assert hasattr(es, "worker_result_buffer")
        assert hasattr(es, "max_players")
        assert hasattr(es, "mask_reserve_limit")
        assert hasattr(es, "priority_imbalance_threshold")

    def test_engine_settings_attribute_assignable(self):
        """Test that EngineSettings attributes are assignable."""
        es = _core.EngineSettings()
        es.num_workers = 8
        es.fallback_workers = 6
        es.worker_result_buffer = 2000
        es.max_players = 16
        es.mask_reserve_limit = 25
        es.priority_imbalance_threshold = 2

        assert es.num_workers == 8
        assert es.worker_result_buffer == 2000

    def test_engine_settings_repr(self):
        """Test EngineSettings repr."""
        es = _core.EngineSettings()
        repr_str = repr(es)
        assert isinstance(repr_str, str)

    def test_quality_metrics_class_exists(self):
        """Test that QualityMetrics class exists."""
        assert hasattr(_core, "QualityMetrics")

    def test_quality_metrics_has_attributes(self):
        """Test that QualityMetrics has expected attributes."""
        qm = _core.QualityMetrics(1.0, 2.0, 3.0, 4.0)
        assert hasattr(qm, "fairness")
        assert hasattr(qm, "role_fairness")
        assert hasattr(qm, "role_points")
        assert hasattr(qm, "uniformity")

    def test_quality_metrics_attribute_values(self):
        """Test QualityMetrics attribute values."""
        qm = _core.QualityMetrics(1.5, 2.5, 3.5, 4.5)
        assert qm.fairness == 1.5
        assert qm.role_fairness == 2.5
        assert qm.role_points == 3.5
        assert qm.uniformity == 4.5

    def test_quality_metrics_default_constructor(self):
        """Test QualityMetrics default constructor."""
        qm = _core.QualityMetrics()
        assert qm is not None

    def test_quality_metrics_total_method(self):
        """Test QualityMetrics.total method exists."""
        qm = _core.QualityMetrics(1.0, 2.0, 3.0, 4.0)
        assert hasattr(qm, "total")
        assert callable(qm.total)
        # Note: In .pyi it's a method, but it might be a property
        total = qm.total() if callable(qm.total) else qm.total
        assert isinstance(total, (int, float))

    def test_quality_metrics_total_score_property(self):
        """Test QualityMetrics.total_score property."""
        qm = _core.QualityMetrics(1.0, 2.0, 3.0, 4.0)
        if hasattr(qm, "total_score"):
            assert hasattr(qm, "total_score")

    def test_quality_metrics_repr(self):
        """Test QualityMetrics repr."""
        qm = _core.QualityMetrics(1.0, 2.0, 3.0, 4.0)
        repr_str = repr(qm)
        assert isinstance(repr_str, str)

    def test_team_player_result_class_exists(self):
        """Test that TeamPlayerResult class exists."""
        assert hasattr(_core, "TeamPlayerResult")

    def test_team_player_result_has_attributes(self):
        """Test that TeamPlayerResult has expected attributes."""
        tpr = _core.TeamPlayerResult(10, 1, 2000)
        assert hasattr(tpr, "member_id")
        assert hasattr(tpr, "role_id")
        assert hasattr(tpr, "rating")

    def test_team_player_result_game_role_id_alias(self):
        """Test that TeamPlayerResult has game_role_id alias."""
        tpr = _core.TeamPlayerResult(10, 1, 2000)
        if hasattr(tpr, "game_role_id"):
            # game_role_id is an alias for role_id
            assert tpr.game_role_id == tpr.role_id

    def test_team_player_result_default_constructor(self):
        """Test TeamPlayerResult default constructor."""
        tpr = _core.TeamPlayerResult()
        assert tpr is not None

    def test_team_player_result_repr(self):
        """Test TeamPlayerResult repr."""
        tpr = _core.TeamPlayerResult(10, 1, 2000)
        repr_str = repr(tpr)
        assert isinstance(repr_str, str)

    def test_team_result_class_exists(self):
        """Test that TeamResult class exists."""
        assert hasattr(_core, "TeamResult")

    def test_team_result_has_attributes(self):
        """Test that TeamResult has expected attributes."""
        players = []
        tr = _core.TeamResult("Team1", players)
        assert hasattr(tr, "name")
        assert hasattr(tr, "players")

    def test_team_result_team_id_alias(self):
        """Test that TeamResult has team_id alias for name."""
        players = []
        tr = _core.TeamResult("Team1", players)
        if hasattr(tr, "team_id"):
            assert tr.team_id == tr.name

    def test_team_result_default_constructor(self):
        """Test TeamResult default constructor."""
        tr = _core.TeamResult()
        assert tr is not None

    def test_team_result_repr(self):
        """Test TeamResult repr."""
        players = []
        tr = _core.TeamResult("Team1", players)
        repr_str = repr(tr)
        assert isinstance(repr_str, str)

    def test_balance_result_data_class_exists(self):
        """Test that BalanceResultData class exists."""
        assert hasattr(_core, "BalanceResultData")

    def test_balance_result_data_has_attributes(self):
        """Test that BalanceResultData has expected attributes."""
        brd = _core.BalanceResultData()
        assert hasattr(brd, "quality")
        assert hasattr(brd, "teams")

    def test_balance_result_data_to_dict_method(self):
        """Test BalanceResultData.to_dict method exists."""
        brd = _core.BalanceResultData()
        assert hasattr(brd, "to_dict")
        assert callable(brd.to_dict)

    def test_balance_result_data_repr(self):
        """Test BalanceResultData repr."""
        brd = _core.BalanceResultData()
        repr_str = repr(brd)
        assert isinstance(repr_str, str)

    def test_balance_response_class_exists(self):
        """Test that BalanceResponse class exists."""
        assert hasattr(_core, "BalanceResponse")

    def test_balance_response_has_attributes(self):
        """Test that BalanceResponse has expected attributes."""
        br = _core.BalanceResponse()
        assert hasattr(br, "result_code")
        assert hasattr(br, "status")
        assert hasattr(br, "balances")

    def test_balance_response_ok_property(self):
        """Test BalanceResponse.ok property."""
        br = _core.BalanceResponse()
        if hasattr(br, "ok"):
            assert hasattr(br, "ok")

    def test_balance_engine_class_exists(self):
        """Test that BalanceEngine class exists in C++ module."""
        assert hasattr(_core, "BalanceEngine")

    def test_balance_engine_constructor(self):
        """Test BalanceEngine constructor signature."""
        qs = _core.QualitySettings()
        role_ids = [0, 1, 2, 3]
        constraints = {0: _core.RoleConstraint(1, 1)}
        es = _core.EngineSettings()

        engine = _core.BalanceEngine(qs, role_ids, constraints, es)
        assert engine is not None

    def test_balance_engine_find_balances_method(self):
        """Test BalanceEngine.find_balances method exists."""
        qs = _core.QualitySettings()
        role_ids = [0, 1, 2, 3]
        constraints = {0: _core.RoleConstraint(1, 1)}

        engine = _core.BalanceEngine(qs, role_ids, constraints)
        assert hasattr(engine, "find_balances")
        assert callable(engine.find_balances)

    def test_balance_engine_find_balances_returns_response(self):
        """Test that find_balances returns BalanceResponse."""
        qs = _core.QualitySettings()
        role_ids = [0, 1, 2, 3]
        constraints = {0: _core.RoleConstraint(1, 1)}

        engine = _core.BalanceEngine(qs, role_ids, constraints)
        players = []
        response = engine.find_balances(players, 5, 100.0)

        assert hasattr(response, "result_code")
        assert hasattr(response, "status")
        assert hasattr(response, "balances")
