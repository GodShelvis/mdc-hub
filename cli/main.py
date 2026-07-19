"""MDC Hub CLI — 一站式命令行工具。

用法:
    mdc-hub install       # 自动检测 AI 工具并安装 MCP + Skills
    mdc-hub serve          # 启动 Web UI（后端 + 前端静态托管）
    mdc-hub mcp            # 启动 MCP Server（stdio）
    mdc-hub scan ./docs    # 扫描 MDC 目录
    mdc-hub summarize ./docs  # 批量 AI 摘要
"""

import os
import sys
import json
import shutil
from pathlib import Path

import click

# 获取项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
#  AI 工具 MCP 配置定义
# ============================================================

AI_TOOLS = {
    "trae": {
        "name": "Trae IDE",
        "config_paths": [
            lambda root: root / ".trae" / "mcp.json",
        ],
        "format": "mcpServers",
        "entry_key": "mdc-hub",
    },
    "claude_code": {
        "name": "Claude Code",
        "config_paths": [
            lambda root: root / ".mcp.json",
        ],
        "format": "mcpServers",
        "entry_key": "mdc-hub",
    },
    "opencode": {
        "name": "OpenCode",
        "config_paths": [
            lambda root: root / "opencode.jsonc",
            lambda root: root / "opencode.json",
            lambda root: Path.home() / ".config" / "opencode" / "config.jsonc",
        ],
        "format": "mcp",
        "entry_key": "mdc-hub",
    },
    "cursor": {
        "name": "Cursor",
        "config_paths": [
            lambda root: Path.home() / ".cursor" / "mcp.json",
        ],
        "format": "mcpServers",
        "entry_key": "mdc-hub",
    },
    "codex": {
        "name": "Codex CLI",
        "config_paths": [
            lambda root: root / ".codex" / "config.toml",
            lambda root: Path.home() / ".codex" / "config.toml",
        ],
        "format": "toml",
        "entry_key": "mdc-hub",
    },
    "workbuddy": {
        "name": "WorkBuddy",
        "config_paths": [
            lambda root: Path.home() / ".workbuddy" / "mcp.json",
        ],
        "format": "mcp",
        "entry_key": "mdc-hub",
    },
    "codebuddy": {
        "name": "CodeBuddy",
        "config_paths": [
            lambda root: root / ".mcp.json",
            lambda root: Path.home() / ".codebuddy" / ".mcp.json",
        ],
        "format": "mcpServers",
        "entry_key": "mdc-hub",
    },
    "windsurf": {
        "name": "Windsurf",
        "config_paths": [
            lambda root: Path.home() / ".codeium" / "windsurf" / "mcp_config.json",
        ],
        "format": "mcpServers",
        "entry_key": "mdc-hub",
    },
    "jetbrains": {
        "name": "JetBrains",
        "config_paths": [
            lambda root: Path.home() / ".jetbrains" / "mcp.json",
        ],
        "format": "mcpServers",
        "entry_key": "mdc-hub",
    },
}

# Skills 安装目标
SKILLS_TARGETS = [
    lambda root: root / ".trae" / "skills",
    lambda root: Path.home() / ".agents" / "skills",
    lambda root: Path.home() / ".claude" / "skills",
]


# ============================================================
#  辅助函数
# ============================================================

def _get_mcp_command() -> str:
    """获取 MCP 启动命令。优先用 uvx，其次 python + mdc-hub-mcp。"""
    # 检测 uv
    if shutil.which("uvx"):
        return "uvx mdc-hub mcp"
    # 检测 mdc-hub-mcp 命令
    if shutil.which("mdc-hub-mcp"):
        return "mdc-hub-mcp"
    # 兜底：python -m
    return f"{sys.executable} -m cli.main mcp"


def _detect_installed_tools(project_root: Path) -> dict[str, bool]:
    """检测安装了哪些 AI 工具（看配置文件是否存在）。"""
    detected = {}
    for tool_id, tool_info in AI_TOOLS.items():
        for path_fn in tool_info["config_paths"]:
            path = path_fn(project_root)
            if path.exists() or path.parent.exists():
                detected[tool_id] = True
                break
        else:
            detected[tool_id] = False
    return detected


def _write_json_config(path: Path, entry_key: str, command: str, format_type: str):
    """写入或更新 JSON 格式的 MCP 配置。"""
    existing = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            pass

    # 根据 format 确定顶层 key
    if format_type == "mcpServers":
        servers = existing.get("mcpServers", {})
        servers[entry_key] = {"command": command}
        existing["mcpServers"] = servers
    elif format_type == "mcp":
        servers = existing.get("mcp", {})
        servers[entry_key] = {
            "type": "local",
            "command": command.split(),
        }
        existing["mcp"] = servers
    elif format_type == "servers":
        servers = existing.get("servers", {})
        servers[entry_key] = {
            "type": "stdio",
            "command": command.split()[0],
            "args": command.split()[1:] if len(command.split()) > 1 else [],
        }
        existing["servers"] = servers

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_toml_config(path: Path, entry_key: str, command: str):
    """写入或更新 TOML 格式的 MCP 配置（Codex）。"""
    existing_lines = []
    if path.exists():
        existing_lines = path.read_text(encoding="utf-8").splitlines()

    # Codex TOML: [mcp_servers.name], command = "...", args = [...]
    section = f"[mcp_servers.{entry_key}]"
    cmd_parts = command.split()
    new_block = [
        section,
        f'command = "{cmd_parts[0]}"',
    ]
    if len(cmd_parts) > 1:
        args_str = ", ".join(f'"{a}"' for a in cmd_parts[1:])
        new_block.append(f"args = [{args_str}]")

    # 替换已有 section 或追加
    new_lines = []
    in_section = False
    found = False
    for line in existing_lines:
        if line.strip() == section:
            new_lines.extend(new_block)
            in_section = True
            found = True
        elif in_section and line.startswith("["):
            in_section = False
            new_lines.append(line)
        elif not in_section:
            new_lines.append(line)

    if not found:
        if new_lines and new_lines[-1]:
            new_lines.append("")
        new_lines.extend(new_block)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _install_skills(project_root: Path) -> int:
    """将 skills/ 复制到各 AI 工具的 Skills 目录。"""
    skills_src = project_root / "skills"
    if not skills_src.is_dir():
        # pip install 时，skills 可能在包目录
        import importlib.resources
        try:
            skills_src = Path(str(importlib.resources.files("mdc_hub") / "skills"))
        except Exception:
            return 0

    count = 0
    for target_fn in SKILLS_TARGETS:
        dst = target_fn(project_root)
        for skill_dir in skills_src.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                name = skill_dir.name
                dst_dir = dst / name
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(skill_dir / "SKILL.md", dst_dir / "SKILL.md")
                count += 1

    return count


# ============================================================
#  CLI 命令
# ============================================================

@click.group()
def cli():
    """MDC Hub — 知识库管理与可视化工具"""
    pass


@cli.command()
@click.option("--project", "-p", default=".", help="项目根目录")
@click.option("--global", "-g", "global_install", is_flag=True, help="全局安装")
@click.option("--dry-run", is_flag=True, help="仅预览，不写入")
def install(project: str, global_install: bool, dry_run: bool):
    """自动检测 AI 工具并安装 MCP 配置 + Skills。"""
    project_root = Path(project).resolve()
    command = _get_mcp_command()

    click.echo(f"\n  MCP 命令: {command}")
    click.echo(f"  项目目录: {project_root}\n")

    # 检测工具
    detected = _detect_installed_tools(project_root)

    installed = 0
    for tool_id, info in AI_TOOLS.items():
        exists = detected[tool_id]
        status = "已检测" if exists else "未检测"
        click.echo(f"  [{status}] {info['name']}")

        if not exists:
            continue

        for path_fn in info["config_paths"]:
            config_path = path_fn(project_root)
            if dry_run:
                click.echo(f"      → 将写入: {config_path}")
                continue

            try:
                if info["format"] == "toml":
                    _write_toml_config(config_path, info["entry_key"], command)
                else:
                    _write_json_config(config_path, info["entry_key"], command, info["format"])
                click.echo(f"      ✓ 已配置: {config_path}")
                installed += 1
                break
            except Exception as e:
                click.echo(f"      ✗ 失败: {e}")

    # 安装 Skills
    click.echo("")
    skill_count = _install_skills(project_root)
    click.echo(f"  ✓ Skills 已安装 ({skill_count} 个)\n")

    if installed == 0 and not dry_run:
        click.echo("  未检测到已安装的 AI 工具。手动配置请参考 mcp-config.json\n")
    else:
        click.echo("  完成！重启 AI 工具后即可使用 MDC Hub。\n")


@cli.command()
@click.option("--host", default="0.0.0.0", help="监听地址")
@click.option("--port", default=8000, help="监听端口")
@click.option("--reload", is_flag=True, help="开发模式热重载")
@click.option("--dev", is_flag=True, help="开发模式：前端单独用 Vite")
def serve(host: str, port: int, reload: bool, dev: bool):
    """启动 Mdc Hub Web 服务（后端 API + 前端静态文件）。"""
    import uvicorn
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles

    os.chdir(str(PROJECT_ROOT))

    # 导入后端 app
    from backend.main import app as backend_app

    if not dev:
        # 前端静态文件托管
        dist_dir = PROJECT_ROOT / "frontend" / "dist"
        if dist_dir.is_dir():
            backend_app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")
            click.echo(f"  前端已打包，访问 http://localhost:{port}")
        else:
            click.echo(f"  前端未打包，仅 API 可用。开发模式请加 --dev")
    else:
        click.echo(f"  开发模式：前端请手动 npm run dev")

    click.echo(f"\n  API:  http://localhost:{port}/api/health")
    uvicorn.run(backend_app, host=host, port=port, reload=reload)


@cli.command(hidden=True)
def mcp():
    """启动 MCP Server（stdio 模式）。供 AI 工具内部调用。"""
    os.chdir(str(PROJECT_ROOT))
    from backend.mcp_server import run
    run()


if __name__ == "__main__":
    cli()
