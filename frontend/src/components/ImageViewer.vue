<template>
  <transition name="viewer-fade">
    <div v-if="visible" class="viewer-overlay" @click.self="$emit('close')">
      <!-- 关闭按钮 -->
      <button class="viewer-close" @click="$emit('close')">✕</button>

      <!-- 图片/视频容器 -->
      <div
        class="viewer-container"
        ref="containerRef"
        @touchstart="onTouchStart"
        @touchmove="onTouchMove"
        @touchend="onTouchEnd"
        @mousedown="onMouseDown"
        @mousemove="onMouseMove"
        @mouseup="onMouseUp"
        @wheel="onWheel"
      >
        <!-- 视频 -->
        <video
          v-if="isVideo"
          ref="videoRef"
          :src="imageUrl"
          class="viewer-video"
          controls
          autoplay
          playsinline
          @loadeddata="onVideoLoad"
        ></video>
        <!-- 图片 -->
        <img
          v-else
          ref="imgRef"
          :src="imageUrl"
          :alt="photo.name"
          class="viewer-img"
          :style="imgStyle"
          draggable="false"
          @load="onImageLoad"
        />
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="viewer-loading">
        <div class="spinner"></div>
      </div>

      <!-- 缩放提示 -->
      <div v-if="showZoomHint" class="zoom-hint">
        {{ zoomPercent }}%
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { getImageUrl } from '../services/api'

const props = defineProps({
  visible: { type: Boolean, default: false },
  photo: { type: Object, default: () => ({}) }
})

const emit = defineEmits(['close'])

const containerRef = ref(null)
const imgRef = ref(null)
const videoRef = ref(null)
const loading = ref(true)
const isVideo = computed(() => props.photo.media_type === 'video')
const showZoomHint = ref(false)
let zoomHintTimer = null

// 变换状态
const scale = ref(1)
const translateX = ref(0)
const translateY = ref(0)

// 触摸状态
let touches = []
let lastTouchDist = 0
let lastTouchCenter = { x: 0, y: 0 }
let isDragging = false
let dragStartX = 0
let dragStartY = 0
let dragStartTransX = 0
let dragStartTransY = 0

// 鼠标拖拽
let isMouseDragging = false
let mouseStartX = 0
let mouseStartY = 0

const imageUrl = computed(() => getImageUrl(props.photo.path))

const zoomPercent = computed(() => Math.round(scale.value * 100))

const imgStyle = computed(() => ({
  transform: `translate(${translateX.value}px, ${translateY.value}px) scale(${scale.value})`
}))

// 重置状态
function resetTransform() {
  scale.value = 1
  translateX.value = 0
  translateY.value = 0
  loading.value = true
}

watch(() => props.visible, (val) => {
  if (val) resetTransform()
})

function onImageLoad() {
  loading.value = false
}

function onVideoLoad() {
  loading.value = false
}

function flashZoomHint() {
  showZoomHint.value = true
  if (zoomHintTimer) clearTimeout(zoomHintTimer)
  zoomHintTimer = setTimeout(() => { showZoomHint.value = false }, 800)
}

// 限制平移范围
function clampTranslate() {
  if (!imgRef.value || !containerRef.value) return
  const cw = containerRef.value.clientWidth
  const ch = containerRef.value.clientHeight
  const nw = imgRef.value.naturalWidth
  const nh = imgRef.value.naturalHeight
  if (!nw || !nh) return

  const containerRatio = cw / ch
  const imgRatio = nw / nh

  // 图片在 scale=1 时的显示尺寸（contain 模式）
  let baseW, baseH
  if (imgRatio > containerRatio) {
    baseW = cw
    baseH = cw / imgRatio
  } else {
    baseH = ch
    baseW = ch * imgRatio
  }

  // 放大后的实际尺寸
  const scaledW = baseW * scale.value
  const scaledH = baseH * scale.value

  // 只有放大到超出容器时才允许平移
  const maxX = Math.max(0, (scaledW - cw) / 2)
  const maxY = Math.max(0, (scaledH - ch) / 2)

  translateX.value = Math.max(-maxX, Math.min(maxX, translateX.value))
  translateY.value = Math.max(-maxY, Math.min(maxY, translateY.value))
}

// 双指距离
function getTouchDist(t) {
  const dx = t[0].clientX - t[1].clientX
  const dy = t[0].clientY - t[1].clientY
  return Math.sqrt(dx * dx + dy * dy)
}

function getTouchCenter(t) {
  return {
    x: (t[0].clientX + t[1].clientX) / 2,
    y: (t[0].clientY + t[1].clientY) / 2
  }
}

// 触摸事件
function onTouchStart(e) {
  e.preventDefault()
  touches = Array.from(e.touches)

  if (touches.length === 1) {
    isDragging = true
    dragStartX = touches[0].clientX
    dragStartY = touches[0].clientY
    dragStartTransX = translateX.value
    dragStartTransY = translateY.value
  } else if (touches.length === 2) {
    isDragging = false
    lastTouchDist = getTouchDist(touches)
    lastTouchCenter = getTouchCenter(touches)
  }
}

function onTouchMove(e) {
  e.preventDefault()
  const currentTouches = Array.from(e.touches)

  if (currentTouches.length === 1 && isDragging) {
    const dx = currentTouches[0].clientX - dragStartX
    const dy = currentTouches[0].clientY - dragStartY
    translateX.value = dragStartTransX + dx
    translateY.value = dragStartTransY + dy
    clampTranslate()
  } else if (currentTouches.length === 2) {
    const dist = getTouchDist(currentTouches)
    const center = getTouchCenter(currentTouches)

    // 缩放
    const scaleFactor = dist / lastTouchDist
    const newScale = Math.max(0.5, Math.min(5, scale.value * scaleFactor))
    scale.value = newScale

    // 平移（跟随中心点）
    translateX.value += center.x - lastTouchCenter.x
    translateY.value += center.y - lastTouchCenter.y

    lastTouchDist = dist
    lastTouchCenter = center
    clampTranslate()
    flashZoomHint()
  }
}

function onTouchEnd(e) {
  if (e.touches.length === 0) {
    isDragging = false
    // 双击检测
    const now = Date.now()
    if (now - (onTouchEnd._lastTap || 0) < 300) {
      // 双击缩放
      if (scale.value > 1.2) {
        scale.value = 1
        translateX.value = 0
        translateY.value = 0
      } else {
        scale.value = 2.5
      }
      flashZoomHint()
    }
    onTouchEnd._lastTap = now
  }
}

// 鼠标事件（PC兼容）
function onMouseDown(e) {
  isMouseDragging = true
  mouseStartX = e.clientX
  mouseStartY = e.clientY
  dragStartTransX = translateX.value
  dragStartTransY = translateY.value
}

function onMouseMove(e) {
  if (!isMouseDragging) return
  translateX.value = dragStartTransX + (e.clientX - mouseStartX)
  translateY.value = dragStartTransY + (e.clientY - mouseStartY)
  clampTranslate()
}

function onMouseUp() {
  isMouseDragging = false
}

// 鼠标滚轮缩放
function onWheel(e) {
  e.preventDefault()
  const factor = e.deltaY > 0 ? 0.9 : 1.1
  const newScale = Math.max(0.5, Math.min(5, scale.value * factor))
  scale.value = newScale
  clampTranslate()
  flashZoomHint()
}
</script>

<style scoped>
.viewer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #000;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.viewer-close {
  position: absolute;
  top: 12px;
  right: 16px;
  top: max(12px, env(safe-area-inset-top));
  z-index: 1001;
  background: rgba(0, 0, 0, 0.4);
  border: none;
  color: #fff;
  font-size: 16px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.viewer-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  touch-action: none;
}

.viewer-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  transition: transform 0.1s ease;
  user-select: none;
  -webkit-user-select: none;
}

.viewer-video {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  outline: none;
}

.viewer-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255, 255, 255, 0.2);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.zoom-hint {
  position: absolute;
  bottom: 60px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  pointer-events: none;
}

.viewer-fade-enter-active {
  transition: opacity 0.2s ease;
}
.viewer-fade-leave-active {
  transition: opacity 0.15s ease;
}
.viewer-fade-enter-from,
.viewer-fade-leave-to {
  opacity: 0;
}
</style>
