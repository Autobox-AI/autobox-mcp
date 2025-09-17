import asyncio
import logging
import platform
from typing import Any, Dict, List, Optional

import docker
from docker.errors import NotFound

logger = logging.getLogger(__name__)


class DockerManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.image_name = "autobox-engine:latest"
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None

    async def list_running_simulations(self) -> List[Dict[str, str]]:
        if not self.client:
            return []

        try:
            containers = self.client.containers.list(
                filters={"label": "com.autobox.simulation=true"}
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
        if not self.client:
            raise RuntimeError("Docker client not initialized")

        try:
            import json
            import os
            from pathlib import Path

            config_name = Path(config_path).stem

            if not server_config_path:
                server_config_path = str(Path.home() / ".autobox/config/server.json")

            api_port = 9000
            try:
                with open(server_config_path, "r") as f:
                    server_config = json.load(f)
                    api_port = server_config.get("port", 9000)
                    logger.info(f"Using API port {api_port} from server config")
            except Exception as e:
                logger.warning(
                    f"Could not read server config, using default port 9000: {e}"
                )

            import socket

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", 0))
                host_port = s.getsockname()[1]
            logger.info(f"Allocated host port {host_port} for container")

            running_in_docker = (
                os.path.exists("/.dockerenv") or str(Path.home()) == "/root"
            )

            container_port = f"{api_port}/tcp"

            if running_in_docker:
                host_home = os.environ.get("HOST_HOME")

                if not host_home:
                    username = os.environ.get("HOST_USER", "root")

                    if platform.system() == "Darwin" or os.path.exists("/Users"):
                        host_home = f"/Users/{username}"
                    else:
                        host_home = f"/home/{username}"

                host_autobox_path = os.path.expanduser(f"{host_home}/.autobox")

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
                        "AUTOBOX_EXTERNAL_PORT": str(host_port),
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
                    ports={container_port: host_port},
                    name=f"autobox-sim-{asyncio.get_event_loop().time():.0f}",
                    labels={
                        "autobox.api_port": str(api_port),
                        "com.autobox.simulation": "true",
                        "com.autobox.name": config_name,
                        "com.autobox.config_path": str(config_path),
                        "com.autobox.created_at": str(asyncio.get_event_loop().time()),
                    },
                    remove=False,
                )
            else:
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
                        "AUTOBOX_EXTERNAL_PORT": str(host_port),
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
                    ports={container_port: host_port},
                    name=f"autobox-sim-{asyncio.get_event_loop().time():.0f}",
                    labels={
                        "com.autobox.simulation": "true",
                        "com.autobox.name": config_name,
                        "com.autobox.config_path": str(config_path),
                        "com.autobox.created_at": str(asyncio.get_event_loop().time()),
                    },
                    remove=False,
                )

            container.reload()
            port_info = container.attrs.get("NetworkSettings", {}).get("Ports", {})
            if container_port in port_info and port_info[container_port]:
                host_port = port_info[container_port][0]["HostPort"]
                logger.info(
                    f"Started simulation container: {container.short_id} with API on port {host_port}"
                )
            else:
                logger.info(f"Started simulation container: {container.short_id}")

            return container.short_id

        except Exception as e:
            logger.error(f"Error starting simulation: {e}")
            raise

    async def stop_simulation(self, container_id: str) -> bool:
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

    async def stop_all_simulations(self) -> Dict[str, Any]:
        if not self.client:
            return {"error": "Docker client not available", "stopped": [], "failed": []}

        stopped = []
        failed = []

        try:
            containers = self.client.containers.list(
                filters={"label": "com.autobox.simulation=true", "status": "running"}
            )

            for container in containers:
                container_id = container.id[:12]
                try:
                    container.stop(timeout=10)
                    container.remove()
                    stopped.append({"id": container_id, "name": container.name})
                    logger.info(f"Stopped simulation container: {container.name}")
                except Exception as e:
                    failed.append(
                        {"id": container_id, "name": container.name, "error": str(e)}
                    )
                    logger.error(f"Failed to stop container {container.name}: {e}")

            return {
                "stopped": stopped,
                "failed": failed,
                "total_stopped": len(stopped),
                "total_failed": len(failed),
            }

        except Exception as e:
            logger.error(f"Error listing/stopping containers: {e}")
            return {
                "error": f"Failed to stop all simulations: {str(e)}",
                "stopped": stopped,
                "failed": failed,
            }

    async def get_container_status(self, container_id: str) -> Optional[Dict]:
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
        if not self.client:
            return None

        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)

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

            memory_usage = stats["memory_stats"].get("usage", 0)
            memory_limit = stats["memory_stats"].get("limit", 0)
            memory_percent = (
                (memory_usage / memory_limit * 100) if memory_limit > 0 else 0
            )

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
        self, container_id: str, port: int = None
    ) -> Optional[Dict]:
        if not self.client:
            return None

        try:
            container = self.client.containers.get(container_id)

            if container.status != "running":
                return None

            if port is None:
                port = int(container.labels.get("autobox.api_port", "9000"))

            container_info = container.attrs
            ports = container_info.get("NetworkSettings", {}).get("Ports", {})

            port_key = f"{port}/tcp"
            if port_key in ports and ports[port_key]:
                host_port = ports[port_key][0]["HostPort"]
                host_ip = ports[port_key][0].get("HostIp", "localhost")
                if host_ip == "0.0.0.0":
                    host_ip = "localhost"

                import httpx

                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.get(
                            f"http://{host_ip}:{host_port}/status",
                            timeout=5.0,
                        )
                        if response.status_code == 200:
                            return response.json()
                    except Exception as e:
                        logger.warning(f"Failed to get status from API: {e}")

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

    async def get_simulation_api_metrics(
        self, container_id: str, port: int = None
    ) -> Optional[Dict]:
        if not self.client:
            return None

        try:
            container = self.client.containers.get(container_id)

            if container.status != "running":
                return None

            if port is None:
                port = int(container.labels.get("autobox.api_port", "9000"))

            container_info = container.attrs
            ports = container_info.get("NetworkSettings", {}).get("Ports", {})

            port_key = f"{port}/tcp"
            if port_key in ports and ports[port_key]:
                host_port = ports[port_key][0]["HostPort"]
                host_ip = ports[port_key][0].get("HostIp", "localhost")
                if host_ip == "0.0.0.0":
                    host_ip = "localhost"

                import httpx

                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.get(
                            f"http://{host_ip}:{host_port}/metrics",
                            timeout=5.0,
                        )
                        if response.status_code == 200:
                            return response.json()
                    except Exception as e:
                        logger.warning(f"Failed to get metrics from API: {e}")

            networks = container_info.get("NetworkSettings", {}).get("Networks", {})
            for network_name, network_info in networks.items():
                ip_address = network_info.get("IPAddress")
                if ip_address:
                    import httpx

                    async with httpx.AsyncClient() as client:
                        try:
                            response = await client.get(
                                f"http://{ip_address}:{port}/metrics",
                                timeout=5.0,
                            )
                            if response.status_code == 200:
                                return response.json()
                        except Exception:
                            pass

            return None
        except Exception as e:
            logger.error(f"Error getting API metrics: {e}")
            return None
