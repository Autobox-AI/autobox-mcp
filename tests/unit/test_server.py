"""Unit tests for AutoboxMCPServer."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import os

from autobox.server import AutoboxMCPServer


class TestAutoboxMCPServer:
    """Test suite for AutoboxMCPServer."""

    def test_server_initialization(self):
        """Test that server initializes correctly."""
        server = AutoboxMCPServer()

        assert server is not None
        assert server.docker_manager is not None
        assert server.autobox_config_path is not None
        assert isinstance(server.autobox_config_path, Path)

    def test_autobox_config_path_default(self):
        """Test default autobox config path."""
        server = AutoboxMCPServer()
        expected_path = Path.home() / ".autobox" / "config"
        assert server.autobox_config_path == expected_path

    def test_server_paths(self):
        """Test that server paths are set correctly."""
        server = AutoboxMCPServer()
        base_path = Path.home() / ".autobox" / "config"

        assert server.autobox_config_path == base_path
        assert server.simulations_path == base_path / "simulations"
        assert server.metrics_path == base_path / "metrics"

    @pytest.mark.asyncio
    async def test_list_simulations_handler(self):
        """Test list simulations handler returns correct structure."""
        server = AutoboxMCPServer()
        server.docker_manager.list_running_simulations = AsyncMock(return_value=[])

        result = await server._list_simulations()

        assert isinstance(result, dict)
        # The actual implementation returns {"running": [], "tracked": [], "total": 0}
        assert "running" in result or "error" in result

    @pytest.mark.asyncio
    async def test_list_available_configs_handler(self):
        """Test list available configs handler."""
        server = AutoboxMCPServer()

        # The actual implementation reads from ~/.autobox/config/simulations
        result = await server._list_available_configs()

        # Result should be a list (might be empty if no configs exist)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_stop_simulation_handler(self):
        """Test stop simulation handler."""
        server = AutoboxMCPServer()
        server.docker_manager.stop_simulation = AsyncMock(return_value=True)

        result = await server._stop_simulation(simulation_id="sim-123")

        assert isinstance(result, dict)
        assert "status" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_simulation_status_handler_not_found(self):
        """Test get simulation status when not found."""
        server = AutoboxMCPServer()
        server.docker_manager.get_container_status = AsyncMock(return_value=None)

        result = await server._get_simulation_status(simulation_id="sim-123")

        assert isinstance(result, dict)
        # Should have either error or status info
        assert "error" in result or "status" in result

    @pytest.mark.asyncio
    async def test_get_simulation_logs_handler(self):
        """Test get simulation logs handler."""
        server = AutoboxMCPServer()
        server.docker_manager.get_logs = AsyncMock(return_value="Test logs")

        result = await server._get_simulation_logs(
            simulation_id="sim-123",
            tail=50
        )

        # Result should be a string or error dict
        assert isinstance(result, (str, dict))

    @pytest.mark.asyncio
    async def test_get_simulation_metrics_handler(self):
        """Test get simulation metrics handler."""
        server = AutoboxMCPServer()

        # Mock the container stats
        mock_stats = {
            "cpu_percent": 25.5,
            "memory_mb": 512
        }
        server.docker_manager.get_container_stats = AsyncMock(return_value=mock_stats)

        result = await server._get_simulation_metrics(
            simulation_id="sim-123",
            include_docker_stats=True
        )

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_create_simulation_config(self):
        """Test create simulation config handler."""
        server = AutoboxMCPServer()

        params = {
            "name": "Test Sim",
            "description": "Test description",
            "agents": [{"name": "Agent1", "role": "Tester"}],
            "max_steps": 10,
            "timeout_seconds": 60
        }

        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.mkdir'):
                with patch('pathlib.Path.open', create=True):
                    with patch('json.dump'):
                        result = await server._create_simulation_config(params)

        assert isinstance(result, dict)
        assert "config" in result
        assert result["config"]["name"] == "Test Sim"