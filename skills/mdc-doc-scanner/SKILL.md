---
name: "mdc-doc-scanner"
description: "Scans documents (Word/PDF/Markdown/TXT) and generates chapter-level MDC knowledge documents. Invoke when analyzing documentation, reports, or knowledge base content."
---

# MDC Doc Scanner — 文档扫描器

## 定位

本 Skill 是 MDC Hub 的**文档类子 Skill**，负责分析 Word（.docx）、PDF（.pdf）、Markdown（.md）、纯文本（.txt）等文档。

## 扫描粒度

- 短文档（< 5 章）→ 1 个节点
- 长文档（≥ 5 章）→ 每章/每节 1 个独立节点 + 1 个总览节点

## 工作流程（3 步）

### 第一步：扫描文档文件

1. 调用 `scan_directory`，`file_types=["文档"]`
2. 调用 `read_files` 读取文件内容
3. 对每个文档提取：

| 提取项 | 说明 |
|--------|------|
| 文档类型 | .docx / .pdf / .md / .txt |
| 标题 | 文档主标题 |
| 章节结构 | 各级标题和层级 |
| 关键概念 | 文档中定义/讨论的核心概念 |
| 引用 | 文档引用了哪些其他文件/节点 |

### 第二步：生成文档

**总览节点**（每个文档一份，长文档必需）：

归档路径：`.mdc-hub/docs/{相对路径}/{文件名}.md`

```yaml
id: "{文件名-kebab}"
title: "{文档标题}"
category: "文档/{来源}"
tags: ["文档", "{文档类型}"]
connections: []
```

正文：
```markdown
## 概述
该文档的用途、目标读者、核心论点。

## 章节索引
| 章节 | 标题 | 关键概念 |
| 第1章 | 概述 | 项目背景 |

## 关键概念
- **概念A**：定义 + 说明
- **概念B**：定义 + 说明

## 引用/被引用
- 引用了：xxx
- 被引用：yyy
```

**章节级节点**（长文档拆分）：

```yaml
id: "{文档id}.{章节编号}"
title: "第X章：{章节标题}"
category: "文档/{来源}/{文档名}"
connections:
  - target: "{文档id}"
    relation: "属于"
```

正文：
```markdown
## 内容摘要
该章节的核心内容总结。

## 关键要点
- 要点1
- 要点2

## 关联
- 与 xxx 节点相关
```

### 第三步：建立连线

| 关系 | 场景 |
|------|------|
| `属于` | 章节 → 文档总览 |
| `说明` | 文档 → 代码节点（文档描述了某个模块） |
| `引用` | 文档引用了其他文档/概念 |
| `关联` | 多个文档讨论同一主题 |

## 注意事项

- PDF 和 Word 文件内容可能无法直接读取，AI 根据文件名和路径推断
- Markdown 文档中已有的 MDC frontmatter 要保留和合并
- 优先分析与代码/数据有直接关系的文档
