<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="暂无气候带数据" @retry="load">
      <div class="zones-root">
        <!-- 标题 -->
        <div class="zones-hd">
          <h1 class="page-h1">气候带分布与演变</h1>
          <p class="page-sub">{{ firstYear }}–{{ selectedYear }} {{ yearCountText }}数据对比 · 站点迁移 · 温度趋势 · 极端事件分布</p>
        </div>

        <!-- 顶部：左8（两图上下并排）+ 右2（饼图跨满） -->
        <div class="zones-top">
          <div class="zt-left">
            <ChartPanel title="各气候带站点数对比" :subtitle="yearCountText + '分组柱状图 · 直观看气候带规模变化'">
              <v-chart :option="barOption" autoresize />
            </ChartPanel>
            <ChartPanel title="各气候带温度变化趋势" :subtitle="'5 条曲线反映各气候带年均温的年际变化（截至 ' + selectedYear + '）'">
              <v-chart :option="zoneLineOption" autoresize />
            </ChartPanel>
          </div>
          <div class="zt-right">
            <ChartPanel title="气候带占比演变" :subtitle="'内→外：' + firstYear + ' → ' + selectedYear">
              <v-chart v-if="pieHasData" :option="pieOption" autoresize />
              <el-empty v-else description="暂无数据" />
            </ChartPanel>
          </div>
        </div>

        <!-- 中间：五个气候带详情卡片 -->
        <div class="zones-cards">
          <GlassCard v-for="z in zoneCards" :key="z.key" class="zone-card" :style="{ borderTop: '3px solid ' + z.color }">
            <div class="zc-hd">
              <span class="zc-dot" :style="{ background: z.color }"></span>
              <span class="zc-name">{{ z.name }}</span>
              <span :class="['zc-trend', z.cntTrend > 0 ? 'up' : z.cntTrend < 0 ? 'down' : '']">
                {{ z.cntTrend > 0 ? '↑' : z.cntTrend < 0 ? '↓' : '→' }} {{ Math.abs(z.cntTrend) }}站
              </span>
            </div>
            <div class="zc-stats">
              <div class="zc-stat">
                <span>站点数</span>
                <strong>{{ z.count }} <small>({{ z.cntChangeText }})</small></strong>
              </div>
              <div class="zc-stat">
                <span>均温</span>
                <strong>{{ z.avgTemp }}°C <small>({{ z.tempTrend }})</small></strong>
              </div>
              <div class="zc-stat">
                <span>年降水</span>
                <strong>{{ z.precip }}mm <small>({{ z.precipTrend }})</small></strong>
              </div>
              <div class="zc-stat">
                <span>极端天数</span>
                <strong>{{ z.extreme }}</strong>
              </div>
              <div class="zc-stat">
                <span>热浪天数</span>
                <strong>{{ z.heatWave }}</strong>
              </div>
              <div class="zc-stat">
                <span>寒潮天数</span>
                <strong>{{ z.coldWave }}</strong>
              </div>
            </div>
            <div class="zc-note">{{ z.note }}</div>
          </GlassCard>
        </div>

        <!-- 底部：三个洞察文本模块（压缩高度，独立滚动，滚动隔离） -->
        <div class="insight-row">
          <GlassCard class="insight-card">
            <div class="ic-hd">
              <span class="ic-icon">🌍</span>
              <span class="ic-title">气候带变化总结</span>
            </div>
            <div class="ic-body"><div class="ic-text">{{ insightSummary }}</div></div>
          </GlassCard>
          <GlassCard class="insight-card">
            <div class="ic-hd">
              <span class="ic-icon">🌡️</span>
              <span class="ic-title">温度带迁移分析</span>
            </div>
            <div class="ic-body"><div class="ic-text">{{ migrationText }}</div></div>
          </GlassCard>
          <GlassCard class="insight-card">
            <div class="ic-hd">
              <span class="ic-icon">⚠️</span>
              <span class="ic-title">极端天气分布</span>
            </div>
            <div class="ic-body"><div class="ic-text">{{ extremeText }}</div></div>
          </GlassCard>
        </div>
      </div>
    </PageState>
  </div>
</template>

<script setup>
import { ref, reactive, inject, watch, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'; import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, BarChart, PieChart, LineChart, GridComponent, TooltipComponent, LegendComponent])
import { getZonesMultiYear, getZoneStats, getZonesTrend } from '../api'
import PageState from '../components/PageState.vue'
import GlassCard from '../components/GlassCard.vue'
import ChartPanel from '../components/ChartPanel.vue'
import { chartColors, zoneColors, zoneCN } from '../composables/useDashboardTheme'

const selectedYear = inject('selectedYear')

const ALL_YEARS = [2015, 2016, 2017, 2021, 2022, 2023, 2024, 2025]
const YEAR_PALETTE = ['#3a674f', '#39656b', '#8b3713', '#c78b3c', '#009f7f', '#5da9b4', '#e08050', '#7a8b9a']
const yearColors = Object.fromEntries(ALL_YEARS.map((y, i) => [y, YEAR_PALETTE[i]]))
const zoneKeys = ['tropical', 'temperate', 'arid', 'continental', 'polar']

const activeYears = computed(() => ALL_YEARS.filter(y => y <= selectedYear.value))
const firstYear = computed(() => activeYears.value[0] || selectedYear.value)
const yearCountText = computed(() => {
  const n = activeYears.value.length
  const map = { 1: '一年', 2: '两年', 3: '三年', 4: '四年', 5: '五年', 6: '六年', 7: '七年', 8: '八年' }
  return map[n] || n + '年'
})

const loading = ref(true); const error = ref(''); const empty = ref(false); const pieHasData = ref(false)
let requestId = 0

const barOption = reactive({
  tooltip: { trigger: 'axis', valueFormatter: (v) => typeof v === 'number' ? v + ' 站' : v },
  legend: { data: [], textStyle: { color: chartColors.text, fontSize: 11 }, top: 0, type: 'scroll' },
  grid: { left: '3%', right: '4%', top: '15%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: zoneKeys.map(k => zoneCN[k]), axisLabel: { color: chartColors.text, fontSize: 12 } },
  yAxis: { type: 'value', name: '站点数', axisLabel: { color: chartColors.text, fontSize: 11 }, splitLine: { lineStyle: { color: chartColors.grid } } },
  series: [],
})

const pieOption = reactive({
  tooltip: { trigger: 'item', formatter: '{b}: {c} 站 ({d}%)' },
  legend: { bottom: 0, textStyle: { color: chartColors.text, fontSize: 10 } },
  series: [],
})

const zoneLineOption = reactive({
  tooltip: { trigger: 'axis', valueFormatter: (v) => typeof v === 'number' ? v.toFixed(1) + '°C' : v },
  legend: { data: zoneKeys.map(k => zoneCN[k]), textStyle: { color: chartColors.text, fontSize: 11 }, top: 0 },
  grid: { left: '3%', right: '4%', top: '14%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: [], axisLabel: { color: chartColors.text, fontSize: 11 } },
  yAxis: { type: 'value', name: '°C', axisLabel: { color: chartColors.text, fontSize: 11 }, splitLine: { lineStyle: { color: chartColors.grid } } },
  series: [],
})

const zoneCards = ref([])
const insightSummary = ref('')
const migrationText = ref('')
const extremeText = ref('')

function safeNumber(v) {
  if (v == null || v === '') return null
  const n = Number(v)
  return isNaN(n) || !isFinite(n) ? null : n
}

function avg(arr) {
  const valid = arr.filter(v => v != null)
  return valid.length ? valid.reduce((a, b) => a + b, 0) / valid.length : null
}

function computeAll(multiData, statsData, trendData, years) {
  const curYear = selectedYear.value
  const fYear = years[0]

  const cntByYear = {}
  years.forEach(y => { cntByYear[y] = {}; zoneKeys.forEach(k => { cntByYear[y][k] = 0 }) })
  multiData.forEach(r => { if (cntByYear[r.year]) cntByYear[r.year][r.climate_zone] = r.cnt || 0 })

  const trendByYear = {}
  years.forEach(y => { trendByYear[y] = {}; zoneKeys.forEach(k => { trendByYear[y][k] = {} }) })
  trendData.forEach(r => {
    if (trendByYear[r.year] && trendByYear[r.year][r.climate_zone]) {
      trendByYear[r.year][r.climate_zone] = {
        avg_temp: safeNumber(r.avg_temp), avg_precip: safeNumber(r.avg_precip),
        extreme_days: safeNumber(r.extreme_days) || 0, heat_wave_days: safeNumber(r.heat_wave_days) || 0,
        cold_wave_days: safeNumber(r.cold_wave_days) || 0, station_count: safeNumber(r.station_count) || 0,
      }
    }
  })

  const statsMap = {}
  statsData.forEach(r => { statsMap[r.climate_zone] = r })

  // 分组柱状图
  barOption.legend.data = years.map(String)
  barOption.series = years.map(y => ({
    name: String(y), type: 'bar', barMaxWidth: 20, barGap: '8%',
    data: zoneKeys.map(k => cntByYear[y][k] || 0),
    itemStyle: { color: yearColors[y], borderRadius: [4, 4, 0, 0] },
  }))

  // 多层环形图
  pieHasData.value = multiData.length > 0
  pieOption.series = years.map((y, i) => ({
    type: 'pie',
    radius: [22 + i * (Math.min(56 / Math.max(years.length, 1), 20)) + '%', 38 + i * (Math.min(56 / Math.max(years.length, 1), 20)) + '%'],
    center: ['50%', '50%'],
    data: zoneKeys.filter(k => cntByYear[y][k] > 0).map(k => ({
      name: zoneCN[k], value: cntByYear[y][k], itemStyle: { color: zoneColors[k] }
    })),
    label: { show: false },
    emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
  }))

  // 气候带温度趋势线
  zoneLineOption.xAxis.data = years.map(String)
  zoneLineOption.series = zoneKeys.map(k => ({
    name: zoneCN[k], type: 'line', smooth: true, symbolSize: 4,
    data: years.map(y => trendByYear[y]?.[k]?.avg_temp ?? null),
    itemStyle: { color: zoneColors[k] }, lineStyle: { width: 2.5 },
    emphasis: { focus: 'series' },
  }))

  // 详细卡片
  zoneCards.value = zoneKeys.map(k => {
    const curCnt = cntByYear[curYear]?.[k] || 0
    const firstCnt = cntByYear[fYear]?.[k] || 0
    const cntTrend = curCnt - firstCnt
    const curStats = trendByYear[curYear]?.[k] || {}
    const firstStats = trendByYear[fYear]?.[k] || {}
    const curTemp = curStats.avg_temp; const firstTemp = firstStats.avg_temp
    const curPrecip = curStats.avg_precip; const firstPrecip = firstStats.avg_precip
    const tempTrendVal = curTemp != null && firstTemp != null ? curTemp - firstTemp : null
    const precipTrendVal = curPrecip != null && firstPrecip != null ? curPrecip - firstPrecip : null
    const stats = statsMap[k] || {}
    const hw = safeNumber(stats.heat_wave_days) || 0
    const cw = safeNumber(stats.cold_wave_days) || 0
    const ext = safeNumber(stats.extreme_days) || 0
    const cntChangeText = cntTrend > 0 ? `+${cntTrend}` : `${cntTrend}`
    const tempTrend = tempTrendVal != null ? (tempTrendVal > 0 ? `↑${tempTrendVal.toFixed(1)}` : `↓${Math.abs(tempTrendVal).toFixed(1)}`) : '--'
    const precipTrend = precipTrendVal != null ? (precipTrendVal > 0 ? `↑${precipTrendVal.toFixed(0)}` : `↓${Math.abs(precipTrendVal).toFixed(0)}`) : '--'
    const notes = []
    if (cntTrend > 50) notes.push('站点数显著增长')
    else if (cntTrend < -50) notes.push('站点数明显减少')
    else if (Math.abs(cntTrend) <= 10) notes.push('站点数保持稳定')
    if (tempTrendVal != null && tempTrendVal > 0.5) notes.push('温度上升明显')
    else if (tempTrendVal != null && tempTrendVal < -0.3) notes.push('温度略有下降')
    const extremeTotal = hw + cw + ext
    if (extremeTotal > 50000) notes.push('极端事件高发区')
    else if (extremeTotal < 1000) notes.push('极端事件较少')
    return {
      key: k, name: zoneCN[k], color: zoneColors[k],
      count: curCnt, cntTrend, cntChangeText,
      avgTemp: curTemp != null ? curTemp.toFixed(1) : (stats.avg_temp ?? '--'),
      tempTrend, precip: curPrecip != null ? curPrecip.toFixed(0) : (stats.avg_precip ?? '--'),
      precipTrend, extreme: ext, heatWave: hw, coldWave: cw,
      note: notes.join(' · ') || '数据收集中',
    }
  })

  // ── 洞察文本 ──
  const sorted = [...zoneCards.value].sort((a, b) => b.cntTrend - a.cntTrend)
  const growing = sorted.filter(z => z.cntTrend > 0)
  const shrinking = sorted.filter(z => z.cntTrend < 0)
  const largest = sorted.reduce((a, b) => (b.count > a.count ? b : a), sorted[0])
  const totalStations = zoneCards.value.reduce((s, z) => s + z.count, 0)

  let summary = `${fYear}–${curYear}年气候带分布变化：`
  if (growing.length) summary += growing.map(z => `${z.name}站点增加 ${z.cntTrend} 个`).join('，') + '。'
  if (shrinking.length) summary += shrinking.map(z => `${z.name}站点减少 ${Math.abs(z.cntTrend)} 个`).join('，') + '。'
  if (!growing.length && !shrinking.length) summary += '各气候带站点数基本保持不变。'
  summary += `${largest.name}是站点数量最多的气候带（${largest.count} 站），占总站点数的 ${totalStations ? ((largest.count / totalStations) * 100).toFixed(0) : '--'}%。`
  if (years.length < 3) {
    summary += `由于仅有${yearCountText.value}数据，长期变化趋势尚不明确，需积累更多年份数据进行验证。`
  } else {
    summary += `整体来看，全球气象站网络覆盖格局基本稳定，但各气候带内部站点数量存在年际波动。`
  }
  insightSummary.value = summary

  // 温度带迁移分析
  const zoneTempChanges = zoneKeys.map(k => {
    const cur = trendByYear[curYear]?.[k]?.avg_temp
    const first = trendByYear[fYear]?.[k]?.avg_temp
    return { name: zoneCN[k], change: cur != null && first != null ? cur - first : null }
  }).filter(z => z.change != null)

  if (zoneTempChanges.length && years.length >= 2) {
    const allWarming = zoneTempChanges.every(z => z.change > 0)
    const fastestWarming = [...zoneTempChanges].sort((a, b) => b.change - a.change)[0]
    migrationText.value = `${fYear}–${curYear}年，${allWarming ? '五大气候带均温全部上升' : '多数气候带均温上升'}。${zoneTempChanges.map(z => `${z.name}${z.change > 0 ? '升温' : '降温'}${Math.abs(z.change).toFixed(1)}°C`).join('，')}。升温最快的是${fastestWarming.name}（+${fastestWarming.change.toFixed(1)}°C），反映了全球变暖在高纬度/高海拔地区的放大效应。${fastestWarming.name === '寒带' ? '寒带升温最快，可能导致永久冻土融化和海冰退缩，对全球海平面产生深远影响。' : ''}${fastestWarming.name === '热带' ? '热带升温显著，可能加剧热浪频率和珊瑚白化风险，威胁生物多样性。' : ''}气候带边界可能随温度变化发生缓慢迁移，温带范围可能向两极扩展。然而，${yearCountText.value}的时间跨度对于气候带迁移研究仍较短，需持续监测。`
  } else {
    migrationText.value = `当前仅有${yearCountText.value}数据，尚不足以分析气候带温度迁移趋势。气候变化研究通常需要30年以上的连续观测数据才能得出可靠结论。随着数据积累，未来将能够识别各气候带的温度变化模式和边界迁移方向。`
  }

  // 极端天气分布
  const zoneExtremes = zoneKeys.map(k => {
    const cur = trendByYear[curYear]?.[k] || {}
    const first = trendByYear[fYear]?.[k] || {}
    const curTotal = (safeNumber(cur.extreme_days) || 0) + (safeNumber(cur.heat_wave_days) || 0) + (safeNumber(cur.cold_wave_days) || 0)
    const firstTotal = (safeNumber(first.extreme_days) || 0) + (safeNumber(first.heat_wave_days) || 0) + (safeNumber(first.cold_wave_days) || 0)
    return { name: zoneCN[k], curTotal, firstTotal, change: curTotal - firstTotal }
  })
  const extremeSorted = [...zoneExtremes].sort((a, b) => b.curTotal - a.curTotal)
  const worstZone = extremeSorted[0]
  const growingExtremes = extremeSorted.filter(z => z.change > 0)

  extremeText.value = `在${curYear}年，极端天气事件（极端温度+热浪+寒潮）分布不均。${worstZone.name}极端事件最为集中（${worstZone.curTotal.toLocaleString()} 天次），远超其他气候带。${years.length >= 2 ? (growingExtremes.length ? `${fYear}→${curYear}年，${growingExtremes.map(z => `${z.name}极端事件增加 ${z.change.toLocaleString()} 天次`).join('，')}。` : '各气候带极端事件变化不大。') : '暂无法进行年际对比。'}极端高温事件主要集中在热带和温带地区，寒潮事件则以寒带和大陆性气候带为主。${growingExtremes.length >= 3 ? '多数气候带极端事件呈增加趋势，与全球气候变暖背景一致，需加强极端天气监测和预警能力。' : '需持续关注极端天气的频次和强度变化趋势。'}`
}

async function load() {
  const id = ++requestId; loading.value = true; error.value = ''; empty.value = false
  const years = activeYears.value
  if (!years.length) { empty.value = true; loading.value = false; return }
  try {
    const [multiRes, statsRes, trendRes] = await Promise.all([
      getZonesMultiYear(years.join(',')),
      getZoneStats(selectedYear.value),
      getZonesTrend(years.join(',')),
    ])
    if (id !== requestId) return
    const multiData = multiRes.data?.data || []
    const statsData = statsRes.data?.data || []
    const trendData = trendRes.data?.data || []
    if (!multiData.length) { empty.value = true; loading.value = false; return }
    computeAll(multiData, statsData, trendData, years)
  } catch (e) {
    if (id === requestId) { error.value = '数据加载失败'; console.error(e) }
  } finally { if (id === requestId) loading.value = false }
}

watch(selectedYear, load, { immediate: true })
</script>

<style scoped>
.zones-root { display: flex; flex-direction: column; flex: 1; min-width: 0; min-height: 0; gap: 8px; }
.zones-hd { flex-shrink: 0; }
.page-sub { color: var(--ci-text-muted); font-size: 13px; margin-top: 1px; }

/* ── 顶部：左8右2，右跨满左两图高度 ── */
.zones-top { display: grid; grid-template-columns: 8fr 2fr; gap: 10px; flex: 1; min-width: 0; min-height: 0; }
.zt-left { display: flex; flex-direction: column; gap: 8px; min-width: 0; min-height: 0; }
.zt-left > * { flex: 1; min-width: 0; min-height: 0; }
.zt-right { min-width: 0; min-height: 0; }
.zt-right > * { height: 100%; }

/* ── 中间卡片 ── */
.zones-cards { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; flex-shrink: 0; }
.zone-card { padding: 10px 12px; display: flex; flex-direction: column; gap: 6px; }
.zone-card::after { content: ''; position: absolute; inset: 0; border-radius: inherit; background: linear-gradient(135deg, rgb(255 255 255 / 20%) 0%, transparent 60%); opacity: 0; transition: opacity .4s var(--ci-ease-out); pointer-events: none; }
.zone-card:hover::after { opacity: 1; }
.zc-hd { display: flex; align-items: center; gap: 6px; }
.zc-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.zc-name { font-size: 14px; font-weight: 700; color: var(--ci-text); flex: 1; }
.zc-trend { font-size: 12px; font-weight: 700; }
.zc-trend.up { color: var(--ci-tertiary); }
.zc-trend.down { color: var(--ci-secondary); }
.zc-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }
.zc-stat { font-size: 11px; color: var(--ci-text-muted); }
.zc-stat strong { display: block; font-size: 14px; color: var(--ci-text); margin-top: 1px; }
.zc-stat strong small { font-size: 10px; font-weight: 500; color: var(--ci-text-muted); }
.zc-note { font-size: 11px; color: var(--ci-primary); font-weight: 500; padding-top: 4px; border-top: 1px solid var(--ci-surface-variant); }

/* ── 底部洞察：三列水平排列，压缩高度，独立滚动隔离 ── */
.insight-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; flex-shrink: 0; }
.insight-card { display: flex; flex-direction: column; min-height: 0; overflow: hidden; max-height: 140px; }
.ic-hd { display: flex; align-items: center; gap: 6px; padding: 8px 10px 4px; flex-shrink: 0; }
.ic-icon { font-size: 16px; flex-shrink: 0; }
.ic-title { font-size: 13px; font-weight: 700; color: var(--ci-primary); }
.ic-body { flex: 1; min-height: 0; overflow-y: auto; padding: 0 10px 8px; overscroll-behavior: contain; }
.ic-body::-webkit-scrollbar { display: none; }
.ic-body { scrollbar-width: none; }
.ic-text { font-size: 12px; color: var(--ci-text-muted); line-height: 1.65; white-space: pre-line; text-indent: 2em; }

@media (max-width: 900px) {
  .zones-top { grid-template-columns: 1fr; }
  .zones-cards { grid-template-columns: repeat(2, 1fr); }
  .insight-row { grid-template-columns: 1fr; }
  .zt-right > * { height: 300px; }
}
</style>
