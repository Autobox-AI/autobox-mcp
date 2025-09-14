# Docker Usage Guide for Autobox MCP Server

## Building the Image

```bash
# Build with default settings (image name: autobox-mcp:latest)
./bin/docker-build

# Build with custom name and tag
./bin/docker-build --name my-mcp --tag v1.0.0

# Build without cache
./bin/docker-build --no-cache

# Build for specific platform
./bin/docker-build --platform linux/amd64
```

## Running the MCP Server

### 1. Interactive Testing

Run the server interactively and send JSON-RPC commands:

```bash
docker run -it --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/.autobox:/root/.autobox \
  autobox-mcp:latest
```

Then send MCP protocol commands (JSON-RPC format):

```json
// Initialize
{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}

// Send initialized notification
{"jsonrpc":"2.0","method":"notifications/initialized"}

// List available tools
{"jsonrpc":"2.0","method":"tools/list","params":{},"id":2}

// Call a tool
{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_available_configs"},"id":3}
```

### 2. Automated Testing

Use the provided test scripts:

```bash
# Run automated test with proper MCP protocol flow
python test_mcp_proper.py

# Run interactive test with instructions
./test_mcp_interactive.sh

# Run simple automated test
./test_mcp_auto.sh
```

### 3. Integration with Claude Desktop

Add this configuration to your `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "autobox": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-v", "${HOME}/.autobox:/root/.autobox",
        "autobox-mcp:latest"
      ]
    }
  }
}
```

## Available MCP Tools

The server provides these tools:

1. **list_simulations** - List all simulations (running and completed)
2. **start_simulation** - Start a new simulation from a configuration file
3. **stop_simulation** - Stop a running simulation gracefully
4. **get_simulation_status** - Get detailed status of a specific simulation
5. **get_simulation_logs** - Get logs from a simulation container
6. **list_available_configs** - List all available simulation configuration templates
7. **get_simulation_metrics** - Get metrics from a running simulation
8. **create_simulation_config** - Create a new simulation configuration with AI assistance

## Docker Socket Access

The container needs access to the Docker socket to manage simulation containers:

- `-v /var/run/docker.sock:/var/run/docker.sock` - Allows the MCP server to create/manage Docker containers
- `-v ~/.autobox:/root/.autobox` - Persists configuration and simulation data

## Troubleshooting

### Container won't start
- Ensure Docker daemon is running
- Check if the image was built successfully: `docker images | grep autobox-mcp`

### MCP protocol errors
- Always send `initialize` request first
- Wait for initialization response before sending other commands
- Send `notifications/initialized` after successful initialization

### Permission errors
- Ensure Docker socket is accessible
- On Linux, you may need to run with `sudo` or add user to docker group

## Example: Running a Simulation

```bash
# 1. Start the container
docker run -it --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/.autobox:/root/.autobox \
  autobox-mcp:latest

# 2. Initialize MCP
{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}

# 3. Send initialized notification
{"jsonrpc":"2.0","method":"notifications/initialized"}

# 4. List available configs
{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_available_configs"},"id":2}

# 5. Start a simulation
{"jsonrpc":"2.0","method":"tools/call","params":{"name":"start_simulation","arguments":{"config_name":"summer_vacation"}},"id":3}

# 6. Check simulation status
{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_simulation_status","arguments":{"simulation_id":"<simulation-id-from-step-5>"}},"id":4}
```