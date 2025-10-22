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
