/** MDC 图谱相关的类型定义 */

export interface Connection {
  target: string
  relation: string
}

export interface NodeMeta {
  id: string
  title: string
  file_path: string
  category: string
  tags: string[]
  connections: Connection[]
  summary: string
  ai_model: string
  ai_summarized_at: string
  body_preview: string
}

export interface EdgeMeta {
  source: string
  target: string
  relation: string
  source_file: string
  target_file: string
}

export interface ScanResult {
  directory: string
  total_files: number
  nodes: NodeMeta[]
}

export interface GraphData {
  nodes: NodeMeta[]
  edges: EdgeMeta[]
}

export interface ScanRequest {
  directory: string
}

export interface GraphRequest {
  directory: string
  selected_files: string[]
}

export interface FileTreeNode {
  path: string
  name: string
  is_dir: boolean
  children?: FileTreeNode[]
}
