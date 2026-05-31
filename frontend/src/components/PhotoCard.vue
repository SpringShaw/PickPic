<template>
  <div
    class="photo-card"
    :class="{ 'card-front': mode === 'front', 'card-back': mode === 'back' }"
    ref="cardRef"
    @touchstart.passive="onTouchStart"
    @touchmove.passive="onTouchMove"
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
      <div v-if="showIndicator && mode === 'front'" class="indicator" :class="indicatorClass">
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
import { ref, computed, onUnmounted } from 'vue'
import { getThumbnailUrl } from '../services/api'

const props = defineProps({
  photo: { type: Object, required: true },
  mode: { type: String, default: 'front' }, // 'front' | 'back'
  revealing: { type: Boolean, default: false }, // back card: true when front is leaving
})

const emit = defineEmits(['swipe-right', 'swipe-up', 'double-tap', 'single-tap', 'leave-start', 'leave-done'])

const cardRef = ref(null)
const loading = ref(true)
const showHeart = ref(false)
const isDragging = ref(false)
const isLeaving = ref(false)
const leaveX = ref(0)
const leaveY = ref(0)
const startX = ref(0)
const startY = ref(0)
const moveX = ref(0)
const moveY = ref(0)
const isMouseDown = ref(false)
const showIndicator = ref(false)
const indicatorType = ref('')
const lastTapTime = ref(0)
const clickTimer = ref(null)

const imageUrl = computed(() => getThumbnailUrl(props.photo))

const cardStyle = computed(() => {
  if (props.mode === 'back') {
    // 背面卡片：cover填满 + 初始放大，revealing时缩回正常
    return {
      transform: props.revealing ? 'scale(1)' : 'scale(1.12)',
      transition: props.revealing ? 'transform 0.35s ease-out' : 'none',
    }
  }

  if (isLeaving.value) {
    return {
      transform: `translate(${leaveX.value}px, ${leaveY.value}px) rotate(${leaveX.value * 0.04}deg)`,
      opacity: 0,
      transition: 'transform 0.28s ease-out, opacity 0.22s ease-out',
      zIndex: 20,
    }
  }
  if (isDragging.value) {
    const rotate = moveX.value * 0.04
    return {
      transform: `translate(${moveX.value}px, ${moveY.value}px) rotate(${rotate}deg)`,
      zIndex: 20,
    }
  }
  return { zIndex: 20 }
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
  if (props.mode !== 'front') return
  const touch = e.touches[0]
  startX.value = touch.clientX
  startY.value = touch.clientY
  isDragging.value = true
  showIndicator.value = false
}

function onTouchMove(e) {
  if (!isDragging.value || props.mode !== 'front') return
  const touch = e.touches[0]
  moveX.value = touch.clientX - startX.value
  moveY.value = touch.clientY - startY.value

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

function onTouchEnd() {
  if (!isDragging.value || props.mode !== 'front') return
  isDragging.value = false
  showIndicator.value = false
  checkSwipe()
}

// 鼠标事件（PC兼容）
function onMouseDown(e) {
  if (props.mode !== 'front') return
  startX.value = e.clientX
  startY.value = e.clientY
  isMouseDown.value = true
  isDragging.value = true
  showIndicator.value = false
}

function onMouseMove(e) {
  if (!isMouseDown.value || props.mode !== 'front') return
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

function onMouseUp() {
  if (!isMouseDown.value || props.mode !== 'front') return
  isMouseDown.value = false
  isDragging.value = false
  showIndicator.value = false
  checkSwipe()
}

function checkSwipe() {
  const threshold = 80
  if (moveX.value > threshold) {
    animateLeave(window.innerWidth * 1.2, moveY.value * 0.5, 'right')
  } else if (moveY.value < -threshold) {
    animateLeave(moveX.value * 0.5, -window.innerHeight * 1.2, 'up')
  } else {
    // 未超过阈值 → 弹回
    moveX.value = 0
    moveY.value = 0
  }
}

function animateLeave(toX, toY, direction) {
  isLeaving.value = true
  leaveX.value = toX
  leaveY.value = toY
  emit('leave-start', direction)

  // 监听动画结束
  const onEnd = () => {
    if (cardRef.value) {
      cardRef.value.removeEventListener('transitionend', onEnd)
    }
    emit('leave-done', direction)
  }

  if (cardRef.value) {
    cardRef.value.addEventListener('transitionend', onEnd, { once: true })
  }

  // 兜底定时器
  setTimeout(() => {
    if (isLeaving.value) {
      emit('leave-done', direction)
    }
  }, 400)
}

// 双击
function onDoubleClick(e) {
  if (props.mode !== 'front') return
  e.preventDefault()
  lastTapTime.value = Date.now() // 标记双击时间，阻止单击
  if (clickTimer.value) {
    clearTimeout(clickTimer.value)
    clickTimer.value = null
  }
  showHeart.value = true
  emit('double-tap')
  // 爱心动画后飞出
  setTimeout(() => {
    showHeart.value = false
    animateLeave(window.innerWidth * 1.2, 0, 'favorite')
  }, 800)
}

// 单击（带双击防抖）
function onSingleClick(e) {
  if (props.mode !== 'front') return
  // 双击后 400ms 内忽略单击
  if (lastTapTime.value && Date.now() - lastTapTime.value < 400) return

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

// 暴露给父组件：重置状态（用于回收复用）
function reset() {
  isDragging.value = false
  isLeaving.value = false
  moveX.value = 0
  moveY.value = 0
  leaveX.value = 0
  leaveY.value = 0
  loading.value = true
  showIndicator.value = false
}

defineExpose({ reset })

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
  position: absolute;
  top: 0;
  left: 0;
  user-select: none;
  -webkit-user-select: none;
}

.card-front {
  cursor: grab;
  z-index: 20;
}

.card-front:active {
  cursor: grabbing;
}

.card-back {
  z-index: 10;
  pointer-events: none;
  overflow: hidden;
  border-radius: 12px;
}

.card-back .photo-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 12px;
  max-width: none;
  max-height: none;
}

.photo-img {
  max-width: 92vw;
  max-height: 78vh;
  object-fit: contain;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  pointer-events: none;
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
