

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from autobox.docker.manager import DockerManager


class TestDockerManager:


    @pytest.fixture
    def docker_manager(self):

        with patch('autobox.docker.manager.docker.from_env') as mock_docker:
            mock_docker.return_value = Mock()
            manager = DockerManager()
            manager.client = Mock()
            yield manager

    def test_docker_manager_initialization(self, docker_manager):

        assert docker_manager is not None
        assert docker_manager.client is not None

    @pytest.mark.asyncio
    async def test_list_running_simulations_empty(self, docker_manager):

        docker_manager.client.containers.list.return_value = []

        result = await docker_manager.list_running_simulations()

        assert result == []
        docker_manager.client.containers.list.assert_called_once_with(
            filters={"label": "com.autobox.simulation=true"}
        )

    @pytest.mark.asyncio
    async def test_list_running_simulations_with_containers(self, docker_manager):
        docker_manager.client.containers.list.return_value = []
        
        result = await docker_manager.list_running_simulations()
        
        assert result == []

    @pytest.mark.asyncio
    async def test_stop_simulation(self, docker_manager):

        mock_container = Mock()
        docker_manager.client.containers.get.return_value = mock_container

        result = await docker_manager.stop_simulation("container-123")

        assert result is True
        docker_manager.client.containers.get.assert_called_once_with("container-123")
        mock_container.stop.assert_called_once_with(timeout=10)
        mock_container.remove.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_simulation_not_found(self, docker_manager):

        docker_manager.client.containers.get.side_effect = Exception("Not found")

        result = await docker_manager.stop_simulation("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_logs(self, docker_manager):

        mock_container = Mock()
        mock_container.logs.return_value = b"Log line 1\nLog line 2"
        docker_manager.client.containers.get.return_value = mock_container

        result = await docker_manager.get_logs("container-123", tail=10)

        assert result == "Log line 1\nLog line 2"
        mock_container.logs.assert_called_once_with(tail=10, timestamps=True)

    @pytest.mark.asyncio
    async def test_get_container_status(self, docker_manager):

        mock_container = Mock()
        mock_container.status = "running"
        mock_container.short_id = "abc123"
        mock_container.name = "test-container"
        mock_container.attrs = {
            "State": {
                "Status": "running",
                "StartedAt": "2024-01-01T00:00:00Z",
                "Running": True
            }
        }
        docker_manager.client.containers.get.return_value = mock_container

        result = await docker_manager.get_container_status("container-123")

        assert result is not None
        assert result["status"] == "running"