# Mixtura Balance

Game team balancer service with C++ optimization engine for fair player distribution.

## Overview

Mixtura Balance is a high-performance team balancing service that uses an optimized C++ algorithm to find optimal team compositions. It processes balance requests asynchronously via RabbitMQ and returns ranked results based on multiple quality metrics.

## Features

- **Fast C++ Engine**: Optimized C++ implementation using bitmask algorithms and parallel processing
- **Multi-metric Quality Scoring**: Fairness, uniformity, role fairness, and role priority metrics
- **Role Constraints**: Configurable min/max players per role in each team
- **Async Processing**: RabbitMQ-based message queue for scalable request handling
- **Type-safe Models**: Pydantic v2 models with comprehensive validation

## Architecture

```
┌──────────────┐     RabbitMQ      ┌─────────────────────┐
│   Client     │ ────────────────> │   Balancer Service │
│              │                    │                     │
│              │ <───────────────── │   (FastStream)     │
└──────────────┘     Response       └─────────────────────┘
```

## Requirements

- Python 3.13+
- RabbitMQ (for message queue)
- C++ compiler with CMake (for building the extension)

## Installation

```bash
# Install all dependencies including C++ module
uv sync --all-extras

# Build C++ module from source
cd cpp_balancer && uv pip install -e .
```

## Quick Start

```python
from balancer_service.domain.models.balance_request import (
    BalanceRequest,
    BalanceSettings,
    MathSettings,
    Player,
    PlayerRole,
    RoleSettings,
)
import uuid

# Create roles
role_dps = uuid.uuid4()
role_support = uuid.uuid4()
role_tank = uuid.uuid4()

# Create players with their roles and ratings
players = [
    Player(
        member_id=uuid.uuid4(),
        roles={
            role_dps: PlayerRole(priority=1, rating=2500),
            role_support: PlayerRole(priority=2, rating=2000),
        }
    ),
    Player(
        member_id=uuid.uuid4(),
        roles={
            role_tank: PlayerRole(priority=1, rating=2300),
            role_dps: PlayerRole(priority=3, rating=2100),
        }
    ),
    # ... more players (must be exactly 2 * max_in_team)
]

# Configure balance settings
balance_settings = BalanceSettings(
    max_in_team=3,
    roles={
        role_dps: RoleSettings(
            original_game_role=role_dps,
            min_in_team=1,
            max_in_team=2,
        ),
        role_support: RoleSettings(
            original_game_role=role_support,
            min_in_team=1,
            max_in_team=1,
        ),
        role_tank: RoleSettings(
            original_game_role=role_tank,
            min_in_team=1,
            max_in_team=1,
        ),
    },
    math=MathSettings(),
)

# Create request
request = BalanceRequest(
    draft_id=uuid.uuid4(),
    players=players,
    balance_settings=balance_settings,
)
```

## Running the Service

```bash
# Start RabbitMQ
docker compose -f docker-compose.dev-depends.yaml up -d

# Run the service
python -m balancer_service.app.main

# Or with FastStream CLI
faststream run balancer_service.app.main:app
```

## Quality Metrics

The engine optimizes for four metrics (lower is better):

| Metric | Description |
|--------|-------------|
| **Fairness** | Difference in total team ratings |
| **Uniformity** | Rating variance within teams |
| **Role Fairness** | Difference in role-specific ratings |
| **Role Points** | Player priority vs. assigned role match |

See [docs/metrics.md](docs/metrics.md) for detailed mathematical formulas.

## Configuration

### Math Settings

```python
from balancer_service.domain.models.balance_request import MathSettings

settings = MathSettings(
    fairness_coef=3.0,           # Weight for fairness
    role_fairness_coef=1.0,      # Weight for role fairness
    role_priority_coef=80.0,     # Weight for role priority
    role_priority_imbalance_coef=0.2,  # Penalty for priority imbalance
    fairness_power_coef=2.0,    # Power for fairness calculation
    uniformity_power_coef=2.0,  # Power for uniformity calculation
)
```

### Engine Settings

```python
settings = EngineSettings(
    num_workers=0,              # 0 = auto-detect CPU cores
    fallback_workers=4,         # Fallback if auto-detect fails
    max_players=32,             # Maximum players supported
)
```

## Testing

```bash
# Run all tests
pytest

# Run C++ module tests
pytest cpp_balancer/tests/

# Run single test file
pytest cpp_balancer/tests/test_models.py

# Run single test
pytest cpp_balancer/tests/test_models.py::TestPlayerInfo::test_player_info_creation

# With coverage
pytest --cov=src --cov-report=html
```

## Linting & Type Checking

```bash
# Lint with ruff
ruff check .

# Type check with mypy
mypy src/balancer_service/
```

## Project Structure

```
.
├── src/balancer_service/          # Python service
│   ├── app/                       # Application entry
│   │   ├── main.py               # FastStream app
│   │   ├── exceptions.py         # Domain exceptions
│   │   └── schemas.py            # Response schemas
│   └── domain/                   # Business logic
│       ├── balance_engine.py     # C++ wrapper
│       └── models/               # Pydantic models
├── cpp_balancer/                  # C++ engine
│   ├── balance_engine.cpp/hpp   # Core implementation
│   ├── pybind11_bindings.cpp    # Python bindings
│   └── tests/                    # Python tests
├── docs/                          # Documentation
│   ├── models.md                 # Data models
│   └── metrics.md                # Math formulas
└── pyproject.toml                # Project config
```

## License

MIT
