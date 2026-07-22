<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="暂无气候带数据" @retry="load">
      <div class="zones-root">
        <h1 class="page-h1">{{ selectedYear }} 年气候带分布 · 三年对比</h1>
        <p class="page-sub">按气象站所属气候带统计，对比 2022/2023/2024 变化趋势</p>

        <!-- 主体：分组柱状图 + 层叠环形图 -->
        <div class="zones-main">
          <ChartPanel title="各气候带站点数对比" subtitle="2022 / 2023 / 2024 三年数据" style="flex:1;min-width:0">
            <v-chart :option="barOption" autoresize />
          </ChartPanel>
          <ChartPanel title="气候带占比变化" subtitle="内→外：2022 → 2024" style="flex:1;min-width:0">
            <v-chart v-if="pieHasData" :option="pieOption" autoresize />
            <el-empty v-else description="暂无数据" />
          </ChartPanel>
        </div>

        <!-- 底部：气候带详情卡片 -->
        <div class="zones-cards">
          <GlassCard v-for="z in zoneCards" :key="z.key" class="zone-card" :style="{ borderTop: '3px solid ' + z.color }">
            <div class="zc-hd">
              <span class="zc-dot" :style="{ background: z.color }"></span>
              <span class="zc-name">{{ z.name }}</span>
              <span :class="['zc-trend', z.trend > 0 ? 'up' : 'down']">{{ z.trend > 0 ? '↑' : z.trend < 0 ? '↓' : '→' }}</span>
            </div>
            <div class="zc-stats">
              <div class="zc-stat"><span>站点数</span><strong>{{ z.count }}</strong></div>
              <div class="zc-stat"><span>均温</span><strong>{{ z.avgTemp }}°C</strong></div>
              <div class="zc-stat"><span>降水</span><strong>{{ z.precip }}mm</strong></div>
              <div class="zc-stat"><span>极端天数</span><strong>{{ z.extreme }}</strong></div>
            </div>
          </GlassCard>
        </div>

        <!-- 洞察 -->
        <GlassCard class="zones-insight">
          <div class="insight-hd">🌍 气候带变化解读</div>
          <div class="insight-text">{{ insightText }}</div>
        </GlassCard>
      </div>
    </PageState>
  </div>
</template>

<script setup>
import { ref, reactive, inject, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'; import { CanvasRenderer } from 'echarts/renderers'; import { BarChart, PieChart } from 'echarts/charts'; import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, BarChart, PieChart, GridComponent, TooltipComponent, LegendComponent])
import { getZonesMultiYear, getZoneStats } from '../api'
import PageState from '../components/PageState.vue'; import GlassCard from '../components/GlassCard.vue'; import ChartPanel from '../components/ChartPanel.vue'
import { chartColors, zoneColors, zoneCN } from '../composables/useDashboardTheme'

const selectedYear = inject('selectedYear')
const loading = ref(true); const error = ref(''); const empty = ref(false); const pieHasData = ref(false)
let requestId = 0

const years = [2022, 2023, 2024]
const yearNames = { 2022: '2022', 2023: '2023', 2024: '2024' }
const yearColors = { 2022: '#3a674f', 2023: '#39656b', 2024: '#8b3713' }
const zoneKeys = ['tropical', 'temperate', 'arid', 'continental', 'polar']

const barOption = reactive({
  tooltip: { trigger: 'axis' },
  legend: { data: years.map(String), textStyle: { color: chartColors.text, fontSize: 13 }, top: 0 },
  grid: { left: '3%', right: '4%', top: '14%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: zoneKeys.map(k => zoneCN[k]), axisLabel: { color: chartColors.text, fontSize: 13 } },
  yAxis: { type: 'value', name: '站点数', axisLabel: { color: chartColors.text, fontSize: 12 }, splitLine: { lineStyle: { color: chartColors.grid } } },
  series: [],
})

const pieOption = reactive({
  tooltip: { trigger: 'item', formatter: '{b}: {c} 站 ({d}%)' },
  legend: { bottom: 0, textStyle: { color: chartColors.text, fontSize: 11 } },
  series: [],
})

const zoneCards = ref([])
const insightText = ref('')

function computeData(multiYearData, statsData) {
  // Group by year+zone
  const byYear = {}; years.forEach(y => { byYear[y] = {}; zoneKeys.forEach(k => { byYear[y][k] = 0 }) })
  multiYearData.forEach(r => { if (byYear[r.year]) byYear[r.year][r.climate_zone] = r.cnt || 0 })

  // Bar chart
  barOption.series = years.map(y => ({
    name: String(y), type: 'bar', barMaxWidth: 28,
    data: zoneKeys.map(k => byYear[y][k] || 0),
    itemStyle: { color: yearColors[y], borderRadius: [6, 6, 0, 0] },
  }))

  // Pie: 3 rings
  const pieColors = { 2022: chartColors.green, 2023: chartColors.secondary, 2024: chartColors.tertiary }
  pieHasData.value = multiYearData.length > 0
  pieOption.series = years.map((y, i) => ({
    type: 'pie',
    radius: [25 + i * 22 + '%', 45 + i * 22 + '%'],
    center: ['50%', '50%'],
    data: zoneKeys.filter(k => byYear[y][k] > 0).map(k => ({
      name: zoneCN[k], value: byYear[y][k], itemStyle: { color: zoneColors[k] }
    })),
    label: { show: false },
    emphasis: { label: { show: true, fontSize: 14 } },
  }))

  // Zone cards from stats
  const statsMap = {}; statsData.forEach(r => { statsMap[r.climate_zone] = r })
  const curYear = multiYearData.filter(r => r.year === 2024)
  const prevYear = multiYearData.filter(r => r.year === 2023)

  zoneCards.value = zoneKeys.map(k => {
    const cur = curYear.find(r => r.climate_zone === k) || { cnt: 0 }
    const prev = prevYear.find(r => r.climate_zone === k) || { cnt: 0 }
    const stats = statsMap[k] || {}
    const trend = cur.cnt - prev.cnt
    return {
      key: k, name: zoneCN[k], color: zoneColors[k],
      count: cur.cnt || 0, trend,
      avgTemp: stats.avg_temp ?? '--', precip: stats.avg_precip ?? '--', extreme: stats.extreme_days ?? '--'
    }
  })

  // Insight
  const sorted = [...zoneCards.value].sort((a, b) => b.trend - a.trend)
  const growing = sorted.filter(z => z.trend > 0)
  const shrinking = sorted.filter(z => z.trend < 0)
  insightText.value = `2023→2024年，${growing.length ? growing.map(z => z.name + '带(+' + z.trend + '站)').join('、') + ' 站点数增加。' : ''}${shrinking.length ? shrinking.map(z => z.name + '带(' + z.trend + '站)').join('、') + ' 站点数减少。' : ''}气候带分布总体保持稳定，温带和热带仍为最主要气候类型。`
}

async function load() {
  const id = ++requestId; loading.value = true; error.value = ''; empty.value = false
  try {
    const [multiRes, statsRes] = await Promise.all([
      getZonesMultiYear('2022,2023,2024'),
      getZoneStats(selectedYear.value),
    ])
    if (id !== requestId) return
    const multiData = multiRes.data?.data || []
    const statsData = statsRes.data?.data || []
    if (!multiData.length) { empty.value = true; loading.value = false; return }
    computeData(multiData, statsData)
  } catch (e) {
    if (id === requestId) { error.value = '数据加载失败'; console.error(e) }
  } finally { if (id === requestId) loading.value = false }
}
watch(selectedYear, load, { immediate: true })
</script>

<style scoped>
.zones-root { display: flex; flex-direction: column; flex: 1; min-height: 0; gap: 10px; }
.page-sub { color: var(--ci-text-muted); font-size: 15px; margin-bottom: 2px; flex-shrink: 0; }
.zones-main { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; flex: 5; min-height: 0; }
.zones-cards { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; flex-shrink: 0; }
.zone-card { padding: 12px; }
.zc-hd { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.zc-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.zc-name { font-size: 15px; font-weight: 600; color: var(--ci-text); flex: 1; }
.zc-trend { font-size: 16px; font-weight: 700; }
.zc-trend.up { color: var(--ci-tertiary); }
.zc-trend.down { color: var(--ci-secondary); }
.zc-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.zc-stat { font-size: 12px; color: var(--ci-text-muted); }
.zc-stat strong { display: block; font-size: 15px; color: var(--ci-text); margin-top: 1px; }
.zones-insight { padding: 12px 16px; flex-shrink: 0; }
.insight-hd { font-size: 16px; font-weight: 600; color: var(--ci-primary); margin-bottom: 6px; }
.insight-text { font-size: 14px; color: var(--ci-text-muted); line-height: 1.6; }
@media (max-width: 900px) {
  .zones-main { grid-template-columns: 1fr; }
  .zones-cards { grid-template-columns: repeat(2, 1fr); }
}
</style>
