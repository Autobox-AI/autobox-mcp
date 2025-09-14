FROM python:3.13-slim

# Install Docker CLI (to manage other containers)
RUN apt-get update && apt-get install -y \
    docker.io \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV for Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY autobox/ ./autobox/

# Install dependencies
RUN uv venv && uv sync

# Install the package
RUN uv pip install -e .

# The MCP server needs to run with stdio
ENTRYPOINT ["uv", "run", "autobox-mcp"]