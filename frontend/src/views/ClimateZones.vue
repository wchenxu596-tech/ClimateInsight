<template>
  <div>
    <h2 class="page-title">🗺️ 气候带分析</h2>
    <div class="chart-row">
      <div class="chart-card" style="flex:1">
        <v-chart :option="pieOption" style="height:400px" autoresize />
      </div>
      <div class="chart-card" style="flex:1">
        <el-empty description="全球气象站分布地图" v-if="true">
          <p style="color:#888">地理可视化需接入地图组件</p>
        </el-empty>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, PieChart, TooltipComponent, LegendComponent])

import { getZones } from '../api'

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

onMounted(async () => {
  try {
    const res = await getZones()
    if (res.data?.data) {
      const zoneCN = { tropical:'热带', temperate:'温带', continental:'大陆性', polar:'寒带', arid:'干旱' }
      const colors = { tropical: '#e53935', temperate: '#43a047', continental: '#1e88e5', polar: '#8e24aa', arid: '#fb8c00' }
      pieOption.series[0].data = res.data.data.map(r => ({
        name: zoneCN[r.climate_zone] || r.climate_zone, value: parseInt(r.cnt),
        itemStyle: { color: colors[r.climate_zone] || '#999' }
      }))
    }
  } catch(e) { console.error(e) }
})
</script>

<style scoped>
.page-title{font-size:22px;font-weight:bold;color:#1a237e;margin-bottom:20px}
.chart-row{display:flex;gap:16px}
.chart-card{flex:1;background:#fff;border-radius:10px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
</style>
