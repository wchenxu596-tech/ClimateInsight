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

        <!-- 3:1 左右两栏 -->
        <div class="alert-body">
          <!-- 左侧 75%：预警站点排名 + 月度极端事件趋势 -->
          <div class="alert-left">
            <GlassCard class="alert-table-card">
              <div class="card-hd">⚠️ 预警站点排名</div>
              <div class="table-wrap">
                <el-table :data="stations" border stripe size="small" style="width:100%">
                  <el-table-column label="等级" align="center">
                    <template #default="{row}">
                      <span :class="['alert-badge', row.alert_level]">{{ row.alert_label }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="气象站">
                    <template #default="{row}">
                      <router-link :to="`/stations/${row.station_id}`" class="station-link">{{ stationCN(row.station_name) }}</router-link>
                    </template>
                  </el-table-column>
                  <el-table-column label="气候带" align="center">
                    <template #default="{row}">{{ zoneCN[row.climate_zone] || row.climate_zone }}</template>
                  </el-table-column>
                  <el-table-column label="风险分" align="center">
                    <template #default="{row}">
                      <div class="risk-bar-wrap">
                        <div class="risk-bar" :class="row.alert_level" :style="{width: row.risk_score+'%'}"></div>
                        <span class="risk-num">{{ row.risk_score }}</span>
                      </div>
                    </template>
                  </el-table-column>
                  <el-table-column label="🔥极端" align="center"><template #default="{row}">{{ row.extreme }}</template></el-table-column>
                  <el-table-column label="🌡️热浪" align="center"><template #default="{row}">{{ row.heat_wave }}</template></el-table-column>
                  <el-table-column label="❄️寒潮" align="center"><template #default="{row}">{{ row.cold_wave }}</template></el-table-column>
                </el-table>
              </div>
            </GlassCard>

            <GlassCard class="alert-chart-card">
              <div class="card-hd">📊 月度极端事件趋势</div>
              <v-chart :option="monthlyOption" autoresize style="flex:1;min-height:0" />
            </GlassCard>
          </div>

          <!-- 右侧 25%：极端天气应对措施推荐 -->
          <div class="alert-right">
            <GlassCard class="ar-measures-card">
              <div class="card-hd">🛡️ 极端天气应对措施</div>
              <div class="ar-measures-list">
                <!-- 热浪 -->
                <div class="ar-mgroup" :class="{ open: openGroups.has('heat') }">
                  <div class="ar-mg-header" @click="toggleGroup('heat')">
                    <span class="ar-mg-icon">🌡️</span>
                    <span class="ar-mg-title">热浪</span>
                    <span class="ar-mg-severity" :class="weatherSeverity.heat">● {{ severityLabel(weatherSeverity.heat) }}</span>
                    <span class="ar-mg-arrow">▾</span>
                  </div>
                  <div class="ar-mg-body">
                    <div class="ar-measure severity-red">
                      <div class="ar-m-label">🔴 红色预警响应</div>
                      <p class="ar-m-text">发布高温红色预警；启动城市应急响应预案；开放公共避暑中心；停止一切户外作业和大型活动；保障医院急救资源充足；对 elderly 和弱势群体进行逐户排查。</p>
                    </div>
                    <div class="ar-measure severity-orange">
                      <div class="ar-m-label">🟠 橙色预警响应</div>
                      <p class="ar-m-text">加强高温监测与预警发布频率；建议减少户外活动至每日 4 小时内；保障城市供水供电系统满负荷运转；学校可调整上下学时间避开正午高温。</p>
                    </div>
                    <div class="ar-measure severity-yellow">
                      <div class="ar-m-label">🟡 黄色预警响应</div>
                      <p class="ar-m-text">关注每日高温预报；注意防暑降温、补充水分；避免 11:00-15:00 期间长时间户外暴露；检查空调和通风设备运转状态。</p>
                    </div>
                  </div>
                </div>

                <!-- 雷暴 -->
                <div class="ar-mgroup" :class="{ open: openGroups.has('thunder') }">
                  <div class="ar-mg-header" @click="toggleGroup('thunder')">
                    <span class="ar-mg-icon">⛈️</span>
                    <span class="ar-mg-title">雷暴</span>
                    <span class="ar-mg-severity" :class="weatherSeverity.thunder">● {{ severityLabel(weatherSeverity.thunder) }}</span>
                    <span class="ar-mg-arrow">▾</span>
                  </div>
                  <div class="ar-mg-body">
                    <div class="ar-measure severity-red">
                      <div class="ar-m-label">🔴 红色预警响应</div>
                      <p class="ar-m-text">发布雷电红色预警；立即停止所有户外活动和生产作业；组织低洼区域人员紧急转移；关闭各类电子设备和通信基站；应急救援队伍进入临战状态。</p>
                    </div>
                    <div class="ar-measure severity-orange">
                      <div class="ar-m-label">🟠 橙色预警响应</div>
                      <p class="ar-m-text">加强雷电监测和短时预警；停止高空、水上等危险户外作业；提醒市民远离高大建筑物、树木和金属设施；检查城市排水系统和防雷装置。</p>
                    </div>
                    <div class="ar-measure severity-yellow">
                      <div class="ar-m-label">🟡 黄色预警响应</div>
                      <p class="ar-m-text">关注雷暴天气预报和预警信息；减少不必要出行；避免在开阔地带、山顶和水边停留；拔掉非必要电器插头以防雷击损坏。</p>
                    </div>
                  </div>
                </div>

                <!-- 寒潮 -->
                <div class="ar-mgroup" :class="{ open: openGroups.has('cold') }">
                  <div class="ar-mg-header" @click="toggleGroup('cold')">
                    <span class="ar-mg-icon">❄️</span>
                    <span class="ar-mg-title">寒潮</span>
                    <span class="ar-mg-severity" :class="weatherSeverity.cold">● {{ severityLabel(weatherSeverity.cold) }}</span>
                    <span class="ar-mg-arrow">▾</span>
                  </div>
                  <div class="ar-mg-body">
                    <div class="ar-measure severity-red">
                      <div class="ar-m-label">🔴 红色预警响应</div>
                      <p class="ar-m-text">发布寒潮红色预警；全面启动供暖应急保障方案；对供水管道和户外设施进行防冻保护；确保能源和食品物资供应链稳定；开放临时取暖中心供有需要人群使用。</p>
                    </div>
                    <div class="ar-measure severity-orange">
                      <div class="ar-m-label">🟠 橙色预警响应</div>
                      <p class="ar-m-text">加强降温监测和道路结冰预警；提醒市民大幅度降温即将来临；检查供暖设备和管道保温状态；储备应急除冰物资和融雪剂。</p>
                    </div>
                    <div class="ar-measure severity-yellow">
                      <div class="ar-m-label">🟡 黄色预警响应</div>
                      <p class="ar-m-text">关注降温预报和寒潮动态；及时增添衣物做好保暖；注意室内通风防止一氧化碳中毒；对水管等易冻设施做好基础防护。</p>
                    </div>
                  </div>
                </div>
              </div>
            </GlassCard>
          </div>
        </div>
      </div>
    </PageState>
  </div>
</template>

<script setup>
import { ref, inject, watch, reactive, computed, onUnmounted, nextTick } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])
import { getAlertRisk, getAlertMonthly } from '../api'
import PageState from '../components/PageState.vue'
import GlassCard from '../components/GlassCard.vue'
import { chartColors, baseTooltip, baseGrid, monthLabels } from '../composables/useDashboardTheme'
import { stationCN } from '../utils/stationNames'
import api from '../api'

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

// ── 各天气类型月总值（用于判断严重度） ──
const monthlyTotals = ref({ heat:0, cold:0, thunder:0 })

// ── 严重度计算 ──
const weatherSeverity = computed(() => {
  const h = monthlyTotals.value.heat
  const t = monthlyTotals.value.thunder
  const c = monthlyTotals.value.cold
  return {
    heat:   h > 8000 ? 'red' : h > 4000 ? 'orange' : 'yellow',
    thunder: t > 3000 ? 'red' : t > 1500 ? 'orange' : 'yellow',
    cold:   c > 5000 ? 'red' : c > 2500 ? 'orange' : 'yellow',
  }
})

function severityLabel(s) {
  return s === 'red' ? '高' : s === 'orange' ? '中' : '低'
}

// ── 手风琴（支持多开）──
const openGroups = ref(new Set(['heat', 'thunder', 'cold']))
function toggleGroup(g) {
  if (openGroups.value.has(g)) openGroups.value.delete(g)
  else openGroups.value.add(g)
  openGroups.value = new Set(openGroups.value)
}

// ── 数据加载 ──
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
      monthlyTotals.value = {
        heat: m.reduce((s, r) => s + (r.heat_wave || 0), 0),
        cold: m.reduce((s, r) => s + (r.cold_wave || 0), 0),
        thunder: m.reduce((s, r) => s + (r.thunder || 0), 0),
      }
    }
  } catch (e) { if (id === requestId) { error.value = '预警数据加载失败'; console.error(e) } }
  finally { if (id === requestId) loading.value = false }
}
watch(selectedYear, load, { immediate: true })
</script>

<style scoped>
.alert-root { display:flex; flex-direction:column; flex:1; min-width:0; min-height:0; gap:8px }
.alert-kpi-row { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; flex-shrink:0; min-width:0 }
.kpi-card { padding:10px 14px; min-height:72px; display:flex; flex-direction:column; justify-content:center }
.kpi-label { font-size:13px; font-weight:500; color:var(--ci-text-muted); margin-bottom:2px }
.kpi-value { font-size:24px; font-weight:700; line-height:1.1 }
.kpi-value.highlight { color:var(--ci-tertiary); font-size:20px }
.kpi-desc { font-size:11px; color:var(--ci-text-muted); margin-top:2px }
.kpi-red .kpi-value { color:#ba1a1a }
.kpi-orange .kpi-value { color:#8b3713 }
.kpi-yellow .kpi-value { color:#b8820e }

/* ── 3:1 左右两栏 ── */
.alert-body { display:grid; grid-template-columns:3fr 1fr; gap:10px; flex:1; min-width:0; min-height:0; overflow:hidden }

/* 左栏 75% */
.alert-left { display:flex; flex-direction:column; gap:8px; min-width:0; min-height:0 }
.alert-left > * { flex:1; min-height:0 }
.alert-table-card { display:flex; flex-direction:column; overflow:hidden; padding:8px }

/* ── 表格独立滚动 + 吸顶表头 ── */
.table-wrap {
  flex:1; min-height:0; overflow-y:auto;
  scrollbar-width: none;
}
.table-wrap::-webkit-scrollbar { display:none }
/* 关键：el-table 默认 overflow:hidden 会阻断 sticky，必须覆盖 */
.table-wrap :deep(.el-table) { overflow:visible }
.table-wrap :deep(.el-table__header-wrapper) {
  position: sticky; top: 0; z-index: 3;
}
.table-wrap :deep(.el-table__header-wrapper) th {
  background: rgb(235 240 236) !important;
}

.alert-chart-card { display:flex; flex-direction:column; overflow:hidden; padding:8px }

/* 右栏 25% */
.alert-right { display:flex; flex-direction:column; gap:8px; min-width:0; min-height:0; overflow:hidden }

.card-hd { font-size:15px; font-weight:600; color:var(--ci-primary); padding:2px 4px 0; flex-shrink:0 }

/* ── 应对措施卡片 ── */
.ar-measures-card { padding:10px; flex:1; min-height:0; display:flex; flex-direction:column; overflow:hidden }
.ar-measures-list { flex:1; overflow-y:auto; scrollbar-width:none; margin-top:4px }
.ar-measures-list::-webkit-scrollbar { display:none }

/* 手风琴组 */
.ar-mgroup {
  margin-bottom:10px; border-radius:10px; overflow:hidden;
  border: 1px solid var(--ci-outline-variant);
  background: rgb(250 249 247 / 50%);
  transition: all .3s var(--ci-ease-out);
}
.ar-mgroup.open { border-color: var(--ci-primary); box-shadow: 0 2px 12px rgb(20 66 45 / 8%); }

.ar-mg-header {
  display:flex; align-items:center; gap:8px; padding:10px 12px;
  cursor:pointer; user-select:none;
  transition: background .2s;
}
.ar-mg-header:hover { background: rgb(58 103 79 / 6%); }
.ar-mg-icon { font-size:20px; flex-shrink:0 }
.ar-mg-title { font-size:14px; font-weight:600; color:var(--ci-text); flex:1; min-width:0 }
.ar-mg-severity { font-size:11px; font-weight:500; white-space:nowrap; flex-shrink:0 }
.ar-mg-severity.red { color:#ba1a1a }
.ar-mg-severity.orange { color:#c26a2a }
.ar-mg-severity.yellow { color:#8a7d14 }
.ar-mg-arrow {
  font-size:12px; color:var(--ci-text-muted); flex-shrink:0;
  transition: transform .3s var(--ci-ease-out);
}
.ar-mgroup.open .ar-mg-arrow { transform: rotate(180deg); }

/* 手风琴展开区域 */
.ar-mg-body {
  max-height:0; overflow:hidden;
  transition: max-height .4s var(--ci-ease-out);
}
.ar-mgroup.open .ar-mg-body { max-height:700px; padding-bottom:6px; }

/* 措施项 */
.ar-measure {
  margin:0 10px 10px; padding:12px 12px; border-radius:8px;
  border-left: 3px solid;
}
.ar-measure.severity-red {
  background: #ffdbce; border-left-color: #ba1a1a;
}
.ar-measure.severity-orange {
  background: #fff3e0; border-left-color: #c26a2a;
}
.ar-measure.severity-yellow {
  background: #fffde7; border-left-color: #b89a20;
}
.ar-m-label { font-size:12px; font-weight:600; color:var(--ci-text); margin-bottom:5px }
.ar-m-text {
  font-size:11px; color:var(--ci-text-muted); margin:0;
  line-height:1.7; text-indent:1em;
}

/* 复用 */
.alert-badge { display:inline-block; padding:2px 8px; border-radius:10px; font-size:12px; font-weight:600; white-space:nowrap }
.alert-badge.red { background:#ba1a1a20; color:#ba1a1a }
.alert-badge.orange { background:#8b371320; color:#8b3713 }
.alert-badge.yellow { background:#b8820e20; color:#b8820e }
.alert-badge.blue { background:#39656b20; color:#39656b }
.station-link { color:var(--ci-primary); text-decoration:none; font-weight:500; font-size:12px }
.station-link:hover { text-decoration:underline }
.risk-bar-wrap { position:relative; width:100%; height:16px; display:flex; align-items:center }
.risk-bar { height:10px; border-radius:5px; transition:width .4s; min-width:3px }
.risk-bar.red { background:linear-gradient(90deg,#ba1a1a,#e84a4a) }
.risk-bar.orange { background:linear-gradient(90deg,#8b3713,#cc5533) }
.risk-bar.yellow { background:linear-gradient(90deg,#b8820e,#e8b030) }
.risk-bar.blue { background:linear-gradient(90deg,#39656b,#5a8f96) }
.risk-num { position:absolute; right:1px; font-size:9px; font-weight:600; color:var(--ci-text) }

@media (max-width: 1023px) {
  .alert-kpi-row { grid-template-columns:repeat(2,1fr) }
  .alert-body { grid-template-columns:1fr }
}
</style>
