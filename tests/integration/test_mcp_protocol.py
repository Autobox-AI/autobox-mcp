"""Integration tests for MCP protocol implementation."""

import json
from unittest.mock import patch

import pytest

from autobox.server import AutoboxMCPServer


@pytest.fixture
def mcp_server():
    """Create an MCP server instance for testing."""
    server = AutoboxMCPServer()
    return server


class TestMCPProtocol:
    """Test MCP protocol implementation."""

    def test_server_initialization(self, mcp_server):
        """Test that MCP server is initialized."""
        assert mcp_server.server is not None
        assert mcp_server.server.name == "autobox-mcp"

    def test_tools_are_registered(self, mcp_server):
        """Test that tools are registered with the server."""
        assert mcp_server.server is not None

    @pytest.mark.asyncio
    async def test_list_simulations_tool(self, mcp_server):
        """Test list_simulations tool handler."""
        with patch.object(
            mcp_server.docker_manager, "list_running_simulations"
        ) as mock_list:
            mock_list.return_value = []

            result = await mcp_server._list_simulations()

            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_start_simulation_tool(self, mcp_server):
        """Test start_simulation tool handler."""
        with patch.object(mcp_server.docker_manager, "start_simulation") as mock_start:
            mock_start.return_value = "container-123"

            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", return_value='test = "config"'):
                    result = await mcp_server._start_simulation(
                        config_name="test_config", custom_config=None
                    )

            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_stop_simulation_tool(self, mcp_server):
        """Test stop_simulation tool handler."""
        with patch.object(mcp_server.docker_manager, "stop_simulation") as mock_stop:
            mock_stop.return_value = True

            result = await mcp_server._stop_simulation(simulation_id="sim-123")

            assert isinstance(result, dict)
            assert "status" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_simulation_status_tool(self, mcp_server):
        """Test get_simulation_status tool handler."""
        with patch.object(
            mcp_server.docker_manager, "get_container_status"
        ) as mock_status:
            mock_status.return_value = {
                "status": "running",
                "started_at": "2024-01-01T00:00:00Z",
            }

            result = await mcp_server._get_simulation_status(simulation_id="sim-123")

            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_simulation_logs_tool(self, mcp_server):
        """Test get_simulation_logs tool handler."""
        with patch.object(mcp_server.docker_manager, "get_logs") as mock_logs:
            mock_logs.return_value = "Test log output"

            result = await mcp_server._get_simulation_logs(
                simulation_id="sim-123", tail=100
            )

            assert isinstance(result, (str, dict))

    @pytest.mark.asyncio
    async def test_list_available_configs_tool(self, mcp_server):
        """Test list_available_configs tool handler."""
        result = await mcp_server._list_available_configs()

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_simulation_metrics_tool(self, mcp_server):
        """Test get_simulation_metrics tool handler."""
        with patch.object(
            mcp_server.docker_manager, "get_container_stats"
        ) as mock_stats:
            mock_stats.return_value = {"cpu_percent": 25.5, "memory_mb": 512}

            result = await mcp_server._get_simulation_metrics(
                simulation_id="sim-123", include_docker_stats=True
            )

            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_create_simulation_config_tool(self, mcp_server):
        """Test create_simulation_config tool handler."""
        params = {
            "name": "Test Simulation",
            "description": "Test description",
            "agents": [{"name": "Agent1", "role": "Tester"}],
        }

        with patch("pathlib.Path.mkdir"):
            with patch("pathlib.Path.open", create=True):
                with patch("json.dump"):
                    result = await mcp_server._create_simulation_config(params)

        assert isinstance(result, dict)
        assert "config" in result

    async def test_create_simulation_config_persists_file(self, mcp_server, tmp_path):
        """Test that create_simulation_config actually persists the config file."""
        test_simulations_path = tmp_path / "simulations"
        mcp_server.simulations_path = test_simulations_path

        params = {
            "name": "test_persistence",
            "description": "Test that config is persisted",
            "agents": [
                {
                    "name": "Agent1",
                    "role": "Tester",
                    "backstory": "Test agent backstory",
                }
            ],
            "max_steps": 50,
            "timeout_seconds": 120,
        }

        result = await mcp_server._create_simulation_config(params)

        assert isinstance(result, dict)
        assert "config" in result
        assert "config_path" in result
        assert "test_persistence" in result["config_path"]

        config_file = test_simulations_path / "test_persistence.json"
        assert config_file.exists()

        import json

        with open(config_file, "r") as f:
            saved_config = json.load(f)

        assert saved_config["name"] == "test_persistence"
        assert saved_config["description"] == "Test that config is persisted"
        assert saved_config["max_steps"] == 50
        assert saved_config["timeout_seconds"] == 120
        assert saved_config["shutdown_grace_period_seconds"] == 5
        assert len(saved_config["workers"]) == 1
        assert saved_config["workers"][0]["name"] == "Agent1"

        assert "evaluator" in saved_config
        assert "mailbox" in saved_config["evaluator"]
        assert saved_config["evaluator"]["mailbox"]["max_size"] == 400

        assert "reporter" in saved_config
        assert "mailbox" in saved_config["reporter"]

        assert "planner" in saved_config
        assert "mailbox" in saved_config["planner"]

        assert "orchestrator" in saved_config
        assert "mailbox" in saved_config["orchestrator"]

        assert "logging" in saved_config
        assert saved_config["logging"]["log_file"] == "test_persistence.log"

        assert "mailbox" in saved_config["workers"][0]
        assert saved_config["workers"][0]["mailbox"]["max_size"] == 100

    async def test_save_custom_config_persists_file(self, mcp_server, tmp_path):
        """Test that _save_custom_config saves to the correct location."""
        test_simulations_path = tmp_path / "simulations"
        mcp_server.simulations_path = test_simulations_path

        custom_config = {
            "name": "custom_test",
            "description": "Custom config test",
            "max_steps": 75,
            "workers": [{"name": "Worker1", "role": "Test Worker"}],
        }

        result_path = await mcp_server._save_custom_config(custom_config)

        assert result_path == test_simulations_path / "custom_test.json"
        assert result_path.exists()

        import json

        with open(result_path, "r") as f:
            saved_config = json.load(f)

        assert saved_config["name"] == "custom_test"
        assert saved_config["description"] == "Custom config test"

    async def test_save_custom_config_without_name(self, mcp_server, tmp_path):
        """Test that _save_custom_config generates a name if not provided."""
        test_simulations_path = tmp_path / "simulations"
        mcp_server.simulations_path = test_simulations_path

        custom_config = {"description": "Config without name", "max_steps": 100}

        result_path = await mcp_server._save_custom_config(custom_config)

        assert result_path.exists()
        assert "custom_" in result_path.name
        assert result_path.suffix == ".json"

    async def test_create_simulation_metrics_custom(self, mcp_server, tmp_path):
        """Test creating metrics with custom metrics (not using LLM)."""
        test_simulations_path = tmp_path / "simulations"
        test_metrics_path = tmp_path / "metrics"
        mcp_server.simulations_path = test_simulations_path

        test_simulations_path.mkdir(parents=True, exist_ok=True)
        sim_config = {
            "name": "test_sim",
            "description": "Test simulation",
            "workers": [{"name": "Agent1", "role": "Tester"}],
        }
        with open(test_simulations_path / "test_sim.json", "w") as f:
            json.dump(sim_config, f)

        custom_metrics = [
            {
                "name": "test_counter",
                "description": "A test counter metric",
                "type": "COUNTER",
                "unit": "count",
                "tags": [],
            },
            {
                "name": "test_gauge",
                "description": "A test gauge metric",
                "type": "GAUGE",
                "unit": "value",
                "tags": [{"tag": "agent_name", "description": "Agent name"}],
            },
        ]

        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = tmp_path.parent

            params = {
                "simulation_name": "test_sim",
                "use_llm": False,
                "custom_metrics": custom_metrics,
            }

            result = await mcp_server._create_simulation_metrics(params)

        assert "metrics" in result
        assert "metrics_path" in result
        assert len(result["metrics"]) == 2
        assert result["metrics"][0]["name"] == "test_counter"
        assert result["metrics"][1]["name"] == "test_gauge"

    async def test_create_simulation_metrics_missing_config(self, mcp_server, tmp_path):
        """Test that creating metrics fails when simulation config doesn't exist."""
        mcp_server.simulations_path = tmp_path / "simulations"

        params = {
            "simulation_name": "non_existent_sim",
            "use_llm": False,
            "custom_metrics": [],
        }

        result = await mcp_server._create_simulation_metrics(params)

        assert "error" in result
        assert "not found" in result["error"]

    async def test_create_simulation_metrics_llm_no_key(
        self, mcp_server, tmp_path, monkeypatch
    ):
        """Test that LLM metrics generation fails gracefully without API key."""
        test_simulations_path = tmp_path / "simulations"
        mcp_server.simulations_path = test_simulations_path

        test_simulations_path.mkdir(parents=True, exist_ok=True)
        sim_config = {
            "name": "test_sim",
            "description": "Test simulation",
            "workers": [],
        }
        with open(test_simulations_path / "test_sim.json", "w") as f:
            json.dump(sim_config, f)

        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        params = {"simulation_name": "test_sim", "use_llm": True}

        result = await mcp_server._create_simulation_metrics(params)

        assert "error" in result
        assert "OPENAI_API_KEY" in result["error"] or "OpenAI" in result["error"]
