<template>
  <transition name="modal-fade">
    <div v-if="visible" class="modal-overlay" @mousedown.self="onOverlayMouseDown" @click.self="onOverlayClick">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">{{ t('favoritesTitle') }}</span>
          <button class="modal-close" @click="$emit('close')">×</button>
        </div>
        <div class="modal-body">
          <!-- 空状态 -->
          <div v-if="!loading && photos.length === 0" class="empty-state">
            <div class="empty-icon">📭</div>
            <div class="empty-text">{{ t('favoritesEmpty') }}</div>
            <div class="empty-hint">{{ t('favoritesHint') }}</div>
          </div>

          <!-- 加载中 -->
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            <div class="loading-text">{{ t('loading') }}</div>
          </div>

          <!-- 照片列表 -->
          <div v-if="!loading && photos.length > 0" class="photo-grid">
            <div
              v-for="photo in photos"
              :key="photo.path"
              class="photo-item"
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
                {{ selected.size === photos.length ? t('deselectAll') : t('selectAll') }}
              </button>
              <span class="select-count" v-if="selected.size > 0">{{ t('selectedCount', { count: selected.size }) }}</span>
            </div>
            <div class="action-buttons">
              <button
                class="action-btn unfav-btn"
                :disabled="selected.size === 0"
                @click="handleUnfavorite"
              >
                {{ t('unfavorite') }}
              </button>
              <button
                class="action-btn delete-btn"
                :disabled="selected.size === 0"
                @click="showDeleteConfirm = true"
              >
                {{ t('deleteSwipe') }}
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
    :message="t('confirmDeleteFavorites', { count: selected.size })"
    @confirm="handleDelete"
    @cancel="showDeleteConfirm = false"
  />
</template>

<script setup>
import { ref, watch } from 'vue'
import { getFavorites, unfavoritePhoto, deleteFavoritePhoto } from '../services/api'
import { formatSize } from '../utils/format'
import { useOverlayClose } from '../utils/overlayClose'
import { t } from '../i18n'
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
  if (photo.thumb_url && (photo.thumb_url.startsWith('/') || photo.thumb_url.startsWith('https://'))) {
    return photo.thumb_url
  }
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
  showResult(t('unfavCount', { count: successCount }), 'success')
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
  showResult(t('deletedToRecycle', { count: successCount }), 'success')
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
@import '../styles/gridPanel.css';
@import '../styles/modal.css';

/* 收藏夹专属按钮 */
.unfav-btn {
  background: #fff;
  color: #333;
  border: 1px solid #e0e0e0;
}

.unfav-btn:active {
  background: #f0f0f0;
}

</style>
