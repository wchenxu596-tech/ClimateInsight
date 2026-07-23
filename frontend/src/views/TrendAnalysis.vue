<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="暂无月度数据" @retry="load">
      <div class="trend-root">
        <!-- 标题区 -->
        <div class="trend-hd">
          <h1 class="page-h1">全球温度趋势分析</h1>
          <p class="page-sub">{{ firstYearLabel }}–{{ selectedYear }} {{ yearCountText }}数据对比 · 多维度温度演变与气候洞察</p>
        </div>

        <!-- KPI 演变卡片（压缩高度） -->
        <div class="kpi-row">
          <GlassCard v-for="k in kpiCards" :key="k.label" class="kpi-card">
            <div class="kpi-top">
              <span class="kpi-label">{{ k.label }}</span>
              <span v-if="k.changeRatio != null" :class="['kpi-badge', k.changeRatio > 0 ? 'up' : 'down']">
                {{ k.changeRatio > 0 ? '↑' : '↓' }} {{ Math.abs(k.changeRatio).toFixed(1) }}%
              </span>
            </div>
            <div class="kpi-val">{{ k.latest }}<span class="kpi-unit">{{ k.unit }}</span></div>
            <div class="kpi-range">{{ k.min }} – {{ k.max }} {{ k.unit }}</div>
          </GlassCard>
        </div>

        <!-- 下方主体：左80%图表 2×2 + 右20%文本面板 -->
        <div class="main-body">
          <!-- 左侧 2×2 图表网格 -->
          <div class="charts-grid">
            <ChartPanel title="多月气温对比" :subtitle="activeYears.map(String).join(' / ') + ' 年月均温走势'">
              <v-chart :option="lineOption" autoresize />
            </ChartPanel>
            <ChartPanel title="四季温度分布" subtitle="春夏秋冬各季节均温年度对比">
              <v-chart :option="seasonOption" autoresize />
            </ChartPanel>
            <ChartPanel title="逐年温度变化量" subtitle="各年全球均温较上一年变化幅度（°C）">
              <v-chart :option="yoyOption" autoresize />
            </ChartPanel>
            <ChartPanel title="月度温度距平" :subtitle="'各月相对' + yearCountText + '均值的偏差（红=偏暖 · 蓝=偏冷）'">
              <v-chart :option="anomalyOption" autoresize />
            </ChartPanel>
          </div>

          <!-- 右侧文本面板（2:1:1:1 高度比，各卡片独立滚动） -->
          <div class="text-panel">
            <GlassCard class="text-card tc-main">
              <div class="tc-hd">
                <span class="tc-icon">📊</span>
                <span class="tc-title">数据洞察</span>
              </div>
              <div class="tc-body"><div class="tc-text">{{ insightText }}</div></div>
            </GlassCard>
            <GlassCard class="text-card tc-sub">
              <div class="tc-hd">
                <span class="tc-icon">📅</span>
                <span class="tc-title">阶段对比</span>
              </div>
              <div class="tc-body"><div class="tc-text">{{ decadeSummary }}</div></div>
            </GlassCard>
            <GlassCard class="text-card tc-sub">
              <div class="tc-hd">
                <span class="tc-icon">🌡️</span>
                <span class="tc-title">季节趋势</span>
              </div>
              <div class="tc-body"><div class="tc-text">{{ seasonSummary }}</div></div>
            </GlassCard>
            <GlassCard class="text-card tc-sub">
              <div class="tc-hd">
                <span class="tc-icon">💡</span>
                <span class="tc-title">建议与展望</span>
              </div>
              <div class="tc-body"><div class="tc-text">{{ recommendation }}</div></div>
            </GlassCard>
          </div>
        </div>
      </div>
    </PageState>
  </div>
</template>

<script setup>
import { ref, reactive, inject, watch, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, VisualMapComponent } from 'echarts/components'
use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, VisualMapComponent])
import { getTrendMultiYear, getTrendKpiHistory } from '../api'
import PageState from '../components/PageState.vue'
import GlassCard from '../components/GlassCard.vue'
import ChartPanel from '../components/ChartPanel.vue'
import { chartColors, monthLabels } from '../composables/useDashboardTheme'

const selectedYear = inject('selectedYear')

const ALL_YEARS = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
const YEAR_PALETTE = ['#3a674f', '#39656b', '#8b3713', '#c78b3c', '#009f7f', '#5da9b4', '#e08050', '#7a8b9a', '#bceecf', '#bae8ef', '#ffdbce']
const yearColors = Object.fromEntries(ALL_YEARS.map((y, i) => [y, YEAR_PALETTE[i]]))

const activeYears = computed(() => {
  const eligible = ALL_YEARS.filter(y => y <= selectedYear.value)
  return eligible.slice(-5)  // 最多 5 年滑动窗口
})
const firstYearLabel = computed(() => activeYears.value[0] || selectedYear.value)
const yearCountText = computed(() => {
  const n = activeYears.value.length
  const map = { 1: '一年', 2: '两年', 3: '三年', 4: '四年', 5: '五年' }
  return map[n] || n + '年'
})

const seasons = [
  { key: 'spring', name: '春季(3-5月)', months: [3, 4, 5] },
  { key: 'summer', name: '夏季(6-8月)', months: [6, 7, 8] },
  { key: 'autumn', name: '秋季(9-11月)', months: [9, 10, 11] },
  { key: 'winter', name: '冬季(12,1-2月)', months: [12, 1, 2] },
]

const loading = ref(true); const error = ref(''); const empty = ref(false)
let requestId = 0

const kpiCards = ref([
  { label: '全球年均温', latest: '--', unit: '°C', min: '--', max: '--', changeRatio: null },
  { label: '最高月均温', latest: '--', unit: '°C', min: '--', max: '--', changeRatio: null },
  { label: '极端事件占比', latest: '--', unit: '%', min: '--', max: '--', changeRatio: null },
  { label: '年温度振幅', latest: '--', unit: '°C', min: '--', max: '--', changeRatio: null },
])

const insightText = ref('')
const decadeSummary = ref('')
const seasonSummary = ref('')
const recommendation = ref('')

const lineOption = reactive({
  tooltip: { trigger: 'axis', valueFormatter: (v) => typeof v === 'number' ? v.toFixed(1) + '°C' : v },
  legend: { data: [], textStyle: { color: chartColors.text, fontSize: 11 }, top: 0, type: 'scroll' },
  grid: { left: '3%', right: '4%', top: '15%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: monthLabels, axisLabel: { color: chartColors.text, fontSize: 11 }, axisLine: { lineStyle: { color: chartColors.outline } } },
  yAxis: { type: 'value', name: '°C', axisLabel: { color: chartColors.text, fontSize: 11 }, splitLine: { lineStyle: { color: chartColors.grid } }, min: 'dataMin', max: 'dataMax' },
  series: [],
})

const yoyOption = reactive({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (v) => typeof v === 'number' ? (v > 0 ? '+' : '') + v.toFixed(2) + '°C' : v },
  grid: { left: '3%', right: '4%', top: '8%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: [], axisLabel: { color: chartColors.text, fontSize: 11 } },
  yAxis: { type: 'value', name: 'Δ°C', axisLabel: { color: chartColors.text, fontSize: 10 }, splitLine: { lineStyle: { color: chartColors.grid } } },
  series: [{ type: 'bar', data: [], barMaxWidth: 32, itemStyle: { borderRadius: [4, 4, 0, 0] },
    label: { show: true, position: 'outside', fontSize: 10, formatter: (p) => (p.value > 0 ? '+' : '') + (p.value?.toFixed(2) ?? '') } }],
})

const seasonOption = reactive({
  tooltip: { trigger: 'axis', valueFormatter: (v) => typeof v === 'number' ? v.toFixed(1) + '°C' : v },
  legend: { data: seasons.map(s => s.name), textStyle: { color: chartColors.text, fontSize: 10 }, top: 0 },
  grid: { left: '3%', right: '4%', top: '14%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: [], axisLabel: { color: chartColors.text, fontSize: 11 } },
  yAxis: { type: 'value', name: '°C', axisLabel: { color: chartColors.text, fontSize: 10 }, splitLine: { lineStyle: { color: chartColors.grid } } },
  series: [],
})

const anomalyOption = reactive({
  tooltip: { trigger: 'item', valueFormatter: (v) => typeof v === 'number' ? (v > 0 ? '+' : '') + v.toFixed(2) + '°C' : v },
  grid: { left: '3%', right: '4%', top: '8%', bottom: '12%', containLabel: true },
  xAxis: { type: 'category', data: monthLabels, axisLabel: { color: chartColors.text, fontSize: 11 } },
  yAxis: { type: 'category', data: [], axisLabel: { color: chartColors.text, fontSize: 11 } },
  visualMap: { min: -3, max: 3, calculable: true, orient: 'horizontal', left: 'center', bottom: 0,
    inRange: { color: ['#39656b', '#7ba5b8', '#e3e2e0', '#e0a090', '#8b3713'] }, text: ['偏暖', '偏冷'], textStyle: { color: chartColors.text, fontSize: 10 } },
  series: [{ type: 'bar', data: [], barMaxWidth: 24, itemStyle: { borderRadius: [2, 2, 0, 0] } }],
})

function safeNumber(v) {
  if (v == null || v === '') return null
  const n = Number(v)
  return isNaN(n) || !isFinite(n) || n === 9999.9 ? null : n
}

function avg(arr) {
  const valid = arr.filter(v => v != null)
  return valid.length ? valid.reduce((a, b) => a + b, 0) / valid.length : null
}

function computeAll(trendData, kpiData, years) {
  // ── 月度数据按年组织 ──
  const monthByYear = {}
  years.forEach(y => { monthByYear[y] = Array(12).fill(null) })
  trendData.forEach(r => {
    const t = safeNumber(r.avg_temp)
    if (t != null && monthByYear[r.year]) monthByYear[r.year][r.month - 1] = t
  })

  // ── 年度统计 ──
  const yearlyAvg = {}; const yearlyMax = {}; const yearlyMin = {}
  years.forEach(y => {
    yearlyAvg[y] = avg(monthByYear[y])
    const validM = monthByYear[y].filter(v => v != null)
    yearlyMax[y] = validM.length ? Math.max(...validM) : null
    yearlyMin[y] = validM.length ? Math.min(...validM) : null
  })
  const validAvgs = Object.values(yearlyAvg).filter(v => v != null)
  const globalMin = Math.min(...validAvgs)
  const globalMax = Math.max(...validAvgs)

  // ── KPI 数据 ──
  const kpiMap = {}
  kpiData.forEach(r => {
    if (!kpiMap[r.kpi_name]) kpiMap[r.kpi_name] = {}
    kpiMap[r.kpi_name][r.year] = safeNumber(r.kpi_value)
  })

  const latestYear = selectedYear.value
  const firstYear = years[0]
  const spanYears = latestYear - firstYear

  // ── KPI 卡片 ──
  const aFirst = yearlyAvg[firstYear]; const aLast = yearlyAvg[latestYear]
  const aChange = aFirst != null && aLast != null ? aLast - aFirst : null
  const aPct = aFirst != null && aChange != null ? (aChange / Math.abs(aFirst)) * 100 : null
  kpiCards.value[0] = {
    label: '全球年均温', latest: yearlyAvg[latestYear]?.toFixed(1) ?? '--', unit: '°C',
    min: globalMin.toFixed(1), max: globalMax.toFixed(1), changeRatio: aPct,
  }
  const maxTemps = years.map(y => yearlyMax[y]).filter(v => v != null && isFinite(v))
  const mxLatest = yearlyMax[latestYear]; const mxFirst = yearlyMax[firstYear]
  const mxChange = mxFirst != null && mxLatest != null ? mxLatest - mxFirst : null
  kpiCards.value[1] = {
    label: '最高月均温', latest: mxLatest?.toFixed(1) ?? '--', unit: '°C',
    min: Math.min(...maxTemps).toFixed(1), max: Math.max(...maxTemps).toFixed(1),
    changeRatio: mxFirst && mxChange ? (mxChange / Math.abs(mxFirst)) * 100 : null,
  }
  const extremeMap = kpiMap['extreme_event_pct'] || {}
  const extVals = years.map(y => extremeMap[y]).filter(v => v != null)
  const extLatest = extremeMap[latestYear]; const extFirst = extremeMap[firstYear]
  const extChange = extFirst != null && extLatest != null ? extLatest - extFirst : null
  kpiCards.value[2] = {
    label: '极端事件占比', latest: extLatest?.toFixed(2) ?? '--', unit: '%',
    min: Math.min(...extVals).toFixed(2), max: Math.max(...extVals).toFixed(2),
    changeRatio: extFirst && extChange ? (extChange / Math.abs(extFirst)) * 100 : null,
  }
  const amps = years.map(y => {
    const mx = yearlyMax[y]; const mn = yearlyMin[y]
    return mx != null && mn != null && isFinite(mx) && isFinite(mn) ? mx - mn : null
  }).filter(v => v != null)
  const ampLatest = amps[amps.length - 1]; const ampFirst = amps[0]
  const ampChange = ampFirst != null && ampLatest != null ? ampLatest - ampFirst : null
  kpiCards.value[3] = {
    label: '年温度振幅', latest: ampLatest?.toFixed(1) ?? '--', unit: '°C',
    min: Math.min(...amps).toFixed(1), max: Math.max(...amps).toFixed(1),
    changeRatio: ampFirst && ampChange ? (ampChange / Math.abs(ampFirst)) * 100 : null,
  }

  // ── 数据洞察（合并为一段文字） ──
  const avgTempEntries = Object.entries(yearlyAvg).filter(([, v]) => v != null).sort((a, b) => a[0] - b[0])
  const warmestYear = avgTempEntries.reduce((a, b) => a[1] > b[1] ? a : b, [0, -Infinity])
  const coldestYear = avgTempEntries.reduce((a, b) => a[1] < b[1] ? a : b, [0, Infinity])
  const ratePerDecade = aChange != null && spanYears > 0 ? (aChange / spanYears) * 10 : null
  const mid = Math.floor(years.length / 2)
  const earlySlice = years.slice(0, mid); const lateSlice = years.slice(mid)
  const earlyAvg = avg(earlySlice.map(y => yearlyAvg[y]))
  const lateAvg = avg(lateSlice.map(y => yearlyAvg[y]))
  const halfDiff = earlyAvg != null && lateAvg != null ? lateAvg - earlyAvg : null

  const hottestMonth = { year: 0, month: '', val: -Infinity }
  years.forEach(y => {
    monthByYear[y].forEach((v, i) => {
      if (v != null && v > hottestMonth.val) hottestMonth.val = v, hottestMonth.year = y, hottestMonth.month = monthLabels[i]
    })
  })
  const hottestStationKpi = kpiMap['hottest_station_temp'] || {}
  const hstationVals = years.map(y => hottestStationKpi[y]).filter(v => v != null)
  const hstationMax = hstationVals.length ? Math.max(...hstationVals) : null

  const yoyDeltas = []
  for (let i = 1; i < years.length; i++) {
    const prev = yearlyAvg[years[i - 1]]; const cur = yearlyAvg[years[i]]
    if (prev != null && cur != null) yoyDeltas.push({ from: years[i - 1], to: years[i], delta: cur - prev })
  }
  const maxRise = yoyDeltas.length ? yoyDeltas.reduce((a, b) => b.delta > a.delta ? b : a, { delta: -Infinity }) : null
  const maxDrop = yoyDeltas.length ? yoyDeltas.reduce((a, b) => b.delta < a.delta ? b : a, { delta: Infinity }) : null
  const hasWarming = aChange > 0.3

  // 综合洞察文本（分段）
  const p1 = `${firstYear}–${latestYear}年，全球均温呈${aChange > 0 ? '显著上升' : '波动变化'}趋势：从 ${aFirst?.toFixed(1)}°C 升至 ${aLast?.toFixed(1)}°C，累计${aChange > 0 ? '升温' : '变化'} ${Math.abs(aChange).toFixed(2)}°C。`
  const p2 = ratePerDecade != null
    ? `变暖速率约 ${ratePerDecade.toFixed(2)}°C/十年，${halfDiff > 0 ? '后半段较前半段升温加速（+' + halfDiff.toFixed(2) + '°C），气候系统正在经历快速变化。' : '变暖速率相对稳定。'}`
    : ''
  const p3 = `最暖年份为${warmestYear[0]}年（${warmestYear[1].toFixed(1)}°C），最冷为${coldestYear[0]}年（${coldestYear[1].toFixed(1)}°C）。该时段最热月份出现在${hottestMonth.year}年${hottestMonth.month}（${hottestMonth.val.toFixed(1)}°C），全球最热单站温度达 ${hstationMax?.toFixed(1)}°C。`
  const p4 = yoyDeltas.length
    ? `年际变化方面，最大升幅在${maxRise.from}→${maxRise.to}年（+${maxRise.delta.toFixed(2)}°C），最大降幅在${maxDrop.from}→${maxDrop.to}年（${maxDrop.delta.toFixed(2)}°C）。极端事件占比在 ${extVals.length ? Math.min(...extVals).toFixed(1) : '--'}%–${extVals.length ? Math.max(...extVals).toFixed(1) : '--'}% 之间波动。`
    : `极端事件占比在 ${extVals.length ? Math.min(...extVals).toFixed(1) : '--'}%–${extVals.length ? Math.max(...extVals).toFixed(1) : '--'}% 之间波动。`
  const p5 = hasWarming
    ? `总体来看，该时段升温幅度远超同期自然变率范围，极端高温事件频率和强度均呈上升趋势，对农业生产、水资源管理和人类健康构成严峻挑战。`
    : `温度变化在自然变率范围内波动，但极端事件占比变化值得持续关注。`
  const p6 = latestYear === 2025 ? '注意：2025年数据尚不完整，仅供参考。' : ''
  insightText.value = [p1, p2, p3, p4, p5, p6].filter(Boolean).join('\n')

  // ── 阶段对比 ──
  if (years.length >= 4) {
    const midPt = Math.floor(years.length / 2)
    const eSlice = years.slice(0, midPt); const lSlice = years.slice(midPt)
    const eAvg = avg(eSlice.map(y => yearlyAvg[y]))
    const lAvg = avg(lSlice.map(y => yearlyAvg[y]))
    const dAvg = eAvg != null && lAvg != null ? lAvg - eAvg : null
    decadeSummary.value = `将${yearCountText.value}数据分为前后两段进行对比：${eSlice[0]}–${eSlice[eSlice.length - 1]}年均温 ${eAvg?.toFixed(2)}°C，${lSlice[0]}–${lSlice[lSlice.length - 1]}年均温 ${lAvg?.toFixed(2)}°C，后半段升高 ${Math.abs(dAvg).toFixed(2)}°C。极端事件占比从 ${extFirst?.toFixed(2)}% ${extChange > 0 ? '上升' : '下降'}至 ${extLatest?.toFixed(2)}%。${dAvg > 0.3 ? '后半段明显偏暖，表明变暖节奏加快。' : ''}`
  } else {
    decadeSummary.value = `当前仅有${yearCountText.value}数据（${years.map(String).join('、')}），数据量不足以进行前后阶段对比分析。随着数据积累，阶段对比将更加有参考价值。`
  }

  // ── 季节趋势 ──
  const seasonTrends = seasons.map(s => {
    const earlyS = earlySlice.map(y => {
      const svals = s.months.map(m => monthByYear[y]?.[m - 1]).filter(v => v != null)
      return svals.length ? svals.reduce((a, b) => a + b, 0) / svals.length : null
    })
    const lateS = lateSlice.map(y => {
      const svals = s.months.map(m => monthByYear[y]?.[m - 1]).filter(v => v != null)
      return svals.length ? svals.reduce((a, b) => a + b, 0) / svals.length : null
    })
    const eAvg = avg(earlyS); const lAvg = avg(lateS)
    return { name: s.name.replace(/\(.+\)/, ''), diff: eAvg != null && lAvg != null ? lAvg - eAvg : null }
  })
  const fastestSeason = [...seasonTrends].filter(s => s.diff != null).sort((a, b) => Math.abs(b.diff) - Math.abs(a.diff))[0]
  seasonSummary.value = years.length >= 4
    ? `四季温度变化如下：${seasonTrends.map(s => s.name + (s.diff > 0 ? '升温' : '降温') + Math.abs(s.diff).toFixed(1) + '°C').join('，')}。其中${fastestSeason ? fastestSeason.name + '变化最为显著（' + (fastestSeason.diff > 0 ? '+' : '') + fastestSeason.diff.toFixed(1) + '°C）' : ''}。${fastestSeason?.name === '冬季' ? '冬季变暖可能导致降雪减少、冰川退缩，影响水资源季节性补给。' : fastestSeason?.name === '夏季' ? '夏季升温加剧热浪和干旱风险，对农业灌溉和能源供应形成压力。' : '季节温度变化正在重塑生态系统节律，动植物物候期可能发生偏移。'}`
    : `数据量不足以进行季节趋势分析，需积累更多年份数据。`

  // ── 建议与展望 ──
  recommendation.value = hasWarming
    ? `基于${yearCountText.value}数据分析，全球气候系统正经历显著变暖，亟需采取适应性措施。\n① 强化极端高温预警和城市热岛效应缓解措施，保护脆弱人群。\n② 农业部门调整种植结构和播种时间以适应温度变化。\n③ 加强水资源管理和干旱监测体系，防范水资源短缺风险。\n④ 推进可再生能源替代，减少温室气体排放。\n⑤ 建立跨区域气候适应协同机制，共享数据和应对经验。`
    : `基于现有数据分析，提出以下建议：\n① 持续监测全球温度变化趋势，补充更长时间序列数据，提高分析可靠性。\n② 关注极端天气事件的季节分布变化，提前做好防灾减灾准备。\n③ 完善气象站网络覆盖，减少数据盲区，提升全球监测能力。\n④ 建立气候异常早期预警机制，降低极端气候事件损失。`

  // ── 图表更新 ──
  lineOption.legend.data = years.map(String)
  lineOption.series = years.map(y => ({
    name: String(y), type: 'line', data: monthByYear[y], smooth: true, symbolSize: 3,
    lineStyle: { width: y === latestYear ? 2.5 : 1.2 },
    itemStyle: { color: yearColors[y] },
    emphasis: { focus: 'series', lineStyle: { width: 4 } },
  }))

  yoyOption.xAxis.data = yoyDeltas.map(d => d.from + '→' + d.to)
  yoyOption.series[0].data = yoyDeltas.map(d => ({
    value: +d.delta.toFixed(2),
    itemStyle: { color: d.delta > 0 ? '#8b3713' : '#39656b' },
  }))

  const seasonColors = ['#3a674f', '#8b3713', '#c78b3c', '#39656b']
  seasonOption.xAxis.data = years.map(String)
  seasonOption.series = seasons.map((s, si) => ({
    name: s.name, type: 'bar', barMaxWidth: 18, barGap: '10%',
    data: years.map(y => {
      const svals = s.months.map(m => monthByYear[y]?.[m - 1]).filter(v => v != null)
      return svals.length ? +(svals.reduce((a, b) => a + b, 0) / svals.length).toFixed(1) : null
    }),
    itemStyle: { color: seasonColors[si], borderRadius: [4, 4, 0, 0] },
  }))

  const monthlyMean = Array(12).fill(null)
  for (let m = 0; m < 12; m++) {
    const vals = years.map(y => monthByYear[y]?.[m]).filter(v => v != null)
    monthlyMean[m] = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null
  }
  const heatData = []
  years.forEach(y => {
    for (let m = 0; m < 12; m++) {
      const v = monthByYear[y]?.[m]; const mean = monthlyMean[m]
      heatData.push([m, years.indexOf(y), v != null && mean != null ? +(v - mean).toFixed(2) : null])
    }
  })
  anomalyOption.yAxis.data = years.map(String)
  anomalyOption.series[0].data = heatData
  const allAnom = heatData.filter(d => d[2] != null).map(d => d[2])
  if (allAnom.length) {
    const aMax = Math.max(...allAnom.map(Math.abs))
    anomalyOption.visualMap.min = -Math.max(2, Math.ceil(aMax))
    anomalyOption.visualMap.max = Math.max(2, Math.ceil(aMax))
  }
}

async function load() {
  const id = ++requestId; loading.value = true; error.value = ''; empty.value = false
  const years = activeYears.value
  if (!years.length) { empty.value = true; loading.value = false; return }
  try {
    const [trendRes, kpiRes] = await Promise.all([
      getTrendMultiYear(years.join(',')),
      getTrendKpiHistory(years.join(',')),
    ])
    if (id !== requestId) return
    const trendData = trendRes.data?.data || []
    const kpiData = kpiRes.data?.data || []
    if (!trendData.length) { empty.value = true; loading.value = false; return }
    computeAll(trendData, kpiData, years)
  } catch (e) {
    if (id === requestId) { error.value = '数据加载失败'; console.error(e) }
  } finally { if (id === requestId) loading.value = false }
}

watch(selectedYear, load, { immediate: true })
</script>

<style scoped>
.trend-root { display: flex; flex-direction: column; flex: 1; min-width: 0; min-height: 0; gap: 8px; }
.trend-hd { flex-shrink: 0; }
.page-sub { color: var(--ci-text-muted); font-size: 13px; margin-top: 1px; }

/* ── KPI 卡片（压缩） ── */
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; flex-shrink: 0; }
.kpi-row > * { min-width: 0; overflow: hidden; }
.kpi-card { padding: 8px 12px; display: flex; flex-direction: column; gap: 2px; }
.kpi-card::before { content: ''; position: absolute; top: 0; left: 12px; right: 12px; height: 2px; border-radius: 0 0 2px 2px; background: linear-gradient(90deg, var(--ci-primary-soft), var(--ci-secondary-soft), var(--ci-tertiary-soft)); opacity: 0; transition: opacity .4s var(--ci-ease-out); }
.kpi-card:hover::before { opacity: 1; }
.kpi-top { display: flex; justify-content: space-between; align-items: center; }
.kpi-label { font-size: 13px; font-weight: 500; color: var(--ci-text-muted); }
.kpi-badge { font-size: 11px; font-weight: 700; padding: 1px 7px; border-radius: 8px; line-height: 1.4; transition: transform .3s var(--ci-ease-spring); }
.kpi-badge.up { color: #8b3713; background: #ffdbce; }
.kpi-badge.down { color: #39656b; background: #bae8ef; }
.kpi-card:hover .kpi-badge { transform: scale(1.08); }
.kpi-val { font-size: 26px; font-weight: 700; color: var(--ci-text); line-height: 1.15; transition: transform .3s var(--ci-ease-spring); }
.kpi-card:hover .kpi-val { transform: scale(1.03); }
.kpi-unit { font-size: 14px; font-weight: 500; color: var(--ci-text-muted); margin-left: 2px; }
.kpi-range { font-size: 11px; color: var(--ci-text-muted); }

/* ── 下方主体：左80% + 右20% ── */
.main-body { display: grid; grid-template-columns: 8fr 2fr; gap: 10px; flex: 1; min-width: 0; min-height: 0; }

/* 左侧 2×2 图表网格 */
.charts-grid { display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 8px; min-width: 0; min-height: 0; }
.charts-grid > * { min-width: 0; overflow: hidden; }

/* 右侧文本面板（各卡片独立滚动，高度比 2:1:1:1） */
.text-panel { display: flex; flex-direction: column; gap: 8px; min-width: 0; min-height: 0; }
.text-card { display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
.text-card.tc-main { flex: 2; }
.text-card.tc-sub  { flex: 1; }
.tc-hd { display: flex; align-items: center; gap: 8px; padding: 10px 12px 6px; flex-shrink: 0; }
.tc-icon { font-size: 18px; flex-shrink: 0; }
.tc-title { font-size: 14px; font-weight: 700; color: var(--ci-primary); }
.tc-body { flex: 1; min-height: 0; overflow-y: auto; padding: 0 12px 10px; overscroll-behavior: contain; }
.tc-body::-webkit-scrollbar { display: none; }
.tc-body { scrollbar-width: none; }
.tc-text { font-size: 12px; color: var(--ci-text-muted); line-height: 1.7; white-space: pre-line; text-indent: 2em; }

@media (max-width: 900px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .main-body { grid-template-columns: 1fr; }
  .charts-grid { grid-template-columns: 1fr; grid-template-rows: auto; }
  .text-panel { max-height: 400px; }
}
</style>
