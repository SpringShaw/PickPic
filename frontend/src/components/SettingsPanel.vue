<template>
  <transition name="modal-fade">
    <div v-if="visible" class="modal-overlay" @mousedown.self="onOverlayMouseDown" @click.self="onOverlayClick">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">{{ t('settings') }}</span>
          <button class="header-lang-btn" @click="toggleLocale" :title="t('languageToggleTitle')">
            {{ t('languageToggle') }}
          </button>
          <button class="modal-close" @click="$emit('close')">×</button>
        </div>
        <div class="modal-body">
          <!-- 目录配置 -->
          <div class="setting-group">
            <div class="setting-label">{{ t('photosDir') }}</div>
            <div class="setting-desc">{{ t('photosDirDesc') }}</div>
            <div class="dir-input-row">
              <input
                class="dir-input"
                v-model="photosDir"
                :placeholder="t('photosDirPlaceholder')"
                @blur="checkDir('photos')"
              />
              <span class="dir-status" :class="dirStatus.photos.class">{{ dirStatus.photos.text }}</span>
            </div>
          </div>

          <div class="setting-group">
            <div class="setting-label">{{ t('starDir') }}</div>
            <div class="setting-desc">{{ t('starDirDesc') }}</div>
            <div class="dir-input-row">
              <input
                class="dir-input"
                v-model="starDir"
                :placeholder="t('starDirPlaceholder')"
                @blur="checkDir('star')"
              />
              <span class="dir-status" :class="dirStatus.star.class">{{ dirStatus.star.text }}</span>
            </div>
          </div>

          <div class="setting-group">
            <div class="setting-label">{{ t('recycleDir') }}</div>
            <div class="setting-desc">{{ t('recycleDirDesc') }}</div>
            <div class="dir-input-row">
              <input
                class="dir-input"
                v-model="recycleDir"
                :placeholder="t('recycleDirPlaceholder')"
                @blur="checkDir('recycle')"
              />
              <span class="dir-status" :class="dirStatus.recycle.class">{{ dirStatus.recycle.text }}</span>
            </div>
          </div>

          <button class="action-btn primary" @click="saveDirs" :disabled="saving">
            {{ saving ? t('saving') : t('saveDirs') }}
          </button>

          <!-- 照片缓存扫描 -->
          <div class="setting-group">
            <div class="setting-row">
              <div>
                <div class="setting-label">{{ t('photoCache') }}</div>
                <div class="setting-desc">{{ scanStatusText }}</div>
              </div>
              <button
                class="action-btn scan-btn"
                @click="triggerScan"
                :disabled="scanning"
              >
                {{ scanning ? t('scanning') : t('rescan') }}
              </button>
            </div>
          </div>

          <div class="divider"></div>

          <!-- 黑名单时长 -->
          <div class="setting-group">
            <div class="setting-label">{{ t('blacklistDuration') }}</div>
            <div class="setting-desc">{{ t('blacklistDesc') }}</div>
            <div class="setting-options">
              <button
                v-for="opt in durationOptions"
                :key="opt.value"
                class="option-btn"
                :class="{ active: settings.blacklist_duration === opt.value }"
                @click="changeSetting('blacklist_duration', opt.value)"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>

          <!-- 重复过滤 -->
          <div class="setting-group">
            <div class="setting-row">
              <div>
                <div class="setting-label">{{ t('dupFilter') }}</div>
                <div class="setting-desc">{{ t('dupFilterDesc') }}</div>
              </div>
              <button
                class="toggle-btn"
                :class="{ on: settings.enable_duplicate_filter === 'true' }"
                @click="toggleDuplicateFilter"
              >
                <span class="toggle-knob"></span>
              </button>
            </div>
          </div>

          <div class="divider"></div>

          <!-- 操作区 -->
          <div class="setting-group">
            <button class="action-btn primary" @click="showRecycle = true">
              {{ t('recycleManage') }}
            </button>
            <button class="action-btn primary" @click="showFavorites = true">
              {{ t('favoritesManage') }}
            </button>
            <button class="action-btn danger" @click="showResetBlacklistConfirm = true">
              {{ t('resetBlacklist') }}
            </button>
            <button class="action-btn danger" @click="showResetStatsConfirm = true">
              {{ t('resetStats') }}
            </button>
          </div>

          <!-- 底部信息 -->
          <div class="footer-info">
            <p>{{ t('footerVersion') }}</p>
            <p>{{ t('footerLocal') }}</p>
          </div>
        </div>
      </div>
    </div>
  </transition>

  <!-- 确认弹窗 -->
  <ConfirmDialog
    :visible="showResetBlacklistConfirm"
    :message="t('confirmResetBlacklist')"
    @confirm="handleResetBlacklist"
    @cancel="showResetBlacklistConfirm = false"
  />
  <ConfirmDialog
    :visible="showResetStatsConfirm"
    :message="t('confirmResetStats')"
    @confirm="handleResetStats"
    @cancel="showResetStatsConfirm = false"
  />
  <RecyclePanel
    :visible="showRecycle"
    @close="showRecycle = false"
    @restored="emit('updated')"
  />
  <FavoritesPanel
    :visible="showFavorites"
    @close="showFavorites = false"
    @updated="emit('updated')"
  />
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { updateSetting as apiUpdateSetting, resetBlacklist, resetStats, getSettings, triggerScan as apiTriggerScan, getScanStatus } from '../services/api'
import { useOverlayClose } from '../utils/overlayClose'
import { t, toggleLocale } from '../i18n'
import ConfirmDialog from './ConfirmDialog.vue'
import RecyclePanel from './RecyclePanel.vue'
import FavoritesPanel from './FavoritesPanel.vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  settings: { type: Object, default: () => ({}) }
})

const emit = defineEmits(['close', 'updated'])
const { onOverlayMouseDown, onOverlayClick } = useOverlayClose(() => emit('close'))

const showResetBlacklistConfirm = ref(false)
const showResetStatsConfirm = ref(false)
const showRecycle = ref(false)
const showFavorites = ref(false)
const saving = ref(false)

const photosDir = ref('')
const starDir = ref('')
const recycleDir = ref('')

// 原始目录检查结果（不含翻译文本）
const dirRaw = ref({
  photos: { state: '', count: 0 },
  star: { state: '', count: 0 },
  recycle: { state: '', count: 0 },
})

// 响应式计算目录状态显示文本（locale 变化时自动更新）
const dirStatus = computed(() => {
  function fmt(type) {
    const raw = dirRaw.value[type]
    if (!raw.state) return { text: t('dirNotSet'), class: 'status-empty' }
    if (raw.state === 'ok') return { text: `${t('dirCheckPrefix')} ${t('dirOkPhotos', { count: raw.count })}`, class: 'status-ok' }
    if (raw.state === 'empty') return { text: `${t('dirCheckPrefix')} ${t('dirExistsEmpty')}`, class: 'status-warn' }
    if (raw.state === 'missing') return { text: `${t('dirCheckFail')} ${t('dirNotExists')}`, class: 'status-error' }
    return { text: t('dirVerifyFailed'), class: 'status-error' }
  }
  return { photos: fmt('photos'), star: fmt('star'), recycle: fmt('recycle') }
})

const scanning = ref(false)
const scanStatus = ref({ status: 'idle', total: 0, processed: 0, new_count: 0 })
let scanTimer = null

const scanStatusText = computed(() => {
  const s = scanStatus.value
  if (s.status === 'scanning') {
    return t('scanStatusScanning', { processed: s.processed, total: s.total, newCount: s.new_count })
  }
  if (s.status === 'idle' && s.total > 0) {
    return t('scanStatusCached', { total: s.total, newCount: s.new_count })
  }
  return t('scanStatusIdle')
})

async function triggerScan() {
  scanning.value = true
  try {
    await apiTriggerScan(true)
    startPolling()
  } catch (e) {
    scanning.value = false
  }
}

function startPolling() {
  scanTimer = setInterval(async () => {
    try {
      const res = await getScanStatus()
      if (res.success) {
        scanStatus.value = res.data
        if (res.data.status !== 'scanning') {
          clearInterval(scanTimer)
          scanTimer = null
          scanning.value = false
          emit('updated')
        }
      }
    } catch (e) {
      clearInterval(scanTimer)
      scanTimer = null
      scanning.value = false
    }
  }, 2000)
}

async function loadScanStatus() {
  try {
    const res = await getScanStatus()
    if (res.success) {
      scanStatus.value = res.data
      if (res.data.status === 'scanning') {
        scanning.value = true
        startPolling() // 仅恢复轮询，不重复发起扫描
      }
    }
  } catch (e) {}
}

onMounted(() => { loadScanStatus() })
onUnmounted(() => { if (scanTimer) clearInterval(scanTimer) })

// 设置面板关闭时停止轮询
watch(() => props.visible, (val) => {
  if (!val && scanTimer) {
    clearInterval(scanTimer)
    scanTimer = null
    scanning.value = false
  }
})

const durationOptions = computed(() => [
  { label: t('oneYear'), value: '1y' },
  { label: t('threeYears'), value: '3y' },
  { label: t('forever'), value: 'forever' },
])

// 监听设置变化，同步目录值
watch(() => props.settings, (val) => {
  if (val) {
    photosDir.value = val.photos_dir || ''
    starDir.value = val.star_dir || ''
    recycleDir.value = val.recycle_dir || ''
  }
}, { immediate: true })

async function checkDir(type) {
  const path = type === 'photos' ? photosDir.value : type === 'star' ? starDir.value : recycleDir.value
  if (!path) {
    dirRaw.value[type] = { state: '', count: 0 }
    return
  }
  try {
    const res = await fetch(`/api/dir/check?path=${encodeURIComponent(path)}`)
    const data = await res.json()
    if (data.success) {
      const info = data.data
      if (info.exists && info.photo_count > 0) {
        dirRaw.value[type] = { state: 'ok', count: info.photo_count }
      } else if (info.exists) {
        dirRaw.value[type] = { state: 'empty', count: 0 }
      } else {
        dirRaw.value[type] = { state: 'missing', count: 0 }
      }
    }
  } catch (e) {
    dirRaw.value[type] = { state: 'error', count: 0 }
  }
}

async function saveDirs() {
  saving.value = true
  try {
    await apiUpdateSetting('photos_dir', photosDir.value)
    await apiUpdateSetting('star_dir', starDir.value)
    await apiUpdateSetting('recycle_dir', recycleDir.value)
    emit('updated')
  } catch (e) {
    console.error('保存失败:', e)
  } finally {
    saving.value = false
  }
}

async function changeSetting(key, value) {
  try {
    await apiUpdateSetting(key, value)
    emit('updated')
  } catch (e) {
    console.error('更新设置失败:', e)
  }
}

async function toggleDuplicateFilter() {
  const newVal = props.settings.enable_duplicate_filter === 'true' ? 'false' : 'true'
  await apiUpdateSetting('enable_duplicate_filter', newVal)
  emit('updated')
}

async function handleResetBlacklist() {
  showResetBlacklistConfirm.value = false
  try {
    await resetBlacklist()
    emit('updated')
  } catch (e) {
    console.error('重置失败:', e)
  }
}

async function handleResetStats() {
  showResetStatsConfirm.value = false
  try {
    await resetStats()
    emit('updated')
  } catch (e) {
    console.error('重置失败:', e)
  }
}
</script>

<style scoped>
@import '../styles/modal.css';

.header-lang-btn {
  padding: 2px 8px;
  border-radius: 10px;
  border: 1px solid #e0e0e0;
  background: #fff;
  color: #999;
  font-size: 11px;
  cursor: pointer;
  flex-shrink: 0;
}

.header-lang-btn:active {
  background: #f0f0f0;
}

.setting-group {
  background: #fff;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 10px;
}

.setting-label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 2px;
}

.setting-desc {
  font-size: 12px;
  color: #999;
  margin-bottom: 10px;
}

.dir-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dir-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 13px;
  color: #333;
  background: #fafafa;
  outline: none;
  font-family: 'SF Mono', 'Menlo', monospace;
}

.dir-input:focus {
  border-color: #007AFF;
  background: #fff;
}

.dir-status {
  font-size: 11px;
  white-space: nowrap;
  min-width: 80px;
  text-align: right;
}

.status-ok { color: #4CAF50; }
.status-warn { color: #FF9800; }
.status-error { color: #F44336; }
.status-empty { color: #ccc; }

.divider {
  height: 1px;
  background: #f0f0f0;
  margin: 16px 0;
}

.setting-options {
  display: flex;
  gap: 8px;
}

.option-btn {
  flex: 1;
  padding: 8px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  background: #fff;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.option-btn.active {
  border-color: #007AFF;
  background: rgba(0, 122, 255, 0.08);
  color: #007AFF;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toggle-btn {
  width: 48px;
  height: 28px;
  border-radius: 14px;
  background: #e0e0e0;
  border: none;
  position: relative;
  cursor: pointer;
  transition: background 0.2s;
  flex-shrink: 0;
}

.toggle-btn.on {
  background: #007AFF;
}

.toggle-knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  transition: transform 0.2s;
}

.toggle-btn.on .toggle-knob {
  transform: translateX(20px);
}

.action-btn {
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  margin-bottom: 8px;
}

.action-btn.primary {
  background: #007AFF;
  color: #fff;
}

.action-btn.primary:disabled {
  opacity: 0.5;
}

.action-btn.danger {
  background: #fff;
  color: #FF3B30;
}

.action-btn.danger:active {
  background: #FFF0F0;
}

.scan-btn {
  width: auto;
  padding: 6px 16px;
  margin: 0;
  background: #007AFF;
  color: #fff;
  font-size: 12px;
  border-radius: 8px;
  flex-shrink: 0;
}

.scan-btn:disabled {
  opacity: 0.5;
}

.footer-info {
  text-align: center;
  padding: 20px 0 0;
}

.footer-info p {
  font-size: 11px;
  color: #ccc;
  line-height: 1.6;
}

</style>
