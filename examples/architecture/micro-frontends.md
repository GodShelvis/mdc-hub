---
id: "micro-frontends"
title: "微前端架构设计"
category: "技术/架构"
tags: [micro-frontends, architecture, module-federation]
connections:
  - target: "component-design"
    relation: "架构基础"
  - target: "react-hooks-deep-dive"
    relation: "子应用技术"
  - target: "vue-composables"
    relation: "子应用技术"
---

# 微前端架构设计

## 方案对比

| 方案 | 特点 | 适用场景 |
|------|------|---------|
| Module Federation | Webpack 原生 | 技术栈统一 |
| qiankun | 基于 single-spa | 多技术栈 |
| Micro-Frontend iframe | 隔离最强 | 遗留系统 |

## 微前端应用加载时序

```mermaid
sequenceDiagram
    participant Browser as 浏览器
    participant Shell as 主应用(Shell)
    participant SubA as 子应用A (React)
    participant SubB as 子应用B (Vue)
    participant Store as 共享Store
    
    Browser->>Shell: 访问页面
    Shell->>Shell: 解析路由
    Shell->>SubA: 加载子应用A
    SubA->>Store: 获取全局状态
    Store-->>SubA: 返回用户信息
    Shell->>SubB: 加载子应用B
    SubB->>Store: 注册共享事件
    SubA->>SubB: 跨应用通信(事件总线)
    SubB-->>SubA: 响应通知
    SubA-->>Browser: 渲染完成
    SubB-->>Browser: 渲染完成
```

## 核心挑战

1. **样式隔离** — CSS 污染问题
2. **状态共享** — 跨子应用通信
3. **路由协同** — 统一路由管理
