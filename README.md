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

### 一键安装

```bash
pip install "mdc-hub[mcp] @ git+https://github.com/GodShelvis/mdc-hub.git"
mdc-hub install
```

`mdc-hub install` 会自动检测已安装的 AI 工具，写入 MCP 配置，并将 5 个内置 Skill 安装到对应目录（支持 Claude Desktop、Cursor、VS Code、Trae 等 9 个平台）。

安装完成后，在任意 AI 工具中直接使用：

> "扫描这个项目，生成知识图谱"

AI 会自动调用 `mdc-directory-scanner` Skill，按 7 步流程完成扫描和归档。

### 启动 Web 可视化

```bash
mdc-hub serve --port 8000
```

打开浏览器访问 `http://localhost:8000`，即可在交互式图谱面板中查看所有 MDC 节点。

## CLI 参考

`mdc-hub` 提供以下子命令：

### install — 安装配置

自动检测 AI 工具，写入 MCP 配置，安装 Skills。

```bash
mdc-hub install              # 自动检测并安装
mdc-hub install --dry-run    # 仅预览，不实际写入
```

支持平台：Claude Desktop、Cursor、VS Code Insiders、VS Code、Windsurf、Trae、Trae CN、CodeBuddy、Qoder。

### serve — 启动 Web UI

一键启动后端 API + 前端静态页面。

```bash
mdc-hub serve                  # 默认端口 8000
mdc-hub serve --port 3000      # 自定义端口
mdc-hub serve --dev            # 开发模式（自动重载）
```

### graph list — 列出节点

列出指定目录下所有 MDC 知识图谱节点。

```bash
mdc-hub graph list ./my-project
mdc-hub graph list ./my-project --json   # JSON 格式输出
```

示例输出（`--json`）：

```json
[
  {"id": "user-service", "title": "UserService — 用户服务", "category": "技术/后端/Service", "tags": ["java", "service"]},
  {"id": "user-service.findById", "title": "UserService.findById()", "category": "技术/后端/Service/UserService", "tags": ["java", "method"]},
  {"id": "user-dao", "title": "UserDao — 用户数据访问", "category": "技术/后端/Dao", "tags": ["java", "dao"]}
]
```

### graph neighbors — 邻居遍历

遍历指定节点的 N 层邻居节点，支持方向控制。

```bash
mdc-hub graph neighbors user-service ./my-project
mdc-hub graph neighbors user-service ./my-project -d 2          # 2 层深度
mdc-hub graph neighbors user-service ./my-project -r down       # 仅下游（被调用的）
mdc-hub graph neighbors user-service ./my-project -r up         # 仅上游（调用方）
mdc-hub graph neighbors user-service ./my-project -r both       # 双向（默认）
```

参数说明：

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--depth` | `-d` | 遍历深度（层数） | 1 |
| `--relation` | `-r` | 遍历方向：`up` / `down` / `both` | `both` |

示例输出：

```
Neighbors of "user-service" (depth=1, direction=both):

  Upstream (调用方):
    user-controller  [依赖]   user-service
    admin-controller [依赖]   user-service

  Downstream (被调用方):
    user-service      [依赖]  user-dao
    user-service      [依赖]  cache-service
    user-service      [依赖]  email-service
```

### graph path — 最短路径

查找两个节点之间的最短调用路径。

```bash
mdc-hub graph path user-controller email-service ./my-project
mdc-hub graph path user-controller email-service ./my-project -d 5   # 限制最大深度
```

参数说明：

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--depth` | `-d` | 最大搜索深度 | 10 |

示例输出：

```
Shortest path from "user-controller" to "email-service" (length=3):

  user-controller
    └─ [依赖] → user-service
                  └─ [依赖] → notification-service
                                └─ [依赖] → email-service
```

## MCP 工具

以下工具由 MCP Server 暴露，AI 加载 Skill 后可直接调用：

| 工具 | 描述 |
|------|------|
| `scan_directory` | 按文件类型扫描目录，支持类型过滤 |
| `read_files` | 批量读取文件内容 |
| `write_mdc_document` | 写入归档文档到 `.mdc-hub/docs/` |
| `list_archived_documents` | 列出已归档文档 |
| `get_workspace_info` | 获取工作区根目录和配置 |
| `open_dashboard` | 获取 Web UI 访问地址 |

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
