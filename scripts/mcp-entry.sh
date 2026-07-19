#!/bin/bash
# MDC Hub MCP Server 启动入口
# 兼容三种安装方式：.venv / pip 全局安装 / uvx
set -e

# 方式1: uvx（最高优先级）
if command -v uvx &>/dev/null; then
    exec uvx mdc-hub mcp
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 方式2: 项目 .venv
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    cd "$PROJECT_ROOT"
    exec .venv/bin/python -m backend.mcp_server
fi

# 方式3: pip 全局安装的 mdc-hub-mcp 命令
if command -v mdc-hub-mcp &>/dev/null; then
    exec mdc-hub-mcp
fi

# 方式4: pip 全局安装的 python -m
if command -v python3 &>/dev/null; then
    exec python3 -m backend.mcp_server
fi

echo "错误：未找到 Python 或 MDC Hub 安装。请先运行 mdc-hub install。" >&2
exit 1
