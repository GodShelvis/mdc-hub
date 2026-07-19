---
id: "nextjs-app-router"
title: "Next.js App Router 架构"
category: "技术/前端/React"
tags: [nextjs, app-router, ssr, routing]
connections:
  - target: "react-server-components"
    relation: "核心特性"
  - target: "react-hooks-deep-dive"
    relation: "基础依赖"
---

# Next.js App Router 架构

## 文件约定

| 文件 | 作用 |
|------|------|
| page.tsx | 页面路由 |
| layout.tsx | 共享布局 |
| loading.tsx | Suspense 加载态 |
| error.tsx | 错误边界 |

## 路由与渲染决策流程

```mermaid
flowchart TD
    Request[用户请求] --> Check{动态参数?}
    Check -->|是| Dynamic[动态渲染]
    Check -->|否| CheckCache{缓存可用?}
    CheckCache -->|是| Cached[返回缓存]
    CheckCache -->|否| Revalidate{ISR 再验证?}
    Revalidate -->|是| Regenerate[后台重新生成]
    Revalidate -->|否| Static[返回静态页面]
    Regenerate --> Cached
    Dynamic --> Stream[流式 SSR]
    Stream --> Client[客户端水合]
```

## 渲染策略

- **Static**（默认）：构建时预渲染
- **Dynamic**：请求时渲染
- **ISR**：增量静态再生成
