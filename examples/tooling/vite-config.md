---
id: "vite-config"
title: "Vite 构建工具配置指南"
category: "devops-core"
tags: [vite, build, tooling, esbuild]
connections:
  - target: "mdc-spec"
    relation: "工具链"
---

# Vite 构建工具配置指南

## 核心特性

- 开发环境使用 ESBuild，快
- 生产构建使用 Rollup，稳
- 原生 ESM，无需打包

## Vite 构建管线

```mermaid
graph LR
    Source[源代码] --> ESBuild[ESBuild 预构建]
    ESBuild --> DevServer[开发服务器 HMR]
    Source --> Rollup[Rollup 生产构建]
    Rollup --> TreeShaking[Tree Shaking]
    TreeShaking --> CodeSplit[代码分割]
    CodeSplit --> Minify[压缩优化]
    Minify --> Bundle[最终产物]
    
    DevServer -->|即时| Browser[浏览器]
    Bundle -->|部署| CDN
```

## 常用配置

```ts
export default defineConfig({
  plugins: [vue(), react()],
  resolve: {
    alias: { '@': '/src' }
  },
  server: { port: 3000 }
})
```
