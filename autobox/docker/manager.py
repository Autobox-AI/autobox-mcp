"""Docker container management for Autobox simulations."""

import asyncio
import logging
from typing import Dict, List, Optional

import docker
from docker.errors import NotFound

logger = logging.getLogger(__name__)


class DockerManager:
    """Manages Docker containers for Autobox simulations."""

    def __init__(self):
        try:
            self.client = docker.from_env()
            self.image_name = "autobox-engine:latest"
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None

    async def list_running_simulations(self) -> List[Dict[str, str]]:
        """List all running Autobox simulation containers."""
        if not self.client:
            return []

        try:
            containers = self.client.containers.list(
                filters={"ancestor": self.image_name}
            )
            return [
                {
                    "id": container.short_id,
                    "name": container.name,
                    "status": container.status,
                    "created": container.attrs["Created"],
                }
                for container in containers
            ]
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return []

    async def start_simulation(
        self, config_path: str, metrics_path: str, server_config_path: str = None
    ) -> Optional[str]:
        """Start a new simulation container."""
        if not self.client:
            raise RuntimeError("Docker client not initialized")

        try:
            import os
            from pathlib import Path

            # Prepare server config path
            if not server_config_path:
                server_config_path = str(Path.home() / ".autobox/config/server.json")

            # Check if we're running inside Docker
            # When MCP server runs in Docker, the config files are in /root/.autobox
            # But we need to mount from the host's actual path
            running_in_docker = (
                os.path.exists("/.dockerenv") or str(Path.home()) == "/root"
            )

            if running_in_docker:
                # Inside Docker container - we're running Docker-in-Docker
                # The Docker daemon is on the host, so we need HOST paths for volumes

                # Try to detect the actual host user's home directory
                # This is tricky - we need to pass this as an environment variable
                host_home = os.environ.get("HOST_HOME")

                if not host_home:
                    # Try to guess based on common patterns
                    # On Mac, it's usually /Users/username
                    # On Linux, it's usually /home/username
                    import platform

                    # Get username from environment or use 'root'
                    username = os.environ.get("HOST_USER", "root")

                    if platform.system() == "Darwin" or os.path.exists("/Users"):
                        host_home = f"/Users/{username}"
                    else:
                        host_home = f"/home/{username}"

                # For the case of Martin's setup specifically
                # TODO: This should be passed as environment variable
                if not os.environ.get("HOST_HOME"):
                    host_home = "~/"

                host_autobox_path = f"{host_home}/.autobox"

                container = self.client.containers.run(
                    self.image_name,
                    command=[
                        "--config",
                        f"/app/configs/simulations/{config_path.split('/')[-1]}",
                        "--metrics",
                        f"/app/configs/metrics/{metrics_path.split('/')[-1]}",
                        "--server",
                        f"/app/configs/server/{server_config_path.split('/')[-1]}"
                        if server_config_path
                        else "",
                    ],
                    detach=True,
                    environment={
                        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
                        "OBJC_DISABLE_INITIALIZE_FORK_SAFETY": "TRUE",
                        "PYTHONUNBUFFERED": "1",
                    },
                    volumes={
                        f"{host_autobox_path}/config/simulations": {
                            "bind": "/app/configs/simulations",
                            "mode": "ro",
                        },
                        f"{host_autobox_path}/config/metrics": {
                            "bind": "/app/configs/metrics",
                            "mode": "ro",
                        },
                        f"{host_autobox_path}/config": {
                            "bind": "/app/configs/server",
                            "mode": "ro",
                        },
                    },
                    name=f"autobox-sim-{asyncio.get_event_loop().time():.0f}",
                    remove=False,
                )
            else:
                # Running natively, use normal volume mounts
                container = self.client.containers.run(
                    self.image_name,
                    command=[
                        "--config",
                        f"/app/configs/simulations/{config_path.split('/')[-1]}",
                        "--metrics",
                        f"/app/configs/metrics/{metrics_path.split('/')[-1]}",
                        "--server",
                        f"/app/configs/server/{server_config_path.split('/')[-1]}",
                    ],
                    detach=True,
                    environment={
                        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
                        "OBJC_DISABLE_INITIALIZE_FORK_SAFETY": "TRUE",
                        "PYTHONUNBUFFERED": "1",
                    },
                    volumes={
                        str(Path.home() / ".autobox/config/simulations"): {
                            "bind": "/app/configs/simulations",
                            "mode": "ro",
                        },
                        str(Path.home() / ".autobox/config/metrics"): {
                            "bind": "/app/configs/metrics",
                            "mode": "ro",
                        },
                        str(Path.home() / ".autobox/config"): {
                            "bind": "/app/configs/server",
                            "mode": "ro",
                        },
                    },
                    name=f"autobox-sim-{asyncio.get_event_loop().time():.0f}",
                    remove=False,
                )

            logger.info(f"Started simulation container: {container.short_id}")
            return container.short_id

        except Exception as e:
            logger.error(f"Error starting simulation: {e}")
            raise

    async def stop_simulation(self, container_id: str) -> bool:
        """Stop a running simulation container."""
        if not self.client:
            return False

        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=10)
            container.remove()
            logger.info(f"Stopped simulation container: {container_id}")
            return True
        except NotFound:
            logger.warning(f"Container not found: {container_id}")
            return False
        except Exception as e:
            logger.error(f"Error stopping container: {e}")
            return False

    async def get_container_status(self, container_id: str) -> Optional[Dict]:
        """Get the status of a container."""
        if not self.client:
            return None

        try:
            container = self.client.containers.get(container_id)
            return {
                "id": container.short_id,
                "name": container.name,
                "status": container.status,
                "running": container.status == "running",
            }
        except NotFound:
            return None
        except Exception as e:
            logger.error(f"Error getting container status: {e}")
            return None

    async def get_logs(self, container_id: str, tail: int = 100) -> Optional[str]:
        """Get logs from a container."""
        if not self.client:
            return None

        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=True).decode("utf-8")
            return logs
        except NotFound:
            return None
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return None

    async def get_container_stats(self, container_id: str) -> Optional[Dict]:
        """Get Docker container statistics."""
        if not self.client:
            return None

        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)

            # Calculate CPU percentage
            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = (
                stats["cpu_stats"]["system_cpu_usage"]
                - stats["precpu_stats"]["system_cpu_usage"]
            )
            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * 100.0

            # Calculate memory usage
            memory_usage = stats["memory_stats"].get("usage", 0)
            memory_limit = stats["memory_stats"].get("limit", 0)
            memory_percent = (
                (memory_usage / memory_limit * 100) if memory_limit > 0 else 0
            )

            # Network I/O
            network_rx = 0
            network_tx = 0
            if "networks" in stats:
                for interface in stats["networks"].values():
                    network_rx += interface.get("rx_bytes", 0)
                    network_tx += interface.get("tx_bytes", 0)

            return {
                "cpu_percent": round(cpu_percent, 2),
                "memory_usage_mb": round(memory_usage / 1024 / 1024, 2),
                "memory_limit_mb": round(memory_limit / 1024 / 1024, 2),
                "memory_percent": round(memory_percent, 2),
                "network_rx_mb": round(network_rx / 1024 / 1024, 2),
                "network_tx_mb": round(network_tx / 1024 / 1024, 2),
            }
        except NotFound:
            return None
        except Exception as e:
            logger.error(f"Error getting container stats: {e}")
            return None

    async def get_simulation_api_status(
        self, container_id: str, port: int = 9000
    ) -> Optional[Dict]:
        """Get simulation status from the container's API."""
        if not self.client:
            return None

        try:
            container = self.client.containers.get(container_id)

            if container.status != "running":
                return None

            container_info = container.attrs
            networks = container_info.get("NetworkSettings", {}).get("Networks", {})

            for network_name, network_info in networks.items():
                ip_address = network_info.get("IPAddress")
                if ip_address:
                    import httpx

                    async with httpx.AsyncClient() as client:
                        try:
                            response = await client.get(
                                f"http://{ip_address}:{port}/status",
                                timeout=5.0,
                            )
                            if response.status_code == 200:
                                return response.json()
                        except Exception:
                            pass

            return None
        except Exception as e:
            logger.error(f"Error getting API status: {e}")
            return None
