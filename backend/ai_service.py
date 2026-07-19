"""DeepSeek AI 摘要服务。

调用 DeepSeek API 对 MDC 文件正文内容进行摘要、关键词提取、
标签建议等操作，并将结果回写到文件的 frontmatter 中。
"""

import os
import json
from datetime import datetime, timezone

import httpx

# DeepSeek API 配置
DEEPSEEK_API_URL = os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

SUMMARIZE_PROMPT = """你是一个知识管理助手。请分析以下 Markdown 文档内容，返回一个 JSON 格式的摘要结果。
JSON 格式如下（不要包含其他文字，只返回纯 JSON）：

{
  "summary": "200字以内的内容摘要，提炼核心要点",
  "tags": ["标签1", "标签2", "标签3"],
  "category": "推荐分类，格式如：技术/前端 或 业务/交易"
}

文档内容：
{body}
"""


async def summarize_content(body: str) -> dict | None:
    """调用 DeepSeek API 对文档内容进行摘要分析。

    Args:
        body: Markdown 文档正文内容

    Returns:
        {"summary": ..., "tags": [...], "category": ...} 或 None
    """
    if not DEEPSEEK_API_KEY:
        return _mock_summarize(body)

    prompt = SUMMARIZE_PROMPT.format(body=body[:8000])

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": DEEPSEEK_MODEL,
                    "messages": [
                        {"role": "system", "content": "你是一个知识管理助手，只返回 JSON。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1024,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content_text = data["choices"][0]["message"]["content"].strip()

            # 尝试提取 JSON
            return _extract_json(content_text)
        except Exception as e:
            print(f"[AI Service] DeepSeek API 调用失败: {e}")
            return None


def _extract_json(text: str) -> dict | None:
    """从文本中提取 JSON 对象。"""
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取 ```json ... ``` 块
    import re
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试找 { ... }
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _mock_summarize(body: str) -> dict:
    """未配置 API Key 时的 Mock 摘要（用于开发调试）。"""
    words = body.strip().split()
    preview = " ".join(words[:30])
    return {
        "summary": f"[Mock] 文档预览: {preview}...",
        "tags": ["mock", "待分类"],
        "category": "未分类",
    }


def save_summary_to_file(file_path: str, result: dict, model: str = DEEPSEEK_MODEL) -> bool:
    """将 AI 摘要结果写回到 MDC 文件的 frontmatter 中。

    Args:
        file_path: MDC 文件路径
        result: AI 返回的摘要结果
        model: 使用的模型名称

    Returns:
        是否写入成功
    """
    from scanner import parse_mdc_file, write_frontmatter

    node = parse_mdc_file(file_path)
    if not node:
        return False

    node.summary = result.get("summary", node.summary)
    node.tags = result.get("tags", node.tags)
    node.category = result.get("category", node.category)
    node.ai_model = model
    node.ai_summarized_at = datetime.now(timezone.utc).isoformat()

    return write_frontmatter(file_path, node)
