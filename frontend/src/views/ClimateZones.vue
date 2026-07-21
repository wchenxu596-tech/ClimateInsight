<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="暂无气候带数据" @retry="load">
      <h1 class="page-h1">{{ selectedYear }} 年气候带分布</h1>
      <p class="page-sub">按气象站所属气候带统计</p>

      <div class="zones-grid">
        <!-- 环形图 -->
        <ChartPanel title="气候带占比" :min-height="'520px'">
          <v-chart v-if="hasData" :option="pieOption" style="height:440px" autoresize />
          <el-empty v-else description="暂无数据" />
        </ChartPanel>

        <!-- 统计列表 -->
        <GlassCard class="zones-list-card">
          <div class="zl-header">各气候带统计</div>
          <div class="zl-rows">
            <div v-for="z in zoneStats" :key="z.name" class="zl-row">
              <span class="zl-dot" :style="{ background: z.color }"></span>
              <span class="zl-name">{{ z.name }}</span>
              <span class="zl-count">{{ z.cnt }} 站</span>
              <span class="zl-pct">{{ z.pct }}</span>
            </div>
          </div>
          <div class="zl-footer">数据来源：NOAA GSOD，按站点年度气候带归类</div>
        </GlassCard>
      </div>
    </PageState>
  </div>
</template>

<script setup>
import { ref, reactive, inject, watch, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, PieChart, TooltipComponent, LegendComponent])

import { getZones } from '../api'
import PageState from '../components/PageState.vue'
import GlassCard from '../components/GlassCard.vue'
import ChartPanel from '../components/ChartPanel.vue'
import { chartColors, zoneColors, zoneCN } from '../composables/useDashboardTheme'

const selectedYear = inject('selectedYear')
const loading = ref(true)
const error = ref('')
const empty = ref(false)
const hasData = ref(false)
let requestId = 0

const pieOption = reactive({
  tooltip: { trigger:'item', backgroundColor:'rgba(255,255,255,0.95)', borderColor:chartColors.outline, textStyle:{color:chartColors.text}, formatter:'{b}: {c} 站 ({d}%)' },
  legend: { bottom:0, textStyle:{color:chartColors.text} },
  series: [{ type:'pie', radius:['50%','75%'], label:{show:false}, emphasis:{label:{show:true,fontSize:18,fontWeight:'bold',color:chartColors.primary}}, labelLine:{show:false}, data:[], itemStyle:{borderRadius:8,borderColor:'#fff',borderWidth:3} }]
})

const zoneStats = ref([])

async function load() {
  const id = ++requestId
  loading.value = true; error.value = ''; empty.value = false; hasData.value = false
  try {
    const res = await getZones(selectedYear.value)
    if (id !== requestId) return
    const rows = res.data?.data || []
    if (!rows.length) { empty.value = true; loading.value = false; return }
    hasData.value = true

    const total = rows.reduce((s, r) => s + (parseInt(r.cnt) || 0), 0)
    zoneStats.value = rows
      .filter(r => zoneCN[r.climate_zone])
      .map(r => {
        const cnt = parseInt(r.cnt) || 0
        return {
          name: zoneCN[r.climate_zone],
          cnt,
          pct: total > 0 ? (cnt / total * 100).toFixed(1) + '%' : '--',
          color: zoneColors[r.climate_zone] || '#999',
        }
      })

    pieOption.series[0].data = rows
      .filter(r => zoneCN[r.climate_zone])
      .map(r => ({
        name: zoneCN[r.climate_zone],
        value: parseInt(r.cnt) || 0,
        itemStyle: { color: zoneColors[r.climate_zone] || '#999' }
      }))
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
.page-sub { color:var(--ci-text-muted); font-size:15px; margin-top:-16px; margin-bottom:24px }
.zones-grid { display:grid; grid-template-columns:minmax(0, 7fr) minmax(300px, 5fr); gap:var(--ci-gap) }
.zones-list-card { padding:24px; display:flex; flex-direction:column; min-height:520px }
.zl-header { font-size:18px; font-weight:600; color:var(--ci-primary); margin-bottom:20px }
.zl-rows { flex:1; display:flex; flex-direction:column; gap:12px }
.zl-row { display:flex; align-items:center; gap:10px }
.zl-dot { width:12px; height:12px; border-radius:50%; flex-shrink:0 }
.zl-name { font-size:15px; font-weight:500; flex:1; color:var(--ci-text) }
.zl-count { font-size:14px; color:var(--ci-text-muted) }
.zl-pct { font-size:14px; font-weight:600; color:var(--ci-primary); width:50px; text-align:right }
.zl-footer { font-size:12px; color:var(--ci-text-muted); margin-top:16px; padding-top:12px; border-top:1px solid var(--ci-outline-variant) }

@media (max-width: 767px) {
  .zones-grid { grid-template-columns:1fr }
}
</style>
