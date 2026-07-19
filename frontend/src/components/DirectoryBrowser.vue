<script setup lang="ts">
/** 目录浏览器弹窗 */
import { ref, onMounted } from 'vue'
import axios from 'axios'

const emit = defineEmits<{
  select: [path: string]
  close: []
}>()

interface BrowseItem {
  name: string
  path: string
  is_dir: boolean
}

const currentPath = ref('/Users/shelvis')
const items = ref<BrowseItem[]>([])
const loading = ref(false)
const error = ref('')

async function browse(path: string) {
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get('/api/browse', { params: { path } })
    currentPath.value = data.path
    items.value = data.items
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '加载失败'
    items.value = []
  } finally {
    loading.value = false
  }
}

function enterDir(item: BrowseItem) {
  if (item.is_dir) {
    browse(item.path)
  }
}

function goUp() {
  const parent = currentPath.value.substring(0, currentPath.value.lastIndexOf('/'))
  if (parent) {
    browse(parent || '/')
  }
}

function selectCurrent() {
  emit('select', currentPath.value)
}

onMounted(() => {
  browse(currentPath.value)
})
</script>

<template>
  <div class="browser-overlay" @click.self="emit('close')">
    <div class="browser-modal">
      <div class="browser-header">
        <h3>选择目录</h3>
        <button class="browser-close" @click="emit('close')">&times;</button>
      </div>

      <div class="browser-path-bar">
        <button class="up-btn" @click="goUp" title="上一级">↑</button>
        <span class="current-path">{{ currentPath }}</span>
      </div>

      <div class="browser-list" v-if="!loading && !error">
        <div v-if="items.length === 0" class="browser-empty">空目录</div>
        <div
          v-for="item in items"
          :key="item.path"
          class="browser-item"
          :class="{ dir: item.is_dir }"
          @dblclick="enterDir(item)"
        >
          <span class="item-icon">{{ item.is_dir ? '📁' : '📄' }}</span>
          <span class="item-name">{{ item.name }}</span>
        </div>
      </div>

      <div v-if="loading" class="browser-loading">加载中...</div>
      <div v-if="error" class="browser-error">{{ error }}</div>

      <div class="browser-footer">
        <button class="select-btn" @click="selectCurrent">选择此目录</button>
        <button class="cancel-btn" @click="emit('close')">取消</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.browser-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.browser-modal { width: 560px; max-height: 80vh; background: var(--bg-elevated); border: 1px solid var(--border); border-radius: 12px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 16px 48px rgba(0,0,0,.4); }
.browser-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border); }
.browser-header h3 { margin: 0; font-size: 16px; color: var(--text-primary); }
.browser-close { background: none; border: none; color: var(--text-dim); font-size: 22px; cursor: pointer; }
.browser-close:hover { color: var(--text-primary); }
.browser-path-bar { display: flex; align-items: center; gap: 10px; padding: 10px 16px; background: var(--bg-surface); border-bottom: 1px solid var(--border); }
.up-btn { background: var(--bg-hover); border: none; color: var(--text-primary); width: 30px; height: 30px; border-radius: 6px; cursor: pointer; font-size: 16px; display: flex; align-items: center; justify-content: center; }
.up-btn:hover { background: var(--border); }
.current-path { font-size: 13px; color: var(--text-secondary); font-family: monospace; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.browser-list { flex: 1; overflow-y: auto; padding: 8px; max-height: 400px; }
.browser-empty, .browser-loading, .browser-error { padding: 32px; text-align: center; color: var(--text-dim); font-size: 14px; }
.browser-error { color: #f38ba8; }
.browser-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 6px; cursor: pointer; transition: background .15s; }
.browser-item:hover { background: var(--bg-hover); }
.browser-item.dir { color: var(--accent); }
.item-icon { font-size: 16px; }
.item-name { font-size: 13px; color: var(--text-primary); }
.browser-footer { display: flex; gap: 8px; padding: 12px 20px; border-top: 1px solid var(--border); justify-content: flex-end; }
.select-btn { padding: 8px 20px; background: var(--accent); color: #fff; border: none; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; }
.select-btn:hover { opacity: .9; }
.cancel-btn { padding: 8px 20px; background: var(--bg-hover); color: var(--text-primary); border: none; border-radius: 6px; font-size: 13px; cursor: pointer; }
.cancel-btn:hover { background: var(--border); }
</style>
