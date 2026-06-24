<template>
  <transition name="modal-fade">
    <div v-if="visible" class="modal-overlay" @mousedown.self="onOverlayMouseDown" @click.self="onOverlayClick">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">{{ t('infoTitle') }}</span>
          <button class="modal-close" @click="$emit('close')">×</button>
        </div>
        <div class="modal-body">
          <div class="info-row">
            <span class="info-label">{{ t('fileName') }}</span>
            <span class="info-value">{{ photo.name }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">{{ t('dateTaken') }}</span>
            <span class="info-value">{{ photo.date || t('unknown') }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">{{ t('resolution') }}</span>
            <span class="info-value">{{ photo.width && photo.height ? `${photo.width} × ${photo.height}` : t('unknown') }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">{{ t('fileSize') }}</span>
            <span class="info-value">{{ formatSize(photo.file_size) }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">{{ t('location') }}</span>
            <span class="info-value">{{ photo.location || (photo.gps ? `${photo.gps.lat}, ${photo.gps.lng}` : t('noGpsData')) }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">{{ t('originalPath') }}</span>
            <span class="info-value path-text">{{ photo.relative_path }}</span>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { formatSize } from '../utils/format'
import { useOverlayClose } from '../utils/overlayClose'
import { t } from '../i18n'

defineProps({
  visible: { type: Boolean, default: false },
  photo: { type: Object, default: () => ({}) }
})

const emit = defineEmits(['close'])
const { onOverlayMouseDown, onOverlayClick } = useOverlayClose(() => emit('close'))
</script>

<style scoped>
@import '../styles/modal.css';

/* InfoPanel overrides for shared modal styles */
.modal-content {
  max-height: 60vh;
  padding: 0;
}
.modal-header {
  position: static;
}
.modal-close {
  padding: 0 4px;
  line-height: 1;
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

</style>
