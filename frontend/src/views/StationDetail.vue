<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="未找到该站点数据" @retry="load">
      <div class="detail-root">
        <!-- 站信息头 -->
        <div class="detail-hd">
          <div>
            <div class="detail-title">{{ info?.station_name || '未知站点' }}</div>
            <div class="detail-meta">
              <span>{{ zoneCN[info?.climate_zone] || '' }}</span>
              <span class="meta-sep">·</span>
              <span>{{ info?.lat?.toFixed(2) }}°N, {{ info?.lon?.toFixed(2) }}°E</span>
              <span class="meta-sep">·</span>
              <span>{{ selectedYear }} 年</span>
            </div>
          </div>
          <div class="detail-rank" v-if="rankings.length">
            <el-tag v-for="r in rankings" :key="r.category" :type="r.category==='hottest'?'danger':r.category==='coldest'?'info':'warning'" size="small" style="margin:2px">
              {{ catLabel(r) }}
            </el-tag>
          </div>
        </div>

        <!-- 卡片行 -->
        <div class="detail-kpi-row">
          <GlassCard class="dk-card">
            <div class="dk-label">年均温</div>
            <div class="dk-value">{{ annualAvg }}°C</div>
          </GlassCard>
          <GlassCard class="dk-card">
            <div class="dk-label">年降水</div>
            <div class="dk-value">{{ annualPrecip }} mm</div>
          </GlassCard>
          <GlassCard class="dk-card">
            <div class="dk-label">极端天数</div>
            <div class="dk-value">{{ extremeTotal }} 天</div>
          </GlassCard>
          <GlassCard class="dk-card">
            <div class="dk-label">观测天数</div>
            <div class="dk-value">{{ obsTotal }} 天</div>
          </GlassCard>
        </div>

        <!-- 图表 -->
        <div class="detail-charts">
          <ChartPanel title="月度气温变化" style="flex:1;min-height:0;min-width:0">
            <v-chart :option="tempOption" autoresize />
          </ChartPanel>
          <ChartPanel title="月度降水" style="flex:1;min-height:0;min-width:0">
            <v-chart :option="precipOption" autoresize />
          </ChartPanel>
        </div>

        <!-- 极端事件明细 -->
        <GlassCard class="detail-events">
          <div class="card-title">⚠️ 极端天气事件</div>
          <div class="events-grid" v-if="months.length">
            <div v-for="(m,i) in months" :key="i" class="event-month">
              <div class="em-label">{{ m.obs_month }}月</div>
              <div class="em-bar-wrap">
                <div class="em-bar heat" :style="{width:(m.heat_wave_days||0)*3+'px'}" title="热浪: {{m.heat_wave_days||0}}天"></div>
                <div class="em-bar cold" :style="{width:(m.cold_wave_days||0)*3+'px'}" title="寒潮: {{m.cold_wave_days||0}}天"></div>
                <div class="em-bar storm" :style="{width:(m.thunder_days||0)*3+'px'}" title="雷暴: {{m.thunder_days||0}}天"></div>
                <div class="em-bar frost" :style="{width:(m.frost_days||0)*3+'px'}" title="霜冻: {{m.frost_days||0}}天"></div>
              </div>
              <div class="em-count">{{ (m.heat_wave_days||0)+(m.cold_wave_days||0)+(m.thunder_days||0)+(m.frost_days||0) }}</div>
            </div>
          </div>
          <div v-else class="events-empty">暂无极端事件数据</div>
        </GlassCard>
      </div>
    </PageState>
  </div>
</template>

<script setup>
import { ref, inject, watch, reactive, computed } from 'vue'
import { useRoute } from 'vue-router'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent])
import { getStationDetail } from '../api'
import PageState from '../components/PageState.vue'
import GlassCard from '../components/GlassCard.vue'
import ChartPanel from '../components/ChartPanel.vue'
import { chartColors, baseTooltip, baseGrid, monthLabels } from '../composables/useDashboardTheme'

const route = useRoute()
const selectedYear = inject('selectedYear')
const loading = ref(true); const error = ref(''); const empty = ref(false)
let requestId = 0

const info = ref(null)
const months = ref([])
const rankings = ref([])

const zoneCN = { tropical:'热带', temperate:'温带', continental:'大陆性', polar:'寒带', arid:'干旱' }

const annualAvg = computed(() => {
  const vals = months.value.map(m => m.avg_temp).filter(v => v != null)
  return vals.length ? (vals.reduce((a,b)=>a+b,0)/vals.length).toFixed(1) : '--'
})
const annualPrecip = computed(() => {
  const total = months.value.reduce((s,m) => s + (m.precip||0), 0)
  return total.toFixed(1)
})
const extremeTotal = computed(() => {
  return months.value.reduce((s,m) => s + (m.extreme_days||0), 0)
})
const obsTotal = computed(() => {
  return months.value.reduce((s,m) => s + (m.obs_days||0), 0)
})

const catLabel = (r) => {
  const map = { hottest:'🔥 最热 TOP'+r.rank_num, coldest:'❄️ 最冷 TOP'+r.rank_num,
    rainiest:'🌧️ 最多降水 TOP'+r.rank_num, most_extreme:'⚠️ 极端 TOP'+r.rank_num }
  return map[r.category] || r.category
}

const tempOption = reactive({
  tooltip: { ...baseTooltip(), axisPointer:{type:'cross'} },
  legend: { data:['均温','最高','最低'], textStyle:{color:chartColors.text,fontSize:10}, top:0, itemWidth:12, itemHeight:8 },
  grid: { ...baseGrid(), top:'16%' },
  xAxis: { type:'category', boundaryGap:false, data:monthLabels, axisLabel:{color:chartColors.text,fontSize:10}, axisLine:{lineStyle:{color:chartColors.outline}} },
  yAxis: { type:'value', name:'°C', axisLabel:{color:chartColors.text,fontSize:9}, splitLine:{lineStyle:{color:chartColors.grid}} },
  series: [
    { name:'均温', type:'line', smooth:true, symbolSize:5, data:[], itemStyle:{color:chartColors.green}, areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(58,103,79,0.12)'},{offset:1,color:'rgba(58,103,79,0)'}]}} },
    { name:'最高', type:'line', smooth:true, symbolSize:5, data:[], itemStyle:{color:chartColors.orange} },
    { name:'最低', type:'line', smooth:true, symbolSize:5, data:[], itemStyle:{color:chartColors.teal} },
  ]
})

const precipOption = reactive({
  tooltip: baseTooltip(),
  grid: baseGrid(),
  xAxis: { type:'category', data:monthLabels, axisLabel:{color:chartColors.text,fontSize:10}, axisLine:{lineStyle:{color:chartColors.outline}} },
  yAxis: { type:'value', name:'mm', axisLabel:{color:chartColors.text,fontSize:9}, splitLine:{lineStyle:{color:chartColors.grid}} },
  series: [{ type:'bar', data:[], barMaxWidth:24, itemStyle:{borderRadius:[4,4,0,0],color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:chartColors.teal},{offset:1,color:'#7ab8c0'}]}}}]
})

async function load() {
  const id = ++requestId
  loading.value = true; error.value = ''; empty.value = false
  const sid = route.params.id
  if (!sid) { empty.value = true; loading.value = false; return }
  try {
    const res = await getStationDetail(sid, selectedYear.value)
    if (id !== requestId) return
    const d = res.data?.data
    if (!d?.info) { empty.value = true; loading.value = false; return }
    info.value = d.info
    months.value = d.months || []
    rankings.value = d.rankings || []

    tempOption.series[0].data = d.months.map(m => m.avg_temp)
    tempOption.series[1].data = d.months.map(m => m.avg_max)
    tempOption.series[2].data = d.months.map(m => m.avg_min)
    precipOption.series[0].data = d.months.map(m => m.precip)
  } catch (e) { if (id === requestId) { error.value = '站点详情加载失败'; console.error(e) } }
  finally { if (id === requestId) loading.value = false }
}
watch(route, () => { if (route.params.id) load() }, { immediate: true })
</script>

<style scoped>
.detail-root { display:flex; flex-direction:column; flex:1; min-height:0; gap:12px; overflow-y:auto; padding-right:4px }
.detail-hd { display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px; flex-shrink:0 }
.detail-title { font-size:22px; font-weight:700; color:var(--ci-primary) }
.detail-meta { font-size:12px; color:var(--ci-text-muted); margin-top:2px }
.meta-sep { margin:0 6px }
.detail-rank { display:flex; flex-wrap:wrap }

.detail-kpi-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; flex-shrink:0 }
.dk-card { padding:10px 14px; display:flex; flex-direction:column }
.dk-label { font-size:10px; font-weight:500; text-transform:uppercase; letter-spacing:0.05em; color:var(--ci-text-muted) }
.dk-value { font-size:20px; font-weight:700; color:var(--ci-primary); margin-top:2px }

.detail-charts { display:grid; grid-template-columns:1fr 1fr; gap:12px; flex:3; min-height:0; overflow:hidden }

.detail-events { padding:14px; flex-shrink:0 }
.card-title { font-size:14px; font-weight:600; color:var(--ci-primary); margin-bottom:8px }
.events-grid { display:flex; flex-direction:column; gap:3px }
.event-month { display:flex; align-items:center; gap:8px; font-size:12px }
.em-label { width:30px; font-weight:600; color:var(--ci-text-muted); flex-shrink:0; text-align:right }
.em-bar-wrap { flex:1; display:flex; gap:2px; height:14px; align-items:center }
.em-bar { height:10px; border-radius:3px; min-width:2px; transition:width .3s }
.em-bar.heat { background:#8b3713 }
.em-bar.cold { background:#39656b }
.em-bar.storm { background:#717973 }
.em-bar.frost { background:#c0c9c1 }
.em-count { width:28px; text-align:right; font-weight:600; color:var(--ci-text-muted); flex-shrink:0 }
.events-empty { font-size:12px; color:var(--ci-text-muted); padding:20px; text-align:center }

@media (max-width: 767px) {
  .detail-kpi-row { grid-template-columns:repeat(2,1fr) }
  .detail-charts { grid-template-columns:1fr }
}
</style>
