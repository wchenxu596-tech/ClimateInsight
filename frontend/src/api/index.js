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

export default api
