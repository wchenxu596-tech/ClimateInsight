<template>
  <div>
    <h2 class="page-title">🏆 城市气候排行榜</h2>
    <el-radio-group v-model="category" @change="load" style="margin-bottom:16px">
      <el-radio-button value="hottest">🔥 最热</el-radio-button>
      <el-radio-button value="coldest">❄️ 最冷</el-radio-button>
      <el-radio-button value="rainiest">🌧️ 最多雨</el-radio-button>
      <el-radio-button value="most_extreme">⚠️ 极端天气</el-radio-button>
    </el-radio-group>
    <div class="chart-card">
      <v-chart :option="option" style="height:420px" autoresize />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
use([CanvasRenderer, BarChart, GridComponent, TooltipComponent])

import { getRanking } from '../api'
import { stationCN } from '../utils/stationNames'

const category = ref('hottest')
const option = reactive({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: [], axisLabel: { rotate: 30 } },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: [], itemStyle: { color: '#e53935' } }]
})

async function load() {
  try {
    const res = await getRanking(2024, category.value, 15)
    if (res.data?.data) {
      option.xAxis.data = res.data.data.map(r => stationCN(r.station_name || r.station_id).substring(0,20))
      option.series[0].data = res.data.data.map(r => parseFloat(r.value))
    }
  } catch(e) { console.error(e) }
}
load()
</script>

<style scoped>
.page-title{font-size:22px;font-weight:bold;color:#1a237e;margin-bottom:20px}
.chart-card{background:#fff;border-radius:10px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
</style>
