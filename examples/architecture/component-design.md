---
id: "component-design"
title: "组件设计原则与模式"
category: "architecture-core"
tags: [component-design, solid, clean-code, architecture]
connections:
  - target: "react-hooks-deep-dive"
    relation: "实现基础"
  - target: "state-management"
    relation: "架构配合"
---

# 组件设计原则与模式

## SOLID 原则在组件中的应用

### 单一职责 (SRP)
每个组件只负责一个功能。例如：
- `UserAvatar` — 只管头像展示
- `UserProfile` — 组合多个子组件
- `UserProfilePage` — 数据获取 + 布局

### 开闭原则 (OCP)
通过 props、slots、render props 扩展组件，而非修改源码。

## 组件分类

| 类型 | 职责 | 示例 |
|------|------|------|
| 展示组件 | 纯渲染，无业务逻辑 | Button, Card, Badge |
| 容器组件 | 数据获取、状态管理 | UserListContainer |
| 页面组件 | 路由入口、布局 | DashboardPage |

## 组合优于继承

```tsx
// 好：组合
function Page({ children }) {
  return (
    <div className="page">
      <Header />
      {children}
      <Footer />
    </div>
  )
}

// 差：继承
class Page extends BasePage { ... }
```

## 组件分类决策树

```mermaid
flowchart TD
    Start[新组件需求] --> Q1{有业务逻辑?}
    Q1 -->|否| Present[展示组件]
    Q1 -->|是| Q2{与路由耦合?}
    Q2 -->|是| Page[页面组件]
    Q2 -->|否| Q3{需要数据获取?}
    Q3 -->|是| Container[容器组件]
    Q3 -->|否| Logic[逻辑组件/Composable]
    
    Present --> Style[纯渲染+Props+Slots]
    Container --> Fetch[数据获取+状态管理+组合子组件]
    Page --> Route[路由入口+布局+SEO]
    Logic --> Hook[可复用业务逻辑]
```

## 组件通信

- 父→子：props
- 子→父：回调 / emit
- 跨层级：provide/inject 或 Context
- 全局：状态管理库
