# Agent Guidelines for mixtura_balance

This is a Python project with a C++ extension (pybind11) for game team balancing.

## Project Structure

```
.
├── src/balancer_service/          # Main Python service
│   ├── app/                       # Application entry points
│   │   ├── main.py                # FastStream RabbitMQ app
│   │   ├── exceptions.py          # Domain exceptions
│   │   └── schemas.py             # Response schemas
│   └── domain/                    # Business logic
│       ├── balance_engine.py      # C++ engine wrapper
│       └── models/                # Pydantic models
├── cpp_balancer/                  # C++ balance engine (pybind11)
│   ├── balance_engine.cpp/hpp     # Core C++ implementation
│   ├── pybind11_bindings.cpp      # Python bindings
│   └── tests/                     # Python tests for C++ module
├── pyproject.toml                 # Root project config
└── cpp_balancer/pyproject.toml    # C++ module config
```

## Build/Lint/Test Commands

### Setup
```bash
# Install all dependencies (includes C++ module in dev mode)
uv sync --all-extras

# Build C++ module from source
cd cpp_balancer && uv pip install -e .
```

### Linting (ruff)
```bash
# Root project
ruff check .

# C++ balancer module
ruff check cpp_balancer/
```

### Type Checking (mypy)
```bash
# Root project (myPy configured in pyproject.toml)
mypy src/balancer_service/

# Ignore specific modules (see pyproject.toml for list)
```

### Testing (pytest)
```bash
# Run all tests
pytest

# Run tests for C++ balancer module
pytest cpp_balancer/tests/

# Run a single test file
pytest cpp_balancer/tests/test_models.py

# Run a single test
pytest cpp_balancer/tests/test_models.py::TestPlayerInfo::test_player_info_creation

# Run tests matching a pattern
pytest -k "test_player"

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html
```

### Running the Service
```bash
# Start RabbitMQ (required)
docker compose -f docker-compose.dev-depends.yaml up -d

# Run the FastStream app (from src/balancer_service)
python -m balancer_service.app.main

# Or use FastStream CLI
faststream run balancer_service.app.main:app
```

## Code Style Guidelines

### General
- Python 3.13+ required
- Line length: 100 characters max
- Use type hints for all function signatures
- Use Pydantic v2 for data validation

### Imports
- Standard library imports first
- Third-party imports second
- Local/relative imports third
- Separate each group with a blank line
- Sort imports alphabetically within groups

```python
import datetime
import logging
from uuid import UUID, uuid4

import balance_engine
from pydantic import BaseModel

from ..app.exceptions import DomainException
from .models.balance import Balance
```

### Naming Conventions
- Classes: `PascalCase` (e.g., `BalanceRequest`)
- Functions/methods: `snake_case` (e.g., `find_balances_async`)
- Variables: `snake_case` (e.g., `balance_request`)
- Constants: `UPPER_SNAKE_CASE`
- Private methods: prefix with underscore (e.g., `_convert_players_to_cpp`)

### Pydantic Models
- Use `BaseModel` for all data models
- Use `Field` for validation and descriptions
- Use `model_validator(mode="after")` for cross-field validation
- Add Russian descriptions for business-domain fields

```python
class RoleSettings(BaseModel):
    max_in_team: int = Field(ge=0, description="Максимум игроков этой роли в команде")
    min_in_team: int = Field(ge=0, description="Минимум игроков этой роли в команде")

    @model_validator(mode="after")
    def validate_min_max(self) -> "RoleSettings":
        if self.min_in_team > self.max_in_team:
            raise ValueError(...)
        return self
```

### Error Handling
- Use custom exception classes inheriting from `DomainException`
- Log errors with appropriate level before raising
- Use Pydantic validation for input validation
- Return structured error responses

```python
class DomainException(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)

# Usage
if result.result_code != 200:
    logger.error(f"Balance engine error: {result.status}")
    raise DomainException(result.result_code, result.status)
```

### Async Code
- Use `async/await` for I/O operations
- Use `asyncio` for concurrent operations
- Configure pytest with `asyncio_mode = "auto"`

### C++ Extension Guidelines
- C++ code uses pybind11 for Python bindings
- UUIDs are automatically converted between Python and C++
- Follow CMakeLists.txt build configuration
- Tests for C++ module are in `cpp_balancer/tests/`

### Logging
- Use module-level loggers: `logger = logging.getLogger(__name__)`
- Use structured logging with context
- Configure via `logging_setup.py`

```python
logger.info(f"Received balance request for draft_id={message.draft_id}")
logger.error(f"Balance engine error: {result.status}")
```

### Configuration
- Use `pydantic_settings.BaseSettings` for environment config
- Load from environment variables with aliases
- Use `.env` file for local development (not committed)

## Tool Selection

- **Dependency Management**: uv
- **Linting**: ruff
- **Type Checking**: mypy
- **Testing**: pytest with pytest-asyncio
- **Build System**: uv + scikit-build-core (for C++)
- **Message Queue**: RabbitMQ with FastStream
