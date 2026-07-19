---
id: "pinia-best-practices"
title: "Pinia 状态管理最佳实践"
category: "技术/前端/Vue"
tags: [vue, pinia, state, store]
connections:
  - target: "vue-composables"
    relation: "配合使用"
  - target: "state-management"
    relation: "对比选型"
---

# Pinia 状态管理最佳实践

## 与 Vuex 对比

Pinia 是 Vuex 的继任者，提供：
- 完整的 TypeScript 支持
- 无需 mutations
- 多个 store 无需嵌套

## Store 组织方式

```
stores/
  ├── auth.ts      # 认证状态
  ├── user.ts      # 用户信息
  └── ui.ts        # UI 状态
```

## 典型 Store 职责分布

```mermaid
pie title Store 代码占比分布
    "认证授权 (auth)" : 25
    "用户管理 (user)" : 20
    "业务数据 (business)" : 30
    "UI 状态 (ui)" : 15
    "配置管理 (config)" : 10
```

## 最佳实践

1. 按功能领域拆分 store
2. 避免跨 store 的循环依赖
3. 复杂逻辑抽取为 composable
