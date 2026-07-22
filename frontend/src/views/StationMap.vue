<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="暂无站点数据" @retry="load">
      <div class="map-root">
        <!-- 筛选栏 -->
        <div class="map-filter">
          <div class="map-stat">🌍 {{ total }} 个气象站</div>
          <el-input v-model="search" placeholder="搜索站点或地区..." size="small" clearable class="map-search" @input="onSearch" @clear="clearSearch">
            <template #prefix><span style="font-size:14px">🔍</span></template>
          </el-input>
          <div class="filter-legend">
            <span v-for="z in zoneList" :key="z.key" class="legend-item">
              <span class="legend-dot" :style="{background:z.color}"></span>{{ z.label }}
            </span>
          </div>
        </div>
        <div class="map-filter-row">
          <span class="filter-label">气候带</span>
          <el-tag v-for="z in zoneList" :key="z.key"
            :type="filterZone === z.key ? '' : 'info'"
            :color="filterZone === z.key ? z.color : ''"
            effect="plain" size="small"
            class="map-tag"
            @click="setFilter('zone', z.key)">
            {{ z.label }}
          </el-tag>
          <span class="filter-label" style="margin-left:12px">洲/洋</span>
          <el-tag v-for="r in regionList" :key="r.key"
            :type="filterRegion === r.key ? '' : 'info'"
            :color="filterRegion === r.key ? '#3a674f' : ''"
            effect="plain" size="small"
            class="map-tag"
            @click="setFilter('region', r.key)">
            {{ r.label }}
          </el-tag>
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

const selectedYear = inject('selectedYear')
const loading = ref(true); const error = ref(''); const empty = ref(false)
const chartRef = ref(null); let requestId = 0

const allStations = ref([])
const selected = ref(null)
const filterZone = ref('')
const filterRegion = ref('')
const search = ref('')
const total = ref(0)

// 气候带
const zoneCN = { tropical:'热带', temperate:'温带', continental:'大陆性', polar:'寒带', arid:'干旱' }
const zoneColors = { tropical:'#8b3713', temperate:'#3a674f', continental:'#39656b', polar:'#c0c9c1', arid:'#bdeaf2' }
const zoneList = Object.entries(zoneColors).map(([k, c]) => ({ key: k, label: zoneCN[k], color: c }))

// 洲/洋 — 中心坐标 + 缩放 + 近似边界
const regions = {
  asia:        { label:'亚洲',   center:[90, 42], zoom:2.5,  lat:[0,80],   lon:[26,180] },
  africa:      { label:'非洲',   center:[20, 0],  zoom:3.0,  lat:[-35,38], lon:[-18,52] },
  europe:      { label:'欧洲',   center:[10, 52], zoom:3.5,  lat:[35,72],  lon:[-25,40] },
  north_america:{ label:'北美洲', center:[-100,50],zoom:2.5, lat:[15,75],  lon:[-170,-50] },
  south_america:{ label:'南美洲', center:[-60,-15],zoom:3.0, lat:[-56,12], lon:[-82,-34] },
  oceania:     { label:'大洋洲', center:[140,-20],zoom:3.5, lat:[-50,0],  lon:[110,180] },
  antarctica:  { label:'南极洲', center:[0,-80],  zoom:3.5,  lat:[-90,-60],lon:[-180,180] },
  pacific:     { label:'太平洋', center:[-140,0], zoom:1.8,  lat:[-60,60], lon:[[-180,-70],[100,180]] },
  atlantic:    { label:'大西洋', center:[-30,0],  zoom:2.0,  lat:[-60,60], lon:[-70,20] },
  indian:      { label:'印度洋', center:[70,-15], zoom:2.5,  lat:[-60,30], lon:[20,120] },
  arctic:      { label:'北冰洋', center:[0,80],   zoom:3.5,  lat:[66,90],  lon:[-180,180] },
}
const regionList = Object.entries(regions).map(([k, v]) => ({ key: k, label: v.label }))

// 判断站点是否在区域内
function inRegion(s, r) {
  if (!r) return true
  const okLat = s.lat >= r.lat[0] && s.lat <= r.lat[1]
  let okLon = false
  if (Array.isArray(r.lon[0])) {
    // 多段经度（如太平洋）
    okLon = r.lon.some(seg => s.lon >= seg[0] && s.lon <= seg[1])
  } else {
    okLon = s.lon >= r.lon[0] && s.lon <= r.lon[1]
  }
  return okLat && okLon
}

const filtered = computed(() => {
  let arr = allStations.value
  if (filterZone.value) arr = arr.filter(s => s.climate_zone === filterZone.value)
  if (filterRegion.value) arr = arr.filter(s => inRegion(s, regions[filterRegion.value]))
  if (search.value.trim()) {
    const q = search.value.trim().toLowerCase()
    arr = arr.filter(s => (s.station_name || '').toLowerCase().includes(q))
  }
  return arr
})

// 设置筛选
function setFilter(type, key) {
  if (type === 'zone') {
    filterZone.value = filterZone.value === key ? '' : key
  } else {
    filterRegion.value = filterRegion.value === key ? '' : key
  }
  applyGeoFocus()
}
function onSearch() { applyGeoFocus() }
function clearSearch() { search.value = ''; applyGeoFocus() }

function applyGeoFocus() {
  const r = filterRegion.value ? regions[filterRegion.value] : null
  if (r) {
    chartOption.geo.center = r.center
    chartOption.geo.zoom = r.zoom
  } else {
    chartOption.geo.center = [0, 20]
    chartOption.geo.zoom = 1.5
  }
  // 如果搜索到单个站点，聚焦该站点
  if (search.value.trim() && !filterRegion.value) {
    const match = allStations.value.find(s =>
      (s.station_name || '').toLowerCase().includes(search.value.trim().toLowerCase())
    )
    if (match) {
      chartOption.geo.center = [match.lon, match.lat]
      chartOption.geo.zoom = 5
    }
  }
}

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
    roam: true,
    center: [0, 20],
    zoom: 1.5,
    left: '2%', right: '2%', top: '2%', bottom: '2%',
    itemStyle: { areaColor: '#ebe4da', borderColor: '#cdc2b2', borderWidth: 0.5 },
    emphasis: { itemStyle: { areaColor: '#e0d6c8' }, label: { show: false } },
    label: { show: false },
  },
  series: [{
    type: 'scatter', coordinateSystem: 'geo',
    symbolSize: 5, data: [],
    emphasis: { itemStyle: { borderColor: '#14422d', borderWidth: 2 } },
  }],
})

function updateChart() {
  const data = filtered.value.map(s => ({
    value: [s.lon, s.lat],
    risk: s.risk_events || 0, zone: s.climate_zone,
    name: s.station_name, avgTemp: s.avg_temp,
    precip: s.total_precip, sid: s.station_id,
    symbolSize: Math.max(3, Math.min(8, ((s.risk_events||0) / 10) + 3)),
    itemStyle: { color: zoneColors[s.climate_zone] || '#999', opacity: 0.7 },
  }))
  chartOption.series[0].data = data
  total.value = data.length
}
watch(filtered, updateChart, { deep: true })

function onChartClick(params) {
  const d = params.data
  if (!d) return
  selected.value = {
    station_id: d.sid, station_name: d.name,
    climate_zone: d.zone, avg_temp: d.avgTemp,
    total_precip: d.precip, risk_events: d.risk,
  }
}

function saveMapState() {
  if (!selected.value) return
  sessionStorage.setItem('mapReturnState', JSON.stringify({
    selected: selected.value, filterZone: filterZone.value,
    filterRegion: filterRegion.value, year: selectedYear.value,
  }))
}
function restoreMapState() {
  const saved = sessionStorage.getItem('mapReturnState')
  if (!saved) return
  sessionStorage.removeItem('mapReturnState')
  try {
    const st = JSON.parse(saved)
    if (!st.selected || st.year !== selectedYear.value) return
    const match = allStations.value.find(s => s.station_id === st.selected.station_id)
    if (match) {
      selected.value = st.selected
      filterZone.value = st.filterZone || ''
      filterRegion.value = st.filterRegion || ''
      applyGeoFocus()
    }
  } catch (_) {}
}

async function load() {
  const id = ++requestId; loading.value = true; error.value = ''; empty.value = false
  try {
    const res = await getStations(selectedYear.value)
    if (id !== requestId) return
    const data = res.data?.data
    if (!data?.length) { empty.value = true; loading.value = false; return }
    allStations.value = data
    updateChart()
    restoreMapState()
  } catch (e) {
    if (id === requestId) { error.value = '站点数据加载失败'; console.error(e) }
  } finally { if (id === requestId) loading.value = false }
}
watch(selectedYear, load, { immediate: true })
</script>

<style scoped>
.map-root { display:flex; flex-direction:column; flex:1; min-height:0; position:relative }
.map-filter { display:flex; align-items:center; gap:12px; flex-wrap:wrap; flex-shrink:0; margin-bottom:6px }
.map-stat { font-size:18px; font-weight:600; color:var(--ci-primary); white-space:nowrap }
.map-search { width:220px; flex-shrink:0 }
.map-filter-row { display:flex; align-items:center; gap:4px; flex-wrap:wrap; flex-shrink:0; margin-bottom:8px }
.filter-label { font-size:13px; font-weight:500; color:var(--ci-text-muted); margin-right:4px }
.filter-legend { display:flex; gap:12px; flex-wrap:wrap; margin-left:auto }
.legend-item { display:flex; align-items:center; gap:6px; font-size:14px; color:var(--ci-text-muted) }
.legend-dot { width:12px; height:12px; border-radius:50%; display:inline-block }
.map-tag { cursor:pointer; border:none; color:#fff }

.map-chart-card { flex:1; min-height:0; display:flex; flex-direction:column; overflow:hidden; padding:12px }

.map-popup { position:absolute; bottom:20px; left:20px; width:300px; z-index:10; padding:18px }
.popup-hd { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px }
.popup-name { font-size:18px; font-weight:600; color:var(--ci-primary) }
.popup-close { background:none; border:none; font-size:20px; color:var(--ci-text-muted); cursor:pointer; padding:4px 8px }
.popup-body { display:flex; flex-direction:column; gap:6px }
.popup-row { display:flex; justify-content:space-between; font-size:15px }
.popup-label { color:var(--ci-text-muted) }
.popup-val { font-weight:600; color:var(--ci-text) }
.popup-link { display:block; margin-top:10px; text-align:center; color:var(--ci-primary); font-weight:600; font-size:15px; text-decoration:none; padding:8px; border-radius:8px; background:var(--ci-primary-soft) }
.popup-link:hover { background:var(--ci-primary); color:#fff }

.fade-enter-active, .fade-leave-active { transition:all .25s ease }
.fade-enter-from, .fade-leave-to { opacity:0; transform:translateY(10px) }

@media (max-width: 900px) {
  .map-filter { flex-direction:column; align-items:flex-start }
  .map-search { width:100% }
  .filter-legend { margin-left:0 }
}
</style>
