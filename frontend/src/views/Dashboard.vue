<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="该年份暂无数据" @retry="load">
      <h1 class="page-h1">{{ selectedYear }} 年全球气候总览</h1>

      <!-- KPI -->
      <div class="kpi-grid">
        <GlassCard v-for="k in kpis" :key="k.name" class="kpi-card">
          <div class="kpi-label">{{ k.label }}</div>
          <div class="kpi-value" :style="{ color: k.color }">{{ k.value }}</div>
          <div class="kpi-desc">{{ k.desc }}</div>
        </GlassCard>
      </div>

      <!-- 中部图表 -->
      <div class="chart-row-2col">
        <ChartPanel title="月度温度变化趋势" subtitle="全球月度平均、平均最高与平均最低气温" :min-height="'450px'">
          <template #actions>
            <el-button size="small" text @click="fullscreenChart(monthlyRef)">⛶</el-button>
            <el-button size="small" text @click="downloadChart(monthlyRef, 'monthly.png')">⬇</el-button>
          </template>
          <v-chart ref="monthlyRef" :option="monthlyOption" style="height:380px" autoresize />
        </ChartPanel>

        <ChartPanel title="气候带分布" subtitle="按气象站所属气候带统计" :min-height="'450px'">
          <v-chart v-if="zoneOption.series[0].data.length" :option="zoneOption" style="height:380px" autoresize />
          <el-empty v-else description="暂无气候带数据" />
        </ChartPanel>
      </div>

      <!-- TOP 15 -->
      <ChartPanel title="最高温站点 TOP 15" subtitle="按年度站点最高温排序" :min-height="'400px'">
        <template #actions>
          <el-button size="small" text @click="fullscreenChart(hotRef)">⛶</el-button>
          <el-button size="small" text @click="downloadChart(hotRef, 'top15.png')">⬇</el-button>
        </template>
        <v-chart v-if="hotOption.series[0].data.length" ref="hotRef" :option="hotOption" style="height:340px" autoresize />
        <el-empty v-else description="暂无排名数据" />
      </ChartPanel>
    </PageState>
  </div>
</template>

<script setup>
import { ref, reactive, inject, watch, onMounted, onBeforeUnmount } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

import { getKPI, getMonthly, getZones, getRanking } from '../api'
import { stationCN } from '../utils/stationNames'
import PageState from '../components/PageState.vue'
import GlassCard from '../components/GlassCard.vue'
import ChartPanel from '../components/ChartPanel.vue'
import { chartColors, baseTooltip, baseGrid, monthLabels, safeNumber, zoneColors, zoneCN } from '../composables/useDashboardTheme'
import { fullscreenChart, downloadChart } from '../composables/useChartActions'

const selectedYear = inject('selectedYear')
const loading = ref(true)
const error = ref('')
const empty = ref(false)
let requestId = 0

const monthlyRef = ref(null)
const hotRef = ref(null)

const kpiColors = { global_avg_temp: chartColors.green, total_stations: chartColors.teal, extreme_event_pct: chartColors.orange, hottest_station_temp: chartColors.error }
const kpiLabels = { global_avg_temp: '全球年平均气温', total_stations: '活跃气象站', extreme_event_pct: '极端天气占比', hottest_station_temp: '年度最高温' }
const kpiUnits = { global_avg_temp: '°C', total_stations: '', extreme_event_pct: '%', hottest_station_temp: '°C' }

const kpis = ref([
  { name:'global_avg_temp', label:'全球年平均气温', value:'--', desc:'', color:chartColors.green },
  { name:'total_stations', label:'活跃气象站', value:'--', desc:'', color:chartColors.teal },
  { name:'extreme_event_pct', label:'极端天气占比', value:'--', desc:'', color:chartColors.orange },
  { name:'hottest_station_temp', label:'年度最高温', value:'--', desc:'', color:chartColors.error },
])

const monthlyOption = reactive({ tooltip: baseTooltip(), legend: { data:['平均气温','平均最高','平均最低'], textStyle:{color:chartColors.text}, top:0 }, grid: baseGrid(), xAxis: { type:'category', boundaryGap:false, data:monthLabels, axisLabel:{color:chartColors.text}, axisLine:{lineStyle:{color:chartColors.outline}} }, yAxis: { type:'value', name:'°C', axisLabel:{color:chartColors.text}, splitLine:{lineStyle:{color:chartColors.grid,type:'solid'}} }, series: [] })
const zoneOption = reactive({ tooltip: { trigger:'item', backgroundColor:'rgba(255,255,255,0.95)', borderColor:chartColors.outline, textStyle:{color:chartColors.text}, formatter:'{b}: {c} 站 ({d}%)' }, legend: { bottom:0, textStyle:{color:chartColors.text} }, series: [{ type:'pie', radius:['50%','75%'], label:{show:false}, emphasis:{label:{show:true,fontSize:18,fontWeight:'bold',color:chartColors.primary}}, labelLine:{show:false}, data:[], itemStyle:{borderRadius:8,borderColor:'#fff',borderWidth:3} }] })
const hotOption = reactive({ tooltip: baseTooltip(), grid: { ...baseGrid(), left:'15%' }, xAxis: { type:'value', name:'°C', axisLabel:{color:chartColors.text}, splitLine:{lineStyle:{color:chartColors.grid}} }, yAxis: { type:'category', data:[], axisLabel:{color:chartColors.text, width:130, overflow:'truncate'}, inverse:true }, series: [{ type:'bar', data:[], barMaxWidth:28, itemStyle:{ borderRadius:[0,6,6,0], color: new echartsInlineGradient() } }] })

function echartsInlineGradient() {
  return { type:'linear', x:0, y:0, x2:1, y2:0, colorStops:[{offset:0,color:chartColors.orangeSoft},{offset:1,color:chartColors.orange}] }
}

async function load() {
  const id = ++requestId
  loading.value = true; error.value = ''; empty.value = false
  const y = selectedYear.value
  try {
    const [kpiRes, monRes, zoneRes, rankRes] = await Promise.all([
      getKPI(y), getMonthly(y), getZones(y), getRanking(y, 'hottest', 15)
    ])
    if (id !== requestId) return

    if (!kpiRes.data?.data?.length && !monRes.data?.data?.length) {
      empty.value = true; loading.value = false; return
    }

    // KPI
    if (kpiRes.data?.data) {
      const m = {}; kpiRes.data.data.forEach(x => { m[x.kpi_name] = x.kpi_value })
      kpis.value.forEach(k => {
        const sv = safeNumber(m[k.name])
        k.value = sv != null ? sv + (kpiUnits[k.name] || '') : '--'
        k.desc = '基于 NOAA GSOD 年度汇总'
      })
    }

    // 月度趋势
    if (monRes.data?.data) {
      const sorted = [...monRes.data.data].sort((a,b) => a.obs_month - b.obs_month)
      monthlyOption.series = [
        { name:'平均气温', type:'line', data: sorted.map(r => safeNumber(r.avg_temp)), smooth:true, symbolSize:8, itemStyle:{color:chartColors.green}, areaStyle:{ color: { type:'linear', x:0,y:0,x2:0,y2:1, colorStops:[{offset:0,color:'rgba(58,103,79,0.15)'},{offset:1,color:'rgba(58,103,79,0)'}] } } },
        { name:'平均最高', type:'line', data: sorted.map(r => safeNumber(r.avg_max)), smooth:true, symbolSize:8, itemStyle:{color:chartColors.orange}, areaStyle:{ color: { type:'linear', x:0,y:0,x2:0,y2:1, colorStops:[{offset:0,color:'rgba(139,55,19,0.12)'},{offset:1,color:'rgba(139,55,19,0)'}] } } },
        { name:'平均最低', type:'line', data: sorted.map(r => safeNumber(r.avg_min)), smooth:true, symbolSize:8, itemStyle:{color:chartColors.teal} },
      ]
    }

    // 气候带
    if (zoneRes.data?.data) {
      zoneOption.series[0].data = zoneRes.data.data
        .filter(r => zoneCN[r.climate_zone])
        .map(r => ({ name: zoneCN[r.climate_zone], value: parseInt(r.cnt), itemStyle: { color: zoneColors[r.climate_zone] || '#999' } }))
    }

    // TOP 15 水平条形图
    if (rankRes.data?.data) {
      const rows = [...rankRes.data.data].sort((a,b) => a.rank_num - b.rank_num)
      hotOption.yAxis.data = rows.map(r => stationCN(r.station_name || r.station_id).substring(0, 22))
      hotOption.series[0].data = rows.map(r => safeNumber(r.value))
    }
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
.kpi-grid { display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:var(--ci-gap); margin-bottom:var(--ci-gap) }
.kpi-card { padding:24px; min-height:170px; display:flex; flex-direction:column; justify-content:space-between }
.kpi-label { font-size:12px; font-weight:500; text-transform:uppercase; letter-spacing:0.05em; color:var(--ci-text-muted) }
.kpi-value { font-size:36px; font-weight:700; line-height:1.1; margin:8px 0 }
.kpi-desc { font-size:12px; color:var(--ci-text-muted) }
.chart-row-2col { display:grid; grid-template-columns: minmax(0, 8fr) minmax(0, 4fr); gap:var(--ci-gap); margin-bottom:var(--ci-gap) }

@media (max-width: 1023px) {
  .kpi-grid { grid-template-columns:repeat(2, minmax(0, 1fr)) }
  .chart-row-2col { grid-template-columns: 1fr }
}
@media (max-width: 639px) {
  .kpi-grid { grid-template-columns: 1fr }
}
</style>
