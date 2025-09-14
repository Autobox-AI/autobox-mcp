#!/usr/bin/env bash

echo "=== Testing MCP Server in Docker ==="
echo ""
echo "Starting MCP server with Docker socket access..."
echo "Send these JSON-RPC requests to test:"
echo ""
echo '1. Initialize:'
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"0.1.0","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}'
echo ""
echo '2. List tools:'
echo '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":2}'
echo ""
echo '3. Call a tool (list simulations):'
echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_simulations"},"id":3}'
echo ""
echo "Press Ctrl+D to send EOF and see results, or Ctrl+C to exit"
echo "---"
echo ""

# Run the container with Docker socket access
docker run -i --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/.autobox:/root/.autobox \
  autobox-mcp:latest