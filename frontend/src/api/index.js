import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
})

api.interceptors.response.use(r => r, err => {
  console.error('[API]', err.response?.data?.message || err.message)
  return Promise.reject(err)
})

export const getKPI = (year) => api.get('/kpi', { params: { year } })
export const getTrend = (year) => api.get('/trend', { params: { year } })
export const getRanking = (year, category = 'hottest', limit = 15) =>
  api.get('/ranking', { params: { year, category, limit } })
export const getMonthly = (year) => api.get('/monthly', { params: { year } })
export const getZones = (year) => api.get('/zones', { params: { year } })
export const getHealth = () => api.get('/health')
export const askAgent = (question, year = 2024) =>
  api.post('/agent/query', { question, year })

// ── 新增 API ──
export const getAlertRisk = (year, limit = 100) =>
  api.get('/alert/risk', { params: { year, limit } })
export const getAlertMonthly = (year) =>
  api.get('/alert/monthly', { params: { year } })
export const getStations = (year) =>
  api.get('/stations', { params: { year } })
export const getStationDetail = (stationId, year = 2024) =>
  api.get('/stations/detail', { params: { station_id: stationId, year } })
export const getTrendMultiYear = (years = '2022,2023,2024') =>
  api.get('/trend/multi-year', { params: { years } })
export const getZonesMultiYear = (years = '2022,2023,2024') =>
  api.get('/zones/multi-year', { params: { years } })
export const getZoneStats = (year) =>
  api.get('/zones/stats', { params: { year } })

export default api
