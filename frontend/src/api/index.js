import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
})

api.interceptors.response.use(r => r, err => {
  console.error('[API]', err.response?.data?.message || err.message)
  return Promise.reject(err)
})

// ── 前端轻量缓存：去重 + 短 TTL ──
const _pCache = new Map() // promise 缓存（去重：同一请求在途时共享）
const _rCache = new Map() // response 缓存（结果缓存 30s）
const CACHE_TTL = 30000 // 30 秒

function cacheKey(url, params) {
  return url + '?' + JSON.stringify(params)
}

function cachedGet(url, config = {}) {
  const key = cacheKey(url, config.params || {})
  // 命中结果缓存
  const cached = _rCache.get(key)
  if (cached && Date.now() - cached.ts < CACHE_TTL) {
    return Promise.resolve(cached.data)
  }
  // 命中在途 promise（去重）
  const inFlight = _pCache.get(key)
  if (inFlight) return inFlight
  // 发起新请求
  const p = api.get(url, config).then(r => {
    _pCache.delete(key)
    _rCache.set(key, { data: r, ts: Date.now() })
    // 定期清理旧缓存
    if (_rCache.size > 100) {
      const now = Date.now()
      for (const [k, v] of _rCache) { if (now - v.ts > CACHE_TTL * 2) _rCache.delete(k) }
    }
    return r
  }).catch(e => {
    _pCache.delete(key)
    throw e
  })
  _pCache.set(key, p)
  return p
}

export const getKPI = (year) => cachedGet('/kpi', { params: { year } })
export const getTrend = (year) => cachedGet('/trend', { params: { year } })
export const getRanking = (year, category = 'hottest', limit = 15) =>
  cachedGet('/ranking', { params: { year, category, limit } })
export const getMonthly = (year) => cachedGet('/monthly', { params: { year } })
export const getZones = (year) => cachedGet('/zones', { params: { year } })
export const getHealth = () => api.get('/health')
export const askAgent = (question, year = 2024) =>
  api.post('/agent/query', { question, year })

// ── 数据 API ──
export const getAlertRisk = (year, limit = 100) =>
  cachedGet('/alert/risk', { params: { year, limit } })
export const getAlertMonthly = (year) =>
  cachedGet('/alert/monthly', { params: { year } })
export const getStations = (year) =>
  cachedGet('/stations', { params: { year } })
export const getStationDetail = (stationId, year = 2024) =>
  cachedGet('/stations/detail', { params: { station_id: stationId, year } })
export const getTrendMultiYear = (years = '2022,2023,2024') =>
  cachedGet('/trend/multi-year', { params: { years } })
export const getZonesMultiYear = (years = '2022,2023,2024') =>
  cachedGet('/zones/multi-year', { params: { years } })
export const getZoneStats = (year) =>
  cachedGet('/zones/stats', { params: { year } })
export const getTrendKpiHistory = (years = '2015,2016,2017,2021,2022,2023,2024,2025') =>
  cachedGet('/trend/kpi-history', { params: { years } })
export const getZonesTrend = (years = '2015,2016,2017,2021,2022,2023,2024,2025') =>
  cachedGet('/zones/trend', { params: { years } })

export default api
