<template>
  <transition name="modal-fade">
    <div v-if="visible" class="modal-overlay" @mousedown.self="onOverlayMouseDown" @click.self="onOverlayClick">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">{{ t('recycleTitle') }}</span>
          <button class="modal-close" @click="$emit('close')">×</button>
        </div>
        <div class="modal-body">
          <!-- 空状态 -->
          <div v-if="!loading && photos.length === 0" class="empty-state">
            <div class="empty-icon">📭</div>
            <div class="empty-text">{{ t('recycleEmpty') }}</div>
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
                class="action-btn restore-btn"
                :disabled="selected.size === 0"
                @click="handleRestore"
              >
                {{ t('restoreSelected') }}
              </button>
              <button
                class="action-btn delete-btn"
                :disabled="selected.size === 0"
                @click="showDeleteSelectedConfirm = true"
              >
                {{ t('deleteSelected') }}
              </button>
            </div>
            <div class="action-buttons" style="margin-top: 8px;">
              <button
                class="action-btn restore-all-btn"
                @click="showRestoreAllConfirm = true"
              >
                {{ t('restoreAll') }}
              </button>
              <button
                class="action-btn empty-btn"
                @click="showEmptyConfirm = true"
              >
                {{ t('emptyAll') }}
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
    :visible="showRestoreAllConfirm"
    :message="t('confirmRestoreAll')"
    @confirm="handleRestoreAll"
    @cancel="showRestoreAllConfirm = false"
  />
  <ConfirmDialog
    :visible="showDeleteSelectedConfirm"
    :message="t('confirmDeleteSelected', { count: selected.size })"
    @confirm="handleDeleteSelected"
    @cancel="showDeleteSelectedConfirm = false"
  />
  <ConfirmDialog
    :visible="showEmptyConfirm"
    :message="t('confirmEmptyRecycle')"
    @confirm="handleEmpty"
    @cancel="showEmptyConfirm = false"
  />
</template>

<script setup>
import { ref, watch } from 'vue'
import { getRecycleList, restorePhoto, restoreAllPhotos, deleteRecycleItem, emptyRecycle } from '../services/api'
import { formatSize } from '../utils/format'
import { useOverlayClose } from '../utils/overlayClose'
import { t } from '../i18n'
import ConfirmDialog from './ConfirmDialog.vue'

const props = defineProps({
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['close', 'restored'])
const { onOverlayMouseDown, onOverlayClick } = useOverlayClose(() => emit('close'))

const loading = ref(false)
const photos = ref([])
const selected = ref(new Set())
const showRestoreAllConfirm = ref(false)
const showDeleteSelectedConfirm = ref(false)
const showEmptyConfirm = ref(false)
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
    const res = await getRecycleList()
    if (res.success) {
      photos.value = res.data || []
    }
  } catch (e) {
    console.error('加载回收站失败:', e)
  } finally {
    loading.value = false
  }
}

async function handleRestore() {
  if (selected.value.size === 0) return
  let successCount = 0
  for (const path of selected.value) {
    try {
      await restorePhoto(path)
      successCount++
    } catch (e) {
      console.error('恢复失败:', path, e)
    }
  }
  showResult(t('restoredCount', { count: successCount }), 'success')
  await loadList()
  emit('restored')
}

async function handleRestoreAll() {
  showRestoreAllConfirm.value = false
  try {
    const res = await restoreAllPhotos()
    if (res.success) {
      showResult(res.message, 'success')
    }
  } catch (e) {
    showResult(t('restoreFailed'), 'error')
  }
  await loadList()
  emit('restored')
}

async function handleDeleteSelected() {
  showDeleteSelectedConfirm.value = false
  if (selected.value.size === 0) return
  let successCount = 0
  for (const path of selected.value) {
    try {
      await deleteRecycleItem(path)
      successCount++
    } catch (e) {
      console.error('删除失败:', path, e)
    }
  }
  showResult(t('deletedCount', { count: successCount }), 'success')
  await loadList()
  emit('restored')
}

async function handleEmpty() {
  showEmptyConfirm.value = false
  try {
    const res = await emptyRecycle()
    if (res.success) {
      showResult(res.message, 'success')
    }
  } catch (e) {
    showResult(t('emptyFailed'), 'error')
  }
  await loadList()
  emit('restored')
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

/* 回收站专属按钮 */
.restore-btn {
  background: #007AFF;
  color: #fff;
}

.restore-all-btn {
  background: #fff;
  color: #333;
  border: 1px solid #e0e0e0;
}

.restore-all-btn:active {
  background: #f0f0f0;
}

.empty-btn {
  background: #fff;
  color: #FF3B30;
  border: 1px solid #FFD5D2;
}

.empty-btn:active {
  background: #FFF0EF;
}

</style>
