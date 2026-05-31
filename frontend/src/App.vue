<template>
  <div class="app-container">
    <!-- 顶部统计栏 -->
    <StatsBar :stats="stats" />

    <!-- 主体内容 -->
    <div class="main-area">
      <!-- 无图片提示 -->
      <div v-if="noPhotos" class="empty-state">
        <div class="empty-icon">📷</div>
        <p class="empty-title">暂无可浏览的图片</p>
        <p class="empty-desc">请确认图片目录已正确挂载</p>
      </div>

      <!-- 错误提示 -->
      <div v-else-if="errorMsg" class="empty-state">
        <div class="empty-icon">⚠️</div>
        <p class="empty-title">{{ errorMsg }}</p>
        <button class="retry-btn" @click="initPhotos">重试</button>
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

        <!-- 前面卡片（当前） -->
        <PhotoCard
          :key="'front-' + currentPhoto.path"
          :photo="currentPhoto"
          mode="front"
          @swipe-progress="onSwipeProgress"
          @leave-start="onLeaveStart"
          @leave-done="onLeaveDone"
          @double-tap="onFavorite"
          @single-tap="showInfo = true"
        />
      </template>
    </div>

    <!-- 底部提示 + 模式切换 -->
    <div class="bottom-hint">
      <span>{{ mediaType === 'video' ? '上滑删除 · 右滑保留' : '上滑删除 · 双击收藏 · 右滑保留' }}</span>
      <div class="mode-toggle">
        <button
          class="mode-btn"
          :class="{ active: mediaType === 'photo' }"
          @click="switchMode('photo')"
        >📷 照片</button>
        <button
          class="mode-btn"
          :class="{ active: mediaType === 'video' }"
          @click="switchMode('video')"
        >🎬 视频</button>
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
      <span>放大查看</span>
    </button>

    <!-- 图片信息弹窗 -->
    <InfoPanel
      :visible="showInfo"
      :photo="currentPhoto || {}"
      @close="showInfo = false"
    />

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
import { ref, onMounted } from 'vue'
import { getRandomPhoto, favoritePhoto, deletePhoto, getStats, getSettings } from './services/api'
import PhotoCard from './components/PhotoCard.vue'
import StatsBar from './components/StatsBar.vue'
import InfoPanel from './components/InfoPanel.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import PhotoInfoBar from './components/PhotoInfoBar.vue'
import ImageViewer from './components/ImageViewer.vue'

const currentPhoto = ref(null)
const nextPhoto = ref(null)
const isRevealing = ref(false)
const swipeProgress = ref(0)
const stats = ref({})
const settings = ref({})
const showInfo = ref(false)
const showSettings = ref(false)
const showViewer = ref(false)
const noPhotos = ref(false)
const errorMsg = ref('')
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
      errorMsg.value = '加载失败，请检查网络连接'
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
  padding: 60px 0 40px;
  position: relative;
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
  bottom: 50px;
  left: 50%;
  transform: translateX(-50%);
  bottom: max(50px, calc(env(safe-area-inset-bottom) + 22px));
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
</style>
