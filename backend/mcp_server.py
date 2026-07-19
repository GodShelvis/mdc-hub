"""MDC Hub MCP Server — 目录扫描、文档生成、知识图谱归档。

以 stdio 方式运行，供 AI 工具（如 Claude、Trae）调用。
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .archiver import (
    find_workspace_root,
    get_archive_path,
    write_archived_doc,
    list_archived_docs,
    load_config,
    save_config,
    get_docs_dir,
    ensure_hub_structure,
)

server = Server("mdc-hub")


# ---- 辅助函数 ----

# 按文件类型分组定义
FILE_TYPE_GROUPS = {
    "代码": {".java", ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".c", ".cpp", ".h", ".hpp", ".vue", ".svelte", ".rb", ".php", ".swift", ".kt", ".kts", ".scala", ".cs", ".fs", ".fsx"},
    "表格": {".xlsx", ".xls", ".csv", ".tsv"},
    "文档": {".docx", ".doc", ".pdf", ".md", ".txt", ".rst"},
    "媒体": {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".mp4", ".mov", ".webm", ".mp3", ".wav"},
    "配置": {".json", ".yaml", ".yml", ".xml", ".toml", ".ini", ".properties", ".env"},
    "其他": {},
}


def _classify_file(ext: str) -> str:
    for group, exts in FILE_TYPE_GROUPS.items():
        if ext.lower() in exts:
            return group
    return "其他"


def _scan_files(directory: str, file_types: list[str] | None = None) -> list[dict]:
    """扫描目录下的所有文件，按类型分组返回。"""
    dir_path = Path(directory).resolve()
    if not dir_path.exists():
        return []

    allowed_exts: set[str] | None = None
    if file_types:
        allowed_exts = set()
        for t in file_types:
            allowed_exts |= FILE_TYPE_GROUPS.get(t, set())

    files = []
    for f in sorted(dir_path.rglob("*")):
        if not f.is_file():
            continue
        if any(p.startswith(".") for p in f.parts):
            continue
        ext = f.suffix.lower()
        if allowed_exts is not None and ext not in allowed_exts:
            continue
        files.append({
            "name": f.name,
            "path": str(f),
            "relative": str(f.relative_to(dir_path)),
            "size": f.stat().st_size,
            "extension": f.suffix,
            "type": _classify_file(f.suffix),
        })
    return files


def _read_files(file_paths: list[str]) -> dict[str, str]:
    """批量读取文件内容。"""
    result = {}
    for path in file_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                result[path] = f.read()
        except Exception as e:
            result[path] = f"[ERROR: {e}]"
    return result


# ---- MCP 工具列表 ----

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="scan_directory",
            description="扫描指定目录下的所有文件。可选按类型过滤（代码/表格/文档/媒体/配置）。返回文件列表（路径、大小、类型、按目录分组），供 AI 分析文件结构、识别领域。",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要扫描的目录绝对路径",
                    },
                    "file_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "可选：按类型过滤，如 ['代码', '表格', '文档', '媒体', '配置']。不传则返回所有类型。",
                    },
                },
                "required": ["directory"],
            },
        ),
        Tool(
            name="read_files",
            description="读取指定文件的原始内容。支持所有文件类型，返回文件路径到内容的映射。",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "要读取的文件绝对路径列表",
                    },
                },
                "required": ["file_paths"],
            },
        ),
        Tool(
            name="write_mdc_document",
            description="将 AI 生成的 MDC 知识文档写入归档目录。文档会镜像源文件目录结构，保存到 .mdc-hub/docs/ 下。",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_file": {
                        "type": "string",
                        "description": "原始文件路径，用于确定归档路径",
                    },
                    "id": {
                        "type": "string",
                        "description": "文档唯一标识，kebab-case 格式。方法级节点用 '类名.方法名'。",
                    },
                    "title": {
                        "type": "string",
                        "description": "文档标题",
                    },
                    "category": {
                        "type": "string",
                        "description": "分类路径，如 '技术/后端/DAO层' 或 '数据/报表/销售'",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "标签列表",
                    },
                    "connections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "target": {"type": "string", "description": "关联节点的 id"},
                                "relation": {"type": "string", "description": "关系：属于/调用/注入/实现/关联/依赖/引用"},
                            },
                        },
                        "description": "关联节点列表",
                    },
                    "body": {
                        "type": "string",
                        "description": "Markdown 正文",
                    },
                },
                "required": ["source_file", "id", "title", "body"],
            },
        ),
        Tool(
            name="list_archived_documents",
            description="列出 .mdc-hub/docs/ 下所有已归档的 MDC 知识文档。",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_workspace_info",
            description="获取当前工作区信息：根目录、配置、.mdc-hub 路径。",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="open_dashboard",
            description="获取 MDC Hub Web 可视化面板地址，可在浏览器中查看知识图谱。",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


# ---- 工具调用处理 ----

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "scan_directory":
        directory = arguments.get("directory", "")
        file_types = arguments.get("file_types", None)
        files = _scan_files(directory, file_types)
        # 按目录且按类型分组
        by_dir: dict[str, dict[str, list]] = {}
        for f in files:
            parent = str(Path(f["relative"]).parent) or "."
            ft = f["type"]
            by_dir.setdefault(parent, {}).setdefault(ft, []).append(f["name"])
        # 统计各类型数量
        type_counts: dict[str, int] = {}
        for f in files:
            type_counts[f["type"]] = type_counts.get(f["type"], 0) + 1
        result = {
            "directory": directory,
            "total_files": len(files),
            "type_counts": type_counts,
            "groups": {
                k: {t: v for t, v in sorted(v.items())}
                for k, v in sorted(by_dir.items())
            },
            "files": files,
        }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "read_files":
        file_paths = arguments.get("file_paths", [])
        contents = _read_files(file_paths)
        return [TextContent(type="text", text=json.dumps(contents, ensure_ascii=False, indent=2))]

    elif name == "write_mdc_document":
        source_file = arguments.get("source_file", "")
        body = arguments.get("body", "")

        frontmatter = {
            "id": arguments.get("id", Path(source_file).stem),
            "title": arguments.get("title", Path(source_file).stem),
            "category": arguments.get("category", "未分类"),
            "tags": arguments.get("tags", []),
            "connections": arguments.get("connections", []),
        }

        archive_path = write_archived_doc(
            source_file=source_file,
            frontmatter=frontmatter,
            body=body,
        )
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "written",
                "archive_path": archive_path,
                "id": frontmatter["id"],
                "title": frontmatter["title"],
            }, ensure_ascii=False, indent=2),
        )]

    elif name == "list_archived_documents":
        docs = list_archived_docs()
        result = {
            "total": len(docs),
            "documents": docs,
        }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "get_workspace_info":
        ensure_hub_structure()
        root = find_workspace_root()
        config = load_config()
        docs_dir = get_docs_dir()
        result = {
            "workspace_root": root,
            "config": config,
            "hub_dir": str(get_docs_dir().parent),
            "docs_dir": str(docs_dir),
            "archived_docs_count": len(list_archived_docs()),
            "web_ui_url": "http://localhost:5173",
        }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "open_dashboard":
        return [TextContent(
            type="text",
            text=json.dumps({
                "message": "MDC Hub Web UI 已就绪",
                "url": "http://localhost:5173",
                "instruction": "请在浏览器中打开上述 URL 查看知识图谱。确保前端 dev server 和后端 API server 已启动。",
            }, ensure_ascii=False, indent=2),
        )]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ---- 入口 ----

async def main():
    """以 stdio 方式启动 MCP Server。"""
    ensure_hub_structure()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
