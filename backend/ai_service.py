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
) -> str:
    """调用 AI 聊天接口，返回文本内容。

    Args:
        messages: [{"role": "system"|"user", "content": "..."}]
        temperature: 随机性（0-2）
        max_tokens: 最大输出 token 数

    Returns:
        AI 返回的文本
    """
    provider = _get_provider_config_or_raise()
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
) -> str:
    """同步版 chat，用于 CLI 命令。"""
    import asyncio
    return asyncio.run(chat(messages, temperature, max_tokens))


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

SCAN_SYSTEM_PROMPT = """你是一个代码分析助手，负责分析源代码并生成结构化的知识文档。

你必须严格按 JSON 格式返回结果，不要包含其他文字。

对于每个文件，你需要提取：
1. 文件概述：一句话描述文件职责
2. 结构分析：
   - 类/接口/结构体定义（名称、注解/装饰器、继承关系）
   - 函数/方法签名（名称、参数、返回值）
   - 导入的依赖
   - 关键常量和配置
3. 逻辑分析：核心业务流程简述
4. 对外暴露的 API/接口

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
    header = f"请分析以下源文件：`{file_path}`"
    if chunk_info:
        header += f"（{chunk_info}）"

    return f"""{header}

``` 
{content}
```

请返回 JSON：
{{
  "id": "文件唯一 ID（kebab-case，如 user-service）",
  "title": "文件名 — 一句话职责描述",
  "category": "从预设分类中选择",
  "tags": ["标签列表"],
  "connections": [
    {{"target": "被引用的其他文件 id", "relation": "关系类型：依赖/调用/实现/继承/配置"}}
  ],
  "summary": "文件概述（≤100字）",
  "classes": [{{"name": "类名", "role": "职责（Service/Controller/Model等）", "methods": ["方法签名"]}}],
  "interfaces": ["接口/协议名"],
  "imports": ["关键依赖"],
  "apis": ["对外暴露的 API 端点或公共方法"]
}}"""


def build_multi_file_prompt(files: list[tuple[str, str]]) -> str:
    """构建多文件批量扫描提示词。"""
    sections = []
    for rel_path, content in files:
        sections.append(f"### 文件: `{rel_path}`\n```\n{content}\n```")
    file_list = "\n\n".join(sections)

    return f"""请同时分析以下 {len(files)} 个文件，返回一个 JSON 数组，每个元素对应一个文件：

{file_list}

返回 JSON 数组（只返回 JSON，不要其他文字）：
[
  {{
    "file": "文件路径（保持原样）",
    "id": "kebab-case ID",
    "title": "文件名 — 一句话职责",
    "category": "从预设中选择",
    "tags": ["标签"],
    "connections": [{{"target": "id", "relation": "依赖/调用/实现"}}],
    "summary": "概述（≤100字）",
    "classes": [{{"name": "类名", "role": "职责", "methods": ["签名"]}}],
    "interfaces": ["接口名"],
    "imports": ["依赖"],
    "apis": ["API"]
  }},
  ...
]"""


def build_directory_summary_prompt(dir_path: str, child_docs: list[dict]) -> str:
    """构建目录级汇总提示词（汇总子文档，不重复扫源文件）。"""
    children_text = ""
    for doc in child_docs:
        children_text += f"- [{doc['id']}] {doc['title']} (category: {doc.get('category', '')})\n"
        if doc.get("summary"):
            children_text += f"  {doc['summary']}\n"

    return f"""以下是目录 `{dir_path}` 下所有已扫描的子文档摘要：

{children_text}

请生成该目录的汇总文档，返回 JSON：
{{
  "id": "目录 ID（kebab-case，如 user-module）",
  "title": "目录名 — 模块职责概述",
  "category": "从预设分类中选择最合适的",
  "tags": ["汇总标签"],
  "connections": [
    {{"target": "子文档 id", "relation": "包含"}},
    {{"target": "外部依赖 id", "relation": "依赖"}}
  ],
  "summary": "模块功能概述（≤200字）",
  "architecture": "简要的模块架构说明（如有）",
  "key_components": ["关键组件名称列表"]
}}

注意：
- connections 中必须包含所有子文档的 "包含" 关系
- 如果子文档中有对外部模块的引用，也要在 connections 中体现
- 基于子文档内容进行抽象总结，不要编造信息"""
