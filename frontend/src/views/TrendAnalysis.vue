<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="暂无月度数据" @retry="load">
      <div class="trend-layout">
        <!-- 左侧信息栏 -->
        <aside class="trend-sidebar">
          <GlassCard class="sb-card">
            <div class="sb-label">数据范围</div>
            <div class="sb-value">全球 / {{ selectedYear }} 年</div>
            <div class="sb-note">数据来源：NOAA GSOD</div>
          </GlassCard>
          <GlassCard class="sb-card">
            <div class="sb-label">年度峰值平均气温</div>
            <div class="sb-value highlight">{{ peakTemp != null ? peakTemp.toFixed(2) + '°C' : '--' }}</div>
            <div class="sb-note">{{ peakMonth ? peakMonth + '月记录' : '暂无数据' }}</div>
          </GlassCard>
        </aside>

        <!-- 主图表 -->
        <section class="trend-main">
          <ChartPanel :title="'月度气温变化'" :subtitle="'全球月度平均、平均最高与平均最低气温'" :min-height="'600px'">
            <template #actions>
              <el-button size="small" text @click="fullscreenChart(chartRef)">⛶</el-button>
              <el-button size="small" text @click="downloadChart(chartRef, 'trend.png')">⬇</el-button>
            </template>
            <v-chart ref="chartRef" :option="option" style="height:520px" autoresize />
          </ChartPanel>

          <!-- 底部统计卡片 -->
          <div class="stat-row">
            <GlassCard class="stat-card">
              <div class="stat-label">全年平均气温</div>
              <div class="stat-value">{{ annualAvg != null ? annualAvg.toFixed(2) + '°C' : '--' }}</div>
            </GlassCard>
            <GlassCard class="stat-card">
              <div class="stat-label">年度最高平均气温</div>
              <div class="stat-value">{{ peakMax != null ? peakMax.toFixed(2) + '°C' : '--' }}</div>
            </GlassCard>
            <GlassCard class="stat-card">
              <div class="stat-label">数据来源</div>
              <div class="stat-value-sm">NOAA GSOD</div>
            </GlassCard>
          </div>
        </section>
      </div>
    </PageState>
  </div>
</template>

<script setup>
import { ref, reactive, inject, watch, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

import { getMonthly } from '../api'
import PageState from '../components/PageState.vue'
import GlassCard from '../components/GlassCard.vue'
import ChartPanel from '../components/ChartPanel.vue'
import { chartColors, baseTooltip, baseGrid, monthLabels, safeNumber } from '../composables/useDashboardTheme'
import { fullscreenChart, downloadChart } from '../composables/useChartActions'

const selectedYear = inject('selectedYear')
const loading = ref(true)
const error = ref('')
const empty = ref(false)
let requestId = 0
const chartRef = ref(null)

const option = reactive({ tooltip: { ...baseTooltip(), axisPointer:{type:'cross'} }, legend: { data:['平均气温','平均最高','平均最低'], textStyle:{color:chartColors.text}, top:0 }, grid: baseGrid(), xAxis: { type:'category', boundaryGap:false, data:monthLabels, axisLabel:{color:chartColors.text}, axisLine:{lineStyle:{color:chartColors.outline}} }, yAxis: { type:'value', name:'气温（°C）', axisLabel:{color:chartColors.text}, splitLine:{lineStyle:{color:chartColors.grid}} }, series: [] })

const peakTemp = ref(null)
const peakMonth = ref(null)
const annualAvg = ref(null)
const peakMax = ref(null)

async function load() {
  const id = ++requestId
  loading.value = true; error.value = ''; empty.value = false
  try {
    const res = await getMonthly(selectedYear.value)
    if (id !== requestId) return
    const rows = (res.data?.data || []).sort((a,b) => a.obs_month - b.obs_month)
    if (!rows.length) { empty.value = true; loading.value = false; return }

    const temps = rows.map(r => safeNumber(r.avg_temp))
    const maxs = rows.map(r => safeNumber(r.avg_max))
    const mins = rows.map(r => safeNumber(r.avg_min))

    option.series = [
      { name:'平均气温', type:'line', data:temps, smooth:true, symbolSize:8, itemStyle:{color:chartColors.green}, areaStyle:{ color: { type:'linear', x:0,y:0,x2:0,y2:1, colorStops:[{offset:0,color:'rgba(58,103,79,0.15)'},{offset:1,color:'rgba(58,103,79,0)'}] } }, markPoint:{ data:[{type:'max',name:'峰值',itemStyle:{color:chartColors.orange},label:{color:'#fff'}}] } },
      { name:'平均最高', type:'line', data:maxs, smooth:true, symbolSize:8, itemStyle:{color:chartColors.orange}, areaStyle:{ color: { type:'linear', x:0,y:0,x2:0,y2:1, colorStops:[{offset:0,color:'rgba(139,55,19,0.12)'},{offset:1,color:'rgba(139,55,19,0)'}] } } },
      { name:'平均最低', type:'line', data:mins, smooth:true, symbolSize:8, itemStyle:{color:chartColors.teal} },
    ]

    // 统计
    const validTemps = temps.filter(Number.isFinite)
    annualAvg.value = validTemps.length ? validTemps.reduce((a,b)=>a+b,0) / validTemps.length : null

    const validMaxs = maxs.filter(Number.isFinite)
    peakMax.value = validMaxs.length ? Math.max(...validMaxs) : null

    // 峰值月份
    let bestVal = -Infinity, bestIdx = -1
    temps.forEach((v, i) => { if (v != null && v > bestVal) { bestVal = v; bestIdx = i } })
    peakTemp.value = bestIdx >= 0 ? bestVal : null
    peakMonth.value = bestIdx >= 0 ? rows[bestIdx].obs_month : null
  } catch(e) {
    if (id === requestId) { error.value = '数据加载失败，请确认后端已启动'; console.error(e) }
  } finally {
    if (id === requestId) loading.value = false
  }
}

watch(selectedYear, load, { immediate: true })
</script>

<style scoped>
.page-container { max-width:var(--ci-content-max); margin:0 auto; padding:48px var(--ci-page-gutter) 80px }
.trend-layout { display:grid; grid-template-columns:280px 1fr; gap:var(--ci-gap); align-items:start }
.trend-sidebar { display:flex; flex-direction:column; gap:var(--ci-gap) }
.sb-card { padding:24px }
.sb-label { font-size:11px; font-weight:500; text-transform:uppercase; letter-spacing:0.05em; color:var(--ci-text-muted); margin-bottom:8px }
.sb-value { font-size:24px; font-weight:700; color:var(--ci-text) }
.sb-value.highlight { color:var(--ci-tertiary) }
.sb-note { font-size:13px; color:var(--ci-text-muted); margin-top:6px }
.stat-row { display:grid; grid-template-columns:repeat(3, 1fr); gap:var(--ci-gap); margin-top:var(--ci-gap) }
.stat-card { padding:20px; text-align:center }
.stat-label { font-size:12px; color:var(--ci-text-muted); margin-bottom:6px }
.stat-value { font-size:28px; font-weight:600; color:var(--ci-primary) }
.stat-value-sm { font-size:20px; font-weight:500; color:var(--ci-text) }

@media (max-width: 767px) {
  .trend-layout { grid-template-columns:1fr }
  .trend-sidebar { flex-direction:row; overflow-x:auto }
  .sb-card { min-width:180px }
  .stat-row { grid-template-columns:1fr }
}
</style>
