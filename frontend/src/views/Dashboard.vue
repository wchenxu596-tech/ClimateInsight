<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="该年份暂无数据" @retry="load">
      <h1 class="page-h1">{{ selectedYear }} 年全球气候总览</h1>

      <!-- KPI 紧凑行 -->
      <div class="kpi-grid">
        <GlassCard v-for="k in kpis" :key="k.name" class="kpi-card">
          <div class="kpi-label">{{ k.label }}</div>
          <div class="kpi-value" :style="{ color: k.color }">{{ k.value }}</div>
          <div class="kpi-desc">{{ k.desc }}</div>
        </GlassCard>
      </div>

      <!-- 中部双图：flex自动填充剩余高度 -->
      <div class="charts-row">
        <ChartPanel title="月度温度变化趋势" subtitle="全球月度平均、平均最高与平均最低气温" class="flex-chart" :loading="false" :empty="false">
          <v-chart ref="monthlyRef" :option="monthlyOption" autoresize />
        </ChartPanel>

        <ChartPanel title="气候带分布" class="flex-chart" :loading="false" :empty="!zoneOption.series[0].data.length" empty-text="暂无气候带数据">
          <v-chart :option="zoneOption" autoresize />
        </ChartPanel>
      </div>

      <!-- 底部 TOP15 条形图 -->
      <ChartPanel title="最高温站点 TOP 15" subtitle="按年度站点最高温排序" class="chart-last" :loading="false" :empty="!hotOption.series[0].data.length" empty-text="暂无排名数据">
        <v-chart ref="hotRef" :option="hotOption" autoresize />
      </ChartPanel>
    </PageState>
  </div>
</template>

<script setup>
import { ref, reactive, inject, watch } from 'vue'
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

const selectedYear = inject('selectedYear')
const loading = ref(true)
const error = ref('')
const empty = ref(false)
let requestId = 0

const monthlyRef = ref(null), hotRef = ref(null)

const kpiColors = { global_avg_temp: chartColors.green, total_stations: chartColors.teal, extreme_event_pct: chartColors.orange, hottest_station_temp: chartColors.error }
const kpiUnits = { global_avg_temp: '°C', total_stations: '', extreme_event_pct: '%', hottest_station_temp: '°C' }

const kpis = ref([
  { name:'global_avg_temp', label:'全球年平均气温', value:'--', desc:'', color:chartColors.green },
  { name:'total_stations', label:'活跃气象站', value:'--', desc:'', color:chartColors.teal },
  { name:'extreme_event_pct', label:'极端天气占比', value:'--', desc:'', color:chartColors.orange },
  { name:'hottest_station_temp', label:'年度最高温', value:'--', desc:'', color:chartColors.error },
])

const monthlyOption = reactive({ tooltip: baseTooltip(), legend: { data:['均温','均最高','均最低'], textStyle:{color:chartColors.text,fontSize:11}, top:0, itemWidth:14, itemHeight:8 }, grid: { left:'3%',right:'4%',top:'14%',bottom:'3%',containLabel:true }, xAxis: { type:'category',boundaryGap:false,data:monthLabels,axisLabel:{color:chartColors.text,fontSize:11},axisLine:{lineStyle:{color:chartColors.outline}} }, yAxis: { type:'value',name:'°C',axisLabel:{color:chartColors.text,fontSize:11},splitLine:{lineStyle:{color:chartColors.grid}} }, series: [] })
const zoneOption = reactive({ tooltip: { trigger:'item',backgroundColor:'rgba(255,255,255,0.95)',borderColor:chartColors.outline,textStyle:{color:chartColors.text},formatter:'{b}: {c} 站 ({d}%)' }, legend: { bottom:0,textStyle:{color:chartColors.text,fontSize:11},itemWidth:10,itemHeight:8 }, series: [{ type:'pie',radius:['45%','72%'],center:['50%','45%'],label:{show:false},emphasis:{label:{show:true,fontSize:16,fontWeight:'bold',color:chartColors.primary}},labelLine:{show:false},data:[],itemStyle:{borderRadius:6,borderColor:'#fff',borderWidth:2} }] })
const hotOption = reactive({ tooltip: baseTooltip(), grid: { left:'3%',right:'6%',top:'3%',bottom:'3%',containLabel:true }, xAxis: { type:'value',name:'°C',axisLabel:{color:chartColors.text,fontSize:11},splitLine:{lineStyle:{color:chartColors.grid}} }, yAxis: { type:'category',data:[],axisLabel:{color:chartColors.text,fontSize:11,width:120,overflow:'truncate'},inverse:true,axisLine:{show:false},axisTick:{show:false} }, series: [{ type:'bar',data:[],barMaxWidth:20,itemStyle:{ borderRadius:[0,4,4,0], color: { type:'linear',x:0,y:0,x2:1,y2:0, colorStops:[{offset:0,color:chartColors.orangeSoft},{offset:1,color:chartColors.orange}] } } }] })

async function load() {
  const id = ++requestId
  loading.value = true; error.value = ''; empty.value = false
  const y = selectedYear.value
  try {
    const [kpiRes, monRes, zoneRes, rankRes] = await Promise.all([getKPI(y), getMonthly(y), getZones(y), getRanking(y,'hottest',15)])
    if (id !== requestId) return
    if (!kpiRes.data?.data?.length && !monRes.data?.data?.length) { empty.value = true; loading.value = false; return }
    if (kpiRes.data?.data) {
      const m = {}; kpiRes.data.data.forEach(x => { m[x.kpi_name] = x.kpi_value })
      kpis.value.forEach(k => { const sv = safeNumber(m[k.name]); k.value = sv != null ? sv + (kpiUnits[k.name]||'') : '--'; k.desc = '基于 NOAA GSOD 年度汇总' })
    }
    if (monRes.data?.data) {
      const sorted = [...monRes.data.data].sort((a,b) => a.obs_month - b.obs_month)
      monthlyOption.series = [
        { name:'均温', type:'line', data:sorted.map(r=>safeNumber(r.avg_temp)), smooth:true, symbolSize:6, itemStyle:{color:chartColors.green}, areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(58,103,79,0.12)'},{offset:1,color:'rgba(58,103,79,0)'}]}} },
        { name:'均最高', type:'line', data:sorted.map(r=>safeNumber(r.avg_max)), smooth:true, symbolSize:6, itemStyle:{color:chartColors.orange}, areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(139,55,19,0.1)'},{offset:1,color:'rgba(139,55,19,0)'}]}} },
        { name:'均最低', type:'line', data:sorted.map(r=>safeNumber(r.avg_min)), smooth:true, symbolSize:6, itemStyle:{color:chartColors.teal} },
      ]
    }
    if (zoneRes.data?.data) {
      zoneOption.series[0].data = zoneRes.data.data.filter(r=>zoneCN[r.climate_zone]).map(r=>({name:zoneCN[r.climate_zone],value:parseInt(r.cnt)||0,itemStyle:{color:zoneColors[r.climate_zone]||'#999'}}))
    }
    if (rankRes.data?.data) {
      const rows = [...rankRes.data.data].sort((a,b)=>a.rank_num-b.rank_num)
      hotOption.yAxis.data = rows.map(r=>stationCN(r.station_name||r.station_id).substring(0,20))
      hotOption.series[0].data = rows.map(r=>safeNumber(r.value))
    }
  } catch(e) { if (id===requestId) { error.value='数据加载失败，请确认后端已启动'; console.error(e) } }
  finally { if (id===requestId) loading.value=false }
}

watch(selectedYear, load, { immediate: true })
</script>

<style scoped>
.kpi-grid { display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:10px; flex-shrink:0; margin-bottom:8px }
.kpi-card { padding:14px 18px; min-height:90px; display:flex; flex-direction:column; justify-content:center }
.kpi-label { font-size:16px; font-weight:500; text-transform:uppercase; letter-spacing:0.05em; color:var(--ci-text-muted) }
.kpi-value { font-size:30px; font-weight:700; line-height:1.1; margin:4px 0 }
.kpi-desc { font-size:13px; color:var(--ci-text-muted) }

.charts-row { display:grid; grid-template-columns: minmax(0, 8fr) minmax(0, 4fr); gap:10px; flex:5; min-height:0; overflow:hidden; margin-bottom:8px }
.charts-row > :deep(*) { display:flex; flex-direction:column; overflow:hidden }
.charts-row > :deep(.cp-body) { flex:1; min-height:0 }

.chart-last { flex:3; min-height:0; overflow:hidden }
.chart-last > :deep(*) { display:flex; flex-direction:column; overflow:hidden }
.chart-last > :deep(.cp-body) { flex:1; min-height:0 }

@media (max-width: 1023px) {
  .kpi-grid { grid-template-columns:repeat(2, minmax(0, 1fr)) }
  .charts-row { grid-template-columns: 1fr; flex:6 }
  .chart-last { flex: 4 }
}
@media (max-width: 639px) {
  .kpi-grid { grid-template-columns: 1fr }
  .kpi-card { min-height:64px }
}
</style>
