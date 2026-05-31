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
        <button class="retry-btn" @click="loadPhoto">重试</button>
      </div>

      <!-- 图片卡片 -->
      <template v-else-if="currentPhoto">
        <PhotoInfoBar :photo="currentPhoto" />
        <PhotoCard
          :key="currentPhoto.path"
          :photo="currentPhoto"
          @swipe-right="onKeep"
          @swipe-up="showDeleteConfirm"
          @double-tap="onFavorite"
          @single-tap="showInfo = true"
        />
      </template>
    </div>

    <!-- 底部提示 -->
    <div class="bottom-hint">
      上滑删除 · 双击收藏 · 右滑保留
    </div>

    <!-- 查看原图按钮（底部居中） -->
    <button
      v-if="currentPhoto && !noPhotos && !errorMsg"
      class="view-btn"
      @click="showViewer = true"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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

    <!-- 删除确认弹窗 -->
    <ConfirmDialog
      :visible="showDeleteDialog"
      message="确认将此照片移入回收站？"
      @confirm="onDeleteConfirm"
      @cancel="showDeleteDialog = false"
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
import ConfirmDialog from './components/ConfirmDialog.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import PhotoInfoBar from './components/PhotoInfoBar.vue'
import ImageViewer from './components/ImageViewer.vue'

const currentPhoto = ref(null)
const stats = ref({})
const settings = ref({})
const showInfo = ref(false)
const showDeleteDialog = ref(false)
const showSettings = ref(false)
const showViewer = ref(false)
const noPhotos = ref(false)
const errorMsg = ref('')
const loading = ref(false)

async function loadPhoto() {
  if (loading.value) return
  loading.value = true
  errorMsg.value = ''
  noPhotos.value = false

  try {
    const res = await getRandomPhoto()
    if (res.success && res.data) {
      currentPhoto.value = res.data
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

// 保留 - 右滑
function onKeep() {
  loadPhoto()
  loadStats()
}

// 删除确认
function showDeleteConfirm() {
  showDeleteDialog.value = true
}

// 确认删除 - 上滑
async function onDeleteConfirm() {
  showDeleteDialog.value = false
  if (!currentPhoto.value) return

  try {
    await deletePhoto(currentPhoto.value.path)
    loadPhoto()
    loadStats()
  } catch (e) {
    errorMsg.value = '删除失败：' + (e.response?.data?.detail || '未知错误')
  }
}

// 收藏 - 双击
async function onFavorite() {
  if (!currentPhoto.value) return
  try {
    await favoritePhoto(currentPhoto.value.path)
    loadStats()
    // 收藏后自动加载下一张
    setTimeout(() => loadPhoto(), 800)
  } catch (e) {
    console.error('收藏失败:', e)
  }
}

// 设置更新
function onSettingsUpdated() {
  loadSettings()
  loadStats()
}

onMounted(() => {
  loadPhoto()
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
  border: none;
  background: rgba(0, 0, 0, 0.5);
  color: rgba(255, 255, 255, 0.9);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  z-index: 50;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  letter-spacing: 0.5px;
}

.view-btn:active {
  background: rgba(0, 0, 0, 0.7);
  transform: translateX(-50%) scale(0.95);
}
</style>
