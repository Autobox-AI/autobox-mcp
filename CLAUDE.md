# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

`autobox-mcp` (previously `autobox-mcp-ts`) is a TypeScript implementation of a Model Context Protocol (MCP) server that enables Claude Desktop and Claude CLI to manage Autobox AI simulations. This is part of the larger Autobox multi-repository monorepo.

**Key Technology Stack:**
- TypeScript 5.7 with strict type checking
- Node.js 18+ with ES modules (Node16 module resolution)
- Yarn 4 (Plug'n'Play) for package management
- Zod for runtime schema validation
- Dockerode for Docker container management
- @modelcontextprotocol/sdk for MCP protocol
- Jest with ts-jest for testing

## Essential Commands

### Development

```bash
yarn dev                    # Run with auto-reload (tsx watch)
yarn build                  # Compile TypeScript to dist/
yarn start                  # Run compiled JavaScript
yarn test                   # Run all tests
yarn test:watch             # Run tests in watch mode
yarn test:coverage          # Run tests with coverage report
yarn lint                   # Lint TypeScript code
yarn lint:fix               # Fix linting issues
yarn format                 # Format code with Prettier
```

### Docker Operations

```bash
./bin/docker-build          # Build TypeScript + Docker image
./bin/docker-run            # Run MCP server in Docker container
```

### Testing with MCP Inspector (Recommended)

```bash
# Run without building (TypeScript directly via tsx)
npx @modelcontextprotocol/inspector tsx src/index.ts

# Or with built JavaScript
npx @modelcontextprotocol/inspector node dist/index.js
```

Opens a web interface at `http://localhost:5173` for interactive tool testing.

### Running Individual Tests

```bash
# Run specific test file
yarn test tests/unit/docker/manager.test.ts

# Run tests matching pattern
yarn test --testNamePattern="should start simulation"

# Run tests in specific directory
yarn test tests/integration/
```

## Architecture

### High-Level Component Structure

```
src/
├── index.ts              # Entry point: initializes MCP server
├── mcp/
│   ├── server.ts         # AutoboxMCPServer class (main MCP logic)
│   ├── tools.ts          # Tool definitions (18 MCP tools)
│   └── metricsGenerator.ts  # AI-assisted metrics generation
├── docker/
│   └── manager.ts        # DockerManager class (container lifecycle)
├── config/
│   └── manager.ts        # ConfigManager (read/write/validate configs)
├── types/
│   ├── simulation.ts     # Zod schemas & TypeScript types
│   └── index.ts          # Type exports
└── utils/
    └── logger.ts         # Structured logging
```

### Key Design Patterns

1. **MCP Protocol Communication**
   - Server communicates via stdio (JSON-RPC 2.0)
   - Tools are stateless functions called by Claude
   - All responses follow MCP SDK conventions

2. **Docker Container Lifecycle**
   - Each simulation runs in an isolated `autobox-engine` container
   - Containers are managed through Dockerode
   - Dynamic port allocation (9000+) for simulation APIs
   - Volume mounting for config access (`~/.autobox/config/simulations/`)

3. **Type Safety with Runtime Validation**
   - Zod schemas define both TypeScript types and runtime validation
   - All configs validated before passing to Docker containers
   - Schemas match autobox-engine-ts expectations

4. **Configuration Management**
   - Simulation configs stored in `~/.autobox/config/simulations/`
   - Metrics configs in `~/.autobox/config/metrics/`
   - AI-assisted config generation using OpenAI
   - Configs can be JSON or TOML (engine supports both)

### Critical Integration Points

**Environment Variables (Required):**
- `OPENAI_API_KEY` - Forwarded to simulation containers for agent LLM calls
- `HOST_HOME` - Required when MCP runs in Docker (for volume mounting)
- `HOST_USER` - Optional, for proper file permissions

**Docker Socket Access:**
- MCP must access `/var/run/docker.sock` to manage containers
- In Docker: `-v /var/run/docker.sock:/var/run/docker.sock`

**Volume Mounts:**
- `${HOME}/.autobox` must be accessible to both MCP and simulation containers
- MCP reads configs, engine containers read them at startup

### MCP Tool Categories

**Simulation Lifecycle (8 tools):**
- `list_simulations`, `start_simulation`, `stop_simulation`, `stop_all_simulations`
- `get_simulation_status`, `get_simulation_logs`, `get_simulation_metrics`
- `abort_simulation`

**Configuration Management (4 tools):**
- `list_available_configs`, `create_simulation_config`
- `create_simulation_metrics`, `delete_simulation`

**Runtime Control (3 tools):**
- `instruct_agent` - Send instructions to agents during simulation
- `ping_simulation`, `get_simulation_health` - Health checks

**API Inspection (3 tools):**
- `get_simulation_execution_status`, `get_simulation_info`
- `get_simulation_api_spec`

### Build and Packaging

**Build Process (`./bin/docker-build`):**
1. Compile TypeScript: `yarn build` → `dist/`
2. Build Docker image with compiled code
3. Image includes docker-cli for container management
4. Uses Yarn 4 PnP (Plug'n'Play) in container

**Docker Image Details:**
- Base: `node:18-alpine`
- Includes: docker-cli, Yarn 4, compiled dist/
- Entrypoint: `yarn node dist/index.js`
- Requires: `/var/run/docker.sock` mount

## Testing Strategy

### Test Organization

```
tests/
├── unit/               # Isolated component tests
│   ├── config/        # ConfigManager tests
│   ├── docker/        # DockerManager tests
│   └── mcp/           # MCP server tests
└── integration/       # End-to-end tests with Docker
```

### Jest Configuration Notes

- Uses `ts-jest` with ESM preset
- ES modules enabled (`extensionsToTreatAsEsm: ['.ts']`)
- Coverage collected from `src/**/*.ts`
- Test files: `**/*.test.ts` or `**/*.spec.ts`

### Running Tests Effectively

```bash
# Fast feedback loop
yarn test:watch

# Coverage to identify untested code
yarn test:coverage

# Integration tests (requires Docker)
yarn test tests/integration/

# Debug specific test
node --inspect-brk node_modules/.bin/jest tests/unit/docker/manager.test.ts
```

## Common Development Patterns

### Adding a New MCP Tool

1. Add tool definition to `src/mcp/tools.ts` (name, description, inputSchema)
2. Implement handler in `AutoboxMCPServer.setupToolHandlers()` in `src/mcp/server.ts`
3. Add Zod schema if new types are needed in `src/types/`
4. Write unit tests in `tests/unit/mcp/`
5. Update README.md tool list

### Modifying Simulation Config Schema

1. Update Zod schema in `src/types/simulation.ts`
2. TypeScript types auto-infer from schema
3. Ensure compatibility with autobox-engine-ts schemas
4. Test with `SimulationConfigSchema.parse(testData)`

### Docker Manager Operations

All Docker interactions go through `DockerManager`:
- `startSimulation()` - Creates and starts container
- `stopSimulation()` - Gracefully stops container
- `getSimulationStatus()` - Queries container state
- `getSimulationLogs()` - Retrieves container logs
- `listSimulations()` - Lists all autobox containers

## Dependencies on Other Autobox Components

**Critical Dependency:**
- **autobox-engine-ts** Docker image must exist (`autobox-engine:latest`)
- Built from `../autobox-engine-ts` via `./bin/docker-build`
- MCP starts this image for each simulation

**Shared Contracts:**
- Simulation config schema must match engine expectations
- API endpoints (`/health`, `/status`, `/agents/instruct`) defined by engine
- Metrics structure defined by engine's FastAPI server

## Troubleshooting Guide

**"Cannot connect to Docker daemon":**
- Ensure Docker Desktop is running
- Check `/var/run/docker.sock` permissions
- On Linux: `sudo usermod -aG docker $USER` and re-login

**"No such file or directory" loading configs:**
- Set `HOST_HOME` environment variable when running MCP in Docker
- Verify `~/.autobox/config/simulations/` exists and contains configs
- Check volume mount syntax in Docker run command

**"401 You didn't provide an API key":**
- Set `OPENAI_API_KEY` before starting MCP
- Verify it's passed to Docker: `-e OPENAI_API_KEY=${OPENAI_API_KEY}`
- Check OpenAI API key validity at platform.openai.com

**MCP tools not appearing in Claude:**
- Rebuild Docker image: `./bin/docker-build`
- Verify `claude_desktop_config.json` has correct Docker command
- Restart Claude Desktop completely (Cmd+Q and reopen)
- Check Claude logs: `~/Library/Logs/Claude/mcp*.log`

**TypeScript errors after pulling changes:**
- Delete `node_modules` and reinstall: `yarn install`
- Clean build: `rm -rf dist && yarn build`
- Check Node.js version: `node --version` (must be 18+)

## Development Tips

1. **Fast Iteration**: Use `yarn dev` + MCP Inspector for instant feedback
2. **Type Checking**: Run `tsc --noEmit` to check types without building
3. **Debug Logging**: Set `LOG_LEVEL=debug` environment variable
4. **Container Cleanup**: Use `docker ps -a | grep autobox` to find orphaned containers
5. **Config Validation**: Test configs with `SimulationConfigSchema.parse()` before running
