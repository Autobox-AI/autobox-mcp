import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autobox.server import AutoboxMCPServer


class TestInstructAgent:
    @pytest.mark.asyncio
    async def test_instruct_agent_success(self):
        server = AutoboxMCPServer()
        
        # Mock Docker container
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_container.labels = {"autobox.api_port": "9000"}
        mock_container.attrs = {
            "NetworkSettings": {
                "Ports": {
                    "9000/tcp": [{"HostPort": "9001", "HostIp": "127.0.0.1"}]
                }
            }
        }
        
        # Mock Docker client
        server.docker_manager.client = MagicMock()
        server.docker_manager.client.containers.get.return_value = mock_container
        
        # Mock httpx client
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "instruction_sent"}
            mock_response.text = '{"status": "instruction_sent"}'
            
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_client
            
            # Call the method
            result = await server._instruct_agent(
                "test_sim_123", 
                "agent1", 
                "Please propose Argentina to Ana"
            )
            
            # Verify result
            result_json = json.loads(result)
            assert result_json["success"] is True
            assert "Instruction sent to agent agent1" in result_json["message"]
            assert result_json["response"] == {"status": "instruction_sent"}
            
            # Verify the API was called correctly
            mock_client.post.assert_called_once_with(
                "http://127.0.0.1:9001/instructions/agents/agent1",
                json={"instruction": "Please propose Argentina to Ana"},
                timeout=10.0,
            )
    
    @pytest.mark.asyncio
    async def test_instruct_agent_container_not_running(self):
        server = AutoboxMCPServer()
        
        # Mock Docker container that's not running
        mock_container = MagicMock()
        mock_container.status = "stopped"
        
        # Mock Docker client
        server.docker_manager.client = MagicMock()
        server.docker_manager.client.containers.get.return_value = mock_container
        
        # Call the method
        result = await server._instruct_agent(
            "test_sim_123",
            "agent1",
            "Test instruction"
        )
        
        # Verify result
        assert "is not running" in result
    
    @pytest.mark.asyncio
    async def test_instruct_agent_api_error(self):
        server = AutoboxMCPServer()
        
        # Mock Docker container
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_container.labels = {"autobox.api_port": "9000"}
        mock_container.attrs = {
            "NetworkSettings": {
                "Ports": {
                    "9000/tcp": [{"HostPort": "9001", "HostIp": "127.0.0.1"}]
                }
            }
        }
        
        # Mock Docker client
        server.docker_manager.client = MagicMock()
        server.docker_manager.client.containers.get.return_value = mock_container
        
        # Mock httpx client to return error
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad request: agent not found"
            
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_client
            
            # Call the method
            result = await server._instruct_agent(
                "test_sim_123",
                "unknown_agent",
                "Test instruction"
            )
            
            # Verify result
            result_json = json.loads(result)
            assert result_json["success"] is False
            assert "API returned status 400" in result_json["error"]
            assert "Bad request: agent not found" in result_json["details"]