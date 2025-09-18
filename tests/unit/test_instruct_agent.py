import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autobox.server import AutoboxMCPServer


class TestInstructAgent:
    @pytest.mark.asyncio
    async def test_instruct_agent_success(self):
        server = AutoboxMCPServer()

        mock_container = MagicMock()
        mock_container.status = "running"
        mock_container.labels = {"autobox.api_port": "9000"}
        mock_container.attrs = {
            "NetworkSettings": {
                "Ports": {"9000/tcp": [{"HostPort": "9001", "HostIp": "127.0.0.1"}]}
            }
        }

        server.docker_manager.client = MagicMock()
        server.docker_manager.client.containers.get.return_value = mock_container

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "instruction_sent"}
            mock_response.text = '{"status": "instruction_sent"}'

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await server._instruct_agent(
                "test_sim_123", "agent1", "Please propose Argentina to Ana"
            )

            result_json = json.loads(result)
            assert result_json["success"] is True
            assert "Instruction sent to agent agent1" in result_json["message"]
            assert result_json["response"] == {"status": "instruction_sent"}

            mock_client.post.assert_called_once_with(
                "http://127.0.0.1:9001/instructions/agents/agent1",
                json={"instruction": "Please propose Argentina to Ana"},
                timeout=10.0,
            )

    @pytest.mark.asyncio
    async def test_instruct_agent_container_not_running(self):
        server = AutoboxMCPServer()

        mock_container = MagicMock()
        mock_container.status = "stopped"

        server.docker_manager.client = MagicMock()
        server.docker_manager.client.containers.get.return_value = mock_container

        result = await server._instruct_agent(
            "test_sim_123", "agent1", "Test instruction"
        )

        assert "is not running" in result

    @pytest.mark.asyncio
    async def test_instruct_agent_api_error(self):
        server = AutoboxMCPServer()

        mock_container = MagicMock()
        mock_container.status = "running"
        mock_container.labels = {"autobox.api_port": "9000"}
        mock_container.attrs = {
            "NetworkSettings": {
                "Ports": {"9000/tcp": [{"HostPort": "9001", "HostIp": "127.0.0.1"}]}
            }
        }

        server.docker_manager.client = MagicMock()
        server.docker_manager.client.containers.get.return_value = mock_container

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad request: agent not found"

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await server._instruct_agent(
                "test_sim_123", "unknown_agent", "Test instruction"
            )

            result_json = json.loads(result)
            assert result_json["success"] is False
            assert "API returned status 400" in result_json["error"]
            assert "Bad request: agent not found" in result_json["details"]

    @pytest.mark.asyncio
    async def test_instruct_agent_accepts_202(self):
        """Test that 202 Accepted status is handled correctly."""
        server = AutoboxMCPServer()

        mock_container = MagicMock()
        mock_container.status = "running"
        mock_container.labels = {"autobox.api_port": "9000"}
        mock_container.attrs = {
            "NetworkSettings": {
                "Ports": {"9000/tcp": [{"HostPort": "9001", "HostIp": "127.0.0.1"}]}
            }
        }

        server.docker_manager.client = MagicMock()
        server.docker_manager.client.containers.get.return_value = mock_container

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 202  # Accepted
            mock_response.json.return_value = {"status": "accepted"}
            mock_response.text = '{"status": "accepted"}'

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await server._instruct_agent(
                "test_sim_123", "agent1", "Test instruction"
            )

            result_json = json.loads(result)
            assert result_json["success"] is True
            assert "Instruction sent to agent agent1" in result_json["message"]
