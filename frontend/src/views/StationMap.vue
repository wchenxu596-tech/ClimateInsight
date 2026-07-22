<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="暂无站点数据" @retry="load">
      <div class="map-root">
        <!-- 筛选栏 -->
        <div class="map-filter">
          <div class="map-stat">🌍 {{ total }} 个气象站</div>
          <div class="filter-tags">
            <el-tag v-for="z in zoneList" :key="z.key"
              :type="filterZone === z.key ? '' : 'info'"
              :color="filterZone === z.key ? z.color : ''"
              effect="plain" size="small"
              style="cursor:pointer;margin:2px;border:none;color:#fff"
              @click="filterZone = (filterZone === z.key) ? '' : z.key">
              {{ z.label }}
            </el-tag>
          </div>
          <div class="filter-legend">
            <span v-for="z in zoneList" :key="z.key" class="legend-item">
              <span class="legend-dot" :style="{background:z.color}"></span>{{ z.label }}
            </span>
          </div>
        </div>

        <!-- 图表区 -->
        <GlassCard class="map-chart-card">
          <v-chart ref="chartRef" :option="chartOption" autoresize style="flex:1;min-height:0" @click="onChartClick" />
        </GlassCard>

        <!-- 选中站点详情浮窗 -->
        <Transition name="fade">
          <GlassCard v-if="selected" class="map-popup">
            <div class="popup-hd">
              <span class="popup-name">{{ selected.station_name }}</span>
              <button class="popup-close" @click="selected=null">✕</button>
            </div>
            <div class="popup-body">
              <div class="popup-row"><span class="popup-label">气候带</span><span>{{ zoneCN[selected.climate_zone] }}</span></div>
              <div class="popup-row"><span class="popup-label">年均温</span><span class="popup-val">{{ selected.avg_temp }}°C</span></div>
              <div class="popup-row"><span class="popup-label">年降水</span><span class="popup-val">{{ selected.total_precip }} mm</span></div>
              <div class="popup-row"><span class="popup-label">极端事件</span><span class="popup-val">{{ selected.risk_events }} 天</span></div>
              <router-link :to="`/stations/${selected.station_id}`" class="popup-link" @click="saveMapState">查看详情 →</router-link>
            </div>
          </GlassCard>
        </Transition>
      </div>
    </PageState>
  </div>
</template>

<script setup>
import { ref, inject, watch, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import VChart from 'vue-echarts'
import { use, registerMap } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { ScatterChart } from 'echarts/charts'
import { GeoComponent, TooltipComponent } from 'echarts/components'
use([CanvasRenderer, ScatterChart, GeoComponent, TooltipComponent])

import worldJson from '../assets/map/world.json'
registerMap('world', worldJson)

import { getStations } from '../api'
import PageState from '../components/PageState.vue'
import GlassCard from '../components/GlassCard.vue'
import { baseTooltip } from '../composables/useDashboardTheme'

const router = useRouter()
const selectedYear = inject('selectedYear')
const loading = ref(true); const error = ref(''); const empty = ref(false)
const chartRef = ref(null); let requestId = 0

const allStations = ref([])
const selected = ref(null)
const filterZone = ref('')
const total = ref(0)

const zoneCN = { tropical:'热带', temperate:'温带', continental:'大陆性', polar:'寒带', arid:'干旱' }
const zoneColors = { tropical:'#8b3713', temperate:'#3a674f', continental:'#39656b', polar:'#c0c9c1', arid:'#bdeaf2' }
const zoneList = Object.entries(zoneColors).map(([k, c]) => ({ key: k, label: zoneCN[k], color: c }))

const filtered = computed(() => {
  if (!filterZone.value) return allStations.value
  return allStations.value.filter(s => s.climate_zone === filterZone.value)
})

const chartOption = reactive({
  tooltip: {
    ...baseTooltip(),
    formatter: (p) => {
      const d = p.data
      if (!d) return ''
      return `<strong>${d.name || '未知'}</strong><br/>
              气温: ${d.avgTemp ?? '--'}°C &nbsp; 降水: ${d.precip ?? '--'}mm<br/>
              气候带: ${zoneCN[d.zone] || d.zone || '--'}`
    }
  },
  geo: {
    map: 'world',
    roam: false,
    left: '2%', right: '2%', top: '2%', bottom: '2%',
    silent: true,
    itemStyle: {
      areaColor: '#ebe4da',
      borderColor: '#cdc2b2',
      borderWidth: 0.5,
    },
    emphasis: {
      itemStyle: { areaColor: '#e0d6c8' },
      label: { show: false },
    },
    label: { show: false },
  },
  series: [{
    type: 'scatter',
    coordinateSystem: 'geo',
    symbolSize: 5,
    data: [],
    emphasis: { itemStyle: { borderColor: '#14422d', borderWidth: 2 } },
  }],
})

function updateChart() {
  const data = filtered.value.map(s => ({
    value: [s.lon, s.lat],
    risk: s.risk_events || 0,
    zone: s.climate_zone,
    name: s.station_name,
    avgTemp: s.avg_temp,
    precip: s.total_precip,
    sid: s.station_id,
    symbolSize: Math.max(3, Math.min(8, ((s.risk_events||0) / 10) + 3)),
    itemStyle: { color: zoneColors[s.climate_zone] || '#999', opacity: 0.7 },
  }))
  chartOption.series[0].data = data
}

watch(filtered, updateChart, { deep: true })

function onChartClick(params) {
  const d = params.data
  if (!d) return
  selected.value = {
    station_id:   d.sid,
    station_name: d.name,
    climate_zone: d.zone,
    avg_temp:     d.avgTemp,
    total_precip: d.precip,
    risk_events:  d.risk,
  }
}

function saveMapState() {
  if (!selected.value) return
  sessionStorage.setItem('mapReturnState', JSON.stringify({
    selected: selected.value,
    filterZone: filterZone.value,
    year: selectedYear.value,
  }))
}

function restoreMapState() {
  const saved = sessionStorage.getItem('mapReturnState')
  if (!saved) return
  sessionStorage.removeItem('mapReturnState')
  try {
    const st = JSON.parse(saved)
    if (!st.selected || st.year !== selectedYear.value) return
    // 等数据加载后查找匹配的站点
    const match = allStations.value.find(s => s.station_id === st.selected.station_id)
    if (match) {
      selected.value = st.selected
      filterZone.value = st.filterZone || ''
    }
  } catch (_) {}
}

async function load() {
  const id = ++requestId
  loading.value = true; error.value = ''; empty.value = false
  try {
    const res = await getStations(selectedYear.value)
    if (id !== requestId) return
    const data = res.data?.data
    if (!data?.length) { empty.value = true; loading.value = false; return }
    allStations.value = data
    total.value = data.length
    updateChart()
    restoreMapState()
  } catch (e) { if (id === requestId) { error.value = '站点数据加载失败'; console.error(e) } }
  finally { if (id === requestId) loading.value = false }
}
watch(selectedYear, load, { immediate: true })
</script>

<style scoped>
.map-root { display:flex; flex-direction:column; flex:1; min-height:0; position:relative }
.map-filter { display:flex; align-items:center; gap:12px; flex-wrap:wrap; flex-shrink:0; margin-bottom:8px }
.map-stat { font-size:14px; font-weight:600; color:var(--ci-primary); white-space:nowrap }
.filter-tags { display:none }
.filter-legend { display:flex; gap:10px; flex-wrap:wrap }
.legend-item { display:flex; align-items:center; gap:4px; font-size:11px; color:var(--ci-text-muted) }
.legend-dot { width:10px; height:10px; border-radius:50%; display:inline-block }

.map-chart-card { flex:1; min-height:0; display:flex; flex-direction:column; overflow:hidden; padding:8px }

.map-popup { position:absolute; bottom:20px; left:20px; width:260px; z-index:10; padding:14px }
.popup-hd { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px }
.popup-name { font-size:14px; font-weight:600; color:var(--ci-primary) }
.popup-close { background:none; border:none; font-size:16px; color:var(--ci-text-muted); cursor:pointer; padding:2px 6px }
.popup-body { display:flex; flex-direction:column; gap:4px }
.popup-row { display:flex; justify-content:space-between; font-size:12px }
.popup-label { color:var(--ci-text-muted) }
.popup-val { font-weight:600; color:var(--ci-text) }
.popup-link { display:block; margin-top:8px; text-align:center; color:var(--ci-primary); font-weight:600; font-size:12px; text-decoration:none; padding:6px; border-radius:6px; background:var(--ci-primary-soft) }
.popup-link:hover { background:var(--ci-primary); color:#fff }

.fade-enter-active, .fade-leave-active { transition:all .25s ease }
.fade-enter-from, .fade-leave-to { opacity:0; transform:translateY(10px) }

@media (max-width: 767px) {
  .filter-tags { display:flex; flex-wrap:wrap }
  .filter-legend { display:none }
}
</style>
