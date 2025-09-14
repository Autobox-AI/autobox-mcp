# Autobox MCP Server

[![Tests](https://github.com/Autobox-AI/autobox-mcp/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/Autobox-AI/autobox-mcp/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/Autobox-AI/autobox-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/Autobox-AI/autobox-mcp)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

An MCP (Model Context Protocol) server for managing Autobox AI simulations.

## Features

- 🚀 **Simulation Management**: Start, stop, and monitor AI simulations
- 🐳 **Docker Integration**: Each simulation runs in an isolated container
- 📊 **Real-time Monitoring**: Get status and logs from running simulations
- 🎯 **Configuration Management**: Create and validate simulation configs
- 🤖 **AI-Assisted Setup**: Generate simulation configurations with AI help

## Quick Install

```bash
# Set your OpenAI API key first
export OPENAI_API_KEY=sk-your-key-here

# One-liner installation
git clone https://github.com/Autobox-AI/autobox-mcp.git && cd autobox-mcp && \
docker build -t autobox-mcp . && \
claude mcp add autobox -s user docker -- run -i --rm -e HOST_HOME=$HOME -e HOST_USER=$USER -e OPENAI_API_KEY=$OPENAI_API_KEY -v /var/run/docker.sock:/var/run/docker.sock -v ${HOME}/.autobox:/root/.autobox autobox-mcp
```

After installation, restart Claude Desktop and you're ready to go!

**Verify Installation:** In Claude, ask "Can you list the available Autobox MCP tools?" - Claude should respond with 8 available tools.

## Prerequisites

1. **Docker**: Must be installed and running
2. **OpenAI API Key**: Required for AI agent simulations
   ```bash
   export OPENAI_API_KEY=sk-your-key-here
   ```
3. **Autobox Engine**: The engine Docker image must be built:
   ```bash
   cd /path/to/autobox-engine
   ./bin/docker-build
   ```

## Setup Instructions

### For Claude Desktop App

1. **Edit Claude Desktop configuration:**
   ```bash
   # Open the config file
   open ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Add the Autobox MCP server to the config:**
   ```json
   {
     "mcpServers": {
       "autobox": {
         "command": "/path/to/autobox-mcp/run_mcp_server.sh",
         "args": [],
         "env": {
           "OPENAI_API_KEY": "${OPENAI_API_KEY}"
         }
       }
     }
   }
   ```

3. **Create the wrapper script** (if not exists):
   ```bash
   cat > run_mcp_server.sh << 'EOF'
   #!/bin/bash
   cd /path/to/autobox-mcp
   exec uv run autobox-mcp
   EOF
   chmod +x run_mcp_server.sh
   ```

4. **Restart Claude Desktop** (Cmd+Q and reopen)

### For Claude CLI

1. **Build the Docker image:**
   ```bash
   cd /path/to/autobox-mcp
   docker build -t autobox-mcp .
   ```

2. **Add to Claude CLI:**
   ```bash
   claude mcp add autobox -s user docker -- run -i --rm \
     -e HOST_HOME=$HOME \
     -e HOST_USER=$USER \
     -e OPENAI_API_KEY=$OPENAI_API_KEY \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -v ${HOME}/.autobox:/root/.autobox \
     autobox-mcp
   ```

3. **Verify connection:**
   ```bash
   claude mcp list
   # Should show: autobox ... ✓ Connected
   ```

4. **Use in Claude CLI:**
   ```bash
   # Start a new chat
   claude

   # Use /mcp command to see available servers
   /mcp

   # Or directly ask about Autobox
   "List available Autobox simulation configs"
   ```

5. **To uninstall:**
   ```bash
   claude mcp remove autobox
   ```

### For Cursor IDE

Cursor doesn't natively support MCP servers, but you can use the Autobox CLI directly:

1. **Install Autobox CLI** (if available):
   ```bash
   # Refer to autobox-cli repository
   go install github.com/Autobox-AI/autobox-cli@latest
   ```

2. **Use via terminal in Cursor:**
   ```bash
   # List simulations
   autobox list

   # Run simulation
   autobox run summer_vacation

   # Get status
   autobox status <container-id>
   ```

3. **Alternative: Use the MCP server via API**

   You can create a local API wrapper that exposes the MCP tools as HTTP endpoints for Cursor to use.

## Available Tools

### Simulation Management
- `list_simulations` - List all simulations (running and completed)
- `start_simulation` - Start a new simulation from config
- `stop_simulation` - Stop a running simulation
- `get_simulation_status` - Get detailed status of a simulation
- `get_simulation_logs` - Retrieve logs from a simulation
- `get_simulation_metrics` - Get real-time metrics (progress, agent stats, Docker stats)

### Configuration
- `list_available_configs` - List available simulation templates
- `create_simulation_config` - Create new simulation config with AI assistance

## Example Usage in Claude

```
"List all available simulation configs"
"Start the summer_vacation simulation"
"Show me the status of running simulations"
"Create a new simulation about negotiating a business deal"
"Get the logs from simulation abc123"
```

## Troubleshooting

### MCP Server Not Connecting

1. **"Failed to connect" error:**
   - Ensure the wrapper script has correct paths
   - Check OPENAI_API_KEY is set: `echo $OPENAI_API_KEY`
   - Verify Docker is running: `docker ps`
   - Test manually: `./run_mcp_server.sh < /dev/null`

2. **"Server not found" in Claude:**
   - Restart Claude after config changes
   - Check config file syntax is valid JSON
   - For CLI: Use `--scope user` for global access

3. **"Invalid request parameters" error:**
   - Update to latest MCP version: `uv sync`
   - Ensure `InitializationOptions` are properly set in server.py

### Docker Issues

1. **"Image not found" error:**
   ```bash
   cd /path/to/autobox-engine
   ./bin/docker-build
   ```

2. **"Cannot connect to Docker" error:**
   - Start Docker Desktop
   - Check Docker daemon: `docker version`
   - On Linux, add user to docker group: `sudo usermod -aG docker $USER`

3. **Permission errors:**
   - Ensure Docker Desktop is running
   - Check logs: `claude mcp logs autobox`

## Development

### Building the Docker Image

```bash
# Build with default settings
./bin/docker-build

# Build with custom tag
./bin/docker-build --tag v1.0.0

# Build without cache
./bin/docker-build --no-cache

# Build for specific platform
./bin/docker-build --platform linux/amd64
```

### Running Tests

```bash
# Run all tests
./bin/test

# Run unit tests only
./bin/test-unit

# Run integration tests
./bin/test-it

# Run with coverage
./bin/test-cov
```

### Docker Socket Access

The MCP server requires access to the Docker socket to manage simulation containers:
- `-v /var/run/docker.sock:/var/run/docker.sock` - Allows creating/managing Docker containers
- `-v ${HOME}/.autobox:/root/.autobox` - Persists configuration and simulation data

### Manual Testing

```bash
# Test MCP server manually
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' | uv run autobox-mcp
```

## Architecture

```
autobox-mcp/
├── autobox/
│   ├── server.py          # Main MCP server
│   ├── docker/            # Docker container management
│   └── config/            # Configuration management
├── tests/
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
└── bin/                   # Utility scripts
```

## License

MIT