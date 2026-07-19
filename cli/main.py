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
import urllib.request
import urllib.error
import yaml
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


def _write_json_config(path: Path, entry_key: str, command: str, format_type: str, cwd: str = ""):
    """写入或更新 JSON 格式的 MCP 配置。"""
    existing = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            pass

    entry: dict = {}
    if command.count(" ") > 0:
        parts = command.split()
        entry["command"] = parts[0]
        entry["args"] = parts[1:]
    else:
        entry["command"] = command
    if cwd:
        entry["cwd"] = cwd

    # 根据 format 确定顶层 key
    if format_type == "mcpServers":
        servers = existing.get("mcpServers", {})
        servers[entry_key] = entry
        existing["mcpServers"] = servers
    elif format_type == "mcp":
        servers = existing.get("mcp", {})
        servers[entry_key] = {
            "type": "local",
            "command": command.split(),
        }
        if cwd:
            servers[entry_key]["cwd"] = cwd
        existing["mcp"] = servers
    elif format_type == "servers":
        servers = existing.get("servers", {})
        servers[entry_key] = {
            "type": "stdio",
            "command": entry.get("command", command.split()[0]),
            "args": entry.get("args", command.split()[1:] if len(command.split()) > 1 else []),
        }
        if cwd:
            servers[entry_key]["cwd"] = cwd
        existing["servers"] = servers

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_toml_config(path: Path, entry_key: str, command: str, cwd: str = ""):
    """写入或更新 TOML 格式的 MCP 配置（Codex）。"""
    existing_lines = []
    if path.exists():
        existing_lines = path.read_text(encoding="utf-8").splitlines()

    # Codex TOML: [mcp_servers.name], command = "...", args = [...], cwd = "..."
    section = f"[mcp_servers.{entry_key}]"
    cmd_parts = command.split()
    new_block = [
        section,
        f'command = "{cmd_parts[0]}"',
    ]
    if len(cmd_parts) > 1:
        args_str = ", ".join(f'"{a}"' for a in cmd_parts[1:])
        new_block.append(f"args = [{args_str}]")
    if cwd:
        new_block.append(f'cwd = "{cwd}"')

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
    # 确定 skills 源目录
    local_skills = project_root / "skills"
    if local_skills.is_dir():
        # 开发模式：使用项目本地的 skills/
        skills_dirs = [(d.name, d / "SKILL.md") for d in local_skills.iterdir()
                       if d.is_dir() and (d / "SKILL.md").exists()]
    else:
        # pip 安装：从包内置读取
        import importlib.resources
        try:
            pkg = importlib.resources.files("skills")
            skills_dirs = []
            for d in pkg.iterdir():
                if d.is_dir():
                    md = d / "SKILL.md"
                    if md.is_file():
                        skills_dirs.append((d.name, md))
        except Exception:
            return 0

    count = 0
    for target_fn in SKILLS_TARGETS:
        dst = target_fn(project_root)
        for name, md_path in skills_dirs:
            dst_dir = dst / name
            dst_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(md_path), str(dst_dir / "SKILL.md"))
            count += 1

    return count


def _load_providers(project_root: Path) -> list[dict]:
    """加载预设提供商列表。

    查找优先级：
    1. 用户 .mdc-hub/config/providers.yaml
    2. 项目根 config/providers.yaml（开发模式）
    3. 包内置 backend/presets/providers.yaml（pip 安装）
    """
    # 优先级1: 用户配置（可能已被自定义）
    providers_path = project_root / ".mdc-hub" / "config" / "providers.yaml"
    if providers_path.exists():
        with open(providers_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data.get("providers", [])

    # 优先级2: 项目根 config/（开发模式源码）
    dev_path = project_root / "config" / "providers.yaml"
    if dev_path.is_file():
        with open(dev_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data.get("providers", [])

    # 优先级3: 包内置 backend/presets/（pip 安装后）
    try:
        import importlib.resources
        src = importlib.resources.files("backend") / "presets" / "providers.yaml"
        if src.is_file():
            data = yaml.safe_load(src.read_text(encoding="utf-8")) or {}
            return data.get("providers", [])
    except Exception:
        pass

    return []


def _fetch_models(base_url: str, api_key: str) -> list[str]:
    """调用提供商 API 获取可用模型列表。"""
    url = base_url.rstrip("/") + "/models"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise click.ClickException(f"获取模型列表失败 (HTTP {e.code}): {body[:200]}")
    except Exception as e:
        raise click.ClickException(f"获取模型列表失败: {e}")

    # 兼容不同 API 返回格式
    models = []
    items = data.get("data", data.get("models", []))
    for item in items:
        model_id = item.get("id", item.get("model", ""))
        if model_id:
            models.append(model_id)
    return models


def _setup_provider(project_root: Path, config: dict):
    """交互式配置 AI 提供商。"""
    providers = _load_providers(project_root)

    click.echo("")
    click.echo("=" * 50)
    click.echo("  配置 AI 提供商（用于智能扫描）")
    click.echo("=" * 50)
    click.echo("")

    # Step 1: 选择提供商
    click.echo("可用提供商：")
    for i, p in enumerate(providers, 1):
        click.echo(f"  [{i}] {p['name']}  ({p['base_url']})")
    click.echo(f"  [c] 自定义")
    click.echo("")

    choice = click.prompt("请选择", default="1").strip()

    if choice.lower() == "c":
        provider_name = click.prompt("提供商名称")
        base_url = click.prompt("Base URL（兼容 OpenAI 接口格式）")
        provider_id = "custom"
    else:
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(providers):
                raise ValueError
            selected = providers[idx]
            provider_id = selected["id"]
            provider_name = selected["name"]
            base_url = selected["base_url"]
        except (ValueError, IndexError):
            raise click.ClickException(f"无效选择: {choice}")

    # Step 2: API Key
    click.echo("")
    api_key = click.prompt("API Key", hide_input=True)

    # Step 3: 获取模型列表
    click.echo("\n  正在获取可用模型列表...")
    try:
        models = _fetch_models(base_url, api_key)
    except click.ClickException:
        click.echo("  自动获取失败，请手动输入模型名")
        model = click.prompt("模型名")
        models = [model]

    if not models:
        click.echo("  未获取到模型，请手动输入")
        model = click.prompt("模型名")
    elif len(models) == 1:
        model = models[0]
        click.echo(f"  唯一可用模型: {model}")
    else:
        click.echo(f"\n  可用模型（共 {len(models)} 个）：")
        for i, m in enumerate(models, 1):
            click.echo(f"    [{i}] {m}")
        click.echo("")
        model_choice = click.prompt("请选择模型", default="1").strip()
        try:
            idx = int(model_choice) - 1
            if idx < 0 or idx >= len(models):
                raise ValueError
            model = models[idx]
        except (ValueError, IndexError):
            model = model_choice  # 允许直接输入模型名

    # Step 4: 保存
    config["provider"] = {
        "id": provider_id,
        "name": provider_name,
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
    }

    click.echo(f"\n  ✓ 提供商已配置: {provider_name} / {model}")


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
                cwd = str(project_root)
                if info["format"] == "toml":
                    _write_toml_config(config_path, info["entry_key"], command, cwd)
                else:
                    _write_json_config(config_path, info["entry_key"], command, info["format"], cwd)
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

    # 提供商配置
    if not dry_run:
        from backend.archiver import load_config as archiver_load_config, save_config as archiver_save_config
        config = archiver_load_config(str(project_root))

        existing_provider = config.get("provider", {})
        has_provider = existing_provider.get("api_key", "")

        if has_provider:
            click.echo(f"  当前 AI 提供商: {existing_provider.get('name', '—')} / {existing_provider.get('model', '—')}")
            if click.confirm("  是否重新配置？", default=False):
                _setup_provider(project_root, config)
                archiver_save_config(config, str(project_root))
        else:
            if click.confirm("  是否配置 AI 提供商用于智能扫描？", default=True):
                _setup_provider(project_root, config)
                archiver_save_config(config, str(project_root))

    click.echo("\n  完成！重启 AI 工具后即可使用 MDC Hub。\n")


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


@cli.group()
def graph():
    """图谱查询：遍历节点关联、查找路径。"""
    pass


@graph.command("list")
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("--json", "output_json", is_flag=True, help="JSON 格式输出")
def graph_list(directory: str, output_json: bool):
    """扫描目录下所有 MDC 节点。"""
    from backend.scanner import scan_directory

    result = scan_directory(directory)
    if output_json:
        click.echo(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
        return
    click.echo(f"\n目录: {result.directory}")
    click.echo(f"节点数: {result.total_files}\n")
    click.echo("-" * 70)
    for i, node in enumerate(result.nodes, 1):
        click.echo(f"\n[{i}] {node.title}")
        click.echo(f"  ID:       {node.id}")
        click.echo(f"  分类:     {node.category}")
        click.echo(f"  标签:     {', '.join(node.tags) if node.tags else '—'}")
        conn_count = len(node.connections)
        if conn_count:
            targets = ", ".join(f"{c.target}({c.relation})" for c in node.connections)
            click.echo(f"  关联({conn_count}): {targets}")
        click.echo("-" * 70)


@graph.command("neighbors")
@click.argument("node_id")
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("--depth", "-d", default=1, help="遍历深度（默认1层）")
@click.option("--direction", "-r", type=click.Choice(["up", "down", "both"]), default="both", help="方向：up(上游)/down(下游)/both(双向)")
def graph_neighbors(node_id: str, directory: str, depth: int, direction: str):
    """查询节点的上下游关联。mdc-hub graph neighbors user-service ./docs -d 3"""
    from backend.scanner import scan_directory
    from collections import deque

    result = scan_directory(directory)
    id_to_node = {n.id: n for n in result.nodes}
    adj = _build_adjacency(result.nodes, direction)

    if node_id not in id_to_node:
        click.echo(f"节点 '{node_id}' 不存在。可用 ID: {', '.join(list(id_to_node)[:20])}")
        return

    # BFS 遍历
    visited = {node_id: 0}
    queue = deque([node_id])
    layers = {0: [node_id]}

    while queue:
        cur = queue.popleft()
        cur_depth = visited[cur]
        if cur_depth >= depth:
            continue
        for neighbor in adj.get(cur, []):
            if neighbor not in visited:
                visited[neighbor] = cur_depth + 1
                queue.append(neighbor)
                layers.setdefault(cur_depth + 1, []).append(neighbor)

    # 打印
    node = id_to_node[node_id]
    click.echo(f"\n  ★ {node.title}  [{node.id}]")
    click.echo(f"    分类: {node.category}")
    click.echo(f"    方向: {direction}, 深度: {depth}")
    click.echo(f"    关联节点数: {len(visited) - 1}\n")
    for d in sorted(layers):
        if d == 0:
            continue
        click.echo(f"  ── 第 {d} 层 ──")
        for nid in layers[d]:
            n = id_to_node.get(nid)
            if n:
                # 找到关系
                rels = []
                for conn in n.connections:
                    if conn.target in adj.get(n.id, []):
                        rels.append(f"{conn.relation}")
                for src in adj:
                    if nid in adj[src] and src in visited:
                        rels.append(f"被 {src} 关联")
                rel_str = f" ({', '.join(rels[:2])})" if rels else ""
                click.echo(f"    {nid} — {n.title}{rel_str}")
    click.echo("")


@graph.command("path")
@click.argument("from_id")
@click.argument("to_id")
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("--max-depth", "-d", default=5, help="最大搜索深度")
def graph_path(from_id: str, to_id: str, directory: str, max_depth: int):
    """查找两个节点间的路径。mdc-hub graph path user-dao order-service ./docs"""
    from backend.scanner import scan_directory
    from collections import deque

    result = scan_directory(directory)
    id_to_node = {n.id: n for n in result.nodes}
    adj = _build_adjacency(result.nodes, "both")

    if from_id not in id_to_node:
        click.echo(f"起点 '{from_id}' 不存在")
        return
    if to_id not in id_to_node:
        click.echo(f"终点 '{to_id}' 不存在")
        return

    # BFS 最短路径
    queue = deque([[from_id]])
    visited = {from_id}

    while queue:
        path = queue.popleft()
        cur = path[-1]
        if cur == to_id:
            _print_path(path, id_to_node)
            return
        if len(path) >= max_depth:
            continue
        for neighbor in adj.get(cur, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])

    click.echo(f"\n  在 {max_depth} 层内未找到从 {from_id} 到 {to_id} 的路径\n")


# ---- 辅助 ----

def _build_adjacency(nodes, direction: str) -> dict[str, list[str]]:
    """构建邻接表。"""
    adj: dict[str, list[str]] = {}
    for n in nodes:
        for conn in n.connections:
            if direction in ("down", "both"):
                adj.setdefault(n.id, []).append(conn.target)
            if direction in ("up", "both"):
                adj.setdefault(conn.target, []).append(n.id)
    return adj


def _print_path(path: list[str], id_to_node: dict):
    """打印路径。"""
    click.echo(f"\n  路径（{len(path) - 1} 步）：\n")
    for i, nid in enumerate(path):
        n = id_to_node.get(nid)
        prefix = "  " if i == 0 else "  ↓ "
        title = f"{n.title} [{n.id}]" if n else nid
        click.echo(f"{prefix}{title}")
    click.echo("")


cli.add_command(graph)


@cli.group()
def provider():
    """AI 提供商配置。"""
    pass


@provider.command("setup")
@click.option("--project", "-p", default=".", help="项目根目录")
def provider_setup(project: str):
    """交互式配置 AI 提供商。"""
    project_root = Path(project).resolve()
    from backend.archiver import load_config, save_config
    config = load_config(str(project_root))
    _setup_provider(project_root, config)
    save_config(config, str(project_root))
    click.echo("  配置已保存到 .mdc-hub/config/settings.yaml\n")


cli.add_command(provider)


@cli.command("scan")
@click.argument("directory", type=click.Path(exists=True, file_okay=False), default=".")
@click.option("--ext", "-e", "extensions", multiple=True, help="指定文件后缀（可多次使用），如 -e .py -e .java")
@click.option("--chunk-size", "-c", default=None, type=int, help="AI 每次处理行数（默认从配置读取）")
@click.option("--dry-run", is_flag=True, help="仅预览扫描计划，不实际执行 AI 调用")
def scan(directory: str, extensions: tuple, chunk_size: int | None, dry_run: bool):
    """扫描目录，使用 AI 分析并生成知识图谱文档。

    自底向上扫描：先分析最深层的源文件，再逐层汇总目录。
    结果归档到 .mdc-hub/docs/。
    """
    project_root = Path(directory).resolve()
    from backend.archiver import find_workspace_root as find_ws, load_config as archiver_load

    ws_root = find_ws(str(project_root))
    config = archiver_load(ws_root)

    # 确定后缀
    if extensions:
        ext_list = list(extensions)
    else:
        ext_list = config.get("scan", {}).get("extensions", [])

    # 确定 chunk_size
    cs = chunk_size or config.get("scan", {}).get("chunk_size", 1000)

    # 检查提供商（dry-run 不需要）
    if not dry_run:
        provider_cfg = config.get("provider", {})
        if not provider_cfg.get("api_key"):
            click.echo("错误: 未配置 AI 提供商。请先运行: mdc-hub provider setup")
            return
        click.echo(f"\n提供商: {provider_cfg['name']} / {provider_cfg['model']}")

    from backend.scan_engine import build_file_tree, plan_batches, execute_scan, _iter_files

    # 构建文件树
    click.echo("→ 构建文件树...")
    tree = build_file_tree(str(project_root), ext_list, cs, ws_root)
    file_count = sum(1 for _ in _iter_files(tree))
    click.echo(f"  找到 {file_count} 个文件")

    # 规划批次
    click.echo("→ 规划扫描批次...")
    batches = plan_batches(tree, cs)
    click.echo(f"  共 {len(batches)} 个批次")

    if dry_run:
        click.echo("\n扫描计划（自底向上）:\n")
        for i, b in enumerate(batches, 1):
            click.echo(f"  [{i}] Pass {b.pass_num} | {b.description}")
        click.echo(f"\n预计 AI 调用次数: {len(batches)}")
        return

    # 检查数量
    if len(batches) > 50:
        if not click.confirm(f"\n这将产生约 {len(batches)} 次 AI 调用，确认继续？"):
            return

    # 执行
    click.echo(f"\n→ 开始扫描...\n")
    stats = execute_scan(batches, ws_root, verbose=True)

    click.echo(f"\n{'='*50}")
    click.echo(f"扫描完成: 成功 {stats['success']}, 失败 {stats['failed']}, 共 {stats['total']}")
    click.echo(f"文档归档: .mdc-hub/docs/")
    click.echo(f"{'='*50}\n")


if __name__ == "__main__":
    cli()
