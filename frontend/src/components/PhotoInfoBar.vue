<template>
  <div class="info-bar" v-if="photo">
    <div class="info-main">
      <span class="info-date">{{ formatDate(photo.date) }}</span>
      <span class="info-sep">·</span>
      <span class="info-filename" :title="photo.name">{{ photo.name }}</span>
    </div>
    <div class="info-sub">
      <span v-if="photo.width && photo.height" class="info-tag">{{ photo.width }}×{{ photo.height }}</span>
      <span class="info-tag">{{ formatSize(photo.file_size) }}</span>
      <span v-if="photo.location" class="info-tag location">📍 {{ photo.location }}</span>
    </div>
  </div>
</template>

<script setup>
import { formatSize, formatDate } from '../utils/format'

defineProps({
  photo: { type: Object, default: null }
})
</script>

<style scoped>
.info-bar {
  position: absolute;
  top: max(8px, calc(env(safe-area-inset-top) + 8px));
  left: 50%;
  transform: translateX(-50%);
  z-index: 50;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 12px;
  padding: 8px 16px;
  max-width: 90vw;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  pointer-events: none;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
}

.info-main {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #333333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80vw;
}

.info-filename {
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 50vw;
  color: #999999;
  font-size: 11px;
}

.info-sep {
  color: #cccccc;
  flex-shrink: 0;
  font-size: 11px;
}

.info-date {
  color: #333333;
  font-weight: 600;
  flex-shrink: 0;
  font-size: 12px;
  letter-spacing: 0.3px;
}

.info-sub {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #888888;
}

.info-tag {
  white-space: nowrap;
}

.info-tag.location {
  color: #FFB6C1;
}
</style>
