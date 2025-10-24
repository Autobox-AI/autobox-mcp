# Autobox MCP Server (TypeScript)

[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-blue.svg)](https://www.typescriptlang.org/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

A TypeScript implementation of the MCP (Model Context Protocol) server for managing Autobox AI simulations. This is a complete rewrite of the Python version with improved type safety, better performance, and unified stack consistency.

## Features

- 🚀 **Simulation Management**: Start, stop, and monitor AI simulations
- 🐳 **Docker Integration**: Each simulation runs in an isolated container
- 📊 **Real-time Monitoring**: Get status and logs from running simulations
- 🎯 **Configuration Management**: Create and validate simulation configs
- 🤖 **AI-Assisted Setup**: Generate simulation configurations with AI help
- 📝 **Type-Safe**: Full TypeScript implementation with Zod schemas
- ⚡ **Modern Stack**: Built with ES modules and latest Node.js features

## Prerequisites

1. **Node.js 18+**: Required for running the server
2. **Docker**: Must be installed and running
3. **OpenAI API Key**: Required for AI agent simulations

   ```bash
   export OPENAI_API_KEY=sk-your-key-here
   ```

4. **Autobox Engine TypeScript**: The engine Docker image must be built:

   ```bash
   cd ../autobox-engine-ts
   ./bin/docker-build
   ```

## Installation

```bash
# Clone and install dependencies
git clone https://github.com/margostino/autobox.git
cd autobox/autobox-mcp-ts
yarn install
```

## Development

```bash
# Run in development mode with auto-reload
yarn dev

# Build TypeScript
yarn build

# Run tests
yarn test

# Run tests with coverage
yarn test:coverage

# Lint code
yarn lint

# Format code
yarn format
```

## Production Setup

### For Claude Desktop App

1. **Build the Docker image:**

   ```bash
   ./bin/docker-build
   ```

2. **Edit Claude Desktop configuration:**

   ```bash
   open ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

3. **Add the Autobox MCP server to the config:**

   ```json
   {
     "mcpServers": {
       "autobox": {
         "command": "docker",
         "args": [
           "run", "-i", "--rm",
           "-e", "HOST_HOME=${HOME}",
           "-e", "HOST_USER=${USER}",
           "-e", "OPENAI_API_KEY=${OPENAI_API_KEY}",
           "-v", "/var/run/docker.sock:/var/run/docker.sock",
           "-v", "${HOME}/.autobox:/root/.autobox",
           "autobox-mcp:latest"
         ]
       }
     }
   }
   ```

4. **Restart Claude Desktop** (Cmd+Q and reopen)

### For Claude CLI

1. **Build the Docker image:**

   ```bash
   ./bin/docker-build
   ```

2. **Add to Claude CLI:**

   ```bash
   claude mcp add autobox -s user docker -- run -i --rm \
     -e HOST_HOME=$HOME \
     -e HOST_USER=$USER \
     -e OPENAI_API_KEY=$OPENAI_API_KEY \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -v ${HOME}/.autobox:/root/.autobox \
     autobox-mcp:latest
   ```

3. **Verify connection:**

   ```bash
   claude mcp list
   # Should show: autobox ... ✓ Connected
   ```

### Important Notes

- **OPENAI_API_KEY**: This environment variable is **required** and must be passed to the MCP container. The MCP forwards it to simulation containers so agents can communicate with OpenAI.
- **HOST_HOME**: Required for proper volume mounting when the MCP runs in Docker. Without this, config files won't be accessible to simulation containers.
- **HOST_USER**: Optional but recommended for proper file permissions.

### Troubleshooting

**Simulation fails with "ENOENT: no such file or directory" when loading configs:**
- Ensure `HOST_HOME` is set in the Docker command
- Verify `${HOME}/.autobox/config/simulations/` contains your simulation configs
- Check that the MCP container has access to `/var/run/docker.sock`

**Simulation fails with "401 You didn't provide an API key":**
- Ensure `OPENAI_API_KEY` is set in your environment before starting the MCP
- Verify the environment variable is being passed to the MCP container with `-e OPENAI_API_KEY`
- Check that your OpenAI API key is valid and has credits

**Cannot connect to Docker:**
- Ensure Docker is running
- Verify `/var/run/docker.sock` is mounted in the MCP container
- Check Docker permissions (user must be in `docker` group on Linux)

## Local Testing with JSON-RPC

You can test the MCP server locally by running it directly and sending JSON-RPC messages via stdin/stdout.

### 1. Run the Server Locally

**Development mode (with auto-reload):**

```bash
yarn dev
```

**Built version:**

```bash
yarn build
node dist/index.js
```

**Using Docker:**

```bash
./bin/docker-run
```

### 2. Send JSON-RPC Messages

The MCP server uses JSON-RPC 2.0 protocol over stdio. Each message must be on a single line.

#### Initialize the Connection

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0.0"}}}' | yarn dev
```

#### List Available Tools

```json
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
```

#### List Running Simulations

```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_simulations","arguments":{}}}
```

#### List Available Configs

```json
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"list_available_configs","arguments":{}}}
```

#### Start a Simulation

```json
{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"start_simulation","arguments":{"config_name":"gift_choice","daemon":false}}}
```

#### Get Simulation Status

```json
{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"get_simulation_status","arguments":{"simulation_id":"03a961047a33"}}}
```

#### Get Simulation Execution Status (from API)

```json
{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"get_simulation_execution_status","arguments":{"simulation_id":"03a961047a33"}}}
```

#### Get Simulation Metrics

```json
{"jsonrpc":"2.0","id":8,"method":"tools/call","params":{"name":"get_simulation_metrics","arguments":{"simulation_id":"03a961047a33","include_docker_stats":true}}}
```

#### Ping Simulation API

```json
{"jsonrpc":"2.0","id":9,"method":"tools/call","params":{"name":"ping_simulation","arguments":{"simulation_id":"abc123def456"}}}
```

#### Get Simulation Health

```json
{"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"get_simulation_health","arguments":{"simulation_id":"03a961047a33"}}}
```

#### Instruct Agent

```json
{"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"instruct_agent","arguments":{"simulation_id":"abc123def456","agent_name":"Alice","instruction":"Focus on being more creative"}}}
```

#### Abort Simulation

```json
{"jsonrpc":"2.0","id":12,"method":"tools/call","params":{"name":"abort_simulation","arguments":{"simulation_id":"abc123def456"}}}
```

#### Stop Simulation

```json
{"jsonrpc":"2.0","id":13,"method":"tools/call","params":{"name":"stop_simulation","arguments":{"simulation_id":"abc123def456"}}}
```

#### Get Simulation Logs

```json
{"jsonrpc":"2.0","id":14,"method":"tools/call","params":{"name":"get_simulation_logs","arguments":{"simulation_id":"abc123def456","tail":50}}}
```

### 3. Interactive Testing Script

Create a test script for interactive testing:

```bash
#!/bin/bash
# test-mcp.sh

# Build and run the server in the background
yarn build
node dist/index.js &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Send test messages
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0.0"}}}' | nc localhost 3000
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | nc localhost 3000
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_simulations","arguments":{}}}' | nc localhost 3000

# Cleanup
kill $SERVER_PID
```

### 4. Using the MCP Inspector

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) provides a visual interface for testing MCP servers:

```bash
# Install MCP Inspector globally
npm install -g @modelcontextprotocol/inspector

# Run the inspector with your MCP server
mcp-inspector node dist/index.js
```

Then open your browser to test the server interactively.

### 5. Testing with MCP Inspector (Recommended)

The MCP Inspector provides the easiest way to test your MCP server during development.

**Using TypeScript directly (no build required):**

```bash
npx @modelcontextprotocol/inspector tsx src/index.ts
```

This will:

- Start the MCP Inspector web interface
- Run your TypeScript source directly via `tsx`
- Open a browser at `http://localhost:5173`
- Provide a visual interface to test all tools interactively

**Using built JavaScript:**

```bash
npx @modelcontextprotocol/inspector node dist/index.js
```

**Advantages:**

- ✅ No need to build (`tsx` runs TypeScript directly)
- ✅ Visual interface for testing tools
- ✅ See requests/responses in real-time
- ✅ Test tool parameters with form validation
- ✅ View full JSON-RPC messages
- ✅ No manual JSON-RPC formatting required

**Quick test without prompts:**

```bash
npx -y @modelcontextprotocol/inspector tsx src/index.ts
```

### Notes

- The server communicates via **stdio** (stdin/stdout), not HTTP
- Each JSON-RPC message must be on a **single line**
- The `id` field is used to match requests with responses
- Docker must be running for simulation-related tools to work
- Set `OPENAI_API_KEY` environment variable before starting
- Set `LOG_LEVEL=debug` for verbose logging during testing

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
- `create_simulation_metrics` - Create metrics configuration with AI assistance
- `delete_simulation` - Delete a simulation configuration and its metrics files

### Advanced

- `instruct_agent` - Send instructions to agents in running simulations
- `stop_all_simulations` - Stop all running simulations at once

## Example Usage in Claude

```
"List all available simulation configs"
"Start the summer_vacation simulation"
"Show me the status of running simulations"
"Create a new simulation about negotiating a business deal"
"Get the logs from simulation abc123"
"Delete the test_simulation config and its metrics"
"Send an instruction to Alice in the running simulation"
```

## Architecture

```
autobox-mcp-ts/
├── src/
│   ├── config/         # Configuration management
│   ├── docker/         # Docker container management
│   ├── mcp/            # MCP server implementation
│   ├── types/          # TypeScript types and schemas
│   ├── utils/          # Utilities (logger, etc.)
│   └── index.ts        # Entry point
├── tests/
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
└── bin/                # Build and run scripts
```

## Type Safety

All configurations are validated using Zod schemas that match the autobox-engine-ts types:

```typescript
import { SimulationConfigSchema, type SimulationConfig } from './types';

// Validated at runtime
const config = SimulationConfigSchema.parse(jsonData);
```

## Differences from Python Version

1. **Type Safety**: Full TypeScript with Zod validation
2. **Modern Async**: Uses native Promises and async/await
3. **ES Modules**: Modern module system
4. **Shared Types**: Can share types with autobox-engine-ts
5. **Better Error Handling**: Strongly typed error responses
6. **Improved Logging**: Structured logging with log levels
7. **Testing**: Jest-based comprehensive test suite

## Troubleshooting

### MCP Server Not Connecting

1. **Check Docker:**

   ```bash
   docker ps
   docker images | grep autobox-mcp-ts
   ```

2. **Check Environment Variables:**

   ```bash
   echo $OPENAI_API_KEY
   ```

3. **Test Manually:**

   ```bash
   ./bin/docker-run
   ```

### Docker Issues

1. **Image not found:**

   ```bash
   cd ../autobox-engine-ts
   ./bin/docker-build
   ```

2. **Permission errors:**
   - Ensure Docker Desktop is running
   - On Linux: `sudo usermod -aG docker $USER`

## Development Tips

1. **Watch Mode**: Use `yarn dev` for auto-reload during development
2. **Type Checking**: Run `tsc --noEmit` to check types without building
3. **Debugging**: Set `LOG_LEVEL=debug` for verbose logging
4. **Testing**: Use `yarn test:watch` for continuous testing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run `yarn lint && yarn test`
5. Submit a pull request

## License

Apache License 2.0

## Support

- **Issues**: [GitHub Issues](https://github.com/margostino/autobox/issues)
- **Discussions**: [GitHub Discussions](https://github.com/margostino/autobox/discussions)

---

Built with ❤️ in TypeScript
