<script setup lang="ts">
/** 分类筛选器 - 默认全选，渐变色标签 */
import { computed } from 'vue'
import { useGraphStore } from '../stores/graph'
import { chipInactiveColor, chipActiveColor } from '../utils/colors'

const store = useGraphStore()
const categories = computed(() => store.getAllCategories())

function isActive(cat: string) {
  return !store.selectedCategories.includes(cat)
}
function toggleCat(cat: string) {
  store.toggleCategory(cat)
}

function chipStyle(cat: string) {
  return {
    '--chip-color': chipInactiveColor(cat),
    '--chip-active': chipActiveColor(cat),
  }
}
</script>

<template>
  <div class="layer-filter" v-if="categories.length > 0">
    <span class="filter-label">分类</span>
    <div class="filter-chips">
      <span
        v-for="cat in categories" :key="cat"
        class="filter-chip"
        :class="{ active: isActive(cat) }"
        :style="chipStyle(cat)"
        @click="toggleCat(cat)"
      >{{ cat }}</span>
    </div>
  </div>
</template>

<style scoped>
.layer-filter { padding: 10px 16px; border-bottom: 1px solid var(--border); display: flex; align-items: flex-start; gap: 10px; background: var(--bg-surface); }
.filter-label { font-size: 12px; color: var(--text-dim); min-width: 32px; padding-top: 4px; flex-shrink: 0; }
.filter-chips { display: flex; flex-wrap: wrap; gap: 6px; }

.filter-chip {
  font-size: 11px; padding: 3px 10px; border-radius: 12px; cursor: pointer;
  transition: all .15s; border: 1px solid var(--chip-color);
  background: color-mix(in srgb, var(--chip-color) 12%, var(--bg-surface));
  color: var(--chip-color);
}
.filter-chip:hover {
  background: color-mix(in srgb, var(--chip-color) 20%, var(--bg-surface));
}
.filter-chip.active {
  background: var(--chip-active);
  color: #fff;
  border-color: var(--chip-active);
}
</style>
