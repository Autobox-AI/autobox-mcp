

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autobox.docker.manager import DockerManager
from autobox.server import AutoboxMCPServer


class TestStopAllSimulations:


    @pytest.mark.asyncio
    async def test_docker_manager_stop_all_simulations(self):

        manager = DockerManager()
        
        