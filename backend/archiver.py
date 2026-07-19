""".mdc-hub/ 归档目录管理模块。

负责：
- .mdc-hub/ 目录结构的初始化和配置
- 将生成的 MDC 文档归档到镜像的目录结构中
- 查询已归档的文档列表
"""

import os
import yaml
from pathlib import Path
from typing import Optional


# ---- 配置常量 ----
HUB_DIR = ".mdc-hub"
CONFIG_DIR = "config"
DOCS_DIR = "docs"
SETTINGS_FILE = "settings.yaml"


def find_workspace_root(start_path: Optional[str] = None) -> str:
    """向上查找项目根目录（有 .mdc-hub 或 .git 的目录）。

    如果找不到，返回当前工作目录。
    """
    current = Path(start_path or os.getcwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / HUB_DIR).is_dir() or (parent / ".git").is_dir():
            return str(parent)
    return str(current)


def get_hub_path(workspace_root: Optional[str] = None) -> Path:
    """获取 .mdc-hub/ 目录路径，不存在则自动创建。"""
    root = Path(workspace_root or find_workspace_root())
    hub = root / HUB_DIR
    hub.mkdir(parents=True, exist_ok=True)
    return hub


def get_config_dir(workspace_root: Optional[str] = None) -> Path:
    d = get_hub_path(workspace_root) / CONFIG_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_docs_dir(workspace_root: Optional[str] = None) -> Path:
    d = get_hub_path(workspace_root) / DOCS_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_config(workspace_root: Optional[str] = None) -> dict:
    """加载 .mdc-hub/config/settings.yaml，不存在则返回默认配置。"""
    config_file = get_config_dir(workspace_root) / SETTINGS_FILE
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {
        "workspace_root": find_workspace_root(workspace_root),
        "doc_dir": "docs",
    }


def save_config(config: dict, workspace_root: Optional[str] = None):
    """保存配置到 .mdc-hub/config/settings.yaml。"""
    config_dir = get_config_dir(workspace_root)
    config_file = config_dir / SETTINGS_FILE
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


def get_archive_path(source_file: str, workspace_root: Optional[str] = None) -> str:
    """将源码路径映射到归档路径。

    例如：
      source:  /project/src/main/java/com/example/dao/UserDao.java
      archive: /project/.mdc-hub/docs/src/main/java/com/example/dao/UserDao.md

    归档文件使用 .md 扩展名，保持与源码相同的目录层级。
    """
    root = Path(workspace_root or find_workspace_root()).resolve()
    source = Path(source_file).resolve()

    try:
        rel = source.relative_to(root)
    except ValueError:
        # source 不在 workspace 下，用文件名
        rel = Path(source.name)

    docs_dir = get_docs_dir(str(root))
    archive_path = docs_dir / rel.parent / (rel.stem + ".md")
    return str(archive_path)


def write_archived_doc(
    source_file: str,
    frontmatter: dict,
    body: str,
    workspace_root: Optional[str] = None,
) -> str:
    """将生成的 MDC 文档写入归档目录。

    Args:
        source_file: 原始源文件路径
        frontmatter: YAML frontmatter 字典（id, title, category, tags, connections 等）
        body: Markdown 正文内容
        workspace_root: 工作区根目录

    Returns:
        归档文件路径
    """
    archive_path = get_archive_path(source_file, workspace_root)
    archive_file = Path(archive_path)
    archive_file.parent.mkdir(parents=True, exist_ok=True)

    # 构建 frontmatter
    fm_lines = ["---"]
    for key, value in frontmatter.items():
        fm_lines.append(yaml.dump({key: value}, allow_unicode=True, default_flow_style=False).strip())
    fm_lines.append("---")

    content = "\n".join(fm_lines) + "\n\n" + body.strip() + "\n"

    with open(archive_file, "w", encoding="utf-8") as f:
        f.write(content)

    return str(archive_file)


def list_archived_docs(workspace_root: Optional[str] = None) -> list[dict]:
    """列出所有已归档的 MDC 文档。"""
    docs_dir = get_docs_dir(workspace_root)
    if not docs_dir.exists():
        return []

    docs = []
    for md_file in sorted(docs_dir.rglob("*.md")):
        rel = md_file.relative_to(docs_dir)
        docs.append({
            "path": str(md_file),
            "relative": str(rel),
            "name": md_file.stem,
        })
    return docs


def ensure_hub_structure(workspace_root: Optional[str] = None):
    """确保 .mdc-hub/ 目录结构存在。"""
    root = find_workspace_root(workspace_root)
    get_config_dir(root)
    get_docs_dir(root)

    # 确保有默认配置
    if not (get_config_dir(root) / SETTINGS_FILE).exists():
        save_config({"workspace_root": root, "doc_dir": "docs"}, root)
