import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type { NodeMeta, EdgeMeta, ScanResult, GraphData } from '../types'

export const useGraphStore = defineStore('graph', () => {
  // 目录路径
  const directory = ref('')

  // 扫描结果
  const scanResult = ref<ScanResult | null>(null)
  const nodes = ref<NodeMeta[]>([])
  const edges = ref<EdgeMeta[]>([])

  // 选中的文件
  const selectedFiles = ref<string[]>([])

  // 图层筛选
  const selectedTags = ref<string[]>([])
  const selectedCategories = ref<string[]>([])

  // 加载状态
  const loading = ref(false)

  // 展开的节点详情（完整 Markdown）
  const expandedNodeId = ref<string | null>(null)
  const expandedNodeBody = ref<string>('')

  /** 扫描目录 */
  async function scan(dirPath: string) {
    loading.value = true
    try {
      const { data } = await axios.post<ScanResult>('/api/scan', {
        directory: dirPath,
      })
      directory.value = dirPath
      scanResult.value = data
      // 扫描后清空已选和图谱
      selectedFiles.value = []
      nodes.value = []
      edges.value = []
      expandedNodeId.value = null
    } catch (err) {
      console.error('扫描失败', err)
      scanResult.value = null
    } finally {
      loading.value = false
    }
  }

  /** 构建图谱（根据当前选中文件即时渲染） */
  async function loadGraph() {
    if (!directory.value || selectedFiles.value.length === 0) {
      nodes.value = []
      edges.value = []
      return
    }

    loading.value = true
    try {
      const { data } = await axios.post<GraphData>('/api/graph', {
        directory: directory.value,
        selected_files: selectedFiles.value,
      })
      nodes.value = data.nodes
      edges.value = data.edges
    } catch (err) {
      console.error('构建图谱失败', err)
    } finally {
      loading.value = false
    }
  }

  /** 切换文件选中，即时刷新图谱 */
  function toggleFile(filePath: string) {
    const idx = selectedFiles.value.indexOf(filePath)
    if (idx >= 0) {
      selectedFiles.value.splice(idx, 1)
    } else {
      selectedFiles.value.push(filePath)
    }
    loadGraph()
  }

  /** 全选/取消全选 */
  function toggleAll(files: string[]) {
    if (selectedFiles.value.length === files.length) {
      selectedFiles.value = []
    } else {
      selectedFiles.value = [...files]
    }
    loadGraph()
  }

  /** 获取节点的完整正文 */
  async function loadNodeBody(filePath: string): Promise<string> {
    try {
      const { data } = await axios.post<{ body: string }>('/api/file/body', {
        file_path: filePath,
      })
      return data.body || ''
    } catch {
      return ''
    }
  }

  /** 展开节点，查看完整 Markdown */
  async function expandNode(nodeId: string, filePath: string) {
    expandedNodeId.value = nodeId
    expandedNodeBody.value = await loadNodeBody(filePath)
  }

  function closeExpandedNode() {
    expandedNodeId.value = null
    expandedNodeBody.value = ''
  }

  function getAllTags(): string[] {
    if (!scanResult.value) return []
    const tagSet = new Set<string>()
    scanResult.value.nodes.forEach((n) => n.tags.forEach((t) => tagSet.add(t)))
    return [...tagSet].sort()
  }

  function getAllCategories(): string[] {
    if (!scanResult.value) return []
    const catSet = new Set<string>()
    scanResult.value.nodes.forEach((n) => {
      if (n.category) catSet.add(n.category)
    })
    return [...catSet].sort()
  }

  function getFilteredNodes(): NodeMeta[] {
    // selectedCategories 含义：排除列表。空 = 全显示
    if (selectedCategories.value.length === 0) {
      return nodes.value
    }
    return nodes.value.filter((n) => !selectedCategories.value.includes(n.category))
  }

  function getFilteredEdges(): EdgeMeta[] {
    const filteredNodeIds = new Set(getFilteredNodes().map((n) => n.id))
    return edges.value.filter(
      (e) => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)
    )
  }

  function toggleTag(tag: string) {
    const idx = selectedTags.value.indexOf(tag)
    if (idx >= 0) {
      selectedTags.value.splice(idx, 1)
    } else {
      selectedTags.value.push(tag)
    }
  }

  function toggleCategory(cat: string) {
    const idx = selectedCategories.value.indexOf(cat)
    if (idx >= 0) {
      selectedCategories.value.splice(idx, 1)
    } else {
      selectedCategories.value.push(cat)
    }
  }

  return {
    directory,
    scanResult,
    nodes,
    edges,
    selectedFiles,
    selectedTags,
    selectedCategories,
    loading,
    expandedNodeId,
    expandedNodeBody,
    scan,
    loadGraph,
    toggleFile,
    toggleAll,
    expandNode,
    closeExpandedNode,
    loadNodeBody,
    getAllTags,
    getAllCategories,
    getFilteredNodes,
    getFilteredEdges,
    toggleTag,
    toggleCategory,
  }
})
