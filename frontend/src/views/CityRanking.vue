<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="暂无排名数据" @retry="load">
      <h1 class="page-h1">{{ selectedYear }} 年全球站点排名</h1>
      <p class="page-sub">基于 NOAA GSOD 年度聚合数据 · TOP 15</p>

      <div class="grid-2x2">
        <GlassCard v-for="cat in categories" :key="cat.key" class="rank-cell">
          <div class="cell-hd">
            <span class="cell-icon">{{ cat.icon }}</span>
            <span class="cell-title">{{ cat.label }}</span>
            <span class="cell-unit">单位：{{ cat.unit }}</span>
          </div>
          <div class="cell-chart">
            <v-chart v-if="charts[cat.key]" :option="charts[cat.key]" autoresize />
            <el-empty v-else description="暂无数据" />
          </div>
        </GlassCard>
      </div>
    </PageState>
  </div>
</template>

<script setup>
import { ref, reactive, inject, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'; import { CanvasRenderer } from 'echarts/renderers'; import { BarChart } from 'echarts/charts'; import { GridComponent, TooltipComponent } from 'echarts/components'
use([CanvasRenderer, BarChart, GridComponent, TooltipComponent])
import { getRanking } from '../api'; import { stationCN } from '../utils/stationNames'
import PageState from '../components/PageState.vue'; import GlassCard from '../components/GlassCard.vue'
import { chartColors, baseTooltip, safeNumber } from '../composables/useDashboardTheme'

const selectedYear = inject('selectedYear')
const loading = ref(true); const error = ref(''); const empty = ref(false)
let requestId = 0

const categories = [
  { key: 'hottest', icon: '🔥', label: '最高温站点', unit: '°C' },
  { key: 'coldest', icon: '❄️', label: '最低温站点', unit: '°C' },
  { key: 'rainiest', icon: '🌧️', label: '最多降水站点', unit: 'mm' },
  { key: 'most_extreme', icon: '⚠️', label: '极端天气站点', unit: '天' },
]

const charts = reactive({ hottest: null, coldest: null, rainiest: null, most_extreme: null })

function lerp(a, b, r) { return Math.round(a + (b - a) * r) }
function hex(r, g, b) { return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('') }

function buildOption(rows, cat) {
  const values = rows.map(r => safeNumber(r.value))
  const vmin = Math.min(...values.filter(Number.isFinite))
  const vmax = Math.max(...values.filter(Number.isFinite))
  const range = vmax - vmin || 1
  const isColdest = cat === 'coldest'

  const barData = values.map(v => {
    const ratio = Number.isFinite(v) ? (v - vmin) / range : 0.5
    const t = Math.max(0, Math.min(1, ratio))
    let color
    if (cat === 'hottest')        color = hex(lerp(0xff,0x8b,t), lerp(0xdb,0x37,t), lerp(0xce,0x13,t))
    else if (cat === 'coldest')    color = hex(lerp(0x1e,0xbb,t), lerp(0x88,0xde,t), lerp(0xe5,0xfb,t))
    else if (cat === 'rainiest')   color = hex(lerp(0xba,0x39,t), lerp(0xe8,0x65,t), lerp(0xef,0x6b,t))
    else                           color = hex(lerp(0xff,0x8b,t), lerp(0xdb,0x37,t), lerp(0xce,0x13,t))
    return {
      value: v,
      itemStyle: { color, borderRadius: isColdest ? [0, 0, 6, 6] : [6, 6, 0, 0] }
    }
  })

  return {
    tooltip: baseTooltip(),
    grid: { left: '3%', right: '6%', top: '4%', bottom: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: rows.map(r => stationCN(r.station_name || r.station_id).substring(0, 8)),
      axisLabel: { color: chartColors.text, fontSize: 10, rotate: 25, width: 50, overflow: 'truncate' },
      axisLine: { lineStyle: { color: chartColors.outline } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: chartColors.text, fontSize: 10 },
      splitLine: { lineStyle: { color: chartColors.grid } }
    },
    series: [{
      type: 'bar', data: barData, barMaxWidth: 20,
      itemStyle: {
        borderRadius: isColdest ? [0, 0, 6, 6] : [6, 6, 0, 0],
        color: !isColdest ? { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: cat === 'hottest' ? [{ offset: 0, color: '#ffdbce' }, { offset: 1, color: chartColors.orange }]
            : cat === 'rainiest' ? [{ offset: 0, color: '#bae8ef' }, { offset: 1, color: chartColors.green }]
            : [{ offset: 0, color: chartColors.tertiarySoft || '#ffdbce' }, { offset: 1, color: chartColors.tertiary }]
        } : undefined
      }
    }]
  }
}

async function load() {
  const id = ++requestId; loading.value = true; error.value = ''; empty.value = false
  const y = selectedYear.value
  try {
    const results = await Promise.all(categories.map(c => getRanking(y, c.key, 15)))
    if (id !== requestId) return

    let anyData = false
    categories.forEach((cat, i) => {
      const rows = (results[i].data?.data || []).sort((a, b) => a.rank_num - b.rank_num)
      if (rows.length) anyData = true
      charts[cat.key] = rows.length ? buildOption(rows, cat.key) : null
    })

    if (!anyData) { empty.value = true }
  } catch (e) {
    if (id === requestId) { error.value = '数据加载失败，请确认后端已启动'; console.error(e) }
  } finally {
    if (id === requestId) loading.value = false
  }
}
watch(selectedYear, load, { immediate: true })
</script>

<style scoped>
.page-sub { color: var(--ci-text-muted); font-size: 16px; margin-bottom: 8px; flex-shrink: 0; }

.grid-2x2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 12px;
  flex: 1; min-width: 0; min-height: 0;
}

.rank-cell {
  display: flex; flex-direction: column;
  overflow: hidden; padding: 12px 14px;
}

.cell-hd {
  display: flex; align-items: center; gap: 8px;
  flex-shrink: 0; margin-bottom: 6px;
}
.cell-icon { font-size: 18px; }
.cell-title { font-size: 16px; font-weight: 600; color: var(--ci-primary); }
.cell-unit { font-size: 12px; color: var(--ci-text-muted); margin-left: auto; }

.cell-chart { flex: 1; min-width: 0; min-height: 0; }

@media (max-width: 900px) {
  .grid-2x2 { grid-template-columns: 1fr; grid-template-rows: auto; }
}
</style>
