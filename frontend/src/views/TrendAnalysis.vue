<template>
  <div>
    <h2 class="page-title">📈 {{ selectedYear }} 年月度气温变化</h2>

    <!-- Loading -->
    <el-skeleton v-if="loading" :rows="6" animated />

    <!-- Error -->
    <el-alert v-else-if="error" :title="error" type="error" show-icon closable @close="error='';load()">
      <el-button type="primary" size="small" @click="load()">重试</el-button>
    </el-alert>

    <!-- Data -->
    <template v-else>
      <div class="chart-card">
        <div class="chart-title">🌡️ 各月平均温度（°C）</div>
        <v-chart v-if="hasData" :option="option" style="height:400px" autoresize />
        <el-empty v-else description="暂无月度数据" />
      </div>
      <p class="data-note">数据来源: NOAA GSOD {{ selectedYear }} | 同比趋势请切换年份对比</p>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, inject, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent])
import { getMonthly } from '../api'

const selectedYear = inject('selectedYear')
const loading = ref(true)
const error = ref('')
const hasData = ref(false)
const option = reactive({
  tooltip: { trigger: 'axis', valueFormatter: v => typeof v === 'number' ? v.toFixed(2) : v },
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
  loading.value = true; error.value = ''; hasData.value = false
  try {
    const res = await getMonthly(selectedYear.value)
    if (res.data?.data && res.data.data.length > 0) {
      option.xAxis.data = res.data.data.map(r => r.obs_month + '月')
      option.series[0].data = res.data.data.map(r => parseFloat(r.avg_temp))
      option.series[1].data = res.data.data.map(r => parseFloat(r.avg_max))
      option.series[2].data = res.data.data.map(r => parseFloat(r.avg_min))
      hasData.value = true
    }
  } catch(e) {
    error.value = '数据加载失败，请确认后端已启动'
    console.error(e)
  } finally { loading.value = false }
}

watch(selectedYear, load)
onMounted(load)
</script>

<style scoped>
.page-title{font-size:22px;font-weight:bold;color:#1a237e;margin-bottom:20px}
.chart-card{background:#fff;border-radius:10px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.chart-title{font-size:16px;font-weight:bold;color:#333;margin-bottom:12px}
.data-note{color:#888;font-size:12px;margin-top:8px;text-align:center}
</style>
