# MDC Hub

**知识库管理与可视化工具** — 将项目代码、文档、数据表自动转化为交互式知识图谱。

## 特性

- **MCP Server** — 6 个工具，AI 可直接调用扫描和分析
- **5 个内置 Skill** — 代码/表格/文档/媒体/统筹扫描，开箱即用
- **方法级知识图谱** — Java/Python/TS 每个方法独立节点，调用关系可视化
- **Web 可视化面板** — 拖拽节点、查看 Markdown 渲染、按分类筛选
- **暗色/亮色主题** — 完整的日夜模式支持
- **Mermaid 图表** — 文档中的 Mermaid 流程图自动渲染

## 快速开始

### 方式一：pip 安装（推荐，MCP 用户）

```bash
pip install git+https://github.com/GodShelvis/mdc-hub.git
```

安装后会获得 `mdc-hub-mcp` 命令。在 AI 工具的 MCP 设置中添加：

```json
{
  "mcpServers": {
    "mdc-hub": {
      "command": "mdc-hub-mcp"
    }
  }
}
```

即可使用。

### 方式二：完整安装（含 Web UI 和 Skills）

```bash
git clone https://github.com/GodShelvis/mdc-hub.git
cd mdc-hub
./install.sh
```

安装后 Skills 会自动复制到 `.trae/skills/`。

### 3. 启动 Web 可视化

终端 1（后端）：
```bash
.venv/bin/uvicorn backend.main:app --reload --port 8000
```

终端 2（前端）：
```bash
cd frontend && npm run dev
```

打开 `http://localhost:5173`

### 4. 使用

在 AI 工具中直接说：

> "扫描这个项目，生成知识图谱"

AI 会自动调用 `mdc-directory-scanner` Skill，按 7 步流程完成扫描。

## 架构

```
mdc-hub/
├── skills/                  # AI Skill（复制到 .trae/skills/ 使用）
│   ├── mdc-directory-scanner/   # 统筹入口（7步流程）
│   ├── mdc-code-scanner/        # 代码 → 方法级节点
│   ├── mdc-excel-scanner/       # 表格 → 表/Sheet级节点
│   ├── mdc-doc-scanner/         # 文档 → 章节级节点
│   └── mdc-media-scanner/       # 媒体 → 资源级节点
├── backend/                 # Python 后端
│   ├── mcp_server.py            # MCP Server（stdio）
│   ├── archiver.py              # .mdc-hub/ 归档管理
│   ├── main.py                  # FastAPI HTTP API
│   ├── scanner.py               # MDC 文件解析
│   └── ai_service.py            # AI 摘要服务
├── frontend/                # Vue 3 前端
│   └── src/
│       ├── components/          # 图表、文件树、分类筛选
│       ├── stores/              # Pinia 状态管理
│       └── utils/               # 颜色、Mermaid渲染
├── examples/                # 示例 MDC 文档
├── install.sh               # 一键安装
├── mcp-config.json          # MCP 配置模板
└── scripts/
    └── mcp-entry.sh         # MCP Server 启动入口
```

## MCP 工具

| 工具 | 描述 |
|------|------|
| `scan_directory` | 按文件类型扫描目录 |
| `read_files` | 批量读取文件 |
| `write_mdc_document` | 写入归档文档到 `.mdc-hub/docs/` |
| `list_archived_documents` | 列出已归档文档 |
| `get_workspace_info` | 获取工作区配置 |
| `open_dashboard` | 获取 Web UI 地址 |

## 文档格式 (MDC)

```yaml
---
id: "user-service"
title: "UserService — 用户服务"
category: "技术/后端/Service"
tags: [java, service, user]
connections:
  - target: "user-dao"
    relation: "依赖"
---

# Markdown 正文
...
```

详见 `examples/tooling/mdc-spec.md`。

## License

MIT
