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
defineProps({
  stats: { type: Object, default: () => ({}) }
})

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}
</script>

<style scoped>
.stats-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  padding-top: max(12px, env(safe-area-inset-top));
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
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
