---
id: "state-management"
title: "前端状态管理方案选型"
category: "技术/前端/架构"
tags: [state-management, pinia, zustand, redux]
connections:
  - target: "react-hooks-deep-dive"
    relation: "被依赖"
  - target: "vue-composables"
    relation: "被依赖"
  - target: "component-design"
    relation: "架构决策"
---

# 前端状态管理方案选型

## React 生态

| 方案 | 适用场景 | 复杂度 |
|------|---------|--------|
| useState + Context | 小型应用 | 低 |
| Zustand | 中小型应用 | 低 |
| Jotai | 原子化状态 | 中 |
| Redux Toolkit | 大型应用 | 高 |

## Vue 生态

| 方案 | 适用场景 |
|------|---------|
| ref + provide/inject | 组件级状态 |
| Pinia | 推荐方案，官方标配 |

## 选型原则

1. **不要过早引入状态管理库** — 先用框架内置方案
2. **按需加载** — 避免将所有状态放在全局 store
3. **服务端状态** — 用 React Query / Vue Query 管理，不要手动
4. **表单状态** — 用 React Hook Form / VeeValidate

## 状态管理层级架构

```mermaid
graph TB
    subgraph Global["全局状态层"]
        Auth[认证Store]
        User[用户Store]
        Config[配置Store]
    end
    
    subgraph Feature["功能状态层"]
        Cart[购物车Store]
        Order[订单Store]
    end
    
    subgraph Local["局部状态层"]
        UI[UI组件状态]
        Form[表单状态]
        Modal[弹窗状态]
    end
    
    subgraph Server["服务端状态层"]
        Query[React Query / Vue Query]
        Cache[缓存管理]
    end
    
    Global --> Feature
    Feature --> Local
    Server -.-> Feature
    Server -.-> Local
```

## 状态分类

| 类型 | 示例 | 存储位置 |
|------|------|---------|
| UI 状态 | 弹窗、加载态 | 组件内部 |
| 路由状态 | 当前页面 | 路由库 |
| 业务状态 | 用户、订单 | Store |
| 缓存状态 | API 响应 | Query 库 |
