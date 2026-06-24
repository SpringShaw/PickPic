<template>
  <transition name="modal-fade">
    <div v-if="visible" class="modal-overlay" @mousedown.self="onOverlayMouseDown" @click.self="onOverlayClick">
      <div class="confirm-box">
        <p class="confirm-text">{{ message }}</p>
        <div class="confirm-actions">
          <button class="btn-cancel" @click="$emit('cancel')">取消</button>
          <button class="btn-confirm" @click="$emit('confirm')">确定</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { useOverlayClose } from '../utils/overlayClose'

defineProps({
  visible: { type: Boolean, default: false },
  message: { type: String, default: '确认操作？' }
})

const emit = defineEmits(['confirm', 'cancel'])
const { onOverlayMouseDown, onOverlayClick } = useOverlayClose(() => emit('cancel'))
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
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.confirm-box {
  background: #fff;
  border-radius: 14px;
  padding: 24px;
  width: 280px;
  text-align: center;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.confirm-text {
  font-size: 15px;
  color: #333;
  line-height: 1.5;
  margin-bottom: 20px;
}

.confirm-actions {
  display: flex;
  gap: 12px;
}

.btn-cancel, .btn-confirm {
  flex: 1;
  padding: 10px;
  border-radius: 10px;
  border: none;
  font-size: 15px;
  cursor: pointer;
  font-weight: 500;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
}

.btn-confirm {
  background: #007AFF;
  color: #fff;
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
</style>
