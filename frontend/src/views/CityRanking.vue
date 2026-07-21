<template>
  <div>
    <h2 class="page-title">🏆 城市气候排行榜 — 2024</h2>

    <!-- Loading -->
    <el-skeleton v-if="loading" :rows="6" animated />

    <!-- Error -->
    <el-alert v-else-if="error" :title="error" type="error" show-icon closable @close="error='';load()">
      <el-button type="primary" size="small" @click="load()">重试</el-button>
    </el-alert>

    <!-- Data -->
    <template v-else>
      <el-radio-group v-model="category" @change="load" style="margin-bottom:16px">
        <el-radio-button value="hottest">🔥 最热 (°C)</el-radio-button>
        <el-radio-button value="coldest">❄️ 最冷 (°C)</el-radio-button>
        <el-radio-button value="rainiest">🌧️ 最多雨 (mm)</el-radio-button>
        <el-radio-button value="most_extreme">⚠️ 极端天气 (天)</el-radio-button>
      </el-radio-group>

      <div class="chart-card">
        <v-chart v-if="hasData" :option="option" style="height:420px" autoresize />
        <el-empty v-else description="暂无排名数据" />
      </div>

      <p class="data-note">数据来源: NOAA GSOD 2024 | 仅含 2024 年数据</p>
    </template>
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
const loading = ref(true)
const error = ref('')
const hasData = ref(false)

const units = { hottest: '°C', coldest: '°C', rainiest: 'mm', most_extreme: '天' }

const option = reactive({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: v => typeof v === 'number' ? v.toFixed(2) : v },
  xAxis: { type: 'category', data: [], axisLabel: { rotate: 30 } },
  yAxis: { type: 'value', name: units[category.value] },
  series: [{ type: 'bar', data: [], itemStyle: { color: '#e53935' } }]
})

async function load() {
  loading.value = true; error.value = ''; hasData.value = false
  try {
    const res = await getRanking(2024, category.value, 15)
    if (res.data?.data && res.data.data.length > 0) {
      option.xAxis.data = res.data.data.map(r => stationCN(r.station_name || r.station_id).substring(0, 20))
      option.series[0].data = res.data.data.map(r => parseFloat(r.value))
      option.yAxis.name = units[category.value] || ''
      hasData.value = true
    }
  } catch(e) {
    error.value = '数据加载失败，请确认后端已启动'
    console.error(e)
  } finally { loading.value = false }
}
load()
</script>

<style scoped>
.page-title{font-size:22px;font-weight:bold;color:#1a237e;margin-bottom:20px}
.chart-card{background:#fff;border-radius:10px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.data-note{color:#888;font-size:12px;margin-top:8px;text-align:center}
</style>
