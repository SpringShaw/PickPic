<template>
  <div
    class="photo-card"
    ref="cardRef"
    @touchstart="onTouchStart"
    @touchmove="onTouchMove"
    @touchend="onTouchEnd"
    @mousedown="onMouseDown"
    @mousemove="onMouseMove"
    @mouseup="onMouseUp"
    @dblclick="onDoubleClick"
    @click="onSingleClick"
    :style="cardStyle"
  >
    <!-- 图片 -->
    <img
      :src="imageUrl"
      :alt="photo.name"
      class="photo-img"
      :class="{ 'transition-transform': !isDragging }"
      @load="onImageLoad"
      @error="onImageError"
      draggable="false"
    />

    <!-- 收藏爱心动画 -->
    <transition name="heart-fade">
      <div v-if="showHeart" class="heart-overlay">
        <svg class="heart-icon" viewBox="0 0 24 24" fill="#FFB6C1">
          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
        </svg>
      </div>
    </transition>

    <!-- 滑动方向指示 -->
    <transition name="fade">
      <div v-if="showIndicator" class="indicator" :class="indicatorClass">
        {{ indicatorText }}
      </div>
    </transition>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-spinner">
      <div class="spinner"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getImageUrl, getThumbnailUrl } from '../services/api'

const props = defineProps({
  photo: { type: Object, required: true },
})

const emit = defineEmits(['swipe-right', 'swipe-up', 'double-tap', 'single-tap'])

const cardRef = ref(null)
const loading = ref(true)
const showHeart = ref(false)
const isDragging = ref(false)
const startX = ref(0)
const startY = ref(0)
const moveX = ref(0)
const moveY = ref(0)
const isMouseDown = ref(false)
const showIndicator = ref(false)
const indicatorType = ref('')
const lastTapTime = ref(0)
const clickTimer = ref(null)

// 优先使用缩略图（加载快10倍+），回退到原图
const imageUrl = computed(() => getThumbnailUrl(props.photo))

const cardStyle = computed(() => {
  if (!isDragging.value) return {}
  return {
    transform: `translate(${moveX.value}px, ${moveY.value}px) rotate(${moveX.value * 0.05}deg)`,
    opacity: Math.max(0.3, 1 - Math.abs(moveY.value) / 500),
  }
})

const indicatorClass = computed(() => {
  if (indicatorType.value === 'right') return 'indicator-right'
  if (indicatorType.value === 'up') return 'indicator-up'
  return ''
})

const indicatorText = computed(() => {
  if (indicatorType.value === 'right') return '保留'
  if (indicatorType.value === 'up') return '删除'
  return ''
})

// 触摸事件
function onTouchStart(e) {
  const touch = e.touches[0]
  startX.value = touch.clientX
  startY.value = touch.clientY
  isDragging.value = true
  showIndicator.value = false
}

function onTouchMove(e) {
  if (!isDragging.value) return
  const touch = e.touches[0]
  moveX.value = touch.clientX - startX.value
  moveY.value = touch.clientY - startY.value

  // 显示方向指示
  if (Math.abs(moveX.value) > 50 && moveX.value > 0) {
    showIndicator.value = true
    indicatorType.value = 'right'
  } else if (Math.abs(moveY.value) > 50 && moveY.value < 0) {
    showIndicator.value = true
    indicatorType.value = 'up'
  } else {
    showIndicator.value = false
  }
}

function onTouchEnd(e) {
  if (!isDragging.value) return
  isDragging.value = false
  showIndicator.value = false

  const threshold = 100
  if (moveX.value > threshold) {
    emit('swipe-right')
  } else if (moveY.value < -threshold) {
    emit('swipe-up')
  }

  moveX.value = 0
  moveY.value = 0
}

// 鼠标事件（PC兼容）
function onMouseDown(e) {
  startX.value = e.clientX
  startY.value = e.clientY
  isMouseDown.value = true
  isDragging.value = true
  showIndicator.value = false
}

function onMouseMove(e) {
  if (!isMouseDown.value) return
  moveX.value = e.clientX - startX.value
  moveY.value = e.clientY - startY.value

  if (Math.abs(moveX.value) > 50 && moveX.value > 0) {
    showIndicator.value = true
    indicatorType.value = 'right'
  } else if (Math.abs(moveY.value) > 50 && moveY.value < 0) {
    showIndicator.value = true
    indicatorType.value = 'up'
  } else {
    showIndicator.value = false
  }
}

function onMouseUp(e) {
  if (!isMouseDown.value) return
  isMouseDown.value = false
  isDragging.value = false
  showIndicator.value = false

  const threshold = 100
  if (moveX.value > threshold) {
    emit('swipe-right')
  } else if (moveY.value < -threshold) {
    emit('swipe-up')
  }

  moveX.value = 0
  moveY.value = 0
}

// 双击
function onDoubleClick(e) {
  e.preventDefault()
  showHeart.value = true
  emit('double-tap')
  setTimeout(() => { showHeart.value = false }, 1000)
}

// 单击（带双击防抖）
function onSingleClick(e) {
  const now = Date.now()
  if (now - lastTapTime.value < 300) return
  lastTapTime.value = now

  if (clickTimer.value) clearTimeout(clickTimer.value)
  clickTimer.value = setTimeout(() => {
    emit('single-tap')
  }, 300)
}

function onImageLoad() {
  loading.value = false
}

function onImageError() {
  loading.value = false
}

onUnmounted(() => {
  if (clickTimer.value) clearTimeout(clickTimer.value)
})
</script>

<style scoped>
.photo-card {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  user-select: none;
  -webkit-user-select: none;
  cursor: grab;
}

.photo-card:active {
  cursor: grabbing;
}

.photo-img {
  max-width: 92vw;
  max-height: 78vh;
  object-fit: contain;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  pointer-events: none;
}

.transition-transform {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.heart-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 10;
}

.heart-icon {
  width: 100px;
  height: 100px;
  filter: drop-shadow(0 2px 8px rgba(255, 182, 193, 0.6));
}

.heart-fade-enter-active {
  animation: heart-pop 0.6s ease-out;
}

.heart-fade-leave-active {
  animation: heart-fade 0.4s ease-in;
}

@keyframes heart-pop {
  0% { transform: translate(-50%, -50%) scale(0); opacity: 0; }
  50% { transform: translate(-50%, -50%) scale(1.3); opacity: 1; }
  100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
}

@keyframes heart-fade {
  0% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
  100% { opacity: 0; transform: translate(-50%, -50%) scale(1.2); }
}

.indicator {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  padding: 8px 20px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  pointer-events: none;
  z-index: 5;
}

.indicator-right {
  right: 20px;
  background: rgba(76, 175, 80, 0.15);
  color: #4CAF50;
}

.indicator-up {
  top: 30%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(244, 67, 54, 0.15);
  color: #F44336;
}

.loading-spinner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f0f0f0;
  border-top-color: #ccc;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
