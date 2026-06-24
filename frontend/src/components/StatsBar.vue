<template>
  <div class="stats-bar">
    <span class="stat-item">
      <span class="stat-label">已浏览</span>
      <span class="stat-value">{{ stats.viewed_count || 0 }}</span>
    </span>
    <span class="stat-divider">·</span>
    <span class="stat-item">
      <span class="stat-label">已收藏</span>
      <span class="stat-value">{{ stats.favorited_count || 0 }}</span>
    </span>
    <span class="stat-divider">·</span>
    <span class="stat-item">
      <span class="stat-label">已清理</span>
      <span class="stat-value">{{ formatSize(stats.cleaned_bytes || 0) }}</span>
    </span>
  </div>
</template>

<script setup>
import { formatSize } from '../utils/format'

defineProps({
  stats: { type: Object, default: () => ({}) }
})
</script>

<style scoped>
.stats-bar {
  position: fixed;
  bottom: max(145px, calc(env(safe-area-inset-bottom) + 112px));
  left: 0;
  right: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  pointer-events: none;
  white-space: nowrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 11px;
  color: #888;
}

.stat-value {
  font-size: 12px;
  color: #666;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.stat-divider {
  color: #ddd;
  font-size: 10px;
  margin: 0 2px;
}
</style>
