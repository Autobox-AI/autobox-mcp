# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Autobox MCP Server is a Model Context Protocol (MCP) server that enables AI assistants like Claude to manage and interact with Autobox AI simulations through Docker containers. It provides tools for starting, stopping, monitoring simulations, and managing simulation configurations.

## Common Development Commands

### Development Setup
```bash
# Install dependencies using uv (Python 3.13+ required)
uv sync

# Build Docker image for deployment
./bin/docker-build

# Build with custom settings
./bin/docker-build --name my-mcp --tag v1.0.0
./bin/docker-build --platform linux/amd64
./bin/docker-build --no-cache
```

### Testing
```bash
# Run all tests
./bin/test

# Run specific test suites
./bin/test-unit           # Unit tests only
./bin/test-it             # Integration tests
./bin/test-cov            # Tests with coverage report

# Run tests directly with pytest
uv run pytest tests/ -v --tb=short
uv run pytest tests/unit -v
uv run pytest -m docker   # Tests requiring Docker
```

### MCP Server Testing
```bash
# Manual interactive testing
./bin/test-mcp-interactive.sh

# Docker-based testing
./bin/test-mcp-docker.sh

# Manual protocol testing
./bin/test-mcp-manual
```

### Running the Server
```bash
# Run directly (for development)
uv run autobox-mcp

# Run in Docker container (production mode)
docker run -it --rm \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ${HOME}/.autobox:/root/.autobox \
  autobox-mcp
```

## High-Level Architecture

### Core Components

**MCP Server (`autobox/server.py`):**
- `AutoboxMCPServer` class orchestrates all MCP functionality
- Handles tool registration and request routing
- Manages simulation lifecycle through Docker containers
- Maintains simulation state and configuration

**Docker Management (`autobox/docker/manager.py`):**
- `DockerManager` class interfaces with Docker daemon
- Creates and manages simulation containers with proper isolation
- Handles container lifecycle (start, stop, logs, metrics)
- Monitors container health and API status

**Data Models (`autobox/models/schemas.py`):**
- Pydantic models for type-safe data validation
- Defines simulation configurations, status, and metrics structures

### MCP Protocol Flow

The server implements the Model Context Protocol:
1. **Initialization**: Server receives `initialize` request, responds with capabilities
2. **Tool Discovery**: Client calls `tools/list` to discover available tools
3. **Tool Invocation**: Client calls `tools/call` with tool name and parameters
4. **Response**: Server executes tool and returns results

### Tool Architecture

Eight tools provide comprehensive simulation management:

**Simulation Control:**
- `list_simulations` - Lists all simulations with status
- `start_simulation` - Launches new simulation container
- `stop_simulation` - Gracefully stops running simulation
- `get_simulation_status` - Retrieves detailed status information

**Monitoring:**
- `get_simulation_logs` - Fetches container logs
- `get_simulation_metrics` - Returns real-time metrics (progress, agents, Docker stats)

**Configuration:**
- `list_available_configs` - Shows available simulation templates
- `create_simulation_config` - AI-assisted config generation

### Docker Integration

Each simulation runs in an isolated Docker container:
- Container name: `autobox-<simulation_name>-<timestamp>`
- Network isolation with port mapping for API access
- Volume mounts for config and metrics persistence
- Environment variable injection for OpenAI API key

### File System Structure

```
~/.autobox/                     # User's Autobox directory
├── simulations/                # Custom simulation configs
├── metrics/                    # Simulation metrics output
└── server_config.json          # Server configuration

/app/                           # Inside MCP container
├── autobox/                    # Python package
│   ├── server.py              # Main MCP server
│   ├── docker/                # Docker management
│   └── models/                # Data models
└── tests/                      # Test suites
```

### Key Integration Points

**Docker Socket Mounting:**
The MCP server requires Docker socket access (`/var/run/docker.sock`) to manage simulation containers. This enables container-in-container operations.

**Configuration Management:**
- Built-in configs stored in autobox-engine image
- Custom configs saved to `~/.autobox/simulations/`
- TOML format for simulation definitions

**Metrics Collection:**
- Simulations write metrics to mounted volume
- Server reads metrics from `~/.autobox/metrics/<container_id>/`
- Real-time progress tracking via API polling

**Environment Variables:**
- `OPENAI_API_KEY`: Required for AI agent functionality
- `HOST_HOME`: User's home directory for path resolution
- `HOST_USER`: Username for proper file ownership

## Testing Strategy

### Test Organization
- `tests/unit/` - Fast, isolated component tests
- `tests/integration/` - Docker and system integration tests
- Markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.docker`

### MCP Protocol Testing
The server must handle the complete MCP handshake:
1. Initialize with protocol version and capabilities
2. Send `initialized` notification
3. Respond to `tools/list` requests
4. Process `tools/call` with proper error handling

### Docker Testing
Integration tests verify:
- Container creation and lifecycle management
- Volume mounting and configuration passing
- Log retrieval and metrics collection
- Proper cleanup on simulation stop

## Development Patterns

### Async/Await Architecture
All MCP handlers use async/await for non-blocking operations, especially critical for Docker operations and API calls.

### Error Handling
- Structured error responses with MCP error codes
- Graceful degradation when Docker unavailable
- Comprehensive logging for debugging

### Type Safety
- Pydantic models for all data structures
- Type hints throughout the codebase
- Runtime validation of tool parameters

### Configuration Validation
- TOML configs validated before container launch
- AI-generated configs checked for required fields
- Safe path handling for mounted volumes