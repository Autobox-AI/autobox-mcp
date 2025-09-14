#!/usr/bin/env bash

echo "=== Automated MCP Server Test ==="
echo ""

# Create a temporary file with MCP requests
cat > /tmp/mcp_test_requests.jsonl << 'EOF'
{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"0.1.0","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}
{"jsonrpc":"2.0","method":"tools/list","params":{},"id":2}
EOF

echo "Sending MCP requests to server..."
echo ""

# Send requests to the MCP server
cat /tmp/mcp_test_requests.jsonl | docker run -i --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/.autobox:/root/.autobox \
  autobox-mcp:latest

echo ""
echo "Test complete!"

# Clean up
rm /tmp/mcp_test_requests.jsonl