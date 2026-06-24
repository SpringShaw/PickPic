<template>
  <transition name="modal-fade">
    <div v-if="visible" class="modal-overlay" @mousedown.self="onOverlayMouseDown" @click.self="onOverlayClick">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">⭐ 收藏夹</span>
          <button class="modal-close" @click="$emit('close')">×</button>
        </div>
        <div class="modal-body">
          <!-- 空状态 -->
          <div v-if="!loading && photos.length === 0" class="empty-state">
            <div class="empty-icon">📭</div>
            <div class="empty-text">还没有收藏的照片</div>
            <div class="empty-hint">双击照片即可收藏</div>
          </div>

          <!-- 加载中 -->
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            <div class="loading-text">加载中...</div>
          </div>

          <!-- 照片列表 -->
          <div v-if="!loading && photos.length > 0" class="fav-grid">
            <div
              v-for="photo in photos"
              :key="photo.path"
              class="fav-item"
              :class="{ selected: selected.has(photo.path) }"
            >
              <div class="thumb-wrapper" @click="toggleSelect(photo.path)">
                <img
                  :src="getThumbUrl(photo)"
                  class="thumb-img"
                  @error="(e) => e.target.style.display = 'none'"
                />
                <div class="check-mark" v-if="selected.has(photo.path)">✓</div>
              </div>
              <div class="item-info">
                <div class="item-name">{{ photo.name }}</div>
                <div class="item-meta">{{ formatSize(photo.size) }}</div>
              </div>
            </div>
          </div>

          <!-- 底部操作栏 -->
          <div v-if="!loading && photos.length > 0" class="action-bar">
            <div class="select-info">
              <button class="link-btn" @click="toggleAll">
                {{ selected.size === photos.length ? '取消全选' : '全选' }}
              </button>
              <span class="select-count" v-if="selected.size > 0">已选 {{ selected.size }} 张</span>
            </div>
            <div class="action-buttons">
              <button
                class="action-btn unfav-btn"
                :disabled="selected.size === 0"
                @click="handleUnfavorite"
              >
                取消收藏
              </button>
              <button
                class="action-btn delete-btn"
                :disabled="selected.size === 0"
                @click="showDeleteConfirm = true"
              >
                删除
              </button>
            </div>
          </div>

          <!-- 结果提示 -->
          <div v-if="resultMsg" class="result-toast" :class="resultType">
            {{ resultMsg }}
          </div>
        </div>
      </div>
    </div>
  </transition>

  <!-- 确认弹窗 -->
  <ConfirmDialog
    :visible="showDeleteConfirm"
    :message="`确定将选中的 ${selected.size} 张照片移入回收站吗？`"
    @confirm="handleDelete"
    @cancel="showDeleteConfirm = false"
  />
</template>

<script setup>
import { ref, watch } from 'vue'
import { getFavorites, unfavoritePhoto, deleteFavoritePhoto } from '../services/api'
import { formatSize } from '../utils/format'
import { useOverlayClose } from '../utils/overlayClose'
import ConfirmDialog from './ConfirmDialog.vue'

const props = defineProps({
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['close', 'updated'])
const { onOverlayMouseDown, onOverlayClick } = useOverlayClose(() => emit('close'))

const loading = ref(false)
const photos = ref([])
const selected = ref(new Set())
const showDeleteConfirm = ref(false)
const resultMsg = ref('')
const resultType = ref('')

function getThumbUrl(photo) {
  if (photo.thumb_url) return photo.thumb_url
  return ''
}

function toggleSelect(path) {
  const s = new Set(selected.value)
  if (s.has(path)) {
    s.delete(path)
  } else {
    s.add(path)
  }
  selected.value = s
}

function toggleAll() {
  if (selected.value.size === photos.value.length) {
    selected.value = new Set()
  } else {
    selected.value = new Set(photos.value.map(p => p.path))
  }
}

async function loadList() {
  loading.value = true
  selected.value = new Set()
  try {
    const res = await getFavorites()
    if (res.success) {
      photos.value = res.data || []
    }
  } catch (e) {
    console.error('加载收藏夹失败:', e)
  } finally {
    loading.value = false
  }
}

async function handleUnfavorite() {
  if (selected.value.size === 0) return
  let successCount = 0
  for (const path of selected.value) {
    try {
      await unfavoritePhoto(path)
      successCount++
    } catch (e) {
      console.error('取消收藏失败:', path, e)
    }
  }
  showResult(`已取消 ${successCount} 张收藏`, 'success')
  await loadList()
  emit('updated')
}

async function handleDelete() {
  showDeleteConfirm.value = false
  if (selected.value.size === 0) return
  let successCount = 0
  for (const path of selected.value) {
    try {
      await deleteFavoritePhoto(path)
      successCount++
    } catch (e) {
      console.error('删除失败:', path, e)
    }
  }
  showResult(`已将 ${successCount} 张照片移入回收站`, 'success')
  await loadList()
  emit('updated')
}

function showResult(msg, type) {
  resultMsg.value = msg
  resultType.value = type
  setTimeout(() => {
    resultMsg.value = ''
    resultType.value = ''
  }, 2000)
}

watch(() => props.visible, (val) => {
  if (val) loadList()
})
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
  max-height: 85vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  position: sticky;
  top: 0;
  background: #F8F8F8;
  z-index: 1;
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
}

.modal-body {
  padding: 16px 20px 32px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 0;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.empty-text {
  font-size: 14px;
  color: #888;
}

.empty-hint {
  font-size: 12px;
  color: #bbb;
  margin-top: 6px;
}

/* 加载 */
.loading-state {
  text-align: center;
  padding: 40px 0;
}

.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid #eee;
  border-top-color: #007AFF;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 13px;
  color: #888;
}

/* 照片网格 */
.fav-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}

.fav-item {
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  border: 2px solid transparent;
  transition: border-color 0.15s;
}

.fav-item.selected {
  border-color: #007AFF;
}

.thumb-wrapper {
  position: relative;
  aspect-ratio: 1;
  background: #f0f0f0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.check-mark {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #007AFF;
  color: #fff;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.item-info {
  padding: 6px 8px;
}

.item-name {
  font-size: 11px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  font-size: 10px;
  color: #888;
  margin-top: 2px;
}

/* 底部操作栏 */
.action-bar {
  position: sticky;
  bottom: 0;
  background: #F8F8F8;
  padding: 12px 0 0;
  border-top: 1px solid #eee;
}

.select-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.link-btn {
  background: none;
  border: none;
  font-size: 13px;
  color: #007AFF;
  cursor: pointer;
  padding: 0;
}

.select-count {
  font-size: 12px;
  color: #888;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-btn {
  flex: 1;
  padding: 10px;
  border-radius: 10px;
  border: none;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.unfav-btn {
  background: #fff;
  color: #333;
  border: 1px solid #e0e0e0;
}

.unfav-btn:active {
  background: #f0f0f0;
}

.delete-btn {
  background: #FF3B30;
  color: #fff;
}

/* 结果提示 */
.result-toast {
  position: fixed;
  bottom: 120px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 24px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  z-index: 1001;
  animation: toast-in 0.3s ease;
}

.result-toast.success {
  background: #fff;
  color: #4CAF50;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.result-toast.error {
  background: #fff;
  color: #FF3B30;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

@keyframes toast-in {
  from { opacity: 0; transform: translateX(-50%) translateY(10px); }
  to { opacity: 1; transform: translateX(-50%) translateY(0); }
}

/* 弹窗动画 */
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
