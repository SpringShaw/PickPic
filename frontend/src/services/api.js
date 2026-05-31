import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 获取随机图片
export async function getRandomPhoto(mediaType = 'photo') {
  const res = await api.get('/photo/random', { params: { media_type: mediaType } })
  return res.data
}

// 获取图片URL（原图）
export function getImageUrl(filePath) {
  return `/api/photo/image?path=${encodeURIComponent(filePath)}`
}

// 获取缩略图URL（优先使用缩略图，更快）
export function getThumbnailUrl(photo) {
  if (photo.file_hash) {
    return `/api/photo/thumbnail/${photo.file_hash}`
  }
  // 回退到原图
  return getImageUrl(photo.path)
}

// 触发照片扫描
export async function triggerScan(force = false) {
  const res = await api.post('/scan', null, { params: { force } })
  return res.data
}

// 获取扫描状态
export async function getScanStatus() {
  const res = await api.get('/scan/status')
  return res.data
}

// 收藏图片
export async function favoritePhoto(filePath) {
  const res = await api.post('/photo/favorite', null, { params: { file_path: filePath } })
  return res.data
}

// 删除图片
export async function deletePhoto(filePath) {
  const res = await api.post('/photo/delete', null, { params: { file_path: filePath } })
  return res.data
}

// 获取统计数据
export async function getStats() {
  const res = await api.get('/stats')
  return res.data
}

// 重置黑名单
export async function resetBlacklist() {
  const res = await api.post('/blacklist/reset')
  return res.data
}

// 重置统计
export async function resetStats() {
  const res = await api.post('/stats/reset')
  return res.data
}

// 获取设置
export async function getSettings() {
  const res = await api.get('/settings')
  return res.data
}

// 更新设置
export async function updateSetting(key, value) {
  const res = await api.post('/settings', null, { params: { key, value } })
  return res.data
}

// 验证目录路径
export async function checkDirectory(path) {
  const res = await api.get('/dir/check', { params: { path } })
  return res.data
}

// 获取回收站列表
export async function getRecycleList() {
  const res = await api.get('/recycle')
  return res.data
}

// 恢复单张照片
export async function restorePhoto(filePath) {
  const res = await api.post('/recycle/restore', null, { params: { file_path: filePath } })
  return res.data
}

// 批量恢复所有照片
export async function restoreAllPhotos() {
  const res = await api.post('/recycle/restore-all')
  return res.data
}

// 清空回收站
export async function emptyRecycle() {
  const res = await api.delete('/recycle/empty')
  return res.data
}
