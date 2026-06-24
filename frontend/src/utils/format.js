/**
 * 共享格式化工具函数
 */

/**
 * 格式化文件大小为人类可读格式
 * @param {number} bytes - 文件大小（字节）
 * @returns {string} 格式化后的大小字符串
 */
export function formatSize(bytes) {
  if (!bytes && bytes !== 0) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}

/**
 * 格式化 EXIF 日期字符串
 * @param {string} dateStr - EXIF 格式日期 "2024:01:15 14:30:22"
 * @returns {string} 格式化后 "2024-01-15 14:30"
 */
export function formatDate(dateStr) {
  if (!dateStr) return ''
  return dateStr.replace(/^(\d{4}):(\d{2}):(\d{2})/, '$1-$2-$3').replace(/\s+\d{2}$/, '')
}

/**
 * 格式化视频时长（秒 → mm:ss）
 * @param {number} seconds - 时长（秒）
 * @returns {string}
 */
export function formatDuration(seconds) {
  if (!seconds) return ''
  const min = Math.floor(seconds / 60)
  const sec = Math.floor(seconds % 60)
  return `${min}:${sec.toString().padStart(2, '0')}`
}
