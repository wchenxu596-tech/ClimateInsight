<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="暂无月度数据" @retry="load">
      <div class="trend-root">
        <!-- 顶部 KPI 对比卡片 -->
        <div class="kpi-row">
          <GlassCard v-for="k in kpiCards" :key="k.label" class="kpi-card">
            <div class="kpi-label">{{ k.label }}</div>
            <div class="kpi-years">
              <span v-for="y in years" :key="y" class="kpi-yr" :style="{ color: yearColors[y] }">
                {{ y }}: <strong>{{ k.values[y] ?? '--' }}</strong>
              </span>
            </div>
            <div class="kpi-trend" v-if="k.trend">
              <span :style="{ color: k.trend > 0 ? 'var(--ci-tertiary)' : k.trend < 0 ? 'var(--ci-secondary)' : '' }">
                {{ k.trend > 0 ? '📈' : k.trend < 0 ? '📉' : '➡️' }} {{ k.trendText }}
              </span>
            </div>
          </GlassCard>
        </div>

        <!-- 主图：多年叠加折线 -->
        <div class="charts-main">
          <ChartPanel :title="'多年月度气温对比'" :subtitle="'2022 / 2023 / 2024 年月均温'" style="flex:1;min-width:0">
            <v-chart :option="lineOption" autoresize />
          </ChartPanel>

          <!-- 洞察面板 -->
          <GlassCard class="insight-panel">
            <div class="insight-hd">📊 数据洞察</div>
            <div class="insight-body">
              <div class="insight-item">
                <span class="insight-icon">{{ warmingTrend ? '🌡️' : '❄️' }}</span>
                <div>
                  <div class="insight-title">温度趋势</div>
                  <div class="insight-text">{{ trendSummary }}</div>
                </div>
              </div>
              <div class="insight-item">
                <span class="insight-icon">📈</span>
                <div>
                  <div class="insight-title">关键发现</div>
                  <div class="insight-text">{{ keyFinding }}</div>
                </div>
              </div>
              <div class="insight-item">
                <span class="insight-icon">💡</span>
                <div>
                  <div class="insight-title">建议措施</div>
                  <div class="insight-text">{{ suggestion }}</div>
                </div>
              </div>
            </div>
          </GlassCard>
        </div>

        <!-- 底部：月度异常热力图 -->
        <ChartPanel title="月度温度距平" subtitle="各月相对三年均值的偏差（红=偏暖，蓝=偏冷）" class="chart-bottom">
          <v-chart :option="anomalyOption" autoresize />
        </ChartPanel>
      </div>
    </PageState>
  </div>
</template>

<script setup>
import { ref, reactive, inject, watch, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'; import { CanvasRenderer } from 'echarts/renderers'; import { LineChart, BarChart } from 'echarts/charts'; import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent])
import { getTrendMultiYear } from '../api'
import PageState from '../components/PageState.vue'; import GlassCard from '../components/GlassCard.vue'; import ChartPanel from '../components/ChartPanel.vue'
import { chartColors, monthLabels } from '../composables/useDashboardTheme'

const selectedYear = inject('selectedYear')
const loading = ref(true); const error = ref(''); const empty = ref(false)
let requestId = 0

const years = [2022, 2023, 2024]
const yearColors = { 2022: '#3a674f', 2023: '#39656b', 2024: '#8b3713' }
const yearNames = { 2022: '2022', 2023: '2023', 2024: '2024' }

const kpiCards = ref([
  { label: '全球年均温 (°C)', values: {}, trend: null, trendText: '' },
  { label: '最高月均温 (°C)', values: {}, trend: null, trendText: '' },
  { label: '最低月均温 (°C)', values: {}, trend: null, trendText: '' },
  { label: '年温度振幅 (°C)', values: {}, trend: null, trendText: '' },
])

const lineOption = reactive({
  tooltip: { trigger: 'axis' },
  legend: { data: years.map(String), textStyle: { color: chartColors.text, fontSize: 13 }, top: 0 },
  grid: { left: '3%', right: '4%', top: '14%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: monthLabels, axisLabel: { color: chartColors.text, fontSize: 12 }, axisLine: { lineStyle: { color: chartColors.outline } } },
  yAxis: { type: 'value', name: '°C', axisLabel: { color: chartColors.text, fontSize: 12 }, splitLine: { lineStyle: { color: chartColors.grid } } },
  series: [],
})

const anomalyOption = reactive({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', top: '8%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: monthLabels, axisLabel: { color: chartColors.text, fontSize: 12 } },
  yAxis: { type: 'value', name: '°C', axisLabel: { color: chartColors.text, fontSize: 11 }, splitLine: { lineStyle: { color: chartColors.grid } } },
  visualMap: { min: -3, max: 3, calculable: true, orient: 'horizontal', left: 'center', bottom: 0,
    inRange: { color: ['#39656b', '#e3e2e0', '#8b3713'] } },
  series: [{ type: 'bar', data: [], barMaxWidth: 32, itemStyle: { borderRadius: [4, 4, 0, 0] } }],
})

const warmingTrend = ref(false)
const trendSummary = ref('')
const keyFinding = ref('')
const suggestion = ref('')

const allData = ref([])

function safeNumber(v) {
  if (v == null || v === '') return null
  const n = Number(v)
  return isNaN(n) || !isFinite(n) || n === 9999.9 ? null : n
}

function computeInsights() {
  const monthData = {}
  years.forEach(y => { monthData[y] = Array(12).fill(null) })

  allData.value.forEach(r => {
    const t = safeNumber(r.avg_temp)
    if (t != null && monthData[r.year]) monthData[r.year][r.month - 1] = t
  })

  // KPI cards
  years.forEach(y => {
    const vals = monthData[y].filter(v => v != null)
    if (!vals.length) return
    const avg = vals.reduce((a, b) => a + b, 0) / vals.length
    const mx = Math.max(...vals)
    const mn = Math.min(...vals)
    kpiCards.value[0].values[y] = avg.toFixed(1)
    kpiCards.value[1].values[y] = mx.toFixed(1)
    kpiCards.value[2].values[y] = mn.toFixed(1)
    kpiCards.value[3].values[y] = (mx - mn).toFixed(1)
  })

  // Trends (2022 → 2024)
  const a22 = parseFloat(kpiCards.value[0].values[2022])
  const a24 = parseFloat(kpiCards.value[0].values[2024])
  if (!isNaN(a22) && !isNaN(a24)) {
    const d = a24 - a22
    kpiCards.value[0].trend = d
    kpiCards.value[0].trendText = d > 0 ? `+${d.toFixed(2)}°C 变暖` : d < 0 ? `${d.toFixed(2)}°C 变冷` : '持平'
    warmingTrend.value = d > 0
    trendSummary.value = `2022-2024年全球年均温${d > 0 ? '上升' : '下降'}了 ${Math.abs(d).toFixed(2)}°C，${d > 0 ? '呈现变暖趋势' : '呈现变冷趋势'}。`
  }

  // Key finding
  const allVals = [].concat(...Object.values(monthData).map(a => a.filter(v => v != null)))
  const hottestMonth = monthLabels.reduce((best, m, i) => {
    const t2024 = monthData[2024][i]
    return t2024 != null && t2024 > (best.val || -Infinity) ? { month: m, val: t2024 } : best
  }, { month: '', val: -Infinity })

  keyFinding.value = `2024年最热月份为${hottestMonth.month}（${hottestMonth.val?.toFixed(1)}°C）。三年数据中，${warmingTrend.value ? '2024年为最暖年份' : '温度变化波动较大'}。`

  suggestion.value = warmingTrend.value
    ? '建议关注全球变暖趋势，减少碳排放，推广可再生能源，加强极端高温预警机制。'
    : '建议持续监测温度变化，关注季节性极端天气事件，做好防灾减灾预案。'

  // Line chart
  lineOption.series = years.map(y => ({
    name: String(y), type: 'line', data: monthData[y], smooth: true, symbolSize: 5,
    itemStyle: { color: yearColors[y] },
    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
      colorStops: [{ offset: 0, color: yearColors[y] + '20' }, { offset: 1, color: yearColors[y] + '00' }] } }
  }))

  // Anomaly chart: 2024 vs 3-year mean
  const mean3y = Array(12).fill(null)
  for (let i = 0; i < 12; i++) {
    const vals = years.map(y => monthData[y][i]).filter(v => v != null)
    mean3y[i] = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null
  }
  anomalyOption.series[0].data = monthData[2024].map((v, i) =>
    v != null && mean3y[i] != null ? +(v - mean3y[i]).toFixed(2) : 0
  )
}

async function load() {
  const id = ++requestId; loading.value = true; error.value = ''; empty.value = false
  try {
    const res = await getTrendMultiYear('2022,2023,2024')
    if (id !== requestId) return
    const data = res.data?.data || []
    if (!data.length) { empty.value = true; loading.value = false; return }
    allData.value = data
    computeInsights()
  } catch (e) {
    if (id === requestId) { error.value = '数据加载失败'; console.error(e) }
  } finally { if (id === requestId) loading.value = false }
}
watch(selectedYear, () => {}, { immediate: true })
load()
</script>

<style scoped>
.trend-root { display: flex; flex-direction: column; flex: 1; min-height: 0; gap: 10px; }
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; flex-shrink: 0; }
.kpi-card { padding: 12px 16px; }
.kpi-label { font-size: 14px; font-weight: 500; color: var(--ci-text-muted); margin-bottom: 6px; }
.kpi-years { display: flex; flex-direction: column; gap: 2px; margin-bottom: 4px; }
.kpi-yr { font-size: 13px; }
.kpi-yr strong { font-weight: 700; }
.kpi-trend { font-size: 13px; font-weight: 600; }
.charts-main { display: grid; grid-template-columns: minmax(0, 7fr) 260px; gap: 12px; flex: 4; min-height: 0; }
.insight-panel { padding: 14px; display: flex; flex-direction: column; overflow-y: auto; }
.insight-hd { font-size: 16px; font-weight: 600; color: var(--ci-primary); margin-bottom: 12px; flex-shrink: 0; }
.insight-body { display: flex; flex-direction: column; gap: 12px; }
.insight-item { display: flex; gap: 10px; }
.insight-icon { font-size: 22px; flex-shrink: 0; line-height: 1.2; }
.insight-title { font-size: 14px; font-weight: 600; color: var(--ci-text); }
.insight-text { font-size: 13px; color: var(--ci-text-muted); margin-top: 2px; line-height: 1.5; }
.chart-bottom { flex: 3; min-height: 0; }
@media (max-width: 900px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .charts-main { grid-template-columns: 1fr; }
}
</style>
