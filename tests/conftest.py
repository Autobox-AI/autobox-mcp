"""Shared pytest fixtures and configuration."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock
import tempfile
import os


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for test configs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_docker_client():
    """Create a mock Docker client."""
    client = Mock()
    client.containers = Mock()
    client.containers.list = Mock(return_value=[])
    client.containers.run = Mock()
    client.images = Mock()
    client.networks = Mock()
    return client


@pytest.fixture
def sample_simulation_config():
    """Create a sample simulation configuration."""
    return {
        "name": "Test Simulation",
        "description": "A test simulation for pytest",
        "agents": [
            {
                "name": "TestAgent1",
                "role": "Tester",
                "backstory": "An agent for testing"
            },
            {
                "name": "TestAgent2",
                "role": "Validator",
                "backstory": "An agent for validation"
            }
        ],
        "max_steps": 10,
        "timeout_seconds": 60
    }


@pytest.fixture
def mock_container():
    """Create a mock Docker container."""
    container = Mock()
    container.id = "mock-container-123"
    container.name = "autobox-sim-test"
    container.status = "running"
    container.labels = {
        "autobox.simulation": "true",
        "autobox.simulation.id": "sim-test-123",
        "autobox.simulation.name": "Test Simulation",
        "autobox.config": "test.toml"
    }
    container.attrs = {
        "State": {
            "Status": "running",
            "StartedAt": "2024-01-01T00:00:00Z",
            "Health": {"Status": "healthy"}
        }
    }
    container.logs = Mock(return_value=b"Test log output")
    container.stats = Mock(return_value=iter([{
        "cpu_stats": {
            "cpu_usage": {"total_usage": 1000000000},
            "system_cpu_usage": 10000000000,
            "online_cpus": 4
        },
        "precpu_stats": {
            "cpu_usage": {"total_usage": 500000000},
            "system_cpu_usage": 5000000000
        },
        "memory_stats": {
            "usage": 536870912,
            "limit": 1073741824
        },
        "networks": {
            "eth0": {
                "rx_bytes": 1024,
                "tx_bytes": 2048
            }
        }
    }]))
    container.stop = Mock()
    container.remove = Mock()
    return container


@pytest.fixture
def docker_available():
    """Check if Docker is available for integration tests."""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


@pytest.fixture
def autobox_image_exists():
    """Check if autobox-mcp Docker image exists."""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "images", "-q", "autobox-mcp:latest"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "docker: mark test as requiring Docker"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )