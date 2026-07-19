#!/bin/bash
# ============================================
# MDC Hub — 一键安装脚本
# ============================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}▸${NC} $1"; }
ok()    { echo -e "${GREEN}✓${NC} $1"; }
err()   { echo -e "${RED}✗${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║       MDC Hub 安装程序          ║"
echo "  ╚══════════════════════════════════╝"
echo ""

# ---- 1. Python 环境 ----
echo "━━━━ Step 1/5: Python 环境 ━━━━"

PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    err "未找到 Python3，请先安装 Python 3.10+"
    exit 1
fi

VENV_PATH="$SCRIPT_DIR/.venv"
if [ -f "$VENV_PATH/bin/python" ]; then
    ok "虚拟环境已存在"
else
    info "创建虚拟环境..."
    "$PYTHON" -m venv "$VENV_PATH"
    ok "虚拟环境创建完成"
fi

info "安装后端依赖..."
"$VENV_PATH/bin/pip" install --upgrade pip --quiet 2>/dev/null || true
"$VENV_PATH/bin/pip" install -e ".[mcp]" --quiet 2>/dev/null || {
    # 如果 mcp 安装失败（cryptography Rust 问题），分开装
    "$VENV_PATH/bin/pip" install -e . --quiet
    "$VENV_PATH/bin/pip" install mcp --no-deps --quiet
}
ok "后端依赖安装完成"

# ---- 2. 前端 ----
echo ""
echo "━━━━ Step 2/5: 前端环境 ━━━━"

if command -v npm &>/dev/null; then
    cd "$SCRIPT_DIR/frontend"
    npm install --silent 2>/dev/null || npm install
    cd "$SCRIPT_DIR"
    ok "前端依赖安装完成"
else
    err "未找到 npm，跳过前端——仅 MCP Server 可用"
fi

# ---- 3. MCP Server ----
echo ""
echo "━━━━ Step 3/5: MCP Server ━━━━"

ENTRY_SH="$SCRIPT_DIR/scripts/mcp-entry.sh"
if [ -f "$ENTRY_SH" ]; then
    chmod +x "$ENTRY_SH"
    ok "MCP 启动入口就绪"
else
    err "缺少 scripts/mcp-entry.sh"
    exit 1
fi

# ---- 4. Skills 安装 ----
echo ""
echo "━━━━ Step 4/5: Skills 安装 ━━━━"

SKILLS_SRC="$SCRIPT_DIR/skills"
SKILLS_DST="$SCRIPT_DIR/.trae/skills"

if [ ! -d "$SKILLS_SRC" ]; then
    err "缺少 skills/ 目录"
    exit 1
fi

mkdir -p "$SKILLS_DST"
skill_count=0
for dir in "$SKILLS_SRC"/*/; do
    name=$(basename "$dir")
    if [ -f "$dir/SKILL.md" ]; then
        mkdir -p "$SKILLS_DST/$name"
        cp "$dir/SKILL.md" "$SKILLS_DST/$name/SKILL.md"
        ok "$name"
        skill_count=$((skill_count + 1))
    fi
done

if [ "$skill_count" -eq 0 ]; then
    err "未找到任何 Skill"
    exit 1
fi
ok "共安装 $skill_count 个 Skill"

# ---- 5. MCP 配置提示 ----
echo ""
echo "━━━━ Step 5/5: 配置 MCP ━━━━"

MCP_JSON="$SCRIPT_DIR/mcp-config.json"
if [ -f "$MCP_JSON" ]; then
    ok "MCP 配置文件: mcp-config.json"
    echo ""
    echo "  请将以下内容添加到 AI 工具的 MCP 设置中："
    echo ""
    sed "s|\${workspaceFolder}|$SCRIPT_DIR|g" "$MCP_JSON"
else
    echo ""
    echo "  请手动在 AI 工具的 MCP 设置中添加："
    echo ""
    echo "  {"
    echo "    \"mcpServers\": {"
    echo "      \"mdc-hub\": {"
    echo "        \"command\": \"$ENTRY_SH\","
    echo "        \"cwd\": \"$SCRIPT_DIR\""
    echo "      }"
    echo "    }"
    echo "  }"
fi

echo ""
echo "╔══════════════════════════════════╗"
echo "║         安装完成！              ║"
echo "╠══════════════════════════════════╣"
echo "║                                ║"
echo "║  启动 Web UI:                  ║"
echo "║    cd frontend && npm run dev   ║"
echo "║    .venv/bin/uvicorn backend.main:app --reload ║"
echo "║                                ║"
echo "║  验证 MCP:                     ║"
echo "║    $ENTRY_SH                   ║"
echo "║                                ║"
echo "╚══════════════════════════════════╝"
echo ""
