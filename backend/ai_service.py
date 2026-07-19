"""AI 服务模块 — 通用 OpenAI 兼容接口。

从 .mdc-hub/config/settings.yaml 读取提供商配置，
支持任意 OpenAI 兼容的 API（OpenAI / DeepSeek / 智谱 / 通义千问 等）。
"""

import json
import re
import httpx

from backend.archiver import load_config, find_workspace_root

# ---- 提供商配置加载 ----

def _get_provider_config(workspace_root: str = "") -> dict | None:
    """从 settings.yaml 读取提供商配置。"""
    config = load_config(workspace_root or find_workspace_root())
    provider = config.get("provider", {})
    if not provider.get("api_key"):
        return None
    return provider


def _get_provider_config_or_raise() -> dict:
    """读取提供商配置，未配置则抛异常。"""
    cfg = _get_provider_config()
    if not cfg:
        raise RuntimeError(
            "未配置 AI 提供商。请先运行:\n"
            "  mdc-hub provider setup\n"
            "或\n  mdc-hub install"
        )
    return cfg


# ---- 核心调用 ----

async def chat(
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 4096,
    workspace_root: str = "",
) -> str:
    """调用 AI 聊天接口，返回文本内容。

    Args:
        messages: [{"role": "system"|"user", "content": "..."}]
        temperature: 随机性（0-2）
        max_tokens: 最大输出 token 数
        workspace_root: 工作区根目录（用于读取配置）

    Returns:
        AI 返回的文本
    """
    provider = _get_provider_config(workspace_root)
    if not provider:
        raise RuntimeError(
            "未配置 AI 提供商。请先运行:\n"
            "  mdc-hub provider setup\n"
            "或\n  mdc-hub install"
        )
    base_url = provider["base_url"].rstrip("/")
    api_key = provider["api_key"]
    model = provider["model"]

    url = base_url + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


def chat_sync(
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 4096,
    workspace_root: str = "",
) -> str:
    """同步版 chat，用于 CLI 命令。"""
    import asyncio
    return asyncio.run(chat(messages, temperature, max_tokens, workspace_root))


# ---- 辅助 ----

def extract_json(text: str) -> dict | None:
    """从文本中提取 JSON 对象。"""
    # 直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # ```json ... ``` 块
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # { ... }
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


# ---- 扫描专用提示词 ----

SCAN_SYSTEM_PROMPT = """你是一个资深代码分析专家，负责深度分析源代码并生成高质量的结构化知识文档。

你必须严格按 JSON 格式返回结果，不要包含其他文字。

## 分析要求

对每个文件进行**逐段逐点的细化分析**，不要只给一两句话的概括。具体要求：

1. **文件概述**（3-5句话）：准确描述文件职责、在项目中的角色、解决了什么问题
2. **架构说明**：详细解释文件的内部架构设计，包括：
   - 模块/组件的组织结构
   - 数据流和控制流
   - 设计模式的使用
   - 与其他模块的交互方式
3. **结构分析**：
   - 类/接口/结构体：名称、作用（详细说明，不是简单标签）、继承关系、关键方法及其用途
   - 函数/方法：逐个列出签名，说明每个方法的**具体业务逻辑**（做了什么，不是泛泛的"处理数据"）
   - 每个关键属性/状态的用途
4. **关键组件**：逐个列出文件中的核心元素，每个附带一句话说明其作用
5. **依赖关系**：导入的外部依赖，说明每个依赖在文件中的具体用途
6. **对外 API**：暴露的接口/端点/公共方法，说明每个的输入输出和用途

## 输出格式

summary 字段要达到 **200-500字**，必须包含文件的核心逻辑流程。
architecture 字段要有实质内容，说明架构设计。
key_components 列出关键组件并逐个说明。

文档分类（category）必须从以下预设分类中选择一个最匹配的：
backend-core, frontend-core, mobile-core, database-core, middleware-core,
devops-core, architecture-core, security-core, testing-core, ui-design-core,
ai-ml-core, data-core, document-core, data-analysis-core, management-core, general

标签（tags）尽量使用以下预设标签（可补充自定义）：
java, python, javascript, typescript, go, rust, c, cpp, swift, kotlin, dart,
spring-boot, mybatis, flask, django, fastapi, express, nestjs, react, vue, angular,
mysql, postgresql, mongodb, redis, kafka, rabbitmq, docker, kubernetes,
class, interface, function, method, config, util, controller, service, dao, dto,
api, cli, script, build, test, deploy, ci, cd"""


def build_file_scan_prompt(file_path: str, content: str, chunk_info: str = "") -> str:
    """构建单文件扫描提示词。"""
    header = f"请深度分析以下源文件：`{file_path}`"
    if chunk_info:
        header += f"（{chunk_info}）"

    return f"""{header}

```
{content}
```

请逐段逐点分析，返回 JSON（summary 至少200字，architecture 必须有实质内容）：
{{
  "id": "文件唯一 ID（kebab-case，如 user-service）",
  "title": "文件名 — 准确描述职责",
  "category": "从预设分类中选择",
  "tags": ["标签列表"],
  "connections": [
    {{"target": "被引用的其他文件 id", "relation": "依赖/调用/实现/继承/配置"}}
  ],
  "summary": "详细概述（200-500字），包含文件核心逻辑流程",
  "architecture": "内部架构说明：模块组织、数据流、设计模式、模块交互",
  "key_components": ["关键组件1 — 简要说明", "关键组件2 — 简要说明"],
  "classes": [{{"name": "类名", "role": "详细职责说明（不是简单标签）", "methods": ["方法签名 — 用途说明"]}}],
  "interfaces": ["接口名 — 用途"],
  "imports": ["依赖 — 在文件中的用途"],
  "apis": ["API/公共方法 — 输入输出和用途"]
}}"""


def build_multi_file_prompt(files: list[tuple[str, str]]) -> str:
    """构建多文件批量扫描提示词。"""
    sections = []
    for rel_path, content in files:
        sections.append(f"### 文件: `{rel_path}`\n```\n{content}\n```")
    file_list = "\n\n".join(sections)

    return f"""请**逐段逐点深度分析**以下 {len(files)} 个文件，每个文件返回一个详细的分析结果。返回 JSON 数组：

{file_list}

要求：
- 每个文件的 summary 至少 200 字，含核心逻辑流程
- architecture 必须有实质内容（模块组织、数据流等）
- key_components 逐个列出并说明
- classes 的方法要附带用途说明
- imports/apis 要说明具体用途

返回 JSON 数组（只返回 JSON，不要其他文字）：
[
  {{
    "file": "文件路径（保持原样）",
    "id": "kebab-case ID",
    "title": "文件名 — 准确职责",
    "category": "从预设中选择",
    "tags": ["标签"],
    "connections": [{{"target": "id", "relation": "依赖/调用/实现"}}],
    "summary": "详细概述（200-500字）",
    "architecture": "内部架构说明",
    "key_components": ["组件 — 说明"],
    "classes": [{{"name": "类名", "role": "详细职责", "methods": ["签名 — 用途"]}}],
    "interfaces": ["接口 — 用途"],
    "imports": ["依赖 — 用途"],
    "apis": ["API — 用途"]
  }},
  ...
]"""


def build_multi_file_mdc_prompt(file_analyses: list[dict]) -> str:
    """构建多文件批量 MDC 生成提示词。
    
    将 Pass 1 的结构分析结果合并，一次 AI 调用生成多个文件的最终 MDC 文档。
    """
    sections = []
    for a in file_analyses:
        pass1_json = json.dumps(a["pass1"], ensure_ascii=False, indent=2)
        sections.append(f"### 文件: `{a['rel_path']}`\n```json\n{pass1_json}\n```")
    file_blocks = "\n\n".join(sections)

    return f"""基于以下 {len(file_analyses)} 个文件的结构分析结果，为每个文件生成**详细的知识文档** JSON，返回一个 JSON 数组：

{file_blocks}

## 要求
- summary 必须 200-500 字，包含文件核心逻辑流程
- architecture 必须有实质内容
- key_components 逐个列出并附说明
- connections 正确关联其他文件

返回 JSON 数组（只返回 JSON，不要其他文字）：
[
  {{
    "file": "文件路径（保持原样）",
    "id": "kebab-case ID（与结构分析一致）",
    "title": "文件名 — 准确职责描述",
    "category": "从预设分类中选择",
    "tags": ["标签"],
    "connections": [{{"target": "其他文件id", "relation": "依赖/调用/实现/继承/配置"}}],
    "summary": "详细概述（200-500字），含逻辑流程",
    "architecture": "内部架构说明",
    "key_components": ["关键组件 — 说明"],
    "classes": [{{"name": "类名", "role": "详细职责", "methods": ["签名 — 用途"]}}],
    "interfaces": ["接口 — 用途"],
    "imports": ["依赖 — 用途"],
    "apis": ["API — 用途"]
  }},
  ...
]"""


def build_directory_summary_prompt(dir_path: str, child_docs: list[dict]) -> str:
    """构建目录级汇总提示词（汇总子文档，不重复扫源文件）。"""
    children_text = ""
    for doc in child_docs:
        children_text += f"- [{doc['id']}] {doc['title']} (category: {doc.get('category', '')})\n"
        if doc.get("summary"):
            children_text += f"  {doc['summary'][:150]}\n"

    return f"""以下是目录 `{dir_path}` 下所有已扫描的子文档摘要：

{children_text}

请为该目录生成**详细的汇总知识文档**，返回 JSON：
{{
  "id": "目录 ID（kebab-case，如 user-module）",
  "title": "目录名 — 模块整体职责概述",
  "category": "从预设分类中选择最合适的",
  "tags": ["汇总标签"],
  "connections": [
    {{"target": "子文档 id", "relation": "包含"}},
    {{"target": "外部依赖 id", "relation": "依赖"}}
  ],
  "summary": "模块功能概述（200-500字），说明该目录的整体职责和设计思路",
  "architecture": "模块架构说明：各子模块之间的关系、数据流、整体设计",
  "key_components": ["子模块1 — 说明", "子模块2 — 说明"]
}}

注意：
- summary 必须 200-500 字，详细说明目录职责
- architecture 说明子模块间的组织关系和交互
- key_components 逐个列出子模块并附说明
- connections 中必须包含所有子文档的 "包含" 关系
- 基于子文档内容进行抽象总结，不要编造信息"""


# ---- 旧 API 兼容（Web Dashboard 使用） ----

async def summarize_content(body: str) -> dict | None:
    """对 MDC 文档正文进行 AI 摘要（兼容旧 API）。"""
    provider = _get_provider_config()
    if not provider:
        return _mock_summarize(body)

    prompt = f"""你是一个知识管理助手。请分析以下 Markdown 文档内容，返回 JSON：
{{"summary": "200字以内的内容摘要", "tags": ["标签1", "标签2"], "category": "推荐分类"}}
文档内容：{body[:8000]}"""

    try:
        text = await chat([
            {"role": "system", "content": "你是一个知识管理助手，只返回 JSON。"},
            {"role": "user", "content": prompt},
        ])
        return extract_json(text)
    except Exception:
        return _mock_summarize(body)


def save_summary_to_file(file_path: str, result: dict, model: str = "") -> bool:
    """将 AI 摘要回写到 MDC 文件（兼容旧 API）。"""
    from datetime import datetime, timezone
    from backend.scanner import parse_mdc_file, write_frontmatter

    node = parse_mdc_file(file_path)
    if not node:
        return False
    node.summary = result.get("summary", node.summary)
    node.tags = result.get("tags", node.tags)
    node.category = result.get("category", node.category)
    node.ai_model = model or _get_provider_config().get("model", "")
    node.ai_summarized_at = datetime.now(timezone.utc).isoformat()
    return write_frontmatter(file_path, node)


def _mock_summarize(body: str) -> dict:
    """未配置 API Key 时的 Mock 摘要。"""
    words = body.strip().split()
    preview = " ".join(words[:30])
    return {
        "summary": f"[Mock] 文档预览: {preview}...",
        "tags": ["mock", "待分类"],
        "category": "未分类",
    }
