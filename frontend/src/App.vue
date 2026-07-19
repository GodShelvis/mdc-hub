<script setup lang="ts">
import { ref } from 'vue'
import { useGraphStore } from './stores/graph'
import { useTheme } from './stores/theme'
import FileTree from './components/FileTree.vue'
import KnowledgeGraph from './components/KnowledgeGraph.vue'
import LayerFilter from './components/LayerFilter.vue'
import DirectoryBrowser from './components/DirectoryBrowser.vue'

const store = useGraphStore()
const { isDark, toggle: toggleTheme } = useTheme()
const dirInput = ref('')
const showBrowser = ref(false)

function handleScan() { const p = dirInput.value.trim(); if (p) store.scan(p) }
function onBrowseSelect(path: string) { dirInput.value = path; showBrowser.value = false; store.scan(path) }
</script>

<template>
  <div class="app-shell" :class="{ light: !isDark }">
    <header class="top-bar">
      <div class="top-bar-left">
        <h1 class="logo">MDC Hub</h1>
        <span class="subtitle">知识图谱</span>
      </div>
      <div class="top-bar-center">
        <div class="dir-input-group">
          <input v-model="dirInput" type="text" placeholder="输入目录路径" class="dir-input" @keyup.enter="handleScan" />
          <button class="browse-btn" @click="showBrowser = true">浏览</button>
          <button class="scan-btn" @click="handleScan" :disabled="store.loading">{{ store.loading ? '扫描中...' : '扫描' }}</button>
        </div>
      </div>
      <div class="top-bar-right">
        <button class="theme-btn" @click="toggleTheme" :title="isDark ? '切换亮色' : '切换暗色'">
          {{ isDark ? '☀' : '☾' }}
        </button>
        <span class="info" v-if="store.directory">{{ store.directory }}</span>
      </div>
    </header>

    <div class="main-area">
      <FileTree />
      <div class="graph-area">
        <LayerFilter />
        <KnowledgeGraph />
      </div>
    </div>

    <DirectoryBrowser v-if="showBrowser" @select="onBrowseSelect" @close="showBrowser = false" />
  </div>
</template>

<style>
/* ========== CSS 变量：暗色/亮色主题 ========== */
:root {
  --bg-base: #11111b;
  --bg-surface: #181825;
  --bg-sidebar: #181825;
  --bg-elevated: #1e1e2e;
  --bg-hover: #313244;
  --border: #313244;
  --text-primary: #cdd6f4;
  --text-secondary: #a6adc8;
  --text-dim: #585b70;
  --accent: #89b4fa;
  --edge-color: #45475a;
  --minimap-bg: #181825;
}

.light {
  --bg-base: #f5f5f5;
  --bg-surface: #ffffff;
  --bg-sidebar: #f0f0f0;
  --bg-elevated: #ffffff;
  --bg-hover: #e0e0e0;
  --border: #d4d4d4;
  --text-primary: #1a1a1a;
  --text-secondary: #555;
  --text-dim: #999;
  --accent: #2563eb;
  --edge-color: #bbb;
  --minimap-bg: #f0f0f0;
}

/* ========== 全局样式 ========== */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, #app {
  height: 100%; width: 100%; overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-base); color: var(--text-primary);
}

.app-shell { display: flex; flex-direction: column; height: 100vh; width: 100vw; }

.top-bar {
  height: 52px; min-height: 52px; background: var(--bg-surface);
  border-bottom: 1px solid var(--border); display: flex;
  align-items: center; padding: 0 16px; gap: 16px; z-index: 100;
}
.top-bar-left { display: flex; align-items: baseline; gap: 8px; min-width: 180px; }
.logo {
  font-size: 18px; font-weight: 700;
  background: linear-gradient(90deg, hsl(225,75%,58%), hsl(240,75%,58%), hsl(255,75%,58%), hsl(270,75%,58%), hsl(285,75%,58%), hsl(300,75%,58%), hsl(315,75%,58%), hsl(330,75%,58%));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.subtitle { font-size: 12px; color: var(--text-dim); }
.top-bar-center { flex: 1; display: flex; justify-content: center; }
.dir-input-group { display: flex; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); width: 100%; max-width: 560px; }
.dir-input { flex: 1; padding: 8px 14px; background: var(--bg-elevated); border: none; color: var(--text-primary); font-size: 13px; outline: none; }
.dir-input::placeholder { color: var(--text-dim); }
.browse-btn { padding: 8px 12px; background: var(--bg-hover); border: none; border-left: 1px solid var(--border); color: var(--text-secondary); font-size: 13px; cursor: pointer; }
.browse-btn:hover { background: var(--border); }
.scan-btn { padding: 8px 18px; background: var(--bg-hover); border: none; border-left: 1px solid var(--border); color: var(--text-primary); font-size: 13px; font-weight: 500; cursor: pointer; }
.scan-btn:hover:not(:disabled) { background: var(--border); }
.scan-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.top-bar-right { display: flex; align-items: center; gap: 10px; min-width: 180px; justify-content: flex-end; }
.theme-btn { background: var(--bg-hover); border: 1px solid var(--border); color: var(--text-primary); width: 30px; height: 30px; border-radius: 6px; cursor: pointer; font-size: 15px; display: flex; align-items: center; justify-content: center; }
.theme-btn:hover { background: var(--border); }
.info { font-size: 12px; color: var(--text-dim); max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.main-area { flex: 1; display: flex; overflow: hidden; }
.graph-area { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--bg-hover); border-radius: 2px; }
</style>
