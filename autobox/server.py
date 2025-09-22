#!/usr/bin/env python3


import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from autobox.docker.manager import DockerManager
from autobox.models.schemas import SimulationConfig, SimulationStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutoboxMCPServer:
    def __init__(self):
        self.server = Server("autobox-mcp")
        self.docker_manager = DockerManager()
        self.simulations: Dict[str, SimulationStatus] = {}
        self.autobox_config_path = Path.home() / ".autobox" / "config"
        self.simulations_path = self.autobox_config_path / "simulations"
        self.metrics_path = self.autobox_config_path / "metrics"
        self.server_config_path = self.autobox_config_path / "server.json"
        self._setup_handlers()

    def _setup_handlers(self):
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
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
                Tool(
                    name="stop_all_simulations",
                    description="Stop ALL running simulations (terminate all autobox Docker containers)",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="create_simulation_metrics",
                    description="Create metrics configuration for a simulation using AI assistance or custom metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "simulation_name": {
                                "type": "string",
                                "description": "Name of the simulation (must match an existing config)",
                            },
                            "use_llm": {
                                "type": "boolean",
                                "description": "Whether to use LLM to generate metrics (default: true)",
                            },
                            "custom_metrics": {
                                "type": "array",
                                "description": "Custom metrics (if use_llm is false)",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "description": {"type": "string"},
                                        "type": {
                                            "type": "string",
                                            "enum": ["COUNTER", "GAUGE", "HISTOGRAM"],
                                        },
                                        "unit": {"type": "string"},
                                        "tags": {
                                            "type": "array",
                                            "items": {"type": "object"},
                                        },
                                    },
                                },
                            },
                        },
                        "required": ["simulation_name"],
                    },
                ),
                Tool(
                    name="instruct_agent",
                    description="Send instructions to a specific agent in an ongoing simulation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "simulation_id": {
                                "type": "string",
                                "description": "ID of the running simulation",
                            },
                            "agent_name": {
                                "type": "string",
                                "description": "Name of the agent to instruct",
                            },
                            "instruction": {
                                "type": "string",
                                "description": "Instruction to send to the agent",
                            },
                        },
                        "required": ["simulation_id", "agent_name", "instruction"],
                    },
                ),
                Tool(
                    name="delete_simulation",
                    description="Delete a simulation configuration and its associated metrics files",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "simulation_name": {
                                "type": "string",
                                "description": "Name of the simulation to delete (without file extension)",
                            },
                        },
                        "required": ["simulation_name"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
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
                    result = await self._get_simulation_status(
                        arguments["simulation_id"]
                    )
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
                elif name == "stop_all_simulations":
                    result = await self._stop_all_simulations()
                elif name == "create_simulation_metrics":
                    result = await self._create_simulation_metrics(arguments)
                elif name == "instruct_agent":
                    result = await self._instruct_agent(
                        arguments["simulation_id"],
                        arguments["agent_name"],
                        arguments["instruction"],
                    )
                elif name == "delete_simulation":
                    result = await self._delete_simulation(arguments["simulation_name"])
                else:
                    result = f"Unknown tool: {name}"

                return [TextContent(type="text", text=str(result))]
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _list_simulations(self) -> Dict[str, Any]:
        running = await self.docker_manager.list_running_simulations()
        return {
            "running": running,
            "tracked": list(self.simulations.keys()),
            "total": len(running) + len(self.simulations),
        }

    async def _start_simulation(
        self, config_name: Optional[str], custom_config: Optional[Dict]
    ) -> Dict[str, Any]:
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
            str(self.server_config_path) if self.server_config_path.exists() else None,
        )

        self.simulations[container_id] = SimulationStatus(
            id=container_id,
            name=custom_config.get("name", config_name)
            if custom_config
            else config_name,
            status="running",
            config_path=str(config_path),
        )

        return {
            "simulation_id": container_id,
            "status": "started",
            "config": str(config_path),
        }

    async def _stop_simulation(self, simulation_id: str) -> Dict[str, Any]:
        success = await self.docker_manager.stop_simulation(simulation_id)
        if success:
            if simulation_id in self.simulations:
                self.simulations[simulation_id].status = "stopped"
            return {"simulation_id": simulation_id, "status": "stopped"}
        return {"error": f"Failed to stop simulation {simulation_id}"}

    async def _stop_all_simulations(self) -> Dict[str, Any]:
        result = await self.docker_manager.stop_all_simulations()

        stopped_ids = [s["id"] for s in result.get("stopped", [])]
        for sim_id in stopped_ids:
            if sim_id in self.simulations:
                self.simulations[sim_id].status = "stopped"

        return result

    async def _get_simulation_status(self, simulation_id: str) -> Dict[str, Any]:
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
        logs = await self.docker_manager.get_logs(simulation_id, tail)
        return logs if logs else f"No logs found for simulation {simulation_id}"

    async def _get_simulation_metrics(
        self, simulation_id: str, include_docker_stats: bool
    ) -> Dict[str, Any]:
        metrics = {}

        api_metrics = await self.docker_manager.get_simulation_api_metrics(
            simulation_id
        )
        if api_metrics:
            metrics.update(api_metrics)

            metrics["simulation_id"] = simulation_id
            metrics["api_metrics"] = api_metrics

            if "progress" in api_metrics:
                metrics["progress"] = api_metrics["progress"]
            if "status" in api_metrics:
                metrics["status"] = api_metrics["status"]
            if "current_step" in api_metrics:
                metrics["current_step"] = api_metrics["current_step"]
            if "max_steps" in api_metrics:
                metrics["max_steps"] = api_metrics["max_steps"]
            if "agents" in api_metrics:
                metrics["agent_count"] = len(api_metrics["agents"])
                metrics["agents"] = {}
                for agent_name, agent_data in api_metrics["agents"].items():
                    metrics["agents"][agent_name] = {
                        "status": agent_data.get("status", "unknown"),
                        "messages_sent": agent_data.get("messages_sent", 0),
                        "messages_received": agent_data.get("messages_received", 0),
                    }
        else:
            api_status = await self.docker_manager.get_simulation_api_status(
                simulation_id
            )
            if api_status:
                metrics["api_status"] = api_status
                metrics["progress"] = api_status.get("progress", 0)
                metrics["status"] = api_status.get("status", "unknown")
                metrics["current_step"] = api_status.get("current_step", 0)
                metrics["max_steps"] = api_status.get("max_steps", 0)
                metrics["agent_count"] = len(api_status.get("agents", {}))

                if "agents" in api_status:
                    metrics["agents"] = {}
                    for agent_name, agent_data in api_status["agents"].items():
                        metrics["agents"][agent_name] = {
                            "status": agent_data.get("status", "unknown"),
                            "messages_sent": agent_data.get("messages_sent", 0),
                            "messages_received": agent_data.get("messages_received", 0),
                        }

        if include_docker_stats:
            docker_stats = await self.docker_manager.get_container_stats(simulation_id)
            if docker_stats:
                metrics["docker_stats"] = docker_stats

        if not metrics:
            return {"error": f"No metrics available for simulation {simulation_id}"}

        metrics["simulation_id"] = simulation_id
        metrics["timestamp"] = asyncio.get_event_loop().time()
        return metrics

    async def _list_available_configs(self) -> List[str]:
        if self.simulations_path.exists():
            configs = [f.stem for f in self.simulations_path.glob("*.json")]
            return configs
        return []

    async def _create_simulation_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
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
            "shutdown_grace_period_seconds": 5,
            "task": config.description,
            "evaluator": {
                "name": "EVALUATOR",
                "mailbox": {"max_size": 400},
                "llm": {"model": "gpt-5-nano"},
            },
            "reporter": {
                "name": "REPORTER",
                "mailbox": {"max_size": 400},
                "llm": {"model": "gpt-5-nano"},
            },
            "planner": {
                "name": "PLANNER",
                "mailbox": {"max_size": 400},
                "llm": {"model": "gpt-5-nano"},
            },
            "orchestrator": {
                "name": "ORCHESTRATOR",
                "mailbox": {"max_size": 400},
                "llm": {"model": "gpt-5-nano"},
            },
            "workers": [],
            "logging": {
                "verbose": False,
                "log_path": "logs",
                "log_file": f"{config.name.lower().replace(' ', '_')}.log",
            },
        }

        for agent in config.agents:
            config_dict["workers"].append(
                {
                    "name": agent["name"],
                    "description": agent.get(
                        "description", f"this is {agent['name'].lower()} agent"
                    ),
                    "role": agent["role"],
                    "backstory": agent.get("backstory", ""),
                    "mailbox": {"max_size": 100},
                    "llm": {"model": "gpt-5-nano"},
                }
            )

        self.simulations_path.mkdir(parents=True, exist_ok=True)

        config_file_path = self.simulations_path / f"{config.name}.json"
        with open(config_file_path, "w") as f:
            json.dump(config_dict, f, indent=2)

        logger.info(f"Saved simulation config to {config_file_path}")

        return {
            "config": config_dict,
            "config_path": str(config_file_path),
            "message": f"Configuration created and saved to {config_file_path}. You can now use 'start_simulation' with config_name: '{config.name}'",
        }

    async def _save_custom_config(self, config: Dict) -> Path:
        self.simulations_path.mkdir(parents=True, exist_ok=True)

        config_name = config.get("name", f"custom_{int(time.time())}")

        config_file_path = self.simulations_path / f"{config_name}.json"

        with open(config_file_path, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Saved custom simulation config to {config_file_path}")
        return config_file_path

    def _get_default_metrics_path(self) -> Path:
        default_metrics = self.metrics_path / "default.json"
        if default_metrics.exists():
            return default_metrics

        if self.metrics_path.exists():
            metrics_files = list(self.metrics_path.glob("*.json"))
            if metrics_files:
                return metrics_files[0]

        return Path("/tmp/empty_metrics.json")

    async def _create_simulation_metrics(
        self, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create metrics configuration for a simulation."""
        import os

        simulation_name = params["simulation_name"]
        use_llm = params.get("use_llm", True)
        custom_metrics = params.get("custom_metrics", [])

        sim_config_path = self.simulations_path / f"{simulation_name}.json"
        if not sim_config_path.exists():
            return {"error": f"Simulation config '{simulation_name}' not found"}

        with open(sim_config_path, "r") as f:
            sim_config = json.load(f)

        if use_llm:
            try:
                from openai import OpenAI

                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    return {"error": "OPENAI_API_KEY environment variable not set"}

                client = OpenAI(api_key=api_key)

                system_prompt = """<objective>
You are a smart Simulation Analyst. Your mission is to evaluate and analyse a simulation and design and define which metrics are relevant to measure the performance of the simulation and the system's behavior.
</objective>

<scope>
These are SOME general aspect of metrics:

1. Performance Metrics:
   • Resource Utilization: Tracks how efficiently resources are used by agents
   • Throughput: Measures the amount of work generated within a time frame
   • Response Time/Latency: Time taken to respond to events

2. Behavioral Metrics:
   • Agent Interaction Frequency: How often agents interact
   • Decision-Making Patterns: Choices agents make under conditions
   • Emergent Behaviors: Patterns arising from collective actions

3. Outcome Metrics:
   • Success Rate/Goal Achievement: How often goals are reached
   • System Stability: How stable the system remains over time
   • Resource Depletion/Regeneration: Resource consumption vs replenishment

4. Efficiency Metrics:
   • Cost Efficiency: Costs vs outputs generated
   • Time Efficiency: Time taken relative to expected time

5. Risk and Uncertainty Metrics:
   • Risk Exposure: Potential risks and impacts
   • Uncertainty Quantification: How uncertainty propagates

6. Adaptability and Resilience Metrics:
   • Adaptation Rate: How quickly agents adapt to changes
   • System Resilience: Ability to recover from disruptions

7. Satisfaction and Quality Metrics:
   • Agent Satisfaction: Overall satisfaction of agents
   • Quality of Output: Quality of outcomes produced
</scope>

<output>
You have to come up with STRUCTURED METRICS. This is a JSON array with a list of metrics that you consider relevant for the simulation you are analyzing.
Each metric should include: name (snake_case), description, type (COUNTER, GAUGE, or HISTOGRAM), unit, and tags array.

Your output MUST be only a valid JSON array of metric objects. Example format:
[
  {
    "name": "agent_interactions_total",
    "description": "Counts total interactions between agents",
    "type": "COUNTER",
    "unit": "interactions",
    "tags": [
      {
        "tag": "agent_name",
        "description": "Name of the interacting agent"
      }
    ]
  },
  {
    "name": "decision_time_seconds",
    "description": "Time taken to make decisions",
    "type": "HISTOGRAM",
    "unit": "seconds",
    "tags": []
  }
]
</output>"""

                user_prompt = f"""Analyze this simulation and create relevant metrics:

Simulation Name: {sim_config["name"]}
Description: {sim_config["description"]}
Task: {sim_config.get("task", sim_config["description"])}

Agents:
"""
                for worker in sim_config.get("workers", []):
                    user_prompt += f"- {worker['name']}: {worker['role']}"
                    if worker.get("backstory"):
                        user_prompt += f" (Background: {worker['backstory'][:200]}...)"
                    user_prompt += "\n"

                user_prompt += "\nCreate appropriate metrics to track this simulation's performance and outcomes."

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                )

                metrics_text = response.choices[0].message.content.strip()

                if "```json" in metrics_text:
                    metrics_text = (
                        metrics_text.split("```json")[1].split("```")[0].strip()
                    )
                elif "```" in metrics_text:
                    metrics_text = metrics_text.split("```")[1].split("```")[0].strip()

                try:
                    metrics = json.loads(metrics_text)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM response as JSON: {e}")
                    logger.error(f"Response was: {metrics_text}")
                    return {"error": f"Failed to parse LLM response: {e}"}

            except ImportError:
                return {
                    "error": "OpenAI library not installed. Run: pip install openai"
                }
            except Exception as e:
                logger.error(f"Error calling OpenAI API: {e}")
                return {"error": f"Failed to generate metrics with LLM: {str(e)}"}
        else:
            if not custom_metrics:
                return {"error": "No custom metrics provided and use_llm is false"}
            metrics = custom_metrics

        metrics_dir = Path.home() / ".autobox" / "config" / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)

        metrics_file_path = metrics_dir / f"{simulation_name}.json"
        with open(metrics_file_path, "w") as f:
            json.dump(metrics, f, indent=4)

        logger.info(f"Saved metrics config to {metrics_file_path}")

        return {
            "metrics": metrics,
            "metrics_path": str(metrics_file_path),
            "message": f"Metrics created and saved to {metrics_file_path}",
            "simulation_name": simulation_name,
        }

    async def _instruct_agent(
        self, simulation_id: str, agent_name: str, instruction: str
    ) -> str:
        try:
            container = self.docker_manager.client.containers.get(simulation_id)
            if container.status != "running":
                return f"Simulation {simulation_id} is not running"

            port = int(container.labels.get("autobox.api_port", "9000"))
            container_info = container.attrs
            ports = container_info.get("NetworkSettings", {}).get("Ports", {})

            port_key = f"{port}/tcp"
            if port_key in ports and ports[port_key]:
                host_port = ports[port_key][0]["HostPort"]
                host_ip = ports[port_key][0].get("HostIp", "localhost")
                if host_ip == "0.0.0.0":
                    import os

                    if os.path.exists("/.dockerenv"):
                        # We're in a container, need to use host gateway
                        # Try host.docker.internal first (works on Docker Desktop)
                        import socket

                        try:
                            socket.gethostbyname("host.docker.internal")
                            host_ip = "host.docker.internal"
                            logger.info(
                                "Using host.docker.internal for container-to-host communication"
                            )
                        except socket.gaierror:
                            try:
                                import subprocess

                                result = subprocess.run(
                                    ["ip", "route", "show", "default"],
                                    capture_output=True,
                                    text=True,
                                    timeout=1,
                                )
                                if result.returncode == 0 and result.stdout:
                                    parts = result.stdout.split()
                                    if (
                                        len(parts) > 2
                                        and parts[0] == "default"
                                        and parts[1] == "via"
                                    ):
                                        host_ip = parts[2]
                                        logger.info(
                                            f"Using Docker gateway IP: {host_ip}"
                                        )
                                    else:
                                        host_ip = "172.17.0.1"
                                else:
                                    host_ip = "172.17.0.1"
                            except Exception as e:
                                logger.warning(
                                    f"Failed to detect Docker gateway: {e}, using default 172.17.0.1"
                                )
                                host_ip = "172.17.0.1"
                    else:
                        host_ip = "localhost"

                import json

                import httpx

                async with httpx.AsyncClient() as client:
                    try:
                        url = f"http://{host_ip}:{host_port}/instructions/agents/{agent_name.lower()}"
                        logger.info(f"Sending instruction to: {url}")
                        response = await client.post(
                            url,
                            json={"instruction": instruction},
                            timeout=10.0,
                        )

                        if response.status_code in [200, 202]:
                            return json.dumps(
                                {
                                    "success": True,
                                    "message": f"Instruction sent to agent {agent_name}",
                                    "response": response.json()
                                    if response.text
                                    else None,
                                }
                            )
                        else:
                            return json.dumps(
                                {
                                    "success": False,
                                    "error": f"API returned status {response.status_code}",
                                    "details": response.text,
                                }
                            )
                    except Exception as e:
                        return json.dumps(
                            {
                                "success": False,
                                "error": f"Failed to send instruction: {str(e)}",
                            }
                        )

            networks = container_info.get("NetworkSettings", {}).get("Networks", {})
            for network_name, network_info in networks.items():
                ip_address = network_info.get("IPAddress")
                if ip_address:
                    import json

                    import httpx

                    async with httpx.AsyncClient() as client:
                        try:
                            response = await client.post(
                                f"http://{ip_address}:{port}/instructions/agents/{agent_name.lower()}",
                                json={"instruction": instruction},
                                timeout=10.0,
                            )

                            if response.status_code in [200, 202]:
                                return json.dumps(
                                    {
                                        "success": True,
                                        "message": f"Instruction sent to agent {agent_name}",
                                        "response": response.json()
                                        if response.text
                                        else None,
                                    }
                                )
                            else:
                                return json.dumps(
                                    {
                                        "success": False,
                                        "error": f"API returned status {response.status_code}",
                                        "details": response.text,
                                    }
                                )
                        except Exception:
                            pass

            return json.dumps(
                {"success": False, "error": "Could not connect to simulation API"}
            )

        except Exception as e:
            logger.error(f"Error instructing agent: {e}")
            return json.dumps({"success": False, "error": str(e)})

    async def _delete_simulation(self, simulation_name: str) -> Dict[str, Any]:
        """Delete a simulation configuration and its associated metrics files."""
        try:
            deleted_files = []
            errors = []

            config_extensions = [".json", ".toml"]
            config_deleted = False

            for ext in config_extensions:
                config_file = self.simulations_path / f"{simulation_name}{ext}"
                if config_file.exists():
                    try:
                        config_file.unlink()
                        deleted_files.append(str(config_file))
                        config_deleted = True
                        logger.info(f"Deleted simulation config: {config_file}")
                    except Exception as e:
                        errors.append(
                            f"Failed to delete config {config_file}: {str(e)}"
                        )
                        logger.error(f"Error deleting config {config_file}: {e}")

            if not config_deleted:
                errors.append(f"No simulation config found for '{simulation_name}'")

            metrics_file = self.metrics_path / f"{simulation_name}.json"
            if metrics_file.exists():
                try:
                    metrics_file.unlink()
                    deleted_files.append(str(metrics_file))
                    logger.info(f"Deleted metrics file: {metrics_file}")
                except Exception as e:
                    errors.append(f"Failed to delete metrics {metrics_file}: {str(e)}")
                    logger.error(f"Error deleting metrics {metrics_file}: {e}")
            else:
                logger.info(f"No metrics file found for '{simulation_name}'")

            running_sim = None
            for sim_id, status in self.simulations.items():
                if status.name == simulation_name and status.status == "running":
                    running_sim = sim_id
                    break

            result = {
                "simulation_name": simulation_name,
                "deleted_files": deleted_files,
                "success": len(deleted_files) > 0,
            }

            if errors:
                result["errors"] = errors

            if running_sim:
                result["warning"] = (
                    f"Simulation '{simulation_name}' is currently running with ID {running_sim}. Configuration deleted but container still active."
                )

            if not deleted_files and not errors:
                result["message"] = f"No files found for simulation '{simulation_name}'"
            elif deleted_files:
                result["message"] = (
                    f"Successfully deleted {len(deleted_files)} file(s) for simulation '{simulation_name}'"
                )

            return result

        except Exception as e:
            logger.error(f"Error deleting simulation {simulation_name}: {e}")
            return {
                "simulation_name": simulation_name,
                "success": False,
                "error": str(e),
            }

    async def run(self):
        from mcp.server import InitializationOptions
        from mcp.types import ServerCapabilities

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                initialization_options=InitializationOptions(
                    server_name="autobox-mcp",
                    server_version="0.1.0",
                    capabilities=ServerCapabilities(tools={}),
                ),
            )


def main():
    server = AutoboxMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
