/**
 * 轻量双语 i18n 模块
 *
 * 规则：用户手动选择 > 浏览器语言（zh-* → 中文，其他 → 英文）> 默认中文
 */
import { ref } from 'vue'

// ── 翻译字典 ──────────────────────────────────────────────
const messages = {
  zh: {
    // App
    appTitle: '拣影 - 相册整理工具',
    noPhotos: '暂无可浏览的图片',
    noPhotosHint: '请确认图片目录已正确挂载',
    loadError: '加载失败，请检查网络连接',
    retry: '重试',
    bottomHintPhoto: '上滑删除 · 双击收藏 · 右滑保留',
    bottomHintVideo: '上滑删除 · 右滑保留',
    photoMode: '📷 照片',
    videoMode: '🎬 视频',
    zoomView: '放大查看',
    noRecall: '没有可找回的照片',
    recalled: '已找回',

    // PhotoCard
    keep: '保留',
    recall: '找回',
    deleteSwipe: '删除',

    // StatsBar
    viewed: '已浏览',
    favorited: '已收藏',
    cleaned: '已清理',

    // InfoPanel
    infoTitle: '图片信息',
    fileName: '文件名',
    dateTaken: '拍摄时间',
    resolution: '分辨率',
    fileSize: '文件大小',
    location: '位置',
    originalPath: '原始路径',
    unknown: '未知',
    noGpsData: '无GPS数据',

    // SettingsPanel
    settings: '设置',
    photosDir: '📂 图片源目录',
    photosDirDesc: 'NAS 上存放照片的文件夹路径',
    photosDirPlaceholder: '例如：/nas/host/共享/photos',
    starDir: '⭐ 收藏目录',
    starDirDesc: '收藏的照片将复制到此目录',
    starDirPlaceholder: '例如：/nas/host/共享/star_photos',
    recycleDir: '🗑️ 回收站目录',
    recycleDirDesc: '删除的照片将移动到此目录',
    recycleDirPlaceholder: '例如：/nas/host/共享/recycle_photos',
    saveDirs: '保存目录配置',
    saving: '保存中...',
    photoCache: '🗄️ 照片缓存',
    rescan: '重新扫描',
    scanning: '扫描中...',
    blacklistDuration: '⏱️ 屏蔽时长',
    blacklistDesc: '已浏览图片的屏蔽期限',
    oneYear: '1年',
    threeYears: '3年',
    forever: '永久',
    dupFilter: '🔄 重复图片过滤',
    dupFilterDesc: '自动跳过已浏览的相似图片',
    recycleManage: '🗑️ 回收站管理',
    favoritesManage: '⭐ 收藏夹',
    resetBlacklist: '重置黑名单',
    resetStats: '重置统计数据',
    footerVersion: '拣影 v1.0 · 纯本地运行',
    footerLocal: '所有数据均保存在 NAS 本地',
    dirNotSet: '未填写',
    dirOkPhotos: '{count} 张图片',
    dirExistsEmpty: '目录存在（无图片）',
    dirNotExists: '目录不存在',
    dirVerifyFailed: '验证失败',
    dirCheckPrefix: '✓',
    dirCheckFail: '✗',
    scanStatusScanning: '扫描中... {processed}/{total} (新增 {newCount})',
    scanStatusCached: '已缓存 {total} 张照片 · 新增 {newCount}',
    scanStatusIdle: '未扫描（启动时自动扫描）',

    // ConfirmDialog
    cancel: '取消',
    confirm: '确定',

    // RecyclePanel
    recycleTitle: '🗑️ 回收站',
    recycleEmpty: '回收站是空的',
    loading: '加载中...',
    selectAll: '全选',
    deselectAll: '取消全选',
    selectedCount: '已选 {count} 张',
    restoreSelected: '恢复选中',
    deleteSelected: '删除选中',
    restoreAll: '全部恢复',
    emptyAll: '全部清空',
    restoredCount: '已恢复 {count} 张照片',
    restoreFailed: '恢复失败',
    deletedCount: '已永久删除 {count} 个文件',
    emptyFailed: '清空失败',

    // FavoritesPanel
    favoritesTitle: '⭐ 收藏夹',
    favoritesEmpty: '还没有收藏的照片',
    favoritesHint: '双击照片即可收藏',
    unfavorite: '取消收藏',
    unfavCount: '已取消 {count} 张收藏',
    deletedToRecycle: '已将 {count} 张照片移入回收站',

    // Confirm messages
    confirmResetBlacklist: '确定要重置黑名单吗？所有已浏览图片将重新出现。',
    confirmResetStats: '确定要重置统计数据吗？浏览、收藏、清理记录将清零。',
    confirmRestoreAll: '确定恢复回收站中的所有照片到源目录吗？',
    confirmDeleteSelected: '确定永久删除选中的 {count} 个文件吗？此操作不可恢复',
    confirmEmptyRecycle: '确定清空回收站吗？所有文件将永久删除，此操作不可恢复',
    confirmDeleteFavorites: '确定将选中的 {count} 张照片移入回收站吗？',

    // Language toggle
    languageToggle: 'English',
    languageToggleTitle: 'Switch to English',
  },

  en: {
    // App
    appTitle: 'PickPic — Photo Organizer',
    noPhotos: 'No photos to browse',
    noPhotosHint: 'Please check that the photo directory is mounted',
    loadError: 'Failed to load. Please check your network connection.',
    retry: 'Retry',
    bottomHintPhoto: 'Swipe up to delete · Double-tap to favorite · Swipe right to keep',
    bottomHintVideo: 'Swipe up to delete · Swipe right to keep',
    photoMode: '📷 Photos',
    videoMode: '🎬 Videos',
    zoomView: 'Zoom In',
    noRecall: 'Nothing to recall',
    recalled: 'Recalled',

    // PhotoCard
    keep: 'Keep',
    recall: 'Recall',
    deleteSwipe: 'Delete',

    // StatsBar
    viewed: 'Viewed',
    favorited: 'Favorited',
    cleaned: 'Cleaned',

    // InfoPanel
    infoTitle: 'Photo Info',
    fileName: 'File Name',
    dateTaken: 'Date Taken',
    resolution: 'Resolution',
    fileSize: 'File Size',
    location: 'Location',
    originalPath: 'Original Path',
    unknown: 'Unknown',
    noGpsData: 'No GPS data',

    // SettingsPanel
    settings: 'Settings',
    photosDir: '📂 Photo Source',
    photosDirDesc: 'Folder path on NAS containing photos',
    photosDirPlaceholder: 'e.g. /nas/host/shared/photos',
    starDir: '⭐ Favorites Folder',
    starDirDesc: 'Favorited photos will be copied here',
    starDirPlaceholder: 'e.g. /nas/host/shared/star_photos',
    recycleDir: '🗑️ Recycle Bin',
    recycleDirDesc: 'Deleted photos will be moved here',
    recycleDirPlaceholder: 'e.g. /nas/host/shared/recycle_photos',
    saveDirs: 'Save Directories',
    saving: 'Saving...',
    photoCache: '🗄️ Photo Cache',
    rescan: 'Rescan',
    scanning: 'Scanning...',
    blacklistDuration: '⏱️ Blacklist Period',
    blacklistDesc: 'How long viewed photos stay hidden',
    oneYear: '1 Year',
    threeYears: '3 Years',
    forever: 'Forever',
    dupFilter: '🔄 Duplicate Filter',
    dupFilterDesc: 'Auto-skip duplicate images already viewed',
    recycleManage: '🗑️ Manage Recycle Bin',
    favoritesManage: '⭐ Favorites',
    resetBlacklist: 'Reset Blacklist',
    resetStats: 'Reset Statistics',
    footerVersion: 'PickPic v1.0 · Fully Offline',
    footerLocal: 'All data stored locally on your NAS',
    dirNotSet: 'Not set',
    dirOkPhotos: '{count} photos',
    dirExistsEmpty: 'Directory exists (empty)',
    dirNotExists: 'Directory not found',
    dirVerifyFailed: 'Verification failed',
    dirCheckPrefix: '✓',
    dirCheckFail: '✗',
    scanStatusScanning: 'Scanning... {processed}/{total} ({newCount} new)',
    scanStatusCached: 'Cached {total} photos · {newCount} new photos',
    scanStatusIdle: 'Not yet scanned (auto on startup)',

    // ConfirmDialog
    cancel: 'Cancel',
    confirm: 'Confirm',

    // RecyclePanel
    recycleTitle: '🗑️ Recycle Bin',
    recycleEmpty: 'Recycle Bin is empty',
    loading: 'Loading...',
    selectAll: 'Select All',
    deselectAll: 'Deselect All',
    selectedCount: '{count} selected',
    restoreSelected: 'Restore Selected',
    deleteSelected: 'Delete Selected',
    restoreAll: 'Restore All',
    emptyAll: 'Empty All',
    restoredCount: '{count} photos restored',
    restoreFailed: 'Restore failed',
    deletedCount: '{count} files permanently deleted',
    emptyFailed: 'Failed to empty recycle bin',

    // FavoritesPanel
    favoritesTitle: '⭐ Favorites',
    favoritesEmpty: 'No favorites yet',
    favoritesHint: 'Double-tap a photo to favorite it',
    unfavorite: 'Unfavorite',
    unfavCount: '{count} unfavorited',
    deletedToRecycle: '{count} photos moved to recycle bin',

    // Confirm messages
    confirmResetBlacklist: 'Reset the blacklist? All previously viewed photos will reappear.',
    confirmResetStats: 'Reset statistics? All counters will be cleared.',
    confirmRestoreAll: 'Restore all photos from recycle bin to source directory?',
    confirmDeleteSelected: 'Permanently delete {count} selected files? This cannot be undone.',
    confirmEmptyRecycle: 'Empty the entire recycle bin? All files will be permanently deleted.',
    confirmDeleteFavorites: 'Move {count} selected photos to recycle bin?',

    // Language toggle
    languageToggle: '中文',
    languageToggleTitle: '切换到中文',
  },
}

// ── 语言状态 ──────────────────────────────────────────────
const LANG_KEY = 'photo_sorter_lang'

function getInitialLocale() {
  const saved = localStorage.getItem(LANG_KEY)
  if (saved === 'zh' || saved === 'en') return saved
  if (!navigator.language) return 'zh'
  return navigator.language.toLowerCase().startsWith('zh') ? 'zh' : 'en'
}

export const locale = ref(getInitialLocale())

// ── 翻译函数 ──────────────────────────────────────────────
export function t(key, params = {}) {
  let text = messages[locale.value]?.[key] || messages.zh[key]
  if (text === undefined) return key
  for (const [name, val] of Object.entries(params)) {
    text = text.replace(`{${name}}`, val)
  }
  return text
}

export function toggleLocale() {
  locale.value = locale.value === 'zh' ? 'en' : 'zh'
  localStorage.setItem(LANG_KEY, locale.value)
}

