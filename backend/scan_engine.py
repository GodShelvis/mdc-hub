"""扫描引擎 — 自底向上的文件树分析与 MDC 文档生成。

流程：
1. 构建文件树（按后缀过滤）
2. 规划扫描批次（自底向上，10000行/块）
3. 逐批调用 AI 分析
4. 生成 MDC 文档归档到 .mdc-hub/docs/
"""

import os
import json
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from backend.archiver import (
    find_workspace_root, get_docs_dir, get_config_dir, load_config,
)
from backend.ai_service import (
    chat_sync, extract_json,
    SCAN_SYSTEM_PROMPT, build_file_scan_prompt, build_multi_file_prompt,
    build_multi_file_mdc_prompt, build_directory_summary_prompt,
)


@dataclass
class FileNode:
    """文件树节点。"""
    path: str                         # 绝对路径
    rel_path: str                     # 相对于 workspace_root 的路径
    name: str                         # 文件名或目录名
    is_dir: bool = False
    ext: str = ""                     # 后缀（文件）或 ""（目录）
    size_lines: int = 0               # 行数
    children: list["FileNode"] = field(default_factory=list)
    chunks: list[str] = field(default_factory=list)  # 文件内容分块
    scanned: bool = False
    doc_id: str = ""                  # 生成的 MDC 文档 ID
    doc_data: dict = field(default_factory=dict)  # 扫描结果


# ---- 第一步：构建文件树 ----

def _count_lines(file_path: str) -> int:
    """快速统计文件行数。"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def _read_file_chunks(file_path: str, chunk_size: int) -> list[str]:
    """读取文件并切分为 N 行一块。"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return []

    chunks = []
    for i in range(0, len(lines), chunk_size):
        chunk = "".join(lines[i:i + chunk_size])
        chunks.append(chunk)
    return chunks


def build_file_tree(
    directory: str,
    extensions: list[str],
    chunk_size: int = 10000,
    workspace_root: str = "",
) -> FileNode:
    """递归构建文件树，只包含匹配后缀的文件。

    返回根节点（目录），其 children 包含所有匹配的文件和子目录。
    """
    ws_root = Path(workspace_root or find_workspace_root()).resolve()
    dir_path = Path(directory).resolve()

    # 规范化扩展名（确保以 . 开头）
    exts = {e if e.startswith(".") else f".{e}" for e in extensions}

    # 默认排除的目录（各语言构建产物/依赖/IDE 缓存等）
    SKIP_DIRS = {
        # JS/TS
        "node_modules", ".next", ".nuxt", ".output", ".turbo",
        # Python
        "__pycache__", ".venv", "venv", ".eggs", ".tox",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", "site-packages",
        # Java/JVM
        "target", ".gradle", "gradle", "out", "bin",
        # .NET
        "obj",
        # PHP
        "vendor", "bower_components",
        # IDE/VCS
        ".git", ".svn", ".hg",
        ".idea", ".vscode", ".settings", ".classpath", ".project",
        # Build/Output
        "dist", "build", "coverage", ".nyc_output",
        # Misc
        ".mdc-hub", ".cache", "generated", "tmp", "temp", ".tmp",
    }

    # 默认排除的文件名（锁文件、生成文件等）
    SKIP_FILES = {
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
        "composer.lock", "Gemfile.lock", "poetry.lock", "Cargo.lock",
        "Pipfile.lock", ".DS_Store", "Thumbs.db",
    }
    # 默认排除的后缀
    SKIP_EXTS = {".map", ".lock", ".min.js", ".min.css"}

    def _build(path: Path) -> FileNode:
        rel = str(path.relative_to(ws_root)) if ws_root in path.parents or path == ws_root else path.name
        node = FileNode(
            path=str(path),
            rel_path=rel,
            name=path.name,
            is_dir=path.is_dir(),
        )

        if path.is_dir():
            sub_items = []
            try:
                for entry in sorted(path.iterdir()):
                    # 跳过隐藏文件和排除目录
                    if entry.name.startswith(".") or entry.name in SKIP_DIRS:
                        continue
                    if entry.is_dir():
                        sub = _build(entry)
                        if sub.children:  # 只保留非空目录
                            sub_items.append(sub)
                    elif entry.suffix.lower() in exts and entry.name not in SKIP_FILES and entry.suffix.lower() not in SKIP_EXTS:
                        sub = _build(entry)
                        sub_items.append(sub)
            except PermissionError:
                pass
            node.children = sub_items
        else:
            node.ext = path.suffix.lower()
            node.size_lines = _count_lines(str(path))
            node.chunks = _read_file_chunks(str(path), chunk_size)

        return node

    return _build(dir_path)


# ---- 第二步：规划扫描批次 ----

@dataclass
class ScanBatch:
    """一个扫描批次。"""
    nodes: list[FileNode]       # 支持多文件合并
    pass_num: int               # 1=结构分析, 2=生成MDC, 3=目录汇总
    chunk_index: int = 0
    description: str = ""

    @property
    def node(self) -> FileNode:
        """兼容单文件访问。"""
        return self.nodes[0] if self.nodes else None


def _max_depth(node: FileNode) -> int:
    """计算节点的最大深度。"""
    if not node.children:
        return 1
    return 1 + max(_max_depth(c) for c in node.children)


def plan_batches(root: FileNode, chunk_size: int = 10000) -> list[ScanBatch]:
    """自底向上规划扫描批次：深度优先，同层文件激进合并。

    策略：
    1. 收集所有文件，按深度降序排列（最深先扫）
    2. 贪心合并：从头开始，累计行数 ≤ chunk_size 的文件合并为一批
    3. 合并可跨目录（同级深度优先），最大化 AI 利用率
    4. 每批文件有一个 Pass 1，然后各自 Pass 2
    5. 所有文件扫完后，自底向上做目录 Pass 3
    """
    batches: list[ScanBatch] = []

    # Step 1: 收集所有文件节点，按深度降序
    all_files: list[FileNode] = []

    def _collect(node: FileNode, depth: int):
        if node.is_dir:
            for child in node.children:
                _collect(child, depth + 1)
        else:
            all_files.append((depth, node))

    _collect(root, 0)
    # 深度降序：最深的文件排最前
    all_files_sorted = [n for _, n in sorted(all_files, key=lambda x: -x[0])]

    # Step 2: 贪心合并文件为 Pass 1 批次
    i = 0
    while i < len(all_files_sorted):
        batch_nodes = []
        batch_lines = 0
        while i < len(all_files_sorted):
            f = all_files_sorted[i]
            f_lines = f.size_lines
            # 大文件单独处理（不合并）
            if not batch_nodes and f_lines > chunk_size:
                batch_nodes = [f]
                i += 1
                break
            if batch_lines + f_lines <= chunk_size:
                batch_nodes.append(f)
                batch_lines += f_lines
                i += 1
            else:
                break
        _add_file_batches(batches, batch_nodes, chunk_size)

    # Step 3: 收集所有目录，自底向上做 Pass 3
    all_dirs: list[FileNode] = []

    def _collect_dirs(node: FileNode):
        if node.is_dir:
            for child in node.children:
                _collect_dirs(child)
            if node.children:
                all_dirs.append(node)

    _collect_dirs(root)
    for d in all_dirs:
        if d.children:
            batches.append(ScanBatch(
                nodes=[d],
                pass_num=3,
                description=f"目录汇总: {d.rel_path} ({len(d.children)}个子项)",
            ))

    return batches


def _add_file_batches(batches: list[ScanBatch], nodes: list[FileNode], chunk_size: int):
    """为文件节点添加 Pass 1 和 Pass 2 批次。多文件合并时 Pass 2 也批量生成。"""
    if len(nodes) == 1:
        node = nodes[0]
        # 大文件分块
        for ci, _ in enumerate(node.chunks):
            chunk_label = f" 分块 {ci + 1}/{len(node.chunks)}" if len(node.chunks) > 1 else ""
            batches.append(ScanBatch(
                nodes=[node],
                pass_num=1,
                chunk_index=ci,
                description=f"结构分析: {node.rel_path}{chunk_label} ({node.size_lines}行)",
            ))
        batches.append(ScanBatch(
            nodes=[node],
            pass_num=2,
            description=f"生成MDC: {node.rel_path}",
        ))
    else:
        # 多文件：Pass 1 + Pass 2 都批量合并
        total_lines = sum(n.size_lines for n in nodes)
        names = ", ".join(n.name for n in nodes[:3])
        if len(nodes) > 3:
            names += f" ...共{len(nodes)}个"
        batches.append(ScanBatch(
            nodes=nodes,
            pass_num=1,
            description=f"批量结构分析: {names} ({total_lines}行)",
        ))
        batches.append(ScanBatch(
            nodes=nodes,
            pass_num=2,
            description=f"批量生成MDC: {names}",
        ))


# ---- 第三步：执行扫描 ----

def _file_to_id(rel_path: str) -> str:
    """将文件路径转为 kebab-case ID。"""
    p = Path(rel_path)
    # e.g., src/main/java/com/example/UserService.java → user-service
    stem = p.stem
    # PascalCase / camelCase → kebab-case
    result = []
    for ch in stem:
        if ch.isupper() and result and result[-1] != "-":
            result.append("-")
        result.append(ch.lower())
    kebab = "".join(result).strip("-")
    # 去掉连续横线
    while "--" in kebab:
        kebab = kebab.replace("--", "-")
    return kebab


def _save_mdc_doc(doc_data: dict, rel_path: str, workspace_root: str):
    """将扫描结果保存为 MDC 文档到 .mdc-hub/docs/。"""
    docs_dir = get_docs_dir(workspace_root)
    # 镜像源文件路径结构
    source_path = Path(rel_path)
    if source_path.suffix:
        doc_rel = source_path.parent / (source_path.stem + ".md")
    else:
        doc_rel = source_path / "_index.md"
    doc_path = docs_dir / doc_rel
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    # 构建 frontmatter + body
    fm = {
        "id": doc_data.get("id", ""),
        "title": doc_data.get("title", source_path.stem),
        "category": doc_data.get("category", "general"),
        "tags": doc_data.get("tags", []),
        "connections": doc_data.get("connections", []),
        "summary": doc_data.get("summary", ""),
    }

    # 正文：保留额外字段
    body_parts = []
    if doc_data.get("classes"):
        body_parts.append("## 类/结构体\n")
        for cls in doc_data["classes"]:
            if isinstance(cls, dict):
                body_parts.append(f"- **{cls.get('name', '?')}** ({cls.get('role', '')})")
                for m in cls.get("methods", []):
                    body_parts.append(f"  - `{m}`")
                body_parts.append("")
    if doc_data.get("interfaces"):
        body_parts.append("## 接口\n")
        for iface in doc_data["interfaces"]:
            body_parts.append(f"- `{iface}`")
        body_parts.append("")
    if doc_data.get("apis"):
        body_parts.append("## 对外 API\n")
        for api in doc_data["apis"]:
            body_parts.append(f"- `{api}`")
        body_parts.append("")
    if doc_data.get("imports"):
        body_parts.append("## 关键依赖\n")
        for imp in doc_data["imports"]:
            body_parts.append(f"- `{imp}`")
        body_parts.append("")
    if doc_data.get("architecture"):
        body_parts.append("## 架构说明\n")
        body_parts.append(doc_data["architecture"])
        body_parts.append("")
    if doc_data.get("key_components"):
        body_parts.append("## 关键组件\n")
        for kc in doc_data["key_components"]:
            body_parts.append(f"- {kc}")
        body_parts.append("")

    body = "\n".join(body_parts) if body_parts else doc_data.get("summary", "")

    # 写入
    fm_lines = ["---"]
    for key, value in fm.items():
        fm_lines.append(yaml.dump({key: value}, allow_unicode=True, default_flow_style=False).strip())
    fm_lines.append("---")
    content = "\n".join(fm_lines) + "\n\n" + body.strip() + "\n"

    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(doc_path)


def execute_scan(
    batches: list[ScanBatch],
    workspace_root: str = "",
    verbose: bool = True,
) -> dict:
    """执行扫描批次，逐批调用 AI。

    Returns:
        {"total": N, "success": N, "failed": N, "docs": [...]}
    """
    stats = {"total": len(batches), "success": 0, "failed": 0, "docs": []}
    ws_root = workspace_root or find_workspace_root()

    # 缓存每次扫描的结果（用于 Pass 2 和目录汇总）
    scan_results: dict[str, dict] = {}  # rel_path → doc_data
    # 缓存目录下的子文档（用于 Pass 3）
    dir_children: dict[str, list[dict]] = {}

    for i, batch in enumerate(batches, 1):
        node = batch.node
        desc = batch.description

        if verbose:
            print(f"\n[{i}/{stats['total']}] {desc}")

        try:
            if batch.pass_num == 1:
                # ---- Pass 1: 文件结构分析 ----
                if len(batch.nodes) == 1:
                    # 单文件
                    node = batch.nodes[0]
                    chunk = node.chunks[batch.chunk_index]
                    chunk_info = ""
                    if len(node.chunks) > 1:
                        chunk_info = f"分块 {batch.chunk_index + 1}/{len(node.chunks)}"
                    prompt = build_file_scan_prompt(node.rel_path, chunk, chunk_info)
                    messages = [{"role": "system", "content": SCAN_SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
                    response = chat_sync(messages, temperature=0.2, max_tokens=8192, workspace_root=ws_root)
                    data = extract_json(response)
                    if data:
                        _init_scan_result(scan_results, node)
                        _merge_scan_data(scan_results[node.rel_path], data)
                else:
                    # 多文件合并
                    file_contents = [(n.rel_path, n.chunks[0]) for n in batch.nodes]
                    prompt = build_multi_file_prompt(file_contents)
                    messages = [{"role": "system", "content": SCAN_SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
                    response = chat_sync(messages, temperature=0.2, max_tokens=8192, workspace_root=ws_root)
                    results = _extract_json_array(response)
                    for item in results:
                        # 根据 file 字段匹配回对应的节点
                        file_path = item.get("file", "")
                        matched = None
                        for n in batch.nodes:
                            if n.rel_path == file_path or n.name == file_path:
                                matched = n
                                break
                        if matched:
                            _init_scan_result(scan_results, matched)
                            _merge_scan_data(scan_results[matched.rel_path], item)
                        else:
                            # 尝试用路径模糊匹配
                            for n in batch.nodes:
                                if file_path in n.rel_path or n.rel_path.endswith(file_path):
                                    _init_scan_result(scan_results, n)
                                    _merge_scan_data(scan_results[n.rel_path], item)
                                    break

                if verbose:
                    total_lines = sum(len(n.chunks[batch.chunk_index].split("\n")) if n.chunks else 0 for n in batch.nodes)
                    print(f"  ✓ 分析完成 ({len(batch.nodes)}文件, {total_lines}行)")

            elif batch.pass_num == 2:
                # ---- Pass 2: 生成 MDC 文档（支持批量） ----
                if len(batch.nodes) == 1:
                    # 单文件 MDC
                    node = batch.nodes[0]
                    key = node.rel_path
                    pass1 = scan_results.get(key, {})

                    summary_msg = f"""基于以下结构分析结果，为文件 `{node.rel_path}` 生成**详细的知识文档** JSON。

结构分析结果：
{json.dumps(pass1, ensure_ascii=False, indent=2)}

要求：
- summary 至少 200 字，包含核心逻辑流程
- architecture 必须有实质内容
- key_components 逐个列出并说明
- 保持 id 为 {pass1.get('id', _file_to_id(node.rel_path))}

请输出完整 JSON（id/title/category/tags/connections/summary/architecture/key_components/classes/interfaces/imports/apis）"""
                    messages = [
                        {"role": "system", "content": SCAN_SYSTEM_PROMPT},
                        {"role": "user", "content": summary_msg},
                    ]
                    response = chat_sync(messages, temperature=0.2, max_tokens=8192, workspace_root=ws_root)
                    final_data = extract_json(response) or pass1

                    if not final_data.get("id"):
                        final_data["id"] = _file_to_id(node.rel_path)

                    scan_results[key] = final_data
                    _finish_pass2(node, final_data, ws_root, stats, dir_children, verbose)
                else:
                    # 多文件批量 MDC 生成
                    analyses = []
                    for n in batch.nodes:
                        pass1 = scan_results.get(n.rel_path, {})
                        analyses.append({"rel_path": n.rel_path, "pass1": pass1})

                    prompt = build_multi_file_mdc_prompt(analyses)
                    messages = [
                        {"role": "system", "content": SCAN_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ]
                    response = chat_sync(messages, temperature=0.2, max_tokens=8192, workspace_root=ws_root)
                    results = _extract_json_array(response)

                    for item in results:
                        file_path = item.get("file", "")
                        matched = None
                        for n in batch.nodes:
                            if n.rel_path == file_path or n.name == file_path or file_path in n.rel_path:
                                matched = n
                                break
                        if matched:
                            final_data = item
                            if not final_data.get("id"):
                                final_data["id"] = _file_to_id(matched.rel_path)
                            scan_results[matched.rel_path] = final_data
                            _finish_pass2(matched, final_data, ws_root, stats, dir_children, verbose)

                    if verbose:
                        print(f"  ✓ 批量MDC完成 ({len(batch.nodes)}文件)")

            elif batch.pass_num == 3:
                # ---- Pass 3: 目录汇总 ----
                dir_rel = node.rel_path
                children = dir_children.get(dir_rel, [])
                if not children:
                    if verbose:
                        print(f"  - 无子文档，跳过")
                    continue

                prompt = build_directory_summary_prompt(dir_rel, children)
                messages = [
                    {"role": "system", "content": SCAN_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
                response = chat_sync(messages, temperature=0.2, max_tokens=8192, workspace_root=ws_root)
                data = extract_json(response)
                if not data:
                    # 兜底：自动生成
                    data = {
                        "id": _file_to_id(dir_rel) or Path(dir_rel).name.lower(),
                        "title": f"{node.name} — 模块总览",
                        "category": children[0].get("category", "general") if children else "general",
                        "tags": [],
                        "connections": [{"target": c["id"], "relation": "包含"} for c in children if c.get("id")],
                        "summary": f"包含 {len(children)} 个子模块",
                        "key_components": [c.get("title", c.get("id", "")) for c in children],
                    }

                # 保存
                doc_path = _save_mdc_doc(data, dir_rel, ws_root)
                node.doc_id = data.get("id", "")
                node.doc_data = data
                node.scanned = True
                stats["success"] += 1
                stats["docs"].append({"path": doc_path, "id": data.get("id", ""), "title": data.get("title", "")})

                # 向上传递
                parent_rel = str(Path(dir_rel).parent)
                if parent_rel not in dir_children:
                    dir_children[parent_rel] = []
                dir_children[parent_rel].append(data)

                if verbose:
                    print(f"  ✓ 目录汇总: {data.get('id', '')}")

        except Exception as e:
            stats["failed"] += 1
            if verbose:
                print(f"  ✗ 失败: {e}")

    return stats


def _merge_scan_data(existing: dict, new_data: dict):
    """合并多轮扫描结果。"""
    # 列表字段：去重追加
    for key in ["tags", "connections", "classes", "interfaces", "imports", "apis"]:
        if key in new_data:
            new_items = new_data[key]
            if isinstance(new_items, list):
                existing_list = existing.get(key, [])
                for item in new_items:
                    if item not in existing_list:
                        existing_list.append(item)
                existing[key] = existing_list

    # 字符串字段：非空则覆盖
    for key in ["id", "title", "category", "summary"]:
        if new_data.get(key):
            existing[key] = new_data[key]


def _finish_pass2(node: FileNode, final_data: dict, ws_root: str,
                   stats: dict, dir_children: dict, verbose: bool):
    """完成 Pass 2：保存 MDC 文档、更新统计。"""
    doc_path = _save_mdc_doc(final_data, node.rel_path, ws_root)
    node.doc_id = final_data["id"]
    node.doc_data = final_data
    node.scanned = True
    stats["success"] += 1
    stats["docs"].append({"path": doc_path, "id": final_data["id"], "title": final_data.get("title", "")})

    # 记录到父目录
    parent_rel = str(Path(node.rel_path).parent)
    if parent_rel not in dir_children:
        dir_children[parent_rel] = []
    dir_children[parent_rel].append(final_data)

    if verbose:
        print(f"  ✓ MDC 已保存: {node.doc_id}")


def _init_scan_result(scan_results: dict, node: FileNode):
    """初始化文件的扫描结果缓存。"""
    key = node.rel_path
    if key not in scan_results:
        scan_results[key] = {
            "id": _file_to_id(node.rel_path),
            "title": f"{node.name}",
            "category": "general",
            "tags": [],
            "connections": [],
            "summary": "",
            "classes": [],
            "interfaces": [],
            "imports": [],
            "apis": [],
        }


def _extract_json_array(text: str) -> list[dict]:
    """从 AI 响应中提取 JSON 数组。"""
    import re
    # 直接解析
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
    except json.JSONDecodeError:
        pass
    # 提取 ```json ... ``` 块
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1))
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return [data]
        except json.JSONDecodeError:
            pass
    # 提取 [ ... ]
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
    return []


# ---- 便捷入口 ----

def scan_workspace(
    directory: str,
    extensions: list[str] | None = None,
    chunk_size: int = 10000,
    verbose: bool = True,
) -> dict:
    """扫描工作区入口函数。

    Args:
        directory: 要扫描的目录
        extensions: 文件后缀列表（None 则从 settings.yaml 读取）
        chunk_size: AI 每次处理的行数
        verbose: 是否打印进度

    Returns:
        扫描统计信息
    """
    ws_root = find_workspace_root(directory)

    # 从配置读取默认值
    if extensions is None:
        config = load_config(ws_root)
        scan_cfg = config.get("scan", {})
        extensions = scan_cfg.get("extensions", [".py", ".java", ".ts", ".js", ".go"])
        if chunk_size == 10000:  # 默认值，尝试从配置覆盖
            chunk_size = scan_cfg.get("chunk_size", 10000)

    if verbose:
        print(f"\n工作区: {ws_root}")
        print(f"扫描目录: {directory}")
        print(f"文件后缀: {', '.join(extensions[:10])}{'...' if len(extensions) > 10 else ''}")
        print(f"分块大小: {chunk_size} 行\n")

    # Step 1: 构建文件树
    if verbose:
        print("→ 构建文件树...")
    tree = build_file_tree(directory, extensions, chunk_size, ws_root)
    file_count = sum(1 for _ in _iter_files(tree))
    if verbose:
        print(f"  找到 {file_count} 个文件")

    # Step 2: 规划批次
    if verbose:
        print("→ 规划扫描批次...")
    batches = plan_batches(tree, chunk_size)
    if verbose:
        print(f"  共 {len(batches)} 个批次")

    # Step 3: 执行
    if verbose:
        print(f"\n→ 开始扫描...")
    stats = execute_scan(batches, ws_root, verbose)

    if verbose:
        print(f"\n{'='*50}")
        print(f"扫描完成: 成功 {stats['success']}, 失败 {stats['failed']}, 共 {stats['total']}")
        print(f"文档归档: .mdc-hub/docs/")
        print(f"{'='*50}\n")

    return stats


def _iter_files(node: FileNode):
    """遍历所有文件节点。"""
    if node.is_dir:
        for child in node.children:
            yield from _iter_files(child)
    else:
        yield node
