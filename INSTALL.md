# Autobox MCP Server Installation

## Quick Install (One-liner)

```bash
git clone https://github.com/margostino/autobox-mcp.git && cd autobox-mcp && \
docker build -t autobox-mcp . && \
claude mcp add autobox -s user docker -- run -i --rm -e HOST_HOME=$HOME -e OPENAI_API_KEY=$OPENAI_API_KEY -v /var/run/docker.sock:/var/run/docker.sock -v ${HOME}/.autobox:/root/.autobox autobox-mcp
```

**Prerequisites:**
- Set your OpenAI API key: `export OPENAI_API_KEY=sk-...`

## Step-by-Step Installation

### 1. Clone the repository
```bash
git clone https://github.com/margostino/autobox-mcp.git
cd autobox-mcp
```

### 2. Build the Docker image
```bash
docker build -t autobox-mcp .
```

Or use the build script:
```bash
./bin/docker-build
```

### 3. Add to Claude Desktop
```bash
claude mcp add autobox -s user docker -- run -i --rm \
  -e HOST_HOME=$HOME \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ${HOME}/.autobox:/root/.autobox \
  autobox-mcp
```

**Note:** Make sure you have `OPENAI_API_KEY` set in your environment before running this command.

### 4. Restart Claude Desktop
Quit and reopen Claude Desktop to load the new MCP server.

## Verify Installation

In Claude Desktop, ask: "Can you list the available Autobox MCP tools?"

Claude should respond with 8 available tools for managing AI simulations.

## Uninstall

To remove the MCP server:
```bash
claude mcp remove autobox
```

## Requirements

- Docker Desktop installed and running
- Claude Desktop with MCP support
- Access to Docker socket (for managing simulation containers)

## What This Gives You

Once installed, Claude can:
- Start and stop AI multi-agent simulations
- Monitor simulation progress and metrics
- View simulation logs
- Create custom simulation configurations
- Manage multiple simulations simultaneously

## Troubleshooting

If you get permission errors:
- Ensure Docker Desktop is running
- On Linux, you may need to add your user to the docker group:
  ```bash
  sudo usermod -aG docker $USER
  ```

If Claude doesn't see the MCP server:
- Restart Claude Desktop
- Check the logs: `claude mcp logs autobox`