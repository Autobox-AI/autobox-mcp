#!/usr/bin/env python3
"""Manual testing script for MCP server interaction."""

import json
import subprocess
import sys
import os
from typing import Dict, Any, Optional


class MCPTester:
    """Manual MCP server tester."""

    def __init__(self, use_docker: bool = False):
        """Initialize the tester.

        Args:
            use_docker: If True, test through Docker container
        """
        self.use_docker = use_docker
        self.request_id = 0

    def next_id(self) -> int:
        """Get next request ID."""
        self.request_id += 1
        return self.request_id

    def send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a request to the MCP server.

        Args:
            request: The JSON-RPC request

        Returns:
            The response dict or None on error
        """
        request_json = json.dumps(request)
        print(f"\n→ Sending: {request_json}")

        if self.use_docker:
            cmd = [
                "docker", "run", "-i", "--rm",
                "-v", "/var/run/docker.sock:/var/run/docker.sock",
                "-v", f"{os.path.expanduser('~')}/.autobox:/root/.autobox",
                "autobox-mcp:latest"
            ]
        else:
            cmd = ["uv", "run", "python", "-m", "autobox.server"]

        try:
            result = subprocess.run(
                cmd,
                input=request_json,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.stdout:
                response = json.loads(result.stdout.strip().split('\n')[-1])
                print(f"← Response: {json.dumps(response, indent=2)}")
                return response

            if result.stderr:
                print(f"← Error: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("← Request timed out")
        except json.JSONDecodeError as e:
            print(f"← Invalid JSON response: {e}")
            print(f"  Raw output: {result.stdout}")
        except Exception as e:
            print(f"← Error: {e}")

        return None

    def test_initialize(self) -> bool:
        """Test initialization."""
        print("\n=== Testing Initialize ===")
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "mcp-tester",
                    "version": "1.0.0"
                }
            },
            "id": self.next_id()
        }

        response = self.send_request(request)
        return response and "result" in response

    def test_list_tools(self) -> bool:
        """Test listing tools."""
        print("\n=== Testing List Tools ===")
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": self.next_id()
        }

        response = self.send_request(request)
        if response and "result" in response and "tools" in response["result"]:
            tools = response["result"]["tools"]
            print(f"\nFound {len(tools)} tools:")
            for tool in tools:
                print(f"  • {tool['name']}: {tool.get('description', 'No description')}")
            return True
        return False

    def test_call_tool(self, tool_name: str, **params) -> bool:
        """Test calling a specific tool.

        Args:
            tool_name: Name of the tool to call
            **params: Tool parameters

        Returns:
            True if successful
        """
        print(f"\n=== Testing Tool: {tool_name} ===")
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                **params
            },
            "id": self.next_id()
        }

        response = self.send_request(request)
        return response and "result" in response

    def run_interactive(self):
        """Run interactive testing session."""
        print("\n" + "="*50)
        print("MCP Server Interactive Tester")
        print("="*50)

        mode = "Docker" if self.use_docker else "Direct"
        print(f"Mode: {mode}")

        # Initialize first
        if not self.test_initialize():
            print("\n❌ Initialization failed")
            return

        print("\n✅ Initialization successful")

        # List tools
        if not self.test_list_tools():
            print("\n❌ Failed to list tools")
            return

        # Interactive loop
        while True:
            print("\n" + "-"*50)
            print("Options:")
            print("1. List simulations")
            print("2. List available configs")
            print("3. Get simulation status")
            print("4. Get simulation logs")
            print("5. Get simulation metrics")
            print("6. Custom tool call")
            print("0. Exit")

            choice = input("\nSelect option: ").strip()

            if choice == "0":
                break
            elif choice == "1":
                self.test_call_tool("list_simulations")
            elif choice == "2":
                self.test_call_tool("list_available_configs")
            elif choice == "3":
                sim_id = input("Enter simulation ID: ").strip()
                self.test_call_tool("get_simulation_status", simulation_id=sim_id)
            elif choice == "4":
                sim_id = input("Enter simulation ID: ").strip()
                tail = input("Number of lines (default 100): ").strip()
                tail = int(tail) if tail else 100
                self.test_call_tool("get_simulation_logs",
                                  simulation_id=sim_id, tail=tail)
            elif choice == "5":
                sim_id = input("Enter simulation ID: ").strip()
                self.test_call_tool("get_simulation_metrics",
                                  simulation_id=sim_id,
                                  include_docker_stats=True)
            elif choice == "6":
                tool_name = input("Tool name: ").strip()
                params_str = input("Parameters (JSON): ").strip()
                try:
                    params = json.loads(params_str) if params_str else {}
                    self.test_call_tool(tool_name, **params)
                except json.JSONDecodeError:
                    print("Invalid JSON parameters")
            else:
                print("Invalid option")

        print("\n👋 Goodbye!")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test MCP server manually")
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Test through Docker container"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run interactive session"
    )

    args = parser.parse_args()

    tester = MCPTester(use_docker=args.docker)

    if args.interactive:
        tester.run_interactive()
    else:
        # Run basic tests
        success = True

        if not tester.test_initialize():
            print("\n❌ Initialize failed")
            success = False
        else:
            print("\n✅ Initialize passed")

        if not tester.test_list_tools():
            print("\n❌ List tools failed")
            success = False
        else:
            print("\n✅ List tools passed")

        if success:
            # Test a simple tool call
            if tester.test_call_tool("list_available_configs"):
                print("\n✅ Tool call passed")
            else:
                print("\n❌ Tool call failed")
                success = False

        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()