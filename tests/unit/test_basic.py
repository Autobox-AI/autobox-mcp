"""Basic unit tests that verify the core functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from autobox.server import AutoboxMCPServer
from autobox.docker.manager import DockerManager


class TestBasicFunctionality:
    """Basic tests to verify imports and initialization."""

    def test_imports_work(self):
        """Test that all imports work correctly."""
        assert AutoboxMCPServer is not None
        assert DockerManager is not None

    def test_server_can_be_created(self):
        """Test that server can be instantiated."""
        server = AutoboxMCPServer()
        assert server is not None
        assert hasattr(server, 'server')
        assert hasattr(server, 'docker_manager')
        assert hasattr(server, 'autobox_config_path')

    @patch('autobox.docker.manager.docker.from_env')
    def test_docker_manager_can_be_created(self, mock_docker):
        """Test that DockerManager can be instantiated."""
        mock_docker.return_value = Mock()
        manager = DockerManager()
        assert manager is not None
        assert hasattr(manager, 'client')

    def test_config_paths(self):
        """Test that config paths are set correctly."""
        server = AutoboxMCPServer()
        assert server.autobox_config_path == Path.home() / ".autobox" / "config"
        assert server.simulations_path == Path.home() / ".autobox" / "config" / "simulations"
        assert server.metrics_path == Path.home() / ".autobox" / "config" / "metrics"

    @pytest.mark.asyncio
    async def test_server_has_handlers(self):
        """Test that server has the expected handler methods."""
        server = AutoboxMCPServer()

        # Check that private handler methods exist
        assert hasattr(server, '_list_simulations')
        assert hasattr(server, '_start_simulation')
        assert hasattr(server, '_stop_simulation')
        assert hasattr(server, '_get_simulation_status')
        assert hasattr(server, '_get_simulation_logs')
        assert hasattr(server, '_get_simulation_metrics')
        assert hasattr(server, '_list_available_configs')
        assert hasattr(server, '_create_simulation_config')

    @patch('autobox.docker.manager.docker.from_env')
    def test_docker_manager_has_methods(self, mock_docker):
        """Test that DockerManager has expected methods."""
        mock_docker.return_value = Mock()
        manager = DockerManager()

        # Check that methods exist
        assert hasattr(manager, 'list_running_simulations')
        assert hasattr(manager, 'start_simulation')
        assert hasattr(manager, 'stop_simulation')
        assert hasattr(manager, 'get_container_status')
        assert hasattr(manager, 'get_logs')
        assert hasattr(manager, 'get_container_stats')