---
id: "react-server-components"
title: "React Server Components 深入理解"
category: "技术/前端/React"
tags: [react, rsc, server-components, nextjs]
connections:
  - target: "react-hooks-deep-dive"
    relation: "扩展概念"
  - target: "nextjs-app-router"
    relation: "依赖框架"
---

# React Server Components

## 核心概念

RSC 允许组件在服务端渲染，直接访问后端资源，减少客户端 JS 体积。

## 与 Client Components 的边界

- Server Components：默认，不能使用 hooks、事件处理
- Client Components：需要在文件顶部标注 `'use client'`

## 数据流

```
Server Component (fetch data)
  → Client Component (interactivity)
    → Server Component (more data)
```

## RSC 渲染架构

```mermaid
graph LR
    subgraph Server["服务端"]
        RSC1[Server Component: 数据获取]
        RSC2[Server Component: 内容渲染]
    end
    
    subgraph Boundary["服务器/客户端边界"]
        RSC1 --> CC1[Client Component: 交互UI]
        RSC2 --> CC2[Client Component: 表单]
    end
    
    subgraph Client["客户端"]
        CC1 --> DOM1[浏览器 DOM]
        CC2 --> DOM2[浏览器 DOM]
    end
    
    RSC1 -.->|序列化 Props| CC1
    RSC2 -.->|序列化 Props| CC2
```

## 最佳实践

1. 尽可能将组件作为 Server Component
2. 只在需要交互时将组件标记为 Client
3. 避免将整个页面树都变成 Client Component
