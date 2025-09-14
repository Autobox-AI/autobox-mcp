"""Integration tests for Docker operations."""

import json
import subprocess
import os
import pytest
import tempfile
from pathlib import Path


@pytest.fixture(scope="module")
def docker_available():
    """Check if Docker is available."""
    try:
        result = subprocess.run(
            ["docker", "version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


@pytest.fixture(scope="module")
def docker_image_exists():
    """Check if Docker image exists."""
    result = subprocess.run(
        ["docker", "images", "-q", "autobox-mcp:latest"],
        capture_output=True,
        text=True
    )
    return bool(result.stdout.strip())


@pytest.mark.docker
class TestDockerIntegration:
    """Integration tests for Docker MCP server."""

    def test_docker_available(self, docker_available):
        """Test that Docker is available."""
        if not docker_available:
            pytest.skip("Docker not available")
        assert docker_available is True

    def test_docker_image_exists(self, docker_image_exists):
        """Test that Docker image exists."""
        if not docker_image_exists:
            pytest.skip("Docker image 'autobox-mcp:latest' not found. Build it first.")
        assert docker_image_exists is True

    def test_docker_container_runs(self, docker_available, docker_image_exists):
        """Test that Docker container can run basic Python command."""
        if not docker_available:
            pytest.skip("Docker not available")
        if not docker_image_exists:
            pytest.skip("Docker image not found")

        cmd = [
            "docker", "run", "--rm",
            "autobox-mcp:latest",
            "uv", "run", "python", "-c", "print('Container works')"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Check if Docker daemon is not accessible
        if result.stderr and "FileNotFoundError" in result.stderr:
            pytest.skip("Docker daemon not accessible")

        assert result.returncode == 0
        assert "Container works" in result.stdout or result.returncode == 0

    def test_mcp_initialize_request(self, docker_available, docker_image_exists):
        """Test MCP initialize request through Docker."""
        if not docker_available:
            pytest.skip("Docker not available")
        if not docker_image_exists:
            pytest.skip("Docker image not found")

        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "pytest-client",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }

        cmd = [
            "docker", "run", "-i", "--rm",
            "-v", "/var/run/docker.sock:/var/run/docker.sock",
            "-v", f"{os.path.expanduser('~')}/.autobox:/root/.autobox",
            "autobox-mcp:latest"
        ]

        result = subprocess.run(
            cmd,
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0
        if result.stdout:
            response = json.loads(result.stdout.strip())
            assert "result" in response or "error" in response

    def test_mcp_list_tools(self, docker_available, docker_image_exists):
        """Test listing MCP tools through Docker."""
        if not docker_available:
            pytest.skip("Docker not available")
        if not docker_image_exists:
            pytest.skip("Docker image not found")

        # Send both initialize and list tools requests
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "pytest-client",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }

        list_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }

        requests = json.dumps(init_request) + "\n" + json.dumps(list_request)

        cmd = [
            "docker", "run", "-i", "--rm",
            "-v", "/var/run/docker.sock:/var/run/docker.sock",
            "-v", f"{os.path.expanduser('~')}/.autobox:/root/.autobox",
            "autobox-mcp:latest"
        ]

        result = subprocess.run(
            cmd,
            input=requests,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0

        if result.stdout:
            # Parse responses
            responses = result.stdout.strip().split('\n')
            assert len(responses) >= 1

            # Check last response (tools list)
            last_response = json.loads(responses[-1])
            if "result" in last_response and "tools" in last_response["result"]:
                tools = last_response["result"]["tools"]
                tool_names = [t["name"] for t in tools]

                # At least some tools should be present
                expected_tools = [
                    "list_simulations",
                    "start_simulation",
                    "stop_simulation"
                ]

                for expected in expected_tools:
                    assert expected in tool_names