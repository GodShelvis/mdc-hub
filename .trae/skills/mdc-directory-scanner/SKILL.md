---
name: "mdc-directory-scanner"
description: "统筹扫描整个目录，按文件类型分流到专业子扫描器。Invoke when user asks to scan a project directory, analyze all files, or build a complete knowledge graph from mixed file types."
---

# MDC Directory Scanner — 统筹目录扫描器

## 定位

本 Skill 是 MDC Hub 的**入口 Skill**。它负责全局扫描、按文件类型分流、协调跨类型节点连线，不处理具体文件的分析逻辑。

具体文件类型的分析由子 Skill 完成：
- `mdc-code-scanner` — 代码（Java/Python/TS 等）
- `mdc-excel-scanner` — 表格（Excel/CSV）
- `mdc-doc-scanner` — 文档（Word/PDF/Markdown）
- `mdc-media-scanner` — 媒体（图片/视频/音频）

## MCP 工具

| 工具 | 用途 |
|------|------|
| `scan_directory` | 扫描目录，支持按类型过滤 |
| `read_files` | 批量读取文件内容 |
| `write_mdc_document` | 写入归档 MDC 文档 |
| `list_archived_documents` | 列出已归档文档 |
| `get_workspace_info` | 获取工作区信息 |
| `open_dashboard` | 获取 Web UI 地址 |

## 分类与标签约束

**强制规则**：生成 MDC 文档时，`category` 和 `tags` 必须从预设库中选取。

### 分类库（categories）
- 位置：`.mdc-hub/categories.yaml`
- 用 `read_files` 读取后，从 `categories.id` 中选择最匹配的分类
- 共 17 个预设大类，覆盖开发、办公、数据分析、项目管理等领域
- 双语别名匹配：文档中出现"数据库"/"database"/"MySQL"均可命中 `database`

### 标签库（tags）
- 位置：`.mdc-hub/tags.yaml`
- 用 `read_files` 读取后，从 `tags.id` 中选择 3-5 个最匹配的标签
- 共 80+ 个预设标签，覆盖编程语言、框架、数据库、中间件、DevOps、AI/ML、办公等
- 通用编程概念（class/function/field/package/dependency 等）仅用英文 id
- 每个标签标注了 `scope`，明确适用领域

### summary 字段约束
- **纯文本**，禁止 Markdown 格式
- 中文 ≤ 50 字，英文 ≤ 50 单词
- 一句话说明文档的核心内容

## CLI 命令参考（graph 子命令）

扫描完成并归档到 `.mdc-hub/docs/` 后，可通过 CLI 查询知识图谱：

```bash
# 列出所有节点
mdc-hub graph list <dir> [--json]

# 遍历邻居节点
mdc-hub graph neighbors <node-id> <dir> [-d depth] [-r up|down|both]

# 查找最短路径
mdc-hub graph path <from-id> <to-id> <dir> [-d max-depth]
```

| 参数 | 说明 |
|------|------|
| `--json` | JSON 格式输出节点列表 |
| `-d / --depth` | 遍历/搜索深度 |
| `-r / --relation` | 遍历方向：`up`（上游）/ `down`（下游）/ `both`（双向） |

## 完整扫描流程（7 步）

### 第一步：初始化

**目标**：确认工作区、加载分类与标签约束。

1. 调用 `get_workspace_info` 获取工作区根目录和 `.mdc-hub/` 路径
2. **必须**调用 `read_files` 读取以下两个文件：
   - `.mdc-hub/categories.yaml` — 分类库
   - `.mdc-hub/tags.yaml` — 标签库
3. 记住 `workspace_root` 和 `docs_dir`，后续步骤要用

### 第二步：全量扫描

**目标**：获取整个项目的文件概览，识别有哪些文件类型。

1. 调用 `scan_directory`，`directory` = `workspace_root`，不传 `file_types`（扫全部）
2. 从返回的 `type_counts` 中确认哪些类型存在：

| type_counts 中的 key | 交给哪个子 Skill |
|---------------------|-----------------|
| `代码` | mdc-code-scanner |
| `表格` | mdc-excel-scanner |
| `文档` | mdc-doc-scanner |
| `媒体` | mdc-media-scanner |
| `配置` | mdc-code-scanner（配置归代码类处理） |
| `其他` | 按后缀自行判断 |

**输出**：各文件类型的文件数量和分布。

### 第三步：逐类分流

**目标**：按文件类型分组，逐组交给专业子 Skill 处理。

对每种存在文件类型，调用 `scan_directory` 并传入 `file_types` 过滤：

```
scan_directory(directory=workspace_root, file_types=["代码"])
scan_directory(directory=workspace_root, file_types=["表格"])
scan_directory(directory=workspace_root, file_types=["文档"])
scan_directory(directory=workspace_root, file_types=["媒体"])
```

**关键约束**：
- 每类独立处理，不要混合
- 如果某类型文件数量为 0，跳过
- 每种类型的处理，严格遵循对应子 Skill 的文档格式要求

### 第四步：执行子 Skill

**目标**：按子 Skill 的规范，为每类文件生成 MDC 文档。

对每个子 Skill 的处理，参考 `.trae/skills/{skill-name}/SKILL.md` 中的详细说明。

- 代码类 → 方法级节点，`{ClassName}.{methodName}` 命名
- 表格类 → 表级+工作表级节点
- 文档类 → 章节级节点
- 媒体类 → 资源级节点

### 第五步：跨类型连线

**目标**：建立不同文件类型节点之间的 connections。

跨类型连接的常见场景：

| 场景 | 连线示例 |
|------|---------|
| 代码引用配置 | `user-service → application-config` (relation: "依赖") |
| 代码读取表格 | `import-service → customer-data-xlsx` (relation: "引用") |
| 文档描述代码 | `architecture-doc → user-service` (relation: "说明") |
| 文档引用图片 | `readme → architecture-diagram` (relation: "插图") |

**操作**：
1. 遍历所有已生成的文档
2. 根据源码中的 import、引用路径、文档中的链接等，推断跨类型关系
3. 使用 `write_mdc_document` 更新相关文档的 `connections` 字段

### 第六步：补全 Mermaid 图表

**目标**：为关键节点补上流程图。

1. 调用 `list_archived_documents` 获取所有文档
2. 对没有 Mermaid 图的文档，分析其内容补上：
   - 代码类 → sequenceDiagram 或 flowchart（调用链）
   - 表格类 → pie（数据分布）
   - 文档类 → graph（章节结构）
   - 媒体类 → 描述性说明即可，不强制 Mermaid

### 第七步：验证

**目标**：确保完整性。

1. 调用 `list_archived_documents`
2. 检查步骤：
   - 每种文件类型是否都有对应的归档文档
   - 所有 `connections` 的 `target` 是否真实存在
   - 关键文件是否有 Mermaid 图
   - 抽查 3-5 个文档确认格式正确
3. 告知用户 Web UI 地址（`open_dashboard`），可在浏览器查看图谱

## 使用注意事项

1. **大项目分批**：文件超 200 个时分批扫描，先代码后文档
2. **增量优先**：如果已有归档文档，优先扫描新增/修改的文件
3. **不影响源码**：所有产出都在 `.mdc-hub/docs/` 下
4. **委托原则**：类型分析完全委托给子 Skill，统筹 Skill 只负责调度和跨类型连线
