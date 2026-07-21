<template>
  <div>
    <h2 class="page-title">📊 全球气候总览 — {{ selectedYear }}</h2>

    <!-- Loading -->
    <el-skeleton v-if="loading" :rows="8" animated />

    <!-- Error -->
    <el-alert v-else-if="error" :title="error" type="error" show-icon closable @close="error='';load()">
      <el-button type="primary" size="small" @click="load()">重试</el-button>
    </el-alert>

    <!-- Empty -->
    <el-empty v-else-if="empty" description="该年份暂无数据" />

    <!-- Data -->
    <template v-else>
      <div class="kpi-row">
        <div class="kpi-card" v-for="k in kpis" :key="k.name">
          <div class="kpi-value">{{ k.value }}</div>
          <div class="kpi-label">{{ k.label }}</div>
        </div>
      </div>

      <div class="chart-row">
        <div class="chart-card" style="flex:2">
          <div class="chart-title">🌡️ 月均温度变化</div>
          <v-chart :option="monthlyOption" style="height:320px" autoresize />
        </div>
        <div class="chart-card" style="flex:1">
          <div class="chart-title">🌍 气候带分布</div>
          <v-chart v-if="zoneOption.series[0].data.length" :option="zoneOption" style="height:320px" autoresize />
          <el-empty v-else description="暂无气候带数据" />
        </div>
      </div>

      <div class="chart-row">
        <div class="chart-card">
          <div class="chart-title">🏆 最热城市 TOP15</div>
          <v-chart v-if="hotOption.series[0].data.length" :option="hotOption" style="height:320px" autoresize />
          <el-empty v-else description="暂无排名数据" />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, inject, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

import { getKPI, getMonthly, getZones, getRanking } from '../api'
import { stationCN } from '../utils/stationNames'

const selectedYear = inject('selectedYear')
const loading = ref(true)
const error = ref('')
const empty = ref(false)

const kpis = ref([
  { name:'avg_temp', label:'全球年均温', value:'--' },
  { name:'stations', label:'活跃气象站', value:'--' },
  { name:'extreme', label:'极端天气占比', value:'--' },
  { name:'hottest', label:'年度最高温', value:'--' },
])

const monthlyOption = reactive({ tooltip:{trigger:'axis', valueFormatter: v => typeof v === 'number' ? v.toFixed(2) : v}, xAxis:{type:'category',data:[]}, yAxis:{type:'value',name:'°C'}, series:[] })
const zoneOption = reactive({ tooltip:{trigger:'item'}, series:[{type:'pie',radius:['40%','70%'],data:[]}] })
const hotOption = reactive({ tooltip:{trigger:'axis', valueFormatter: v => typeof v === 'number' ? v.toFixed(2) : v}, xAxis:{type:'category',data:[],axisLabel:{rotate:30}}, yAxis:{type:'value',name:'°C'}, series:[{type:'bar',data:[]}] })

async function load() {
  loading.value = true; error.value = ''; empty.value = false
  const y = selectedYear.value
  try {
    const [kpiRes, monRes, zoneRes, rankRes] = await Promise.all([
      getKPI(y), getMonthly(y), getZones(y), getRanking(y, 'hottest', 15)
    ])
    if (!kpiRes.data?.data?.length && !monRes.data?.data?.length) {
      empty.value = true; loading.value = false; return
    }
    if (kpiRes.data?.data) {
      const m = {}; kpiRes.data.data.forEach(x => { m[x.kpi_name] = x.kpi_value })
      kpis.value[0].value = (m.global_avg_temp || '--') + '°C'
      kpis.value[1].value = (m.total_stations || '--')
      kpis.value[2].value = (m.extreme_event_pct || '--') + '%'
      kpis.value[3].value = (m.hottest_station_temp || '--') + '°C'
    }
    if (monRes.data?.data) {
      monthlyOption.xAxis.data = monRes.data.data.map(r => r.obs_month + '月')
      monthlyOption.series = [
        { name:'均温', type:'line', data: monRes.data.data.map(r => parseFloat(r.avg_temp)), smooth:true, itemStyle:{color:'#e53935'} },
        { name:'最高', type:'line', data: monRes.data.data.map(r => parseFloat(r.avg_max)), smooth:true, itemStyle:{color:'#fb8c00'} },
        { name:'最低', type:'line', data: monRes.data.data.map(r => parseFloat(r.avg_min)), smooth:true, itemStyle:{color:'#1e88e5'} },
      ]
    }
    if (zoneRes.data?.data) {
      const zoneCN = { tropical:'热带', temperate:'温带', continental:'大陆性', polar:'寒带', arid:'干旱' }
      zoneOption.series[0].data = zoneRes.data.data.map(r => ({ name: zoneCN[r.climate_zone] || r.climate_zone, value: parseInt(r.cnt) }))
    }
    if (rankRes.data?.data) {
      hotOption.xAxis.data = rankRes.data.data.map(r => stationCN(r.station_name || r.station_id).substring(0,18))
      hotOption.series[0].data = rankRes.data.data.map(r => parseFloat(r.value))
    }
  } catch(e) {
    error.value = '数据加载失败，请确认后端已启动 (localhost:5000)'
    console.error(e)
  } finally {
    loading.value = false
  }
}

watch(selectedYear, load)
onMounted(load)
</script>

<style scoped>
.page-title{font-size:22px;font-weight:bold;color:#1a237e;margin-bottom:20px}
.kpi-row{display:flex;gap:16px;margin-bottom:20px;flex-wrap:wrap}
.kpi-card{flex:1;min-width:180px;background:#fff;border-radius:10px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.06);text-align:center}
.kpi-value{font-size:32px;font-weight:bold;color:#1a237e}
.kpi-label{font-size:13px;color:#888;margin-top:4px}
.chart-row{display:flex;gap:16px;margin-bottom:20px;flex-wrap:wrap}
.chart-card{flex:1;min-width:320px;background:#fff;border-radius:10px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.chart-title{font-size:16px;font-weight:bold;color:#333;margin-bottom:12px}
</style>
