#!/usr/bin/env python3
"""Main MCP server for Autobox simulation management."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from autobox.docker.manager import DockerManager
from autobox.models.schemas import SimulationConfig, SimulationStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoboxMCPServer:
    """MCP Server for managing Autobox simulations."""

    def __init__(self):
        self.server = Server("autobox-mcp")
        self.docker_manager = DockerManager()
        self.simulations: Dict[str, SimulationStatus] = {}
        # Use proper ~/.autobox config directory
        self.autobox_config_path = Path.home() / ".autobox" / "config"
        self.simulations_path = self.autobox_config_path / "simulations"
        self.metrics_path = self.autobox_config_path / "metrics"
        self.server_config_path = self.autobox_config_path / "server.json"
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP tool handlers."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="list_simulations",
                    description="List all simulations (running and completed)",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="start_simulation",
                    description="Start a new simulation from a configuration file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "config_name": {
                                "type": "string",
                                "description": "Name of the simulation config (e.g., 'summer_vacation')",
                            },
                            "custom_config": {
                                "type": "object",
                                "description": "Optional: Custom simulation config object instead of using a file",
                            },
                        },
                        "required": [],
                    },
                ),
                Tool(
                    name="stop_simulation",
                    description="Stop a running simulation gracefully",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "simulation_id": {
                                "type": "string",
                                "description": "ID of the simulation to stop",
                            },
                        },
                        "required": ["simulation_id"],
                    },
                ),
                Tool(
                    name="get_simulation_status",
                    description="Get detailed status of a specific simulation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "simulation_id": {
                                "type": "string",
                                "description": "ID of the simulation",
                            },
                        },
                        "required": ["simulation_id"],
                    },
                ),
                Tool(
                    name="get_simulation_logs",
                    description="Get logs from a simulation container",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "simulation_id": {
                                "type": "string",
                                "description": "ID of the simulation",
                            },
                            "tail": {
                                "type": "integer",
                                "description": "Number of lines to retrieve from the end (default: 100)",
                                "default": 100,
                            },
                        },
                        "required": ["simulation_id"],
                    },
                ),
                Tool(
                    name="list_available_configs",
                    description="List all available simulation configuration templates",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="get_simulation_metrics",
                    description="Get metrics from a running simulation (progress, agent interactions, API status)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "simulation_id": {
                                "type": "string",
                                "description": "ID of the simulation",
                            },
                            "include_docker_stats": {
                                "type": "boolean",
                                "description": "Include Docker container stats (CPU, memory, network)",
                                "default": True,
                            },
                        },
                        "required": ["simulation_id"],
                    },
                ),
                Tool(
                    name="create_simulation_config",
                    description="Create a new simulation configuration with AI assistance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name for the simulation",
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of what the simulation should accomplish",
                            },
                            "agents": {
                                "type": "array",
                                "description": "List of agent descriptions",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "role": {"type": "string"},
                                        "backstory": {"type": "string"},
                                    },
                                },
                            },
                            "max_steps": {
                                "type": "integer",
                                "description": "Maximum number of simulation steps",
                                "default": 100,
                            },
                            "timeout_seconds": {
                                "type": "integer",
                                "description": "Timeout in seconds",
                                "default": 300,
                            },
                        },
                        "required": ["name", "description"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            try:
                if name == "list_simulations":
                    result = await self._list_simulations()
                elif name == "start_simulation":
                    result = await self._start_simulation(
                        arguments.get("config_name"),
                        arguments.get("custom_config"),
                    )
                elif name == "stop_simulation":
                    result = await self._stop_simulation(arguments["simulation_id"])
                elif name == "get_simulation_status":
                    result = await self._get_simulation_status(arguments["simulation_id"])
                elif name == "get_simulation_logs":
                    result = await self._get_simulation_logs(
                        arguments["simulation_id"],
                        arguments.get("tail", 100),
                    )
                elif name == "list_available_configs":
                    result = await self._list_available_configs()
                elif name == "get_simulation_metrics":
                    result = await self._get_simulation_metrics(
                        arguments["simulation_id"],
                        arguments.get("include_docker_stats", True),
                    )
                elif name == "create_simulation_config":
                    result = await self._create_simulation_config(arguments)
                else:
                    result = f"Unknown tool: {name}"

                return [TextContent(type="text", text=str(result))]
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _list_simulations(self) -> Dict[str, Any]:
        """List all simulations."""
        running = await self.docker_manager.list_running_simulations()
        return {
            "running": running,
            "tracked": list(self.simulations.keys()),
            "total": len(running) + len(self.simulations),
        }

    async def _start_simulation(
        self, config_name: Optional[str], custom_config: Optional[Dict]
    ) -> Dict[str, Any]:
        """Start a new simulation."""
        if custom_config:
            config_path = await self._save_custom_config(custom_config)
            metrics_path = self._get_default_metrics_path()
        else:
            if not config_name:
                return {"error": "Either config_name or custom_config must be provided"}
            config_path = self.simulations_path / f"{config_name}.json"
            metrics_path = self.metrics_path / f"{config_name}.json"

            if not config_path.exists():
                return {"error": f"Config file not found: {config_name}"}

        container_id = await self.docker_manager.start_simulation(
            str(config_path),
            str(metrics_path),
            str(self.server_config_path) if self.server_config_path.exists() else None
        )

        self.simulations[container_id] = SimulationStatus(
            id=container_id,
            name=custom_config.get("name", config_name) if custom_config else config_name,
            status="running",
            config_path=str(config_path),
        )

        return {
            "simulation_id": container_id,
            "status": "started",
            "config": str(config_path),
        }

    async def _stop_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Stop a running simulation."""
        success = await self.docker_manager.stop_simulation(simulation_id)
        if success:
            if simulation_id in self.simulations:
                self.simulations[simulation_id].status = "stopped"
            return {"simulation_id": simulation_id, "status": "stopped"}
        return {"error": f"Failed to stop simulation {simulation_id}"}

    async def _get_simulation_status(self, simulation_id: str) -> Dict[str, Any]:
        """Get simulation status."""
        container_status = await self.docker_manager.get_container_status(simulation_id)

        if simulation_id in self.simulations:
            sim_status = self.simulations[simulation_id]
            return {
                "id": simulation_id,
                "name": sim_status.name,
                "status": container_status.get("status", sim_status.status),
                "container": container_status,
            }
        elif container_status:
            return {
                "id": simulation_id,
                "status": container_status.get("status", "unknown"),
                "container": container_status,
            }
        else:
            return {"error": f"Simulation {simulation_id} not found"}

    async def _get_simulation_logs(self, simulation_id: str, tail: int) -> str:
        """Get simulation logs."""
        logs = await self.docker_manager.get_logs(simulation_id, tail)
        return logs if logs else f"No logs found for simulation {simulation_id}"

    async def _get_simulation_metrics(
        self, simulation_id: str, include_docker_stats: bool
    ) -> Dict[str, Any]:
        """Get metrics from a running simulation."""
        metrics = {}

        # Try to get metrics from the simulation API
        api_status = await self.docker_manager.get_simulation_api_status(simulation_id)
        if api_status:
            metrics["api_status"] = api_status
            metrics["progress"] = api_status.get("progress", 0)
            metrics["status"] = api_status.get("status", "unknown")
            metrics["current_step"] = api_status.get("current_step", 0)
            metrics["max_steps"] = api_status.get("max_steps", 0)
            metrics["agent_count"] = len(api_status.get("agents", {}))

            # Extract agent-specific metrics if available
            if "agents" in api_status:
                metrics["agents"] = {}
                for agent_name, agent_data in api_status["agents"].items():
                    metrics["agents"][agent_name] = {
                        "status": agent_data.get("status", "unknown"),
                        "messages_sent": agent_data.get("messages_sent", 0),
                        "messages_received": agent_data.get("messages_received", 0),
                    }

        # Get Docker container stats if requested
        if include_docker_stats:
            docker_stats = await self.docker_manager.get_container_stats(simulation_id)
            if docker_stats:
                metrics["docker_stats"] = docker_stats

        # If we have no metrics at all, return an error
        if not metrics:
            return {"error": f"No metrics available for simulation {simulation_id}"}

        metrics["simulation_id"] = simulation_id
        metrics["timestamp"] = asyncio.get_event_loop().time()
        return metrics

    async def _list_available_configs(self) -> List[str]:
        """List available configuration templates."""
        if self.simulations_path.exists():
            configs = [f.stem for f in self.simulations_path.glob("*.json")]
            return configs
        return []

    async def _create_simulation_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new simulation configuration."""
        config = SimulationConfig(
            name=params["name"],
            description=params["description"],
            max_steps=params.get("max_steps", 100),
            timeout_seconds=params.get("timeout_seconds", 300),
            agents=params.get("agents", []),
        )

        config_dict = {
            "name": config.name,
            "description": config.description,
            "max_steps": config.max_steps,
            "timeout_seconds": config.timeout_seconds,
            "task": config.description,
            "evaluator": {
                "name": "EVALUATOR",
                "llm": {"model": "gpt-4o-mini"},
            },
            "reporter": {
                "name": "REPORTER",
                "llm": {"model": "gpt-4o-mini"},
            },
            "planner": {
                "name": "PLANNER",
                "llm": {"model": "gpt-4o-mini"},
            },
            "orchestrator": {
                "name": "ORCHESTRATOR",
                "llm": {"model": "gpt-4o-mini"},
            },
            "workers": [],
        }

        for agent in config.agents:
            config_dict["workers"].append({
                "name": agent["name"],
                "role": agent["role"],
                "backstory": agent.get("backstory", ""),
                "llm": {"model": "gpt-4o-mini"},
            })

        return {
            "config": config_dict,
            "message": "Configuration created. Use this with start_simulation's custom_config parameter.",
        }

    async def _save_custom_config(self, config: Dict) -> Path:
        """Save custom config to a temporary file."""
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, dir="/tmp"
        ) as f:
            json.dump(config, f, indent=2)
            return Path(f.name)

    def _get_default_metrics_path(self) -> Path:
        """Get default metrics path."""
        # Try default metrics first
        default_metrics = self.metrics_path / "default.json"
        if default_metrics.exists():
            return default_metrics

        # Try to find any metrics file
        if self.metrics_path.exists():
            metrics_files = list(self.metrics_path.glob("*.json"))
            if metrics_files:
                return metrics_files[0]

        # Return a temporary empty metrics file if none exist
        return Path("/tmp/empty_metrics.json")

    async def run(self):
        """Run the MCP server."""
        from mcp.server import InitializationOptions
        from mcp.types import ServerCapabilities

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                initialization_options=InitializationOptions(
                    server_name="autobox-mcp",
                    server_version="0.1.0",
                    capabilities=ServerCapabilities(
                        tools={}
                    )
                )
            )


def main():
    """Main entry point."""
    server = AutoboxMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()