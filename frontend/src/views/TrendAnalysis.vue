<template>
  <div>
    <h2 class="page-title">📈 2024 年月度气温变化</h2>
    <el-alert v-if="error" :title="error" type="error" show-icon closable @close="error='';load()">
      <el-button type="primary" size="small" @click="load()">重试</el-button>
    </el-alert>
    <el-skeleton v-else-if="loading" :rows="6" animated />
    <div v-else class="chart-card">
      <div class="chart-title">🌡️ 各月平均温度（°C）</div>
      <v-chart :option="option" style="height:400px" autoresize />
      <p style="color:#888;font-size:12px;margin-top:8px">数据来源: NOAA GSOD 2024 | 仅含单年数据，同比趋势需导入更多年份</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent])
import { getMonthly } from '../api'

const loading = ref(true)
const error = ref('')
const option = reactive({
  tooltip: { trigger: 'axis' },
  legend: { data: ['均温', '均最高', '均最低'] },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '°C' },
  series: [
    { name: '均温', type: 'line', data: [], smooth: true, itemStyle: { color: '#e53935' } },
    { name: '均最高', type: 'line', data: [], smooth: true, itemStyle: { color: '#fb8c00' } },
    { name: '均最低', type: 'line', data: [], smooth: true, itemStyle: { color: '#1e88e5' } },
  ]
})

async function load() {
  loading.value = true; error.value = ''
  try {
    const res = await getMonthly(2024)
    if (res.data?.data) {
      option.xAxis.data = res.data.data.map(r => r.obs_month + '月')
      option.series[0].data = res.data.data.map(r => parseFloat(r.avg_temp))
      option.series[1].data = res.data.data.map(r => parseFloat(r.avg_max))
      option.series[2].data = res.data.data.map(r => parseFloat(r.avg_min))
    }
  } catch(e) {
    error.value = '数据加载失败，请确认后端已启动'
    console.error(e)
  } finally { loading.value = false }
}

onMounted(load)
</script>

<style scoped>
.page-title{font-size:22px;font-weight:bold;color:#1a237e;margin-bottom:20px}
.chart-card{background:#fff;border-radius:10px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.chart-title{font-size:16px;font-weight:bold;color:#333;margin-bottom:12px}
</style>
