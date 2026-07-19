# MDC Hub

[English](README.en.md) | 中文

**知识库管理与可视化工具** — 将项目代码、文档、数据表自动转化为交互式知识图谱。

## 特性

- **一键安装离线可用** — wheel 包内置前端+Skills+预设，`pip install` 即可
- **AI 深度扫描** — 逐段逐点分析代码，生成 200-500 字详细知识文档
- **批量合并策略** — 自底向上 + 跨目录合并最大化 AI 利用率，Pass 2 自动分小批
- **Web 可视化面板** — 交互式知识图谱，查看 Markdown 文档，按分类/标签筛选
- **暗色/亮色主题** — 完整的日夜模式支持
- **内置 Skills** — 5 个专业 Skill（代码/表格/文档/媒体/统筹扫描），开箱即用

## 快速开始

### 安装

```bash
# 方式一：从 GitHub Release 下载 wheel 离线安装
pip install mdc_hub-0.3.0-py3-none-any.whl

# 方式二：从源码安装
pip install "mdc-hub @ git+https://github.com/GodShelvis/mdc-hub.git"
```

### 初始化配置

```bash
mdc-hub install       # 选择 AI 工具（Claude Code / OpenCode）安装 MCP 配置 + Skills
mdc-hub provider setup  # 配置 AI 提供商
```

### 扫描并生成知识图谱

```bash
mdc-hub scan src --dry-run  # 预览扫描计划
mdc-hub scan src            # 执行 AI 深度扫描
```

### 一键启动 Web

```bash
mdc-hub serve
```

打开 `http://localhost:8000`，前端自动加载已扫描的知识文档。

## CLI 参考

| 命令 | 说明 |
|------|------|
| `mdc-hub install` | 选择 AI 工具，安装 MCP 配置 + Skills |
| `mdc-hub serve` | 启动后端 API + 前端静态页面 |
| `mdc-hub scan <dir>` | AI 深度扫描，生成知识图谱文档 |
| `mdc-hub mcp` | 启动 MCP Server（stdio 模式） |
| `mdc-hub provider setup` | 交互式配置 AI 提供商 |
| `mdc-hub graph list` | 列出 MDC 知识节点 |
| `mdc-hub graph neighbors` | 遍历节点 N 层邻居 |
| `mdc-hub graph path` | 查找两节点最短路径 |

### scan — AI 智能扫描

```bash
mdc-hub scan                     # 扫描当前目录
mdc-hub scan ./src               # 扫描指定目录
mdc-hub scan --dry-run           # 预览扫描计划
mdc-hub scan -e .py -e .java     # 仅扫描指定后缀
```

扫描策略：自底向上 → 批量合并 Pass 1 → Pass 2 分小批生成 MDC → Pass 3 目录汇总。默认 10000 行/块，支持 29 种文件格式。

### serve — 启动 Web UI

```bash
mdc-hub serve                  # 默认端口 8000
mdc-hub serve --port 3000      # 自定义端口
mdc-hub serve -p ./my-project  # 指定项目目录
```

自动初始化 `.mdc-hub/`，同时托管后端 API 和前端静态页面。

### provider setup — 配置 AI 提供商

```bash
mdc-hub provider setup
```

选择预设提供商（OpenAI/DeepSeek/智谱/通义千问 等）或自定义 → 输入 API Key → 自动获取模型列表。

### graph — 图谱查询

```bash
mdc-hub graph list ./docs              # 列出节点
mdc-hub graph neighbors user-svc ./docs -d 2  # 2层邻居
mdc-hub graph path a b ./docs          # 最短路径
```

## 开发状态

### 已完成

- [x] CLI 工具：`install` / `serve` / `scan` / `provider` / `graph` / `mcp`
- [x] AI 深度扫描引擎（Pass 1 结构分析 → Pass 2 MDC 生成 → Pass 3 目录汇总）
- [x] 批量合并策略 + 自底向上分析
- [x] Wheel 离线打包（前端+Skills+预设全内置）
- [x] Web 可视化面板（节点拖拽、Markdown 渲染、分类筛选）
- [x] 5 个内置 Skill（代码/表格/文档/媒体/统筹）
- [x] Claude Code / OpenCode MCP 配置 + Skills 安装
- [x] 跨平台（Windows/macOS/Linux）纯 Python wheel
- [x] 暗色/亮色主题

### 进行中

- [ ] MCP Server — 基础框架已有（`mdc-hub mcp` 可启动），工具和 Skill 联动待完善
- [ ] Web 端 Markdown 文档在线编辑
- [ ] 基于 AI 的文档内容调整（局部重写 / 全文优化）

### 计划中

- [ ] 文档解析器：Word (.docx) / Excel (.xlsx) / PowerPoint (.pptx)
- [ ] Web 端工作区内创建新文档
- [ ] 更多 AI 工具 MCP 集成（Codex、Cursor 等）
- [ ] 增量扫描（只分析变更文件）

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
│   ├── scan_engine.py           # 扫描引擎
│   └── web_dist/                # 前端静态文件（打包到 wheel）
├── cli/                     # CLI 命令行
│   └── main.py                  # install / serve / provider / scan / graph / mcp
├── frontend/                # Vue 3 前端
├── config/                  # 预设配置（providers/tags/categories）
└── .github/workflows/       # CI/CD（Release 自动构建 wheel）
```

## License

MIT
