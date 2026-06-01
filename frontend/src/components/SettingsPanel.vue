<template>
  <transition name="modal-fade">
    <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">设置</span>
          <button class="modal-close" @click="$emit('close')">×</button>
        </div>
        <div class="modal-body">
          <!-- 目录配置 -->
          <div class="setting-group">
            <div class="setting-label">📂 图片源目录</div>
            <div class="setting-desc">NAS 上存放照片的文件夹路径</div>
            <div class="dir-input-row">
              <input
                class="dir-input"
                v-model="photosDir"
                placeholder="例如：/nas/host/共享/photos"
                @blur="checkDir('photos')"
              />
              <span class="dir-status" :class="dirStatus.photos.class">{{ dirStatus.photos.text }}</span>
            </div>
          </div>

          <div class="setting-group">
            <div class="setting-label">⭐ 收藏目录</div>
            <div class="setting-desc">收藏的照片将复制到此目录</div>
            <div class="dir-input-row">
              <input
                class="dir-input"
                v-model="starDir"
                placeholder="例如：/nas/host/共享/star_photos"
                @blur="checkDir('star')"
              />
              <span class="dir-status" :class="dirStatus.star.class">{{ dirStatus.star.text }}</span>
            </div>
          </div>

          <div class="setting-group">
            <div class="setting-label">🗑️ 回收站目录</div>
            <div class="setting-desc">删除的照片将移动到此目录</div>
            <div class="dir-input-row">
              <input
                class="dir-input"
                v-model="recycleDir"
                placeholder="例如：/nas/host/共享/recycle_photos"
                @blur="checkDir('recycle')"
              />
              <span class="dir-status" :class="dirStatus.recycle.class">{{ dirStatus.recycle.text }}</span>
            </div>
          </div>

          <button class="action-btn primary" @click="saveDirs" :disabled="saving">
            {{ saving ? '保存中...' : '保存目录配置' }}
          </button>

          <!-- 照片缓存扫描 -->
          <div class="setting-group">
            <div class="setting-row">
              <div>
                <div class="setting-label">🗄️ 照片缓存</div>
                <div class="setting-desc">{{ scanStatusText }}</div>
              </div>
              <button
                class="action-btn scan-btn"
                @click="triggerScan"
                :disabled="scanning"
              >
                {{ scanning ? '扫描中...' : '重新扫描' }}
              </button>
            </div>
          </div>

          <div class="divider"></div>

          <!-- 黑名单时长 -->
          <div class="setting-group">
            <div class="setting-label">⏱️ 屏蔽时长</div>
            <div class="setting-desc">已浏览图片的屏蔽期限</div>
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
                <div class="setting-label">🔄 重复图片过滤</div>
                <div class="setting-desc">自动跳过已浏览的相似图片</div>
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
              🗑️ 回收站管理
            </button>
            <button class="action-btn primary" @click="showFavorites = true">
              ⭐ 收藏夹
            </button>
            <button class="action-btn danger" @click="showResetBlacklistConfirm = true">
              重置黑名单
            </button>
            <button class="action-btn danger" @click="showResetStatsConfirm = true">
              重置统计数据
            </button>
          </div>

          <!-- 底部信息 -->
          <div class="footer-info">
            <p>去留 v1.0 · 纯本地运行</p>
            <p>所有数据均保存在 NAS 本地</p>
          </div>
        </div>
      </div>
    </div>
  </transition>

  <!-- 确认弹窗 -->
  <ConfirmDialog
    :visible="showResetBlacklistConfirm"
    message="确定要重置黑名单吗？所有已浏览图片将重新出现。"
    @confirm="handleResetBlacklist"
    @cancel="showResetBlacklistConfirm = false"
  />
  <ConfirmDialog
    :visible="showResetStatsConfirm"
    message="确定要重置统计数据吗？浏览、收藏、清理记录将清零。"
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
import ConfirmDialog from './ConfirmDialog.vue'
import RecyclePanel from './RecyclePanel.vue'
import FavoritesPanel from './FavoritesPanel.vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  settings: { type: Object, default: () => ({}) }
})

const emit = defineEmits(['close', 'updated'])

const showResetBlacklistConfirm = ref(false)
const showResetStatsConfirm = ref(false)
const showRecycle = ref(false)
const showFavorites = ref(false)
const saving = ref(false)

const photosDir = ref('')
const starDir = ref('')
const recycleDir = ref('')

const dirStatus = ref({
  photos: { text: '', class: '' },
  star: { text: '', class: '' },
  recycle: { text: '', class: '' },
})

const scanning = ref(false)
const scanStatus = ref({ status: 'idle', total: 0, processed: 0, new_count: 0 })
let scanTimer = null

const scanStatusText = computed(() => {
  const s = scanStatus.value
  if (s.status === 'scanning') {
    return `扫描中... ${s.processed}/${s.total} (新增 ${s.new_count})`
  }
  if (s.status === 'idle' && s.total > 0) {
    return `已缓存 ${s.total} 张照片 · 新增 ${s.new_count}`
  }
  return '未扫描（启动时自动扫描）'
})

async function triggerScan() {
  scanning.value = true
  try {
    await apiTriggerScan(true)
    // 开始轮询状态
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
  } catch (e) {
    scanning.value = false
  }
}

async function loadScanStatus() {
  try {
    const res = await getScanStatus()
    if (res.success) {
      scanStatus.value = res.data
      if (res.data.status === 'scanning') {
        scanning.value = true
        triggerScan() // 继续轮询
      }
    }
  } catch (e) {}
}

onMounted(() => { loadScanStatus() })
onUnmounted(() => { if (scanTimer) clearInterval(scanTimer) })

const durationOptions = [
  { label: '1年', value: '1y' },
  { label: '3年', value: '3y' },
  { label: '永久', value: 'forever' },
]

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
    dirStatus.value[type] = { text: '未填写', class: 'status-empty' }
    return
  }
  try {
    const res = await fetch(`/api/dir/check?path=${encodeURIComponent(path)}`)
    const data = await res.json()
    if (data.success) {
      const info = data.data
      if (info.exists && info.photo_count > 0) {
        dirStatus.value[type] = { text: `✓ ${info.photo_count} 张图片`, class: 'status-ok' }
      } else if (info.exists) {
        dirStatus.value[type] = { text: '✓ 目录存在（无图片）', class: 'status-warn' }
      } else {
        dirStatus.value[type] = { text: '✗ 目录不存在', class: 'status-error' }
      }
    }
  } catch (e) {
    dirStatus.value[type] = { text: '验证失败', class: 'status-error' }
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
