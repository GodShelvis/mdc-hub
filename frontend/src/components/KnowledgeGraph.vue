<script setup lang="ts">
/** 知识图谱 - shallowRef 增量更新，节点对象引用保持稳定 */
import { ref, shallowRef, watch, onMounted, onUnmounted, markRaw } from 'vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import dagre from 'dagre'
import { useGraphStore } from '../stores/graph'
import NodeCard from './NodeCard.vue'
import EdgeLabel from './EdgeLabel.vue'
import { renderMermaidInHtml } from '../utils/mermaid'
import type { NodeMeta, EdgeMeta } from '../types'

const store = useGraphStore()

const flowNodes = shallowRef<any[]>([])
const flowEdges = shallowRef<any[]>([])

function dagrePositions(nodes: NodeMeta[], edges: { source: string; target: string }[]): Map<string, { x: number; y: number }> {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'TB', nodesep: 100, ranksep: 140, marginx: 60, marginy: 60 })
  for (const n of nodes) g.setNode(n.id, { width: 300, height: 200 })
  for (const e of edges) g.setEdge(e.source, e.target)
  dagre.layout(g)
  const map = new Map<string, { x: number; y: number }>()
  for (const n of nodes) {
    const p = g.node(n.id)
    if (p) map.set(n.id, { x: p.x - 150, y: p.y - 100 })
  }
  return map
}

watch(
  [() => store.getFilteredNodes(), () => store.getFilteredEdges()],
  ([nodes, edges]) => {
    if (nodes.length === 0) {
      flowNodes.value = []
      flowEdges.value = []
      return
    }

    const existingNodeMap = new Map<string, any>()
    for (const n of flowNodes.value) existingNodeMap.set(n.id, n)

    // 计算所有节点的新 dagre 位置
    const positions = dagrePositions(nodes, edges)
    // 但已有节点保留当前位置（用户可能拖过）
    const newNodes: any[] = []
    for (const n of nodes) {
      const exist = existingNodeMap.get(n.id)
      if (exist) {
        // 保持原有对象引用，仅更新 data
        exist.data = { nodeData: n }
        newNodes.push(exist)
      } else {
        // 新节点用 dagre 位置
        const pos = positions.get(n.id) || { x: 0, y: 0 }
        newNodes.push({
          id: n.id,
          type: 'node-card',
          position: pos,
          data: { nodeData: n },
          draggable: true,
        })
      }
    }

    // 新数组，但已有节点保持引用
    flowNodes.value = newNodes

    // 边
    flowEdges.value = edges.map((e, i) => ({
      id: `e-${e.source}-${e.target}-${i}`,
      source: e.source, target: e.target,
      type: 'edge-label',
      data: { relation: e.relation },
      animated: true,
      style: { stroke: 'var(--edge-color)', strokeWidth: 2 },
      markerEnd: 'arrowclosed',
    }))
  },
  { deep: true, immediate: true }
)

// ---- 交互 ----
const detailNode = ref<NodeMeta | null>(null)
const expandedNode = ref<NodeMeta | null>(null)
const expandedHtml = ref('')

function onNodeClick(event: any) {
  const nd = event.node?.data?.nodeData as NodeMeta | undefined
  if (nd) detailNode.value = nd
}
function onNodeDblClick(event: any) {
  const nd = event.node?.data?.nodeData as NodeMeta | undefined
  if (nd) expandNode(nd)
}
function onPaneClick() { detailNode.value = null }

async function expandNode(nd: NodeMeta) {
  expandedNode.value = nd
  const body = await store.loadNodeBody(nd.file_path)
  try {
    let html = DOMPurify.sanitize(marked.parse(body) as string)
    html = await renderMermaidInHtml(html)
    expandedHtml.value = html
  }
  catch { expandedHtml.value = `<pre>${body}</pre>` }
}
function closeExpand() { expandedNode.value = null; expandedHtml.value = '' }

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    if (expandedNode.value) closeExpand()
    else detailNode.value = null
  }
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div class="graph-container">
    <div class="graph-canvas">
      <VueFlow
        :nodes="flowNodes"
        :edges="flowEdges"
        :node-types="{ 'node-card': markRaw(NodeCard) }"
        :edge-types="{ 'edge-label': markRaw(EdgeLabel) }"
        :min-zoom="0.1"
        :max-zoom="2"
        fit-view-on-init
        @node-click="onNodeClick"
        @node-dblclick="onNodeDblClick"
        @pane-click="onPaneClick"
      >
        <Background :gap="16" />
        <Controls position="bottom-right" />
        <MiniMap />
      </VueFlow>
    </div>

    <Transition name="slide">
      <div v-if="detailNode && !expandedNode" class="detail-panel">
        <button class="detail-close" @click="detailNode = null">&times;</button>
        <h2>{{ detailNode.title }}</h2>
        <div class="detail-meta">
          <span class="detail-cat">{{ detailNode.category }}</span>
          <span class="detail-id">ID: {{ detailNode.id }}</span>
        </div>
        <div class="detail-tags" v-if="detailNode.tags.length">
          <span v-for="tag in detailNode.tags" :key="tag" class="detail-tag">{{ tag }}</span>
        </div>
        <div class="detail-conn" v-if="detailNode.connections.length">
          <h3>关联节点</h3>
          <ul><li v-for="c in detailNode.connections" :key="c.target">{{ c.target }} <span class="conn-r">— {{ c.relation }}</span></li></ul>
        </div>
        <div class="detail-sum"><h3>摘要</h3><p>{{ detailNode.summary || detailNode.body_preview || '暂无摘要' }}</p></div>
        <div class="detail-path">{{ detailNode.file_path }}</div>
        <button class="expand-btn" @click="expandNode(detailNode)">展开全文</button>
      </div>
    </Transition>

    <Transition name="modal">
      <div v-if="expandedNode" class="expanded-overlay" @click.self="closeExpand">
        <div class="expanded-card">
          <div class="expanded-hd">
            <div><span class="expanded-cat">{{ expandedNode.category }}</span><h2>{{ expandedNode.title }}</h2></div>
            <button class="expanded-close" @click="closeExpand">&times;</button>
          </div>
          <div class="expanded-bd"><div class="md-body" v-html="expandedHtml" /></div>
          <div class="expanded-ft">
            <div class="expanded-tags" v-if="expandedNode.tags.length">
              <span v-for="tag in expandedNode.tags" :key="tag" class="expanded-tag">{{ tag }}</span>
            </div>
            <span class="expanded-path">{{ expandedNode.file_path }}</span>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style>
@import '@vue-flow/core/dist/style.css';
@import '@vue-flow/core/dist/theme-default.css';
@import '@vue-flow/controls/dist/style.css';
@import '@vue-flow/minimap/dist/style.css';
.vue-flow__minimap { background: var(--minimap-bg) !important; }
.vue-flow__controls-button { background: var(--bg-elevated) !important; border-color: var(--border) !important; color: var(--text-primary) !important; }
.vue-flow__controls-button:hover { background: var(--bg-hover) !important; }
</style>

<style scoped>
.graph-container { flex: 1; position: relative; background: var(--bg-base); overflow: hidden; height: 100%; }
.graph-canvas { width: 100%; height: 100%; }

.detail-panel { position: absolute; top: 16px; right: 16px; width: 320px; max-height: calc(100% - 32px); overflow-y: auto; background: var(--bg-elevated); border: 1px solid var(--border); border-radius: 12px; padding: 20px; box-shadow: 0 8px 32px rgba(0,0,0,.3); z-index: 10; }
.detail-close { position: absolute; top: 12px; right: 16px; background: none; border: none; color: var(--text-dim); font-size: 22px; cursor: pointer; }
.detail-close:hover { color: var(--text-primary); }
.detail-panel h2 { margin: 0 0 12px; font-size: 18px; color: var(--text-primary); }
.detail-meta { display: flex; gap: 12px; margin-bottom: 12px; }
.detail-cat { font-size: 11px; padding: 2px 10px; background: var(--bg-hover); color: var(--accent); border-radius: 4px; }
.detail-id { font-size: 11px; color: var(--text-dim); }
.detail-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 16px; }
.detail-tag { font-size: 10px; padding: 2px 8px; background: var(--bg-hover); color: var(--text-secondary); border-radius: 4px; }
.detail-conn { margin-bottom: 16px; }
.detail-conn h3, .detail-sum h3 { font-size: 13px; color: var(--text-dim); margin: 0 0 8px; }
.detail-conn ul { list-style: none; padding: 0; margin: 0; }
.detail-conn li { padding: 4px 0; font-size: 13px; color: var(--text-primary); }
.conn-r { color: var(--text-dim); font-size: 12px; }
.detail-sum p { font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin: 0; }
.detail-path { margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border); font-size: 11px; color: var(--text-dim); word-break: break-all; }
.expand-btn { margin-top: 12px; width: 100%; padding: 8px; background: var(--bg-hover); color: var(--accent); border: 1px solid var(--border); border-radius: 6px; font-size: 13px; cursor: pointer; }
.expand-btn:hover { background: var(--border); }

/* 展开视图：fixed 定位，覆盖整个视口 */
.expanded-overlay { position: fixed; inset: 0; z-index: 1000; background: rgba(0,0,0,.6); display: flex; align-items: center; justify-content: center; padding: 40px; }
.expanded-card { width: 100%; max-width: 900px; max-height: 85vh; background: var(--bg-elevated); border: 1px solid var(--border); border-radius: 16px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 16px 64px rgba(0,0,0,.5); }
.expanded-hd { display: flex; justify-content: space-between; align-items: flex-start; padding: 20px 24px; border-bottom: 1px solid var(--border); }
.expanded-cat { font-size: 11px; padding: 2px 10px; background: var(--accent); color: #fff; border-radius: 4px; display: inline-block; margin-bottom: 6px; font-weight: 500; }
.expanded-hd h2 { margin: 0; font-size: 20px; color: var(--text-primary); }
.expanded-close { background: none; border: none; color: var(--text-dim); font-size: 26px; cursor: pointer; line-height: 1; }
.expanded-close:hover { color: var(--text-primary); }
.expanded-bd { flex: 1; overflow-y: auto; padding: 24px; }
.expanded-ft { display: flex; flex-direction: column; gap: 8px; padding: 12px 24px; border-top: 1px solid var(--border); }
.expanded-tags { display: flex; gap: 4px; overflow-x: auto; padding-bottom: 2px; }
.expanded-tags::-webkit-scrollbar { height: 2px; }
.expanded-tags::-webkit-scrollbar-thumb { background: var(--border); border-radius: 1px; }
.expanded-tag { font-size: 10px; padding: 2px 8px; background: var(--bg-hover); color: var(--text-secondary); border-radius: 4px; white-space: nowrap; flex-shrink: 0; }
.expanded-path { font-size: 11px; color: var(--text-dim); font-family: monospace; word-break: break-all; }

.md-body { color: var(--text-primary); line-height: 1.8; font-size: 14px; }
.md-body :deep(h1) { font-size: 24px; border-bottom: 1px solid var(--border); padding-bottom: 8px; margin: 24px 0 16px; }
.md-body :deep(h2) { font-size: 18px; margin: 20px 0 12px; }
.md-body :deep(h3) { font-size: 15px; margin: 16px 0 8px; }
.md-body :deep(p) { margin: 8px 0; }
.md-body :deep(code) { background: var(--bg-hover); padding: 2px 6px; border-radius: 4px; font-size: 13px; font-family: monospace; }
.md-body :deep(pre) { background: var(--bg-base); padding: 16px; border-radius: 8px; overflow-x: auto; margin: 12px 0; border: 1px solid var(--border); }
.md-body :deep(pre code) { background: none; padding: 0; }
.md-body :deep(ul), .md-body :deep(ol) { margin: 8px 0; padding-left: 24px; }
.md-body :deep(li) { margin: 4px 0; }
.md-body :deep(table) { border-collapse: collapse; margin: 12px 0; width: 100%; }
.md-body :deep(th), .md-body :deep(td) { border: 1px solid var(--border); padding: 8px 12px; text-align: left; font-size: 13px; }
.md-body :deep(th) { background: var(--bg-surface); }
.md-body :deep(blockquote) { border-left: 3px solid var(--accent); padding-left: 16px; margin: 12px 0; color: var(--text-secondary); }
.md-body :deep(a) { color: var(--accent); }
.md-body :deep(hr) { border: none; border-top: 1px solid var(--border); margin: 16px 0; }
.md-body :deep(.mermaid-svg) { display: flex; justify-content: center; margin: 12px 0; overflow-x: auto; }
.md-body :deep(.mermaid-svg svg) { max-width: 100%; height: auto; }

.slide-enter-active, .slide-leave-active { transition: all .25s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateX(20px); }
.modal-enter-active { transition: all .3s ease; }
.modal-leave-active { transition: all .2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
