---
name: "mdc-media-scanner"
description: "Scans media files (images/videos/audio) and generates resource-level MDC knowledge documents. Invoke when analyzing media assets, building asset catalogs, or documenting visual resources."
---

# MDC Media Scanner — 媒体扫描器

## 定位

本 Skill 是 MDC Hub 的**媒体类子 Skill**，负责分析图片（.png/.jpg/.svg 等）、视频（.mp4/.mov）、音频（.mp3/.wav）等媒体资源。

## 扫描粒度

- 每个媒体文件 → 1 个节点
- 可按目录做分组总览节点

## 工作流程（3 步）

### 第一步：扫描媒体文件

1. 调用 `scan_directory`，`file_types=["媒体"]`
2. 媒体文件无法读取二进制内容，AI 根据文件名、路径、扩展名推断
3. 提取：

| 提取项 | 说明 |
|--------|------|
| 文件名 | 含后缀 |
| 类型 | 图片/视频/音频 |
| 格式 | png/jpg/svg/mp4 等 |
| 大小 | 文件大小 |
| 推测用途 | 从路径和文件名推断（如 `logo.png` → Logo） |

### 第二步：生成文档

**单文件节点**：

归档路径：`.mdc-hub/docs/{相对路径}/{文件名}.md`

```yaml
id: "{文件名-kebab}"
title: "{文件名} — {推测用途}"
category: "资源/{类型}"
tags: ["媒体", "{类型}", "{用途标签}"]
connections: []
```

正文：
```markdown
## 基本信息
| 属性 | 值 |
| 文件名 | logo.png |
| 类型 | 图片 |
| 格式 | PNG |
| 大小 | 24KB |
| 推测用途 | 产品 Logo |

## 引用关系
- 被 `README.md` 引用（见 `readme` 节点）
- 用于 `LoginPage` 界面（见 `login-page` 节点）
```

**目录总览**（某个目录下媒体文件较多时）：

```yaml
id: "{目录名}-media-overview"
title: "{目录名} — 媒体资源总览"
category: "资源/{类型}"
tags: ["媒体", "总览"]
connections:
  - target: "{各子文件id}"
    relation: "包含"
```

正文：
```markdown
## 资源清单
| 文件 | 类型 | 大小 | 用途 |
| logo.png | 图片 | 24KB | Logo |

## 统计
- 图片: 15 个
- 视频: 3 个
- 音频: 2 个
```

### 第三步：建立连线

| 关系 | 场景 |
|------|------|
| `包含` | 目录总览 → 媒体文件 |
| `插图` | 代码/文档 → 图片（某文档用了这张图） |
| `关联` | 多个媒体文件属于同一功能模块 |

## 注意事项

- 媒体文件无法读取内容，主要依赖路径和文件名推断
- 通过 `read_files` 读取会报错，属于正常现象
- 重点追踪与代码/文档有引用关系的媒体文件
- 不需要为每个媒体文件都生成文档，聚焦关键的（Logo、架构图、数据截图等）
