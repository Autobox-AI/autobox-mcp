

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import os

from autobox.server import AutoboxMCPServer


class TestAutoboxMCPServer:


    def test_server_initialization(self):

        server = AutoboxMCPServer()

        assert server is not None
        assert server.docker_manager is not None
        assert server.autobox_config_path is not None
        assert isinstance(server.autobox_config_path, Path)

    def test_autobox_config_path_default(self):

        server = AutoboxMCPServer()
        expected_path = Path.home() / ".autobox" / "config"
        assert server.autobox_config_path == expected_path

    def test_server_paths(self):

        server = AutoboxMCPServer()
        base_path = Path.home() / ".autobox" / "config"

        assert server.autobox_config_path == base_path
        assert server.simulations_path == base_path / "simulations"
        assert server.metrics_path == base_path / "metrics"

    @pytest.mark.asyncio
    async def test_list_simulations_handler(self):

        server = AutoboxMCPServer()
        server.docker_manager.list_running_simulations = AsyncMock(return_value=[])

        result = await server._list_simulations()

        assert isinstance(result, dict)
