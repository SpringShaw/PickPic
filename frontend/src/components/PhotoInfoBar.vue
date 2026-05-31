<template>
  <div class="info-bar" v-if="photo">
    <div class="info-main">
      <span class="info-filename" :title="photo.name">{{ photo.name }}</span>
      <span class="info-sep">·</span>
      <span class="info-date">{{ formatDate(photo.date) }}</span>
    </div>
    <div class="info-sub">
      <span v-if="photo.width && photo.height" class="info-tag">{{ photo.width }}×{{ photo.height }}</span>
      <span class="info-tag">{{ formatSize(photo.file_size) }}</span>
      <span v-if="photo.location" class="info-tag location">📍 {{ photo.location }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  photo: { type: Object, default: null }
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  // EXIF格式: "2024:01:15 14:30:22" → "2024-01-15 14:30"
  return dateStr.replace(/^(\d{4}):(\d{2}):(\d{2})/, '$1-$2-$3').replace(/\s+\d{2}$/, '')
}

function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.info-bar {
  position: fixed;
  top: 82px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 50;
  background: rgba(0, 0, 0, 0.25);
  border-radius: 10px;
  padding: 6px 14px;
  max-width: 90vw;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  pointer-events: none;
}

.info-main {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80vw;
}

.info-filename {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 50vw;
}

.info-sep {
  color: rgba(255, 255, 255, 0.4);
  flex-shrink: 0;
}

.info-date {
  color: rgba(255, 255, 255, 0.7);
  flex-shrink: 0;
}

.info-sub {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
}

.info-tag {
  white-space: nowrap;
}

.info-tag.location {
  color: rgba(255, 200, 100, 0.9);
}
</style>
