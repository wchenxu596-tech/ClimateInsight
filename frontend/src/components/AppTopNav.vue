<template>
  <nav class="topnav">
    <!-- 左侧：日期 + 实时时钟 -->
    <div class="tn-left">
      <span class="tn-date">{{ dateStr }}</span>
      <span class="tn-divider">·</span>
      <span class="tn-time">{{ timeStr }}</span>
    </div>

    <!-- 中间：品牌标题 -->
    <div class="tn-center">
      <span class="topnav-brand">🌍 ClimateInsight</span>
      <span class="topnav-subtitle">全球气候智能分析平台</span>
    </div>

    <!-- 右侧：天气 + 数据概览 -->
    <div class="tn-right">
      <span v-if="weatherText" class="tn-weather" :title="weatherTitle">{{ weatherText }}</span>
      <span class="tn-divider">·</span>
      <span class="tn-stat">📊 {{ selectedYear }} 年数据</span>
    </div>
  </nav>
</template>

<script setup>
import { ref, inject, onMounted, onUnmounted } from 'vue'

const selectedYear = inject('selectedYear', ref(2024))

// ── 实时时钟 ──
const dateStr = ref('')
const timeStr = ref('')
let timer = null

function tick() {
  const now = new Date()
  dateStr.value = now.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short' })
  timeStr.value = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}

// ── 当地天气（Open-Meteo 免费 API + 浏览器定位） ──
const weatherText = ref('')
const weatherTitle = ref('')
const weatherCodeMap = {
  0: '☀️', 1: '🌤️', 2: '🌤️', 3: '☁️',
  45: '🌫️', 48: '🌫️',
  51: '🌧️', 53: '🌧️', 55: '🌧️', 56: '🌧️', 57: '🌧️',
  61: '🌧️', 63: '🌧️', 65: '🌧️', 66: '🌧️', 67: '🌧️',
  71: '❄️', 73: '❄️', 75: '❄️', 77: '❄️',
  80: '🌦️', 81: '🌦️', 82: '🌦️',
  85: '❄️', 86: '❄️',
  95: '⛈️', 96: '⛈️', 99: '⛈️',
}

async function fetchWeather(lat, lon) {
  try {
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat.toFixed(2)}&longitude=${lon.toFixed(2)}&current=temperature_2m,weather_code&timezone=auto`
    const res = await fetch(url, { signal: AbortSignal.timeout(5000) })
    if (!res.ok) return
    const data = await res.json()
    const cur = data.current
    if (!cur) return
    const icon = weatherCodeMap[cur.weather_code] || '🌡️'
    weatherText.value = `${icon} ${cur.temperature_2m}°C`
    weatherTitle.value = `当地时间: ${cur.time}`
  } catch {
    // 天气获取失败，静默忽略
  }
}

function tryLocate() {
  if (!navigator.geolocation) {
    // 默认北京
    fetchWeather(39.9, 116.4)
    return
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => fetchWeather(pos.coords.latitude, pos.coords.longitude),
    () => fetchWeather(39.9, 116.4), // 拒绝定位则默认北京
    { timeout: 5000, maximumAge: 600000 },
  )
}

onMounted(() => {
  tick()
  timer = setInterval(tick, 1000)
  tryLocate()
})

onUnmounted(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.topnav {
  display: flex; align-items: center; justify-content: space-between;
  height: 52px; padding: 0 16px; margin-bottom: 8px;
  background: rgb(250 249 247 / 70%); backdrop-filter: blur(12px) saturate(1.4);
  border: 1px solid rgb(255 255 255 / 45%); border-radius: 20px;
  box-shadow: 0 2px 8px rgb(0 0 0 / 5%);
  flex-shrink: 0;
}

/* ── 左·中·右 统一文字 ── */
.tn-left,
.tn-right { display: flex; align-items: center; gap: 5px; flex-shrink: 0; }
.tn-date,
.tn-time,
.tn-weather,
.tn-stat { font-size: 18px; white-space: nowrap; }
.tn-date { color: var(--ci-text-muted); font-weight: 500; }
.tn-time { color: var(--ci-primary); font-weight: 700; font-variant-numeric: tabular-nums; letter-spacing: 0.02em; }
.tn-weather { color: var(--ci-text); font-weight: 600; }
.tn-stat { color: var(--ci-text-muted); font-weight: 500; }
.tn-divider { font-size: 18px; color: var(--ci-outline-variant); }

/* ── 中间 ── */
.tn-center { display: flex; align-items: center; gap: 8px; flex-shrink: 1; min-width: 0; justify-content: center; }
.topnav-brand { font-size: 22px; font-weight: 700; color: var(--ci-primary); white-space: nowrap; }
.topnav-subtitle { font-size: 16px; color: var(--ci-text-muted); white-space: nowrap; }

@media (max-width: 900px) {
  .topnav { height: 44px; padding: 0 12px; border-radius: 18px; }
  .topnav-brand { font-size: 17px; }
  .topnav-subtitle { display: none; }
  .tn-date { display: none; }
}
@media (max-width: 600px) {
  .topnav { justify-content: center; }
  .tn-left, .tn-right { display: none; }
}
</style>
