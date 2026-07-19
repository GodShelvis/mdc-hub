#!/bin/bash
# MDC Hub MCP Server 启动入口

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

if [ ! -f ".venv/bin/python" ]; then
    echo "错误：未找到 .venv，请先运行 install.sh" >&2
    exit 1
fi

exec .venv/bin/python -m backend.mcp_server
