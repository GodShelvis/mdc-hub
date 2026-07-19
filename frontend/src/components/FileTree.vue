<script setup lang="ts">
/** 文件树 - 自定义复选框右侧，文件夹图标开合 */
import { computed, h, ref } from 'vue'
import { NTree } from 'naive-ui'
import type { TreeOption } from 'naive-ui'
import { useGraphStore } from '../stores/graph'
import { useTheme } from '../stores/theme'
import type { NodeMeta } from '../types'

const store = useGraphStore()
const { isDark } = useTheme()

interface TNode { name: string; path: string; isDir: boolean; children: TNode[]; node?: NodeMeta }

function buildTree(nodes: NodeMeta[], baseDir: string): TNode[] {
  const root: TNode[] = []
  const dirMap = new Map<string, TNode>()
  const nb = baseDir.endsWith('/') ? baseDir : baseDir + '/'
  for (const n of nodes) {
    let rel = n.file_path; if (rel.startsWith(nb)) rel = rel.substring(nb.length)
    const parts = rel.split('/'); let lv = root; let cur = nb
    for (let i = 0; i < parts.length; i++) {
      cur += (i === 0 ? '' : '/') + parts[i]
      if (i === parts.length - 1) lv.push({ name: parts[i], path: n.file_path, isDir: false, children: [], node: n })
      else { let d = dirMap.get(cur); if (!d) { d = { name: parts[i], path: cur, isDir: true, children: [] }; lv.push(d); dirMap.set(cur, d) }; lv = d.children }
    }
  }
  return root
}

function toOptions(nodes: TNode[]): TreeOption[] {
  return nodes.map(n => ({ key: n.path, label: n.name, isLeaf: !n.isDir, children: n.isDir ? toOptions(n.children) : undefined }))
}

const treeOptions = computed(() => store.scanResult?.nodes?.length ? toOptions(buildTree(store.scanResult.nodes, store.scanResult.directory)) : [])
const expandedKeys = ref<string[]>([])

// ---- 前缀图标 ----
function renderPrefix({ option }: { option: TreeOption }) {
  const expanded = expandedKeys.value.includes(option.key as string)
  if (option.isLeaf) {
    return h('svg', { width: 14, height: 14, viewBox: '0 0 24 24', fill: 'none', stroke: '#6c7086', strokeWidth: 2, style: { flexShrink: '0', marginRight: '6px' } }, [
      h('path', { d: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z' }),
      h('polyline', { points: '14 2 14 8 20 8' }),
    ])
  }
  return expanded
    ? h('svg', { width: 14, height: 14, viewBox: '0 0 24 24', fill: 'none', stroke: '#89b4fa', strokeWidth: 2, style: { flexShrink: '0', marginRight: '6px' } }, [
        h('path', { d: 'M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z' }),
        h('path', { d: 'M2 10h20', stroke: '#89b4fa', strokeWidth: 1.5, opacity: 0.6 }),
      ])
    : h('svg', { width: 14, height: 14, viewBox: '0 0 24 24', fill: 'none', stroke: '#89b4fa', strokeWidth: 2, style: { flexShrink: '0', marginRight: '6px' } }, [
        h('path', { d: 'M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z' }),
      ])
}

// ---- 复选框 ----
function checkboxState(opt: TreeOption): 'on' | 'partial' | 'off' {
  if (opt.isLeaf) {
    return store.selectedFiles.includes(opt.key as string) ? 'on' : 'off'
  }
  const files = collectAll(opt)
  if (files.length === 0) return 'off'
  const selected = files.filter(f => store.selectedFiles.includes(f)).length
  if (selected === 0) return 'off'
  if (selected === files.length) return 'on'
  return 'partial'
}

function renderLabel({ option }: { option: TreeOption }) {
  const state = checkboxState(option)
  return h('span', { style: { display: 'flex', alignItems: 'center', width: '100%' } }, [
    h('span', {
      style: { flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' },
      onClick: option.isLeaf ? (e: Event) => {
        e.stopPropagation()
        const key = option.key as string
        const idx = store.selectedFiles.indexOf(key)
        if (idx >= 0) store.selectedFiles.splice(idx, 1)
        else store.selectedFiles.push(key)
        store.loadGraph()
      } : undefined,
    }, option.label),
    h('span', {
      class: ['tree-check', state === 'partial' ? 'tree-check--partial' : '', state === 'on' ? 'tree-check--on' : ''],
      onClick: (e: Event) => {
        e.stopPropagation()
        if (option.isLeaf) {
          if (state === 'on') {
            const i = store.selectedFiles.indexOf(option.key as string)
            if (i >= 0) store.selectedFiles.splice(i, 1)
          } else {
            store.selectedFiles.push(option.key as string)
          }
        } else {
          toggleDir(option)
        }
        store.loadGraph()
      },
    }, state === 'on' ? '✓' : state === 'partial' ? '—' : ''),
  ])
}

function toggleDir(opt: TreeOption) {
  const files = collectAll(opt)
  if (files.every(f => store.selectedFiles.includes(f))) {
    files.forEach(f => { const i = store.selectedFiles.indexOf(f); if (i >= 0) store.selectedFiles.splice(i, 1) })
  } else {
    files.forEach(f => { if (!store.selectedFiles.includes(f)) store.selectedFiles.push(f) })
  }
}

function collectAll(opt: TreeOption): string[] {
  if (opt.isLeaf) return [opt.key as string]
  const files: string[] = []
  opt.children?.forEach(c => files.push(...collectAll(c)))
  return files
}

function onNodeClick({ option }: { option: TreeOption }) {
  if (option.isLeaf) return
  // 目录：切换展开（备用，expand-on-click 已处理）
  const key = option.key as string
  const idx = expandedKeys.value.indexOf(key)
  if (idx >= 0) expandedKeys.value.splice(idx, 1)
  else expandedKeys.value.push(key)
}

// Naive UI 主题覆盖：响应式
const treeTheme = computed(() => isDark.value ? {
  nodeTextColor: '#cdd6f4',
  nodeColorHover: '#252536',
  nodeColorActive: '#252536',
  nodeColorHoverInPopup: '#252536',
} : {
  nodeTextColor: '#333',
  nodeColorHover: '#e8e8e8',
  nodeColorActive: '#e8e8e8',
  nodeColorHoverInPopup: '#e8e8e8',
})
</script>

<template>
  <div class="sidebar">
    <div class="sidebar-hd">
      <span>资源管理器</span>
      <span class="count" v-if="store.scanResult">{{ store.scanResult.total_files }}</span>
    </div>
    <div v-if="treeOptions.length === 0" class="sidebar-empty">请先选择目录并扫描</div>
    <div v-else class="sidebar-body">
      <n-tree
        :data="treeOptions"
        :expanded-keys="expandedKeys"
        :render-prefix="renderPrefix"
        :render-label="renderLabel"
        :theme-overrides="treeTheme"
        :selectable="false"
        expand-on-click
        block-line
        :node-props="() => ({ style: { padding: '2px 0' } })"
        @update:expanded-keys="(keys) => expandedKeys = keys"
        @node-click="onNodeClick"
      />
    </div>
  </div>
</template>

<style scoped>
.sidebar { width: 260px; min-width: 260px; background: var(--bg-sidebar); border-right: 1px solid var(--border); display: flex; flex-direction: column; height: 100%; overflow: hidden; user-select: none; }
.sidebar-hd { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; color: var(--text-dim); }
.count { background: var(--bg-hover); color: var(--text-secondary); padding: 1px 6px; border-radius: 8px; font-size: 10px; }
.sidebar-empty { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--text-dim); font-size: 13px; padding: 20px; }
.sidebar-body { flex: 1; overflow-y: auto; padding: 4px; }

:deep(.n-tree-node-switcher) { display: none !important; }
:deep(.n-tree-node-content__prefix) { margin-right: 0 !important; }
:deep(.n-tree-node-content__text) { flex: 1; }
:deep(.n-tree-node-indent) { width: 14px; }
:deep(.n-tree) { background: transparent; font-size: 13px; }
:deep(.n-tree-node__content) { border-radius: 4px; }
:deep(.n-tree-node--selected .n-tree-node__content) { background: transparent !important; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--bg-hover); border-radius: 2px; }
</style>

<!-- 非 scoped：h() 渲染的元素需要全局样式 -->
<style>
.tree-check {
  width: 16px; height: 16px; flex-shrink: 0;
  border: 1.5px solid #6c7086; border-radius: 3px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 10px; cursor: pointer;
  color: transparent; transition: all .15s;
}
.tree-check:hover { border-color: #89b4fa; }
.tree-check--on { background: #89b4fa; border-color: #89b4fa; color: #fff; }
.tree-check--partial { background: #89b4fa; border-color: #89b4fa; color: #fff; }
</style>
