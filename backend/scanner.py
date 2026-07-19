"""MDC 文件扫描与解析模块。

递归扫描指定目录，解析所有 .md 文件的 YAML frontmatter，
提取节点信息、标签、连接关系，构建知识图谱数据结构。
"""

import os
from pathlib import Path
from typing import Optional

import frontmatter
import yaml
from pydantic import BaseModel


class Connection(BaseModel):
    """节点间的连接关系"""
    target: str
    relation: str = "关联"


class NodeMeta(BaseModel):
    """MDC 文件解析后的节点元数据"""
    id: str
    title: str
    file_path: str
    category: str = "未分类"
    tags: list[str] = []
    connections: list[Connection] = []
    summary: str = ""
    ai_model: str = ""
    ai_summarized_at: str = ""
    body_preview: str = ""  # 正文前 200 字符预览

    class Config:
        extra = "allow"


class ScanResult(BaseModel):
    """目录扫描结果"""
    directory: str
    total_files: int
    nodes: list[NodeMeta]


class Edge(BaseModel):
    """图谱边数据"""
    source: str
    target: str
    relation: str
    source_file: str
    target_file: str


class GraphData(BaseModel):
    """完整的图谱数据"""
    nodes: list[NodeMeta]
    edges: list[Edge]


def parse_mdc_file(file_path: str) -> Optional[NodeMeta]:
    """解析单个 MDC 文件，提取 frontmatter 元数据。

    Args:
        file_path: MDC 文件的绝对路径

    Returns:
        NodeMeta 对象，解析失败返回 None
    """
    try:
        post = frontmatter.load(file_path)
    except Exception:
        return None

    meta = post.metadata or {}
    body = post.content or ""

    # 从 frontmatter 提取字段
    node_id = meta.get("id", "")
    title = meta.get("title", "")

    # 如果缺少 id 或 title，用文件名兜底
    if not node_id:
        node_id = Path(file_path).stem
    if not title:
        title = node_id

    # 解析 connections
    raw_connections = meta.get("connections", [])
    connections = []
    if isinstance(raw_connections, list):
        for conn in raw_connections:
            if isinstance(conn, dict):
                connections.append(
                    Connection(target=conn.get("target", ""), relation=conn.get("relation", "关联"))
                )
            elif isinstance(conn, str):
                connections.append(Connection(target=conn))

    # 正文预览（前 200 字符）
    body_preview = body.strip()[:200]

    return NodeMeta(
        id=node_id,
        title=title,
        file_path=file_path,
        category=meta.get("category", "未分类"),
        tags=meta.get("tags", []) if isinstance(meta.get("tags"), list) else [],
        connections=connections,
        summary=meta.get("summary", ""),
        ai_model=meta.get("ai_model", ""),
        ai_summarized_at=meta.get("ai_summarized_at", ""),
        body_preview=body_preview,
    )


def scan_directory(directory: str) -> ScanResult:
    """递归扫描目录下的所有 .md 文件。

    Args:
        directory: 要扫描的目录路径

    Returns:
        ScanResult 包含所有解析出的节点
    """
    dir_path = Path(directory).resolve()
    if not dir_path.exists():
        return ScanResult(directory=str(dir_path), total_files=0, nodes=[])

    nodes: list[NodeMeta] = []

    for md_file in sorted(dir_path.rglob("*.md")):
        node = parse_mdc_file(str(md_file))
        if node:
            nodes.append(node)

    return ScanResult(
        directory=str(dir_path),
        total_files=len(nodes),
        nodes=nodes,
    )


def build_graph(selected_file_paths: list[str], all_nodes: list[NodeMeta]) -> GraphData:
    """根据选中的文件列表，构建节点和边的图谱数据。

    仅包含选中文件的节点，边则包含这些节点之间的所有连接关系。
    如果一条边的 target 指向的节点不在选中文件中，也会将该节点加入。

    Args:
        selected_file_paths: 用户选中的文件路径列表
        all_nodes: 扫描出的全部节点

    Returns:
        GraphData 包含图谱所需的 nodes 和 edges
    """
    # 建立 id -> node 的映射
    id_to_node: dict[str, NodeMeta] = {n.id: n for n in all_nodes}

    selected_ids = set()
    selected_nodes_map: dict[str, NodeMeta] = {}

    for n in all_nodes:
        if n.file_path in selected_file_paths:
            selected_ids.add(n.id)
            selected_nodes_map[n.id] = n

    edges: list[Edge] = []
    referenced_ids: set[str] = set()

    # 遍历选中节点的连接关系
    for node_id, node in selected_nodes_map.items():
        for conn in node.connections:
            target_node = id_to_node.get(conn.target)
            edge = Edge(
                source=node_id,
                target=conn.target,
                relation=conn.relation,
                source_file=node.file_path,
                target_file=target_node.file_path if target_node else "",
            )
            edges.append(edge)
            # 如果 target 节点不在选中列表中，也把它加入（作为被引用节点）
            if conn.target not in selected_ids:
                referenced_ids.add(conn.target)

    # 加入被引用的节点
    for ref_id in referenced_ids:
        ref_node = id_to_node.get(ref_id)
        if ref_node and ref_node.id not in selected_nodes_map:
            selected_nodes_map[ref_node.id] = ref_node

    return GraphData(
        nodes=list(selected_nodes_map.values()),
        edges=edges,
    )


def write_frontmatter(file_path: str, node: NodeMeta) -> bool:
    """将 NodeMeta 写回到 MDC 文件的 frontmatter 中。

    Args:
        file_path: MDC 文件路径
        node: 要写入的节点元数据

    Returns:
        写入是否成功
    """
    try:
        post = frontmatter.load(file_path)
        body = post.content

        meta: dict = {
            "id": node.id,
            "title": node.title,
            "category": node.category,
            "tags": node.tags,
            "connections": [c.model_dump() for c in node.connections],
        }

        if node.summary:
            meta["summary"] = node.summary
        if node.ai_model:
            meta["ai_model"] = node.ai_model
        if node.ai_summarized_at:
            meta["ai_summarized_at"] = node.ai_summarized_at

        # 保留原有 metadata 中没有被覆盖的字段
        original_meta = post.metadata or {}
        for key, value in original_meta.items():
            if key not in meta:
                meta[key] = value

        new_post = frontmatter.Post(body, **meta)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(new_post))
        return True
    except Exception:
        return False


def read_full_body(file_path: str) -> str:
    """读取 MDC 文件的正文内容（不含 frontmatter）。

    Args:
        file_path: MDC 文件路径

    Returns:
        正文内容
    """
    try:
        post = frontmatter.load(file_path)
        return post.content or ""
    except Exception:
        return ""
