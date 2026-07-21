<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="暂无排名数据" @retry="load">
      <div class="ranking-header">
        <div>
          <h1 class="page-h1">{{ selectedYear }} 年全球站点排名</h1>
          <p class="page-sub">基于 NOAA GSOD 年度聚合数据</p>
        </div>
        <div class="cat-tabs" role="tablist">
          <button v-for="cat in categories" :key="cat.key" role="tab" :aria-selected="category === cat.key"
            :class="['cat-btn', { active: category === cat.key }]" @click="category = cat.key; load()">
            {{ cat.label }}
          </button>
        </div>
      </div>

      <!-- 图表 -->
      <ChartPanel :title="meta.title" :subtitle="'单位：' + meta.unit" :min-height="'540px'" style="margin-bottom:var(--ci-gap)">
        <v-chart v-if="hasData" :option="chartOption" style="height:460px" autoresize />
        <el-empty v-else description="暂无数据" />
      </ChartPanel>

      <!-- 明细表 -->
      <GlassCard>
        <div style="padding:20px">
          <div class="cp-title">详细数据</div>
        </div>
        <el-table :data="tableData" border stripe size="small" style="width:100%">
          <el-table-column prop="rank_num" label="排名" width="70" align="center">
            <template #default="{ row }">
              <span :style="{ fontWeight: row.rank_num === 1 ? 'bold' : '', color: row.rank_num === 1 ? 'var(--ci-tertiary)' : '' }">#{{ row.rank_num }}</span>
            </template>
          </el-table-column>
          <el-table-column label="站点名称" min-width="180">
            <template #default="{ row }">{{ stationCN(row.station_name || '') }}</template>
          </el-table-column>
          <el-table-column prop="station_id" label="站点 ID" width="140" />
          <el-table-column :label="meta.label + '(' + meta.unit + ')'" width="140" align="right">
            <template #default="{ row }">{{ safeNumber(row.value)?.toFixed(2) ?? '--' }}</template>
          </el-table-column>
        </el-table>
      </GlassCard>
    </PageState>
  </div>
</template>

<script setup>
import { ref, reactive, inject, watch, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
use([CanvasRenderer, BarChart, GridComponent, TooltipComponent])

import { getRanking } from '../api'
import { stationCN } from '../utils/stationNames'
import PageState from '../components/PageState.vue'
import GlassCard from '../components/GlassCard.vue'
import ChartPanel from '../components/ChartPanel.vue'
import { chartColors, baseTooltip, baseGrid, safeNumber } from '../composables/useDashboardTheme'

const selectedYear = inject('selectedYear')
const loading = ref(true)
const error = ref('')
const empty = ref(false)
const hasData = ref(false)
let requestId = 0

const category = ref('hottest')
const categories = [
  { key: 'hottest', label: '🔥 最高温' },
  { key: 'coldest', label: '❄️ 最低温' },
  { key: 'rainiest', label: '🌧️ 最多降水' },
  { key: 'most_extreme', label: '⚠️ 极端天气' },
]
const metaMap = {
  hottest: { label: '最高温', unit: '°C', title: '最高温站点 TOP 15' },
  coldest: { label: '最低温', unit: '°C', title: '最低温站点 TOP 15' },
  rainiest: { label: '最多降水', unit: 'mm', title: '最多降水站点 TOP 15' },
  most_extreme: { label: '极端天气', unit: '天', title: '极端天气站点 TOP 15' },
}
const meta = computed(() => metaMap[category.value])

const chartOption = reactive({ tooltip: baseTooltip(), grid: baseGrid(), xAxis: { type:'category', data:[], axisLabel:{color:chartColors.text, rotate:25, width:80, overflow:'truncate'}, axisLine:{lineStyle:{color:chartColors.outline}} }, yAxis: { type:'value', name:'', axisLabel:{color:chartColors.text}, splitLine:{lineStyle:{color:chartColors.grid}} }, series: [{ type:'bar', data:[], barMaxWidth:44, itemStyle:{ borderRadius:[6,6,0,0], color: { type:'linear', x:0,y:0,x2:0,y2:1, colorStops:[{offset:0,color:chartColors.primary},{offset:1,color:chartColors.teal}] } } }] })
const tableData = ref([])

async function load() {
  const id = ++requestId
  loading.value = true; error.value = ''; empty.value = false; hasData.value = false
  try {
    const res = await getRanking(selectedYear.value, category.value, 15)
    if (id !== requestId) return
    const rows = (res.data?.data || []).sort((a,b) => a.rank_num - b.rank_num)
    if (!rows.length) { empty.value = true; loading.value = false; return }
    hasData.value = true
    chartOption.xAxis.data = rows.map(r => stationCN(r.station_name || r.station_id).substring(0, 12))
    chartOption.yAxis.name = meta.value.unit
    chartOption.series[0].data = rows.map(r => safeNumber(r.value))
    tableData.value = rows.map(r => ({ ...r, _cn: stationCN(r.station_name || '') }))
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
.ranking-header { display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:16px }
.cat-tabs { display:flex; gap:4px; background:var(--ci-surface-container); border-radius:10px; padding:4px; margin-bottom:24px }
.cat-btn { padding:8px 16px; border:none; border-radius:8px; background:transparent; color:var(--ci-text-muted); font-size:14px; font-weight:500; cursor:pointer; transition:all .2s; white-space:nowrap }
.cat-btn:hover { background:rgb(58 103 79 / 8%) }
.cat-btn.active { background:var(--ci-primary); color:#fff }
.cp-title { font-size:16px; font-weight:600; color:var(--ci-primary) }

@media (max-width: 767px) {
  .ranking-header { flex-direction:column; align-items:flex-start }
  .cat-tabs { overflow-x:auto; width:100% }
}
</style>
