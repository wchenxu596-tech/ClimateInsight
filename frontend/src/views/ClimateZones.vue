<template>
  <div>
    <h2 class="page-title">🗺️ 气候带分析 — 2024</h2>

    <!-- Loading -->
    <el-skeleton v-if="loading" :rows="6" animated />

    <!-- Error -->
    <el-alert v-else-if="error" :title="error" type="error" show-icon closable @close="error='';load()">
      <el-button type="primary" size="small" @click="load()">重试</el-button>
    </el-alert>

    <!-- Data -->
    <template v-else>
      <div class="chart-row">
        <div class="chart-card" style="flex:1">
          <v-chart v-if="hasData" :option="pieOption" style="height:400px" autoresize />
          <el-empty v-else description="暂无气候带数据" />
        </div>
        <div class="chart-card" style="flex:1">
          <el-empty description="全球气象站分布地图">
            <p style="color:#888;font-size:13px">地理可视化需接入地图组件</p>
          </el-empty>
        </div>
      </div>
      <p class="data-note">数据来源: NOAA GSOD 2024 | 仅含 2024 年数据</p>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, PieChart, TooltipComponent, LegendComponent])

import { getZones } from '../api'

const loading = ref(true)
const error = ref('')
const hasData = ref(false)

const pieOption = reactive({
  tooltip: { trigger: 'item', formatter: '{b}: {c} 站 ({d}%)' },
  legend: { orient: 'vertical', left: 'left' },
  series: [{
    type: 'pie', radius: ['30%', '65%'], center: ['50%', '50%'],
    label: { formatter: '{b}\n{d}%' },
    data: [],
    itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 }
  }]
})

async function load() {
  loading.value = true; error.value = ''; hasData.value = false
  try {
    const res = await getZones()
    if (res.data?.data && res.data.data.length > 0) {
      const zoneCN = { tropical: '热带', temperate: '温带', continental: '大陆性', polar: '寒带', arid: '干旱' }
      const colors = { tropical: '#e53935', temperate: '#43a047', continental: '#1e88e5', polar: '#8e24aa', arid: '#fb8c00' }
      pieOption.series[0].data = res.data.data.map(r => ({
        name: zoneCN[r.climate_zone] || r.climate_zone, value: parseInt(r.cnt),
        itemStyle: { color: colors[r.climate_zone] || '#999' }
      }))
      hasData.value = true
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
.chart-row{display:flex;gap:16px;flex-wrap:wrap}
.chart-card{flex:1;min-width:320px;background:#fff;border-radius:10px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.data-note{color:#888;font-size:12px;margin-top:12px;text-align:center}
</style>
