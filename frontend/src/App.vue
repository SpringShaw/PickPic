<template>
  <div class="app-container">
    <!-- 主体内容 -->
    <div class="main-area">
      <!-- 无图片提示 -->
      <div v-if="noPhotos" class="empty-state">
        <div class="empty-icon">📷</div>
        <p class="empty-title">{{ t('noPhotos') }}</p>
        <p class="empty-desc">{{ t('noPhotosHint') }}</p>
      </div>

      <!-- 错误提示 -->
      <div v-else-if="errorMsg" class="empty-state">
        <div class="empty-icon">⚠️</div>
        <p class="empty-title">{{ errorMsg }}</p>
        <button class="retry-btn" @click="initPhotos">{{ t('retry') }}</button>
      </div>

      <!-- 双层卡片 -->
      <template v-else-if="currentPhoto">
        <PhotoInfoBar :photo="currentPhoto" />

        <!-- 背面卡片（下一张） -->
        <PhotoCard
          v-if="nextPhoto"
          :key="'back-' + nextPhoto.path"
          :photo="nextPhoto"
          mode="back"
          :revealing="isRevealing"
          :revealProgress="swipeProgress"
        />

        <!-- 召回卡片（找回上一张） -->
        <PhotoCard
          v-if="isRecalling && skippedPhoto"
          :key="'recall-' + skippedPhoto.path"
          :photo="skippedPhoto"
          mode="back"
          :revealing="true"
          :revealProgress="recallProgress"
        />

        <!-- 前面卡片（当前） -->
        <PhotoCard
          v-if="!isRecalling"
          :key="'front-' + currentPhoto.path"
          :photo="currentPhoto"
          mode="front"
          @swipe-progress="onSwipeProgress"
          @leave-start="onLeaveStart"
          @leave-done="onLeaveDone"
          @swipe-left="onRecall"
          @double-tap="onFavorite"
          @single-tap="showInfo = true"
        />
      </template>
    </div>

    <!-- 底部提示 + 模式切换 -->
    <div class="bottom-hint">
      <span>{{ mediaType === 'video' ? t('bottomHintVideo') : t('bottomHintPhoto') }}</span>
      <div class="mode-toggle">
        <button
          class="mode-btn"
          :class="{ active: mediaType === 'photo' }"
          @click="switchMode('photo')"
        >{{ t('photoMode') }}</button>
        <button
          class="mode-btn"
          :class="{ active: mediaType === 'video' }"
          @click="switchMode('video')"
        >{{ t('videoMode') }}</button>
      </div>
    </div>

    <!-- 查看原图按钮（底部居中） -->
    <button
      v-if="currentPhoto && !noPhotos && !errorMsg"
      class="view-btn"
      @click="showViewer = true"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        <line x1="11" y1="8" x2="11" y2="14"/>
        <line x1="8" y1="11" x2="14" y2="11"/>
      </svg>
      <span>{{ t('zoomView') }}</span>
    </button>

    <!-- 统计信息（照片和放大镜之间） -->
    <StatsBar :stats="stats" v-if="currentPhoto && !noPhotos && !errorMsg" />

    <!-- 图片信息弹窗 -->
    <InfoPanel
      :visible="showInfo"
      :photo="currentPhoto || {}"
      @close="showInfo = false"
    />

    <!-- 找回提示 -->
    <transition name="fade">
      <div v-if="recallMsg" class="recall-toast">{{ recallMsg }}</div>
    </transition>

    <!-- 设置入口（左下角齿轮） -->
    <button class="settings-btn" @click="showSettings = true">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="2">
        <circle cx="12" cy="12" r="3"/>
        <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
      </svg>
    </button>

    <!-- 图片查看器 -->
    <ImageViewer
      :visible="showViewer"
      :photo="currentPhoto || {}"
      @close="showViewer = false"
    />

    <!-- 设置弹窗 -->
    <SettingsPanel
      :visible="showSettings"
      :settings="settings"
      @close="showSettings = false"
      @updated="onSettingsUpdated"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { getRandomPhoto, favoritePhoto, deletePhoto, getStats, getSettings } from './services/api'
import { t, locale } from './i18n'
import PhotoCard from './components/PhotoCard.vue'
import StatsBar from './components/StatsBar.vue'
import InfoPanel from './components/InfoPanel.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import PhotoInfoBar from './components/PhotoInfoBar.vue'
import ImageViewer from './components/ImageViewer.vue'

// 同步页面标题
watch(locale, () => { document.title = t('appTitle') }, { immediate: true })

const currentPhoto = ref(null)
const nextPhoto = ref(null)
const skippedPhoto = ref(null) // 右滑跳过的照片（用于召回）
const isRecalling = ref(false) // 是否正在召回动画中
const recallProgress = ref(0) // 召回动画进度 0→1
const isRevealing = ref(false)
const swipeProgress = ref(0)
const stats = ref({})
const settings = ref({})
const showInfo = ref(false)
const showSettings = ref(false)
const showViewer = ref(false)
const noPhotos = ref(false)
const errorMsg = ref('')
const recallMsg = ref('')
const loading = ref(false)
const mediaType = ref('photo') // 'photo' | 'video'

// 切换模式
async function switchMode(mode) {
  if (mediaType.value === mode) return
  mediaType.value = mode
  currentPhoto.value = null
  nextPhoto.value = null
  await initPhotos()
}

// 预加载下一张（静默，不设 errorMsg）
async function preloadNext() {
  try {
    const res = await getRandomPhoto(mediaType.value)
    if (res.success && res.data) {
      nextPhoto.value = res.data
    } else {
      nextPhoto.value = null
    }
  } catch {
    nextPhoto.value = null
  }
}

// 加载照片（首次或需要刷新时）
async function initPhotos() {
  if (loading.value) return
  loading.value = true
  errorMsg.value = ''
  noPhotos.value = false
  currentPhoto.value = null
  nextPhoto.value = null

  try {
    // 先加载当前
    const res = await getRandomPhoto(mediaType.value)
    if (res.success && res.data) {
      currentPhoto.value = res.data
      // 预加载下一张
      preloadNext()
    } else {
      noPhotos.value = true
    }
  } catch (e) {
    if (e.response?.status === 404) {
      noPhotos.value = true
    } else {
      errorMsg.value = t('loadError')
    }
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const res = await getStats()
    if (res.success) stats.value = res.data
  } catch (e) {
    console.error('加载统计失败:', e)
  }
}

async function loadSettings() {
  try {
    const res = await getSettings()
    if (res.success) settings.value = res.data
  } catch (e) {
    console.error('加载设置失败:', e)
  }
}

// 滑动进度 → 驱动背面卡片渐进揭示
function onSwipeProgress(progress) {
  swipeProgress.value = progress
}

// 卡片开始飞出 → 触发背面卡片揭示动画
function onLeaveStart() {
  isRevealing.value = true
  swipeProgress.value = 1
}

// 卡片飞出完成 → 切换到下一张
async function onLeaveDone(direction) {
  // 右滑保留：记住这张，用于左滑找回
  if (direction === 'right' && currentPhoto.value) {
    skippedPhoto.value = { ...currentPhoto.value }
  }
  // 上滑删除
  if (direction === 'up' && currentPhoto.value) {
    try {
      await deletePhoto(currentPhoto.value.path)
    } catch (e) {
      console.error('删除失败:', e)
    }
  }
  // favorite / right → 不调删除API，直接切下一张

  isRevealing.value = false
  swipeProgress.value = 0

  if (nextPhoto.value) {
    currentPhoto.value = nextPhoto.value
    nextPhoto.value = null
    preloadNext()
  } else {
    await initPhotos()
  }
  loadStats()
}

// 左滑找回 - 带放大动画
function onRecall() {
  if (!skippedPhoto.value) {
    showRecallMsg(t('noRecall'))
    return
  }
  if (isRecalling.value) return

  // 开始召回动画
  isRecalling.value = true
  recallProgress.value = 0

  // 用 requestAnimationFrame 做动画，从 scale(0.3) 到 scale(1.0)
  const duration = 350 // ms
  const startTime = performance.now()

  function animate(now) {
    const elapsed = now - startTime
    const t = Math.min(1, elapsed / duration)
    // ease-out 缓动
    const eased = 1 - Math.pow(1 - t, 3)
    recallProgress.value = eased

    if (t < 1) {
      requestAnimationFrame(animate)
    } else {
      // 动画完成：召回照片成为当前照片，原来的下一张保留在后面
      const recalled = skippedPhoto.value
      skippedPhoto.value = null
      isRecalling.value = false
      recallProgress.value = 0
      // 关键：nextPhoto 要变成原来的 currentPhoto，这样用户找回后还能看到第二张
      nextPhoto.value = currentPhoto.value
      currentPhoto.value = recalled
      showRecallMsg(t('recalled'))
    }
  }
  requestAnimationFrame(animate)
}

function showRecallMsg(msg) {
  recallMsg.value = msg
  setTimeout(() => { recallMsg.value = '' }, 1500)
}

// 收藏 - 双击
async function onFavorite() {
  if (!currentPhoto.value) return
  try {
    await favoritePhoto(currentPhoto.value.path)
    loadStats()
  } catch (e) {
    console.error('收藏失败:', e)
  }
}

// 设置更新
function onSettingsUpdated() {
  loadSettings()
  loadStats()
  initPhotos()
}

onMounted(() => {
  initPhotos()
  loadStats()
  loadSettings()
})
</script>

<style scoped>
.app-container {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  background: #FFFFFF;
  position: relative;
  overflow: hidden;
}

.main-area {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: max(30px, calc(env(safe-area-inset-top) + 20px)) 0 160px;
  position: relative;
}

@media (min-width: 768px) {
  .main-area {
    padding-top: 36px;
  }
}

.bottom-hint {
  text-align: center;
  padding: 12px 0;
  padding-bottom: max(12px, env(safe-area-inset-bottom));
  font-size: 12px;
  color: #ccc;
  letter-spacing: 2px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.mode-toggle {
  display: flex;
  gap: 8px;
}

.mode-btn {
  padding: 6px 16px;
  border-radius: 20px;
  border: 1px solid #e0e0e0;
  background: #fff;
  color: #888;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-btn.active {
  background: #007AFF;
  color: #fff;
  border-color: #007AFF;
}

.empty-state {
  text-align: center;
  padding: 40px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 16px;
  color: #666;
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 13px;
  color: #999;
}

.retry-btn {
  margin-top: 16px;
  padding: 8px 24px;
  border-radius: 20px;
  border: 1px solid #ddd;
  background: #fff;
  color: #666;
  font-size: 14px;
  cursor: pointer;
}

.settings-btn {
  position: fixed;
  bottom: 40px;
  left: 20px;
  bottom: max(40px, calc(env(safe-area-inset-bottom) + 12px));
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #eee;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 50;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.settings-btn:active {
  background: #f0f0f0;
}

.view-btn {
  position: fixed;
  bottom: 90px;
  left: 50%;
  transform: translateX(-50%);
  bottom: max(90px, calc(env(safe-area-inset-bottom) + 62px));
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: 24px;
  border: 1px solid #eee;
  background: rgba(255, 255, 255, 0.92);
  color: #333333;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  z-index: 50;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
}

.view-btn:active {
  background: #f0f0f0;
  transform: translateX(-50%) scale(0.97);
}

.recall-toast {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  padding: 10px 28px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  z-index: 200;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  pointer-events: none;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
