<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="暂无预警数据" @retry="load">
      <div class="alert-root">
        <!-- 顶部 KPI -->
        <div class="alert-kpi-row">
          <GlassCard class="kpi-card kpi-red">
            <div class="kpi-label">🔴 红色预警</div>
            <div class="kpi-value">{{ stats.red_count }}</div>
            <div class="kpi-desc">风险评分 ≥ 60</div>
          </GlassCard>
          <GlassCard class="kpi-card kpi-orange">
            <div class="kpi-label">🟠 橙色预警</div>
            <div class="kpi-value">{{ stats.orange_count }}</div>
            <div class="kpi-desc">风险评分 40-59</div>
          </GlassCard>
          <GlassCard class="kpi-card kpi-yellow">
            <div class="kpi-label">🟡 黄色预警</div>
            <div class="kpi-value">{{ stats.yellow_count }}</div>
            <div class="kpi-desc">风险评分 20-39</div>
          </GlassCard>
          <GlassCard class="kpi-card kpi-top">
            <div class="kpi-label">🏆 最高风险</div>
            <div class="kpi-value highlight">{{ stats.top_risk }}</div>
            <div class="kpi-desc">{{ stats.top_station }}</div>
          </GlassCard>
        </div>

        <!-- 预警排名表 + 月度趋势 -->
        <div class="alert-body">
          <GlassCard class="alert-table-card">
            <div class="card-hd">⚠️ 预警站点排名</div>
            <el-table :data="stations" border stripe size="small" max-height="480" style="width:100%">
              <el-table-column label="风险等级" width="110" align="center">
                <template #default="{row}">
                  <span :class="['alert-badge', row.alert_level]">{{ row.alert_label }}</span>
                </template>
              </el-table-column>
              <el-table-column label="气象站" min-width="150">
                <template #default="{row}">
                  <router-link :to="`/stations/${row.station_id}`" class="station-link">{{ row.station_name }}</router-link>
                </template>
              </el-table-column>
              <el-table-column label="气候带" width="80" align="center">
                <template #default="{row}">{{ zoneCN[row.climate_zone] || row.climate_zone }}</template>
              </el-table-column>
              <el-table-column label="风险分" width="80" align="center">
                <template #default="{row}">
                  <div class="risk-bar-wrap">
                    <div class="risk-bar" :class="row.alert_level" :style="{width: row.risk_score+'%'}"></div>
                    <span class="risk-num">{{ row.risk_score }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="极端🔥" width="55" align="center">
                <template #default="{row}">{{ row.extreme }}</template>
              </el-table-column>
              <el-table-column label="热浪🌡️" width="55" align="center">
                <template #default="{row}">{{ row.heat_wave }}</template>
              </el-table-column>
              <el-table-column label="寒潮❄️" width="55" align="center">
                <template #default="{row}">{{ row.cold_wave }}</template>
              </el-table-column>
              <el-table-column label="雷暴⛈️" width="55" align="center">
                <template #default="{row}">{{ row.thunder }}</template>
              </el-table-column>
              <el-table-column label="霜冻" width="50" align="center">
                <template #default="{row}">{{ row.frost }}</template>
              </el-table-column>
              <el-table-column label="暴雪" width="50" align="center">
                <template #default="{row}">{{ row.snow }}</template>
              </el-table-column>
            </el-table>
          </GlassCard>

          <GlassCard class="alert-chart-card">
            <div class="card-hd">📊 月度极端事件趋势</div>
            <v-chart :option="monthlyOption" autoresize style="flex:1;min-height:0" />
          </GlassCard>
        </div>
      </div>
    </PageState>
  </div>
</template>

<script setup>
import { ref, inject, watch, reactive } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent])
import { getAlertRisk, getAlertMonthly } from '../api'
import PageState from '../components/PageState.vue'
import GlassCard from '../components/GlassCard.vue'
import { chartColors, baseTooltip, baseGrid, monthLabels } from '../composables/useDashboardTheme'

const selectedYear = inject('selectedYear')
const loading = ref(true); const error = ref(''); const empty = ref(false)
let requestId = 0

const stats = ref({ red_count:0, orange_count:0, yellow_count:0, blue_count:0, top_risk:0, top_station:'' })
const stations = ref([])

const zoneCN = { tropical:'热带', temperate:'温带', continental:'大陆性', polar:'寒带', arid:'干旱' }

const monthlyOption = reactive({
  tooltip: { ...baseTooltip(), trigger:'axis' },
  legend: { data:['热浪','寒潮','极端','雷暴'], textStyle:{color:chartColors.text,fontSize:10}, top:0, itemWidth:12, itemHeight:8 },
  grid: { ...baseGrid(), top:'16%' },
  xAxis: { type:'category', data:monthLabels, axisLabel:{color:chartColors.text,fontSize:10}, axisLine:{lineStyle:{color:chartColors.outline}} },
  yAxis: { type:'value', name:'事件数', axisLabel:{color:chartColors.text,fontSize:9}, splitLine:{lineStyle:{color:chartColors.grid}} },
  series: [
    { name:'热浪', type:'bar', stack:'total', barMaxWidth:16, itemStyle:{color:'#8b3713'}, data:[] },
    { name:'寒潮', type:'bar', stack:'total', barMaxWidth:16, itemStyle:{color:'#39656b'}, data:[] },
    { name:'极端', type:'bar', stack:'total', barMaxWidth:16, itemStyle:{color:'#ba1a1a'}, data:[] },
    { name:'雷暴', type:'bar', stack:'total', barMaxWidth:16, itemStyle:{color:'#717973'}, data:[] },
  ]
})

async function load() {
  const id = ++requestId
  loading.value = true; error.value = ''; empty.value = false
  try {
    const [riskRes, monRes] = await Promise.all([
      getAlertRisk(selectedYear.value, 200),
      getAlertMonthly(selectedYear.value),
    ])
    if (id !== requestId) return

    const riskData = riskRes.data?.data
    if (!riskData?.stations?.length) { empty.value = true; loading.value = false; return }

    stats.value = riskData.stats
    stations.value = riskData.stations

    if (monRes.data?.data) {
      const m = monRes.data.data
      monthlyOption.series[0].data = m.map(r => r.heat_wave)
      monthlyOption.series[1].data = m.map(r => r.cold_wave)
      monthlyOption.series[2].data = m.map(r => r.extreme)
      monthlyOption.series[3].data = m.map(r => r.thunder)
    }
  } catch (e) { if (id === requestId) { error.value = '预警数据加载失败'; console.error(e) } }
  finally { if (id === requestId) loading.value = false }
}
watch(selectedYear, load, { immediate: true })
</script>

<style scoped>
.alert-root { display:flex; flex-direction:column; flex:1; min-height:0; gap:8px }
.alert-kpi-row { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; flex-shrink:0 }
.kpi-card { padding:10px 14px; min-height:72px; display:flex; flex-direction:column; justify-content:center }
.kpi-label { font-size:12px; font-weight:500; text-transform:uppercase; letter-spacing:0.05em; color:var(--ci-text-muted); margin-bottom:2px }
.kpi-value { font-size:24px; font-weight:700; line-height:1.1 }
.kpi-value.highlight { color:var(--ci-tertiary) }
.kpi-desc { font-size:10px; color:var(--ci-text-muted); margin-top:2px }
.kpi-red .kpi-value { color:#ba1a1a }
.kpi-orange .kpi-value { color:#8b3713 }
.kpi-yellow .kpi-value { color:#b8820e }

.alert-body { display:grid; grid-template-columns:1fr 1fr; gap:10px; flex:1; min-height:0; overflow:hidden }
.alert-table-card { display:flex; flex-direction:column; overflow:hidden; padding:0 0 4px }
.alert-chart-card { display:flex; flex-direction:column; overflow:hidden; padding:8px }

.card-hd { font-size:15px; font-weight:600; color:var(--ci-primary); padding:8px 12px 4px; flex-shrink:0 }

.alert-badge { display:inline-block; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; white-space:nowrap }
.alert-badge.red { background:#ba1a1a20; color:#ba1a1a }
.alert-badge.orange { background:#8b371320; color:#8b3713 }
.alert-badge.yellow { background:#b8820e20; color:#b8820e }
.alert-badge.blue { background:#39656b20; color:#39656b }

.station-link { color:var(--ci-primary); text-decoration:none; font-weight:500 }
.station-link:hover { text-decoration:underline }

.risk-bar-wrap { position:relative; width:100%; height:18px; display:flex; align-items:center }
.risk-bar { height:12px; border-radius:6px; transition:width .4s ease; min-width:4px }
.risk-bar.red { background:linear-gradient(90deg,#ba1a1a,#e84a4a) }
.risk-bar.orange { background:linear-gradient(90deg,#8b3713,#cc5533) }
.risk-bar.yellow { background:linear-gradient(90deg,#b8820e,#e8b030) }
.risk-bar.blue { background:linear-gradient(90deg,#39656b,#5a8f96) }
.risk-num { position:absolute; right:2px; font-size:10px; font-weight:600; color:var(--ci-text) }

@media (max-width: 1023px) {
  .alert-kpi-row { grid-template-columns:repeat(2,1fr) }
  .alert-body { grid-template-columns:1fr }
}
</style>
