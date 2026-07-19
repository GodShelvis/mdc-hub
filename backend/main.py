"""MDC Hub FastAPI 后端服务。

提供目录扫描、图谱构建、AI 摘要等 API 接口。
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .scanner import scan_directory, build_graph, read_full_body, parse_mdc_file, write_frontmatter
from .ai_service import summarize_content, save_summary_to_file
from .archiver import (
    find_workspace_root,
    get_hub_path,
    get_docs_dir,
    list_archived_docs,
    load_config,
    ensure_hub_structure,
)

app = FastAPI(title="MDC Hub", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Request/Response Models ----

class ScanRequest(BaseModel):
    directory: str


class GraphRequest(BaseModel):
    directory: str
    selected_files: list[str]


class FileBodyRequest(BaseModel):
    file_path: str


class SummarizeRequest(BaseModel):
    file_path: str
    write_back: bool = True


class NodeUpdateRequest(BaseModel):
    file_path: str
    title: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    connections: Optional[list[dict]] = None
    summary: Optional[str] = None


# ---- API Routes ----

@app.get("/api/browse")
async def browse(path: str = Query("/")):
    """浏览文件系统目录，返回子目录和文件列表。"""
    dir_path = Path(path).expanduser().resolve()
    if not dir_path.exists() or not dir_path.is_dir():
        raise HTTPException(status_code=404, detail="目录不存在")

    items = []
    try:
        for entry in sorted(dir_path.iterdir()):
            if entry.name.startswith("."):
                continue
            items.append({
                "name": entry.name,
                "path": str(entry),
                "is_dir": entry.is_dir(),
            })
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权限访问")

    return {
        "path": str(dir_path),
        "parent": str(dir_path.parent) if dir_path.parent != dir_path else None,
        "items": items,
    }


@app.post("/api/scan")
async def scan(request: ScanRequest):
    """扫描指定目录，返回所有 MDC 文件的节点信息。"""
    result = scan_directory(request.directory)
    return result.model_dump()


@app.get("/api/auto-scan")
async def auto_scan():
    """自动扫描工作区的 .mdc-hub/docs/ 目录。"""
    ws_root = find_workspace_root()
    docs_dir = str(Path(ws_root) / ".mdc-hub" / "docs")
    result = scan_directory(docs_dir) if Path(docs_dir).is_dir() else scan_directory(ws_root)
    return result.model_dump()


@app.post("/api/graph")
async def graph(request: GraphRequest):
    """根据选中的文件路径，构建知识图谱数据。"""
    scan_result = scan_directory(request.directory)
    graph_data = build_graph(request.selected_files, scan_result.nodes)
    return graph_data.model_dump()


@app.post("/api/file/body")
async def get_file_body(request: FileBodyRequest):
    """获取单个文件的完整正文内容。"""
    body = read_full_body(request.file_path)
    return {"body": body}


@app.post("/api/summarize")
async def summarize(request: SummarizeRequest):
    """对指定文档调用 AI 摘要，可选择是否回写文件。"""
    body = read_full_body(request.file_path)
    if not body.strip():
        raise HTTPException(status_code=400, detail="文档内容为空")

    result = await summarize_content(body)
    if not result:
        raise HTTPException(status_code=500, detail="AI 摘要失败，请检查 API Key 配置")

    if request.write_back:
        saved = save_summary_to_file(request.file_path, result)
        if not saved:
            raise HTTPException(status_code=500, detail="回写文件失败")

    return {"result": result, "written": request.write_back}


@app.post("/api/node/update")
async def update_node(request: NodeUpdateRequest):
    """手动更新节点的 frontmatter 字段。"""
    node = parse_mdc_file(request.file_path)
    if not node:
        raise HTTPException(status_code=404, detail="文件解析失败")

    if request.title is not None:
        node.title = request.title
    if request.category is not None:
        node.category = request.category
    if request.tags is not None:
        node.tags = request.tags
    if request.connections is not None:
        from scanner import Connection
        node.connections = [
            Connection(target=c.get("target", ""), relation=c.get("relation", "关联"))
            for c in request.connections
        ]
    if request.summary is not None:
        node.summary = request.summary

    success = write_frontmatter(request.file_path, node)
    if not success:
        raise HTTPException(status_code=500, detail="写入文件失败")

    return node.model_dump()


# ---- Workspace & Archive API ----


@app.get("/api/workspace")
async def workspace_info():
    """获取工作区信息：根目录、.mdc-hub 路径等。"""
    ensure_hub_structure()
    root = find_workspace_root()
    config = load_config()
    return {
        "workspace_root": root,
        "hub_dir": str(get_hub_path(root)),
        "docs_dir": str(get_docs_dir(root)),
        "config": config,
        "archived_count": len(list_archived_docs(root)),
    }


@app.get("/api/archive")
async def list_archive():
    """列出 .mdc-hub/docs/ 下所有归档的 MDC 文档。"""
    return {"documents": list_archived_docs()}


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}
