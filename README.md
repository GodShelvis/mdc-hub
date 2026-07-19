# MDC Hub

[English](README.en.md) | 中文

**知识库管理与可视化工具** — 将项目代码、文档、数据表自动转化为交互式知识图谱。

## 特性

- **一键安装离线可用** — wheel 包内置前端+Skills+预设，`pip install` 即可
- **AI 深度扫描** — 逐段逐点分析代码，生成 200-500 字详细知识文档
- **批量合并策略** — 自底向上 + 跨目录合并，28 文件仅需 24 次 AI 调用
- **Web 可视化面板** — 拖拽节点、查看详细 Markdown 文档、按分类筛选
- **暗色/亮色主题** — 完整的日夜模式支持
- **MCP Server** — 6 个工具，AI 可直接调用扫描和分析
- **5 个内置 Skill** — 代码/表格/文档/媒体/统筹扫描，开箱即用

## 快速开始

### 安装

```bash
# 方式一：从 GitHub Release 下载 wheel 离线安装
pip install mdc_hub-0.3.0-py3-none-any.whl

# 方式二：从源码安装（含 MCP）
pip install "mdc-hub @ git+https://github.com/GodShelvis/mdc-hub.git"
```

### 初始化配置

```bash
mdc-hub install       # 选择 AI 工具安装 MCP 配置 + Skills
mdc-hub provider setup  # 配置 AI 提供商（DeepSeek/OpenAI 等）
```

`mdc-hub install` 会列出所有 AI 工具及其状态，让你自由选择要配置哪些。

### 扫描并生成知识图谱

```bash
mdc-hub scan src --dry-run  # 预览扫描计划
mdc-hub scan src            # 执行 AI 深度扫描
```

### 一键启动 Web

```bash
mdc-hub serve
# 或指定项目目录
mdc-hub serve -p /path/to/project
```

打开 `http://localhost:8000`，前端自动加载已扫描的知识文档。

## CLI 参考

| 命令 | 说明 |
|------|------|
| `mdc-hub install` | 选择 AI 工具，安装 MCP 配置 + Skills |
| `mdc-hub serve` | 启动后端 API + 前端静态页面 |
| `mdc-hub scan <dir>` | AI 深度扫描，生成知识图谱文档 |
| `mdc-hub provider setup` | 交互式配置 AI 提供商 |
| `mdc-hub graph list` | 列出 MDC 知识节点 |
| `mdc-hub graph neighbors` | 遍历节点 N 层邻居 |
| `mdc-hub graph path` | 查找两节点最短路径 |

### install — 安装配置

```bash
mdc-hub install              # 选择工具安装
mdc-hub install --dry-run    # 仅预览
mdc-hub install --project ./my-project
```

交互式选择：展示所有工具（Trae/Cursor/Claude Code 等 9 个平台）的检测状态和配置状态，输入编号选择要安装的工具。

### serve — 启动 Web UI

```bash
mdc-hub serve                  # 默认端口 8000
mdc-hub serve --port 3000      # 自定义端口
mdc-hub serve -p ./my-project  # 指定项目目录
```

自动初始化 `.mdc-hub/` 结构，同时托管后端 API 和前端静态页面。

### scan — AI 智能扫描

```bash
mdc-hub scan                     # 扫描当前目录
mdc-hub scan ./src               # 扫描指定目录
mdc-hub scan --dry-run           # 预览扫描计划
mdc-hub scan -e .py -e .java     # 仅扫描指定后缀
```

扫描策略：
- 自底向上：先分析最深层文件 → 逐层汇总目录
- 批量合并：同深度文件一次分析，最大化 AI 利用率
- 默认 10000 行/块，支持 29 种文件格式
- AI 逐段逐点分析，生成 200-500 字详细文档

### provider setup — 配置 AI 提供商

```bash
mdc-hub provider setup
```

流程：选择提供商（OpenAI/DeepSeek/智谱/通义千问等）→ 输入 API Key → 自动获取模型列表。

### graph — 图谱查询

```bash
mdc-hub graph list ./docs              # 列出节点
mdc-hub graph neighbors user-svc ./docs -d 2  # 2层邻居
mdc-hub graph path a b ./docs          # 最短路径
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

## 架构

```
mdc-hub/
├── skills/                  # 5 个内置 Skill
│   ├── mdc-directory-scanner/   # 统筹入口
│   ├── mdc-code-scanner/        # 代码 → 方法级节点
│   ├── mdc-excel-scanner/       # 表格分析
│   ├── mdc-doc-scanner/         # 文档分析
│   └── mdc-media-scanner/       # 媒体分析
├── backend/                 # Python 后端
│   ├── mcp_server.py            # MCP Server（stdio）
│   ├── archiver.py              # .mdc-hub/ 归档管理
│   ├── main.py                  # FastAPI HTTP API
│   ├── scanner.py               # MDC 文件解析
│   ├── ai_service.py            # AI 接口 + 提示词
│   ├── scan_engine.py           # 扫描引擎（自底向上批量分析）
│   └── web_dist/                # 前端静态文件（打包到 wheel）
├── cli/                     # CLI 命令行
│   └── main.py                  # install / serve / provider / scan / graph
├── frontend/                # Vue 3 前端
├── config/                  # 预设配置
└── .github/workflows/       # CI/CD（Release 自动构建 wheel）
```

## 文档格式 (MDC)

```yaml
---
id: "user-service"
title: "UserService — 用户服务"
category: "backend-core"
tags: [java, service, user]
connections:
  - target: "user-dao"
    relation: "依赖"
summary: "用户服务核心模块，负责用户注册、登录、信息管理等业务逻辑..."
---

## 架构说明
...

## 关键组件
- UserController — 处理 HTTP 请求
- UserService — 核心业务逻辑
...
```

## License

MIT
