# Autobox MCP Server Tests

## Structure

```
tests/
├── unit/               # Unit tests for individual components
├── integration/        # Integration tests for MCP protocol and Docker
├── scripts/           # Test utility scripts
└── conftest.py        # Shared pytest fixtures
```

## Running Tests

### Install Dependencies
```bash
uv sync --extra dev
```

### Run All Tests
```bash
uv run pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
uv run pytest tests/unit/

# Integration tests only
uv run pytest tests/integration/

# Tests with coverage
uv run pytest --cov=autobox --cov-report=html

# Tests with markers
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m "not docker"  # Skip Docker tests
```

### Run Individual Test Files
```bash
uv run pytest tests/unit/test_server.py
uv run pytest tests/unit/test_docker_manager.py::TestDockerManager::test_list_simulations_no_containers
```

## Test Utilities

### Manual Testing Script
```bash
# Direct testing
bin/test-mcp-manual

# Docker testing
bin/test-mcp-manual --docker

# Interactive mode
bin/test-mcp-manual --interactive
```

### Docker Test Scripts
```bash
# Quick Docker test
bin/test-mcp-docker.sh

# Interactive Docker test
bin/test-mcp-interactive.sh
```

## Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.docker` - Tests requiring Docker
- `@pytest.mark.slow` - Slow running tests

## Writing Tests

### Unit Test Example
```python
import pytest
from unittest.mock import Mock
from autobox.server import AutoboxMCPServer

@pytest.mark.unit
class TestServer:
    def test_initialization(self):
        server = AutoboxMCPServer()
        assert server is not None
```

### Async Test Example
```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
    assert result == expected
```

### Using Fixtures
```python
def test_with_mock_docker(mock_docker_client):
    # mock_docker_client is provided by conftest.py
    mock_docker_client.containers.list.return_value = []
    # ... test logic
```

## Docker Testing

For integration tests that require Docker:

1. Build the Docker image:
```bash
docker build -t autobox-mcp:latest .
```

2. Run Docker integration tests:
```bash
uv run pytest tests/integration/test_docker_integration.py
```

## Troubleshooting

### Docker Tests Failing
- Ensure Docker daemon is running
- Ensure autobox-mcp:latest image is built
- Check Docker socket permissions

### Async Test Issues
- Use `@pytest.mark.asyncio` decorator
- Ensure proper event loop handling

### Import Errors
- Verify `pythonpath = .` in pytest.ini
- Check that autobox package is properly installed