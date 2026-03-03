"""
Pytest configuration and shared fixtures for balance_engine tests.
"""

import uuid
import pytest
from balance_engine.models import (
    PlayerInfo,
    PlayerRoleInfo,
    RoleConstraint,
    QualitySettings,
    EngineSettings,
)


@pytest.fixture
def sample_roles():
    """Create sample role UUIDs for testing."""
    return {
        "carry": uuid.UUID("12345678-1234-5678-1234-567812345678"),
        "mid": uuid.UUID("87654321-4321-8765-4321-876543218765"),
        "support": uuid.UUID("11111111-2222-3333-4444-555555555555"),
        "tank": uuid.UUID("66666666-7777-8888-9999-000000000000"),
    }


@pytest.fixture
def role_list(sample_roles):
    """Return list of role UUIDs."""
    return list(sample_roles.values())


@pytest.fixture
def role_constraints(sample_roles):
    """Create standard role constraints for a 5-player team."""
    return {
        sample_roles["carry"]: RoleConstraint(min_in_team=1, max_in_team=1),
        sample_roles["mid"]: RoleConstraint(min_in_team=1, max_in_team=1),
        sample_roles["support"]: RoleConstraint(min_in_team=1, max_in_team=2),
        sample_roles["tank"]: RoleConstraint(min_in_team=1, max_in_team=2)
    }


@pytest.fixture
def quality_settings():
    """Create default quality settings for testing."""
    return QualitySettings(
        fairness_coef=1.0,
        role_fairness_coef=1.0,
        role_priority_coef=1.0,
        imbalance_role_priority_coef=0.2,
        fairness_power=1.0,
        uniformity_power=1.0,
        role_fairness_power=1.0,
        max_priority=3,
    )


@pytest.fixture
def engine_settings():
    """Create engine settings for testing."""
    return EngineSettings(
        num_workers=2,
        fallback_workers=4,
        worker_result_buffer=1000,
        max_players=32,
        mask_reserve_limit=20,
        priority_imbalance_threshold=1,
    )


@pytest.fixture
def sample_players(sample_roles):
    """Create sample players with various roles and ratings."""
    return [
        PlayerInfo(
            member_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            roles=[
                PlayerRoleInfo(
                    role_id=sample_roles["carry"],
                    rating=2500,
                    priority=1,  # Primary role
                ),
                PlayerRoleInfo(
                    role_id=sample_roles["mid"],
                    rating=2400,
                    priority=2,
                ),
            ],
        ),
        PlayerInfo(
            member_id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
            roles=[
                PlayerRoleInfo(
                    role_id=sample_roles["mid"],
                    rating=2600,
                    priority=1,
                ),
                PlayerRoleInfo(
                    role_id=sample_roles["carry"],
                    rating=2400,
                    priority=2,
                ),
            ],
        ),
        PlayerInfo(
            member_id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
            roles=[
                PlayerRoleInfo(
                    role_id=sample_roles["support"],
                    rating=2200,
                    priority=1,
                ),
            ],
        ),
        PlayerInfo(
            member_id=uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
            roles=[
                PlayerRoleInfo(
                    role_id=sample_roles["support"],
                    rating=2100,
                    priority=1,
                ),
            ],
        ),
        PlayerInfo(
            member_id=uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
            roles=[
                PlayerRoleInfo(
                    role_id=sample_roles["tank"],
                    rating=2300,
                    priority=1,
                ),
            ],
        ),
        PlayerInfo(
            member_id=uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
            roles=[
                PlayerRoleInfo(
                    role_id=sample_roles["tank"],
                    rating=2250,
                    priority=1,
                ),
            ],
        ),
        PlayerInfo(
            member_id=uuid.UUID("10101010-1010-1010-1010-101010101010"),
            roles=[
                PlayerRoleInfo(
                    role_id=sample_roles["carry"],
                    rating=2350,
                    priority=1,
                ),
            ],
        ),
        PlayerInfo(
            member_id=uuid.UUID("20202020-2020-2020-2020-202020202020"),
            roles=[
                PlayerRoleInfo(
                    role_id=sample_roles["mid"],
                    rating=2450,
                    priority=1,
                ),
            ],
        ),
        PlayerInfo(
            member_id=uuid.UUID("30303030-3030-3030-3030-303030303030"),
            roles=[
                PlayerRoleInfo(
                    role_id=sample_roles["support"],
                    rating=2150,
                    priority=1,
                ),
            ],
        ),
        PlayerInfo(
            member_id=uuid.UUID("40404040-4040-4040-4040-404040404040"),
            roles=[
                PlayerRoleInfo(
                    role_id=sample_roles["tank"],
                    rating=2200,
                    priority=1,
                ),
            ],
        ),
    ]


@pytest.fixture
def min_players(sample_roles):
    """Create minimal set of players (5 players for one team)."""
    return [
        PlayerInfo(
            member_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            roles=[
                PlayerRoleInfo(
                    role_id=sample_roles["carry"],
                    rating=2000,
                    priority=1,
                ),
            ],
        ),
        PlayerInfo(
            member_id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
            roles=[
                PlayerRoleInfo(
                    role_id=sample_roles["mid"],
                    rating=2000,
                    priority=1,
                ),
            ],
        ),
        PlayerInfo(
            member_id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
            roles=[
                PlayerRoleInfo(
                    role_id=sample_roles["support"],
                    rating=2000,
                    priority=1,
                ),
            ],
        ),
        PlayerInfo(
            member_id=uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
            roles=[
                PlayerRoleInfo(
                    role_id=sample_roles["tank"],
                    rating=2000,
                    priority=1,
                ),
            ],
        ),
        PlayerInfo(
            member_id=uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
            roles=[
                PlayerRoleInfo(
                    role_id=sample_roles["support"],
                    rating=2000,
                    priority=1,
                ),
            ],
        ),
    ]
