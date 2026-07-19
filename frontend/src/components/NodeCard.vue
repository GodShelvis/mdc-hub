<script setup lang="ts">
/** 自定义方形节点卡片 - Markdown 渲染 + 分类色条 + 标签 */
import { computed, ref, watch } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import type { NodeMeta } from '../types'
import { headerColor } from '../utils/colors'
import { renderMermaidInHtml } from '../utils/mermaid'

const props = defineProps<{
  data: { nodeData: NodeMeta }
}>()

const node = computed(() => props.data.nodeData)

const headerBg = computed(() => headerColor(node.value.category))

const renderedHtml = ref('')

watch(
  () => node.value.summary || node.value.body_preview || '',
  async (text) => {
    if (!text) { renderedHtml.value = ''; return }
    try {
      let html = DOMPurify.sanitize(marked.parse(text.substring(0, 300)) as string)
      html = await renderMermaidInHtml(html)
      renderedHtml.value = html
    } catch {
      renderedHtml.value = text.substring(0, 300)
    }
  },
  { immediate: true }
)
</script>

<template>
  <div class="node-card">
    <!-- 顶部分类色条 -->
    <div class="node-header" :style="{ background: headerBg }">
      <span class="node-category">{{ node.category }}</span>
      <span class="node-title">{{ node.title }}</span>
    </div>

    <!-- 内容区 - Markdown 渲染 -->
    <div class="node-body">
      <div
        v-if="renderedHtml"
        class="node-markdown"
        v-html="renderedHtml"
      />
      <span v-else class="node-empty">暂无内容</span>
    </div>

    <!-- 底部标签 -->
    <div class="node-footer" v-if="node.tags.length > 0">
      <span v-for="tag in node.tags" :key="tag" class="node-tag">{{ tag }}</span>
    </div>

    <!-- 连接点 -->
    <Handle type="target" :position="Position.Top" class="handle" />
    <Handle type="source" :position="Position.Bottom" class="handle" />
  </div>
</template>

<style scoped>
.node-card { width: 280px; background: var(--bg-elevated); border-radius: 8px; border: 1px solid var(--border); overflow: hidden; font-size: 12px; box-shadow: 0 2px 12px rgba(0,0,0,.2); transition: box-shadow .2s, border-color .2s; }
.node-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,.4); border-color: var(--text-dim); }
.node-header { padding: 8px 12px; display: flex; flex-direction: column; gap: 2px; }
.node-category { font-size: 10px; opacity: .8; color: #fff; font-weight: 500; }
.node-title { font-size: 14px; font-weight: 600; color: #fff; line-height: 1.3; }
.node-body { padding: 10px 12px; max-height: 160px; overflow: hidden; }
.node-markdown { color: var(--text-primary); line-height: 1.5; font-size: 12px; word-break: break-word; }
.node-markdown :deep(h1), .node-markdown :deep(h2), .node-markdown :deep(h3) { font-size: 13px; margin: 4px 0; color: var(--text-primary); }
.node-markdown :deep(p) { margin: 4px 0; }
.node-markdown :deep(code) { background: var(--bg-hover); padding: 1px 4px; border-radius: 3px; font-size: 11px; }
.node-markdown :deep(pre) { background: var(--bg-base); padding: 6px; border-radius: 4px; overflow-x: auto; font-size: 11px; margin: 4px 0; }
.node-markdown :deep(pre code) { background: none; padding: 0; }
.node-markdown :deep(ul), .node-markdown :deep(ol) { margin: 4px 0; padding-left: 16px; }
.node-markdown :deep(li) { margin: 2px 0; }
.node-markdown :deep(.mermaid-svg) { display: flex; justify-content: center; margin: 6px 0; max-width: 100%; overflow-x: auto; }
.node-markdown :deep(.mermaid-svg svg) { max-width: 100%; height: auto; }
.node-empty { color: var(--text-dim); font-style: italic; }
.node-footer { padding: 6px 12px; display: flex; flex-wrap: wrap; gap: 4px; border-top: 1px solid var(--border); }
.node-tag { font-size: 10px; padding: 2px 8px; background: var(--bg-hover); color: var(--text-secondary); border-radius: 4px; }
.handle { width: 10px; height: 10px; background: var(--text-dim); border: 2px solid var(--bg-elevated); }
</style>
