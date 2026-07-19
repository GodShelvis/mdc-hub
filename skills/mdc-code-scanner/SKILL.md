---
name: "mdc-code-scanner"
description: "Scans code files (Java/Python/TS/Go etc.) and generates method-level MDC knowledge documents with dependency graphs. Invoke when analyzing code, building method-level documentation, or creating code knowledge graphs."
---

# MDC Code Scanner — 代码扫描器

## 定位

本 Skill 是 MDC Hub 的**代码类子 Skill**，由 `mdc-directory-scanner` 调度，也可独立使用。

## 分类与标签约束

**强制规则**：`category` 必须从 `.mdc-hub/config/categories.yaml` 中选取，`tags` 从 `.mdc-hub/config/tags.yaml` 中选取。

- 分类示例：`backend` / `frontend` / `database` / `architecture`
- 标签示例：`java` / `spring-boot` / `mybatis` / `class` / `function`
- 通用编程概念（class/function/field/package/dependency/interface）统一使用英文 id
- **summary 字段**：纯文本，中文 ≤50 字 / 英文 ≤50 单词，禁止 Markdown

## 工作流程（4 步）

### 第一步：类级别扫描

**目标**：提取每个类的结构化信息。

1. 调用 `scan_directory`，`file_types=["代码"]`，获取代码文件列表
2. 对每个类提取：

| 提取项 | 说明 |
|--------|------|
| 类名 | 完整类名 |
| 注解 | `@Service`, `@RestController` 等 |
| 继承/实现 | `extends Foo`, `implements Bar` |
| 注入依赖 | `@Autowired` / 构造器注入 |
| 方法列表 | 所有 public 方法签名 |

### 第二步：生成类总览文档

**目标**：为每个类生成总览 `.md`。

文档归档路径：`.mdc-hub/docs/{包路径}/{ClassName}.md`

```yaml
id: "{class-name-kebab}"
title: "{类名} — {一句话职责}"
category: "backend-core"
tags: ["java", "class", "spring-boot"]
connections: []
```

正文结构：
```markdown
## 概述
## 字段
| 字段 | 类型 | 说明 |
## 方法索引
| 方法 | 参数 | 返回 | 说明 |
## 依赖注入
| 依赖 | 类型 | 用途 |
```

### 第三步：生成方法级文档

**目标**：每个 public 方法独立一份 `.md`。

归档路径：`.mdc-hub/docs/{包路径}/{ClassName}/{methodName}.md`

```yaml
id: "{ClassName-kebab}.{methodName}"
title: "{ClassName}.{methodName}()"
category: "backend-core"
tags: ["java", "function", "spring-boot"]
connections:
  - target: "{父类id}"
    relation: "属于"
```

正文：
```markdown
## 签名
## 参数
## 返回值
## 执行流程
```mermaid
flowchart TD
    ...
```

## 业务逻辑
## 调用的方法
## 被哪些方法调用
```

**关键规则**：
- `id` 格式：`{类名kebab}.{方法名}`
- `connections` 必须含 `属于` → 指向父类
- 每个方法必须有 Mermaid 流程图

### 第四步：建立调用连线

**目标**：补全方法间的 `调用` 关系。

| 关系 | 方向 | 示例 |
|------|------|------|
| 属于 | 方法 → 类 | `user-service.register → user-service` |
| 调用 | 调用方 → 被调用方 | `user-controller.getUser → user-service.findById` |
| 注入 | 类 → 依赖类 | `user-service → user-dao` |

**禁止**：悬空引用（target 不存在）、循环调用（A→B→A）

## 节点 ID 命名规范

```
类总览：{类名-kebab}
方法：  {类名-kebab}.{方法名}
示例：  user-service / user-service.register / user-service.findById
```
