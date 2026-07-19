<script setup lang="ts">
/** 边关系标签 - 响应式路径 */
import { computed } from 'vue'
import { BaseEdge, getBezierPath } from '@vue-flow/core'

const props = defineProps<{
  id: string
  sourceX: number
  sourceY: number
  targetX: number
  targetY: number
  sourcePosition: any
  targetPosition: any
  data?: { relation: string }
  markerEnd?: string
  style?: any
}>()

const edgePath = computed(() => getBezierPath({
  sourceX: props.sourceX,
  sourceY: props.sourceY,
  sourcePosition: props.sourcePosition,
  targetX: props.targetX,
  targetY: props.targetY,
  targetPosition: props.targetPosition,
}))

const relation = computed(() => props.data?.relation || '关联')
const labelX = computed(() => (props.sourceX + props.targetX) / 2)
const labelY = computed(() => (props.sourceY + props.targetY) / 2)
</script>

<template>
  <g>
    <BaseEdge :id="id" :path="edgePath[0]" :marker-end="markerEnd" :style="style" />
    <foreignObject :x="labelX - 30" :y="labelY - 12" width="60" height="24">
      <div class="edge-label">{{ relation }}</div>
    </foreignObject>
  </g>
</template>

<style scoped>
.edge-label {
  font-size: 10px;
  color: var(--text-secondary, #a6adc8);
  background: var(--bg-hover, #313244);
  padding: 2px 8px;
  border-radius: 4px;
  text-align: center;
  white-space: nowrap;
  pointer-events: none;
  border: 1px solid var(--border, #45475a);
}
</style>
