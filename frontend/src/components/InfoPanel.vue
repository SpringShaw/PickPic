<template>
  <transition name="modal-fade">
    <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">图片信息</span>
          <button class="modal-close" @click="$emit('close')">×</button>
        </div>
        <div class="modal-body">
          <div class="info-row">
            <span class="info-label">文件名</span>
            <span class="info-value">{{ photo.name }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">拍摄时间</span>
            <span class="info-value">{{ photo.date || '未知' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">分辨率</span>
            <span class="info-value">{{ photo.width && photo.height ? `${photo.width} × ${photo.height}` : '未知' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">文件大小</span>
            <span class="info-value">{{ formatSize(photo.file_size) }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">位置</span>
            <span class="info-value">{{ photo.location || (photo.gps ? `${photo.gps.lat}, ${photo.gps.lng}` : '无GPS数据') }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">原始路径</span>
            <span class="info-value path-text">{{ photo.relative_path }}</span>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  photo: { type: Object, default: () => ({}) }
})

defineEmits(['close'])

function formatSize(bytes) {
  if (!bytes) return '未知'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #F8F8F8;
  width: 100%;
  max-width: 500px;
  border-radius: 16px 16px 0 0;
  padding: 0;
  max-height: 60vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}

.modal-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}

.modal-body {
  padding: 16px 20px 32px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 13px;
  color: #888;
  flex-shrink: 0;
  min-width: 70px;
}

.info-value {
  font-size: 13px;
  color: #333;
  text-align: right;
  word-break: break-all;
  flex: 1;
  margin-left: 16px;
}

.path-text {
  font-size: 11px;
  color: #666;
  font-family: 'SF Mono', 'Menlo', monospace;
}

.modal-fade-enter-active {
  transition: opacity 0.2s ease;
}

.modal-fade-leave-active {
  transition: opacity 0.15s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-active .modal-content {
  animation: slide-up 0.25s ease-out;
}

.modal-fade-leave-active .modal-content {
  animation: slide-down 0.15s ease-in;
}

@keyframes slide-up {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

@keyframes slide-down {
  from { transform: translateY(0); }
  to { transform: translateY(100%); }
}
</style>
