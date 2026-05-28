import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 获取随机图片
export async function getRandomPhoto() {
  const res = await api.get('/photo/random')
  return res.data
}

// 获取图片URL
export function getImageUrl(filePath) {
  return `/api/photo/image?path=${encodeURIComponent(filePath)}`
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
