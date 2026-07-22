<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="暂无站点数据" @retry="load">
      <div class="map-root">
        <!-- 合并行：气候带 + 大洲大洋 -->
        <div class="map-filter-row">
          <span class="row-label">气候带</span>
          <button v-for="z in zoneList" :key="z.key"
            :class="['tag-zone', { active: activeZones.has(z.key) }]"
            :style="activeZones.has(z.key) ? { background: z.color, borderColor: z.color } : { borderColor: z.color, color: z.color }"
            @click="toggleZone(z.key)">
            <span class="tag-dot" :style="{ background: activeZones.has(z.key) ? '#fff' : z.color }"></span>{{ z.label }}
          </button>
          <button class="tag-action" @click="selectAllZones">全部显示</button>
          <span class="row-sep">|</span>
          <span class="row-label">洲洋</span>
          <button class="tag-action globe-btn" @click="clearRegion">🌐 全球</button>
          <button v-for="r in regionList" :key="r.key"
            :class="['tag-region', { active: filterRegion === r.key }]"
            @click="setRegion(r.key)">{{ r.label }}</button>
          <span class="map-stat">🌍 {{ total }} 站</span>
        </div>

        <!-- 图表区 -->
        <GlassCard class="map-chart-card" @wheel.prevent.stop>
          <v-chart ref="chartRef" :option="chartOption" autoresize style="flex:1;min-height:0" @click="onChartClick" />
        </GlassCard>

        <!-- 选中站点浮窗 -->
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
import { ref, inject, watch, reactive, computed, onMounted, onUnmounted, onActivated, onDeactivated } from 'vue'
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
const filterRegion = ref('')
const total = ref(0)

// 气候带多选 — 默认全选
const zoneCN = { tropical:'热带', temperate:'温带', continental:'大陆性', polar:'寒带', arid:'干旱' }
const zoneColors = { tropical:'#8b3713', temperate:'#3a674f', continental:'#39656b', polar:'#8a9ba8', arid:'#c78b3c' }
const zoneList = Object.entries(zoneColors).map(([k, c]) => ({ key: k, label: zoneCN[k], color: c }))
const activeZones = ref(new Set(zoneList.map(z => z.key)))

function toggleZone(key) {
  const s = activeZones.value
  if (s.has(key)) {
    if (s.size > 1) { const ns = new Set(s); ns.delete(key); activeZones.value = ns }
  } else {
    const ns = new Set(s); ns.add(key); activeZones.value = ns
  }
}
function selectAllZones() {
  activeZones.value = new Set(zoneList.map(z => z.key))
}

// 大洲大洋 单选
const regions = {
  asia:        { label:'亚洲',   center:[90, 42], zoom:2.5,  lat:[0,80],   lon:[26,180] },
  africa:      { label:'非洲',   center:[20, 0],  zoom:3.0,  lat:[-35,38], lon:[-18,52] },
  europe:      { label:'欧洲',   center:[10, 52], zoom:3.5,  lat:[35,72],  lon:[-25,40] },
  north_america:{ label:'北美洲', center:[-100,50],zoom:2.5, lat:[15,75],  lon:[-170,-50] },
  south_america:{ label:'南美洲', center:[-60,-15],zoom:3.0, lat:[-56,12], lon:[-82,-34] },
  oceania:     { label:'大洋洲', center:[140,-20],zoom:3.5, lat:[-50,0],  lon:[110,180] },
  antarctica:  { label:'南极洲', center:[0,-80],  zoom:3.5,  lat:[-90,-60],lon:[-180,180] },
  pacific:     { label:'太平洋', center:[-150,-5], zoom:1.5,  lat:[-60,60], lon:[[-180,-70],[100,180]] },
  atlantic:    { label:'大西洋', center:[-30,0],  zoom:2.0,  lat:[-60,60], lon:[-70,20] },
  indian:      { label:'印度洋', center:[70,-15], zoom:2.5,  lat:[-60,30], lon:[20,120] },
  arctic:      { label:'北冰洋', center:[0,80],   zoom:3.5,  lat:[66,90],  lon:[-180,180] },
}
const regionList = Object.entries(regions).map(([k, v]) => ({ key: k, label: v.label }))

function setRegion(key) {
  filterRegion.value = filterRegion.value === key ? '' : key
  applyGeoFocus()
}
function clearRegion() {
  filterRegion.value = ''
  applyGeoFocus()
}

function inRegion(s, r) {
  const okLat = s.lat >= r.lat[0] && s.lat <= r.lat[1]
  let okLon = false
  if (Array.isArray(r.lon[0])) okLon = r.lon.some(seg => s.lon >= seg[0] && s.lon <= seg[1])
  else okLon = s.lon >= r.lon[0] && s.lon <= r.lon[1]
  return okLat && okLon
}

const filtered = computed(() => {
  let arr = allStations.value.filter(s => activeZones.value.has(s.climate_zone))
  if (filterRegion.value) arr = arr.filter(s => inRegion(s, regions[filterRegion.value]))
  return arr
})

function applyGeoFocus() {
  const r = filterRegion.value ? regions[filterRegion.value] : null
  chartOption.geo.center = r ? r.center : [8, 5]
  chartOption.geo.zoom  = r ? r.zoom  : 1.0
}

const chartOption = reactive({
  tooltip: {
    ...baseTooltip(),
    formatter: (p) => {
      const d = p.data; if (!d) return ''
      return `<strong>${d.name||'未知'}</strong><br/>气温: ${d.avgTemp??'--'}°C &nbsp; 降水: ${d.precip??'--'}mm<br/>气候带: ${zoneCN[d.zone]||d.zone||'--'}`
    }
  },
  geo: {
    map:'world', roam:true, silent:true, center:[8,5], zoom:1.0,
    left:'1%', right:'1%', top:'1%', bottom:'1%',
    itemStyle:{ areaColor:'#ebe4da', borderColor:'#cdc2b2', borderWidth:.5 },
    emphasis:{ itemStyle:{ areaColor:'#e0d6c8' }, label:{ show:false } },
    label:{ show:false },
  },
  series:[{ type:'scatter', coordinateSystem:'geo', symbolSize:8, data:[],
    silent: false, emphasis:{ itemStyle:{ borderColor:'#14422d', borderWidth:3, shadowBlur:8, shadowColor:'rgb(20 66 45 / 30%)' }, scale:1.8 },
  }],
})

function updateChart() {
  const data = filtered.value.map(s => ({
    value:[s.lon,s.lat], risk:s.risk_events||0, zone:s.climate_zone,
    name:s.station_name, avgTemp:s.avg_temp, precip:s.total_precip, sid:s.station_id,
    symbolSize:Math.max(5,Math.min(12,((s.risk_events||0)/10)+5)),
    itemStyle:{ color:zoneColors[s.climate_zone]||'#999', opacity:.7 },
  }))
  chartOption.series[0].data = data
  total.value = data.length
}
watch([filtered, filterRegion], () => { updateChart(); if (filterRegion.value) applyGeoFocus() }, { deep:true })

function onChartClick(p) {
  if (!p || p.componentSubType !== 'scatter') return
  const d = p.data; if (!d || !d.sid) return
  selected.value = { station_id:d.sid, station_name:d.name, climate_zone:d.zone, avg_temp:d.avgTemp, total_precip:d.precip, risk_events:d.risk }
}
function saveMapState() {
  if(!selected.value) return
  sessionStorage.setItem('mapReturnState', JSON.stringify({ selected:selected.value, filterRegion:filterRegion.value, year:selectedYear.value }))
}
function restoreMapState() {
  const s=sessionStorage.getItem('mapReturnState'); if(!s) return; sessionStorage.removeItem('mapReturnState')
  try {
    const st=JSON.parse(s); if(!st.selected||st.year!==selectedYear.value) return
    const m=allStations.value.find(x=>x.station_id===st.selected.station_id)
    if(m){ selected.value=st.selected; filterRegion.value=st.filterRegion||''; applyGeoFocus() }
  } catch(_){}
}

// 锁定页面滚动 — 地图区域内滚轮/拖拽不触发页面切换
function lockScroll() {
  const el = document.querySelector('.home-root')
  if (el) { el.dataset.prevOverflow = el.style.overflow || ''; el.style.overflow = 'hidden' }
}
function unlockScroll() {
  const el = document.querySelector('.home-root')
  if (el) el.style.overflow = el.dataset.prevOverflow || ''
}
onMounted(lockScroll)
onActivated(lockScroll)
onDeactivated(unlockScroll)
onUnmounted(unlockScroll)

async function load() {
  const id=++requestId; loading.value=true; error.value=''; empty.value=false
  try{
    const res=await getStations(selectedYear.value); if(id!==requestId) return
    const d=res.data?.data; if(!d?.length){ empty.value=true; loading.value=false; return }
    allStations.value=d; updateChart(); restoreMapState()
  }catch(e){ if(id===requestId){ error.value='数据加载失败'; console.error(e) } }
  finally{ if(id===requestId) loading.value=false }
}
watch(selectedYear, load, { immediate:true })
</script>

<style scoped>
.map-root { display:flex; flex-direction:column; flex:1; min-height:0; position:relative }
.map-filter-row { display:flex; align-items:center; gap:6px; flex-wrap:wrap; flex-shrink:0; margin-bottom:8px }
.row-label { font-size:13px; font-weight:600; color:var(--ci-text); margin-right:4px; white-space:nowrap }
.row-sep { color:var(--ci-outline-variant); margin:0 2px; font-size:14px }

/* 气候带标签 — 圆角边框 + 色点 */
.tag-zone {
  display:inline-flex; align-items:center; gap:4px;
  padding:3px 10px; border-radius:14px; border:1.5px solid;
  background:transparent; font-size:13px; font-weight:500;
  cursor:pointer; transition:all .2s; white-space:nowrap;
  font-family:inherit; line-height:1.4;
}
.tag-zone.active { color:#fff; }
.tag-zone:not(.active) { background:rgb(255 255 255 / 60%); }
.tag-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
.tag-zone:hover { opacity:.85; }

/* 大洲大洋标签 — 实心矩形 */
.tag-region {
  display:inline-block; padding:4px 12px; border-radius:6px; border:none;
  background:var(--ci-surface-container); color:var(--ci-text-muted);
  font-size:13px; font-weight:500; cursor:pointer; transition:all .2s;
  white-space:nowrap; font-family:inherit; line-height:1.4;
}
.tag-region:hover { background:rgb(58 103 79 / 15%); color:var(--ci-primary); }
.tag-region.active { background:var(--ci-secondary); color:#fff; }

/* 操作按钮 */
.tag-action {
  display:inline-block; padding:4px 10px; border-radius:6px; border:1px dashed var(--ci-outline);
  background:transparent; color:var(--ci-text-muted); font-size:12px; font-weight:500;
  cursor:pointer; transition:all .2s; white-space:nowrap; font-family:inherit;
}
.tag-action:hover { border-color:var(--ci-primary); color:var(--ci-primary); background:rgb(58 103 79 / 5%); }

.map-stat { font-size:15px; font-weight:600; color:var(--ci-primary); margin-left:auto; white-space:nowrap }

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

.fade-enter-active,.fade-leave-active { transition:all .25s ease }
.fade-enter-from,.fade-leave-to { opacity:0; transform:translateY(10px) }

@media (max-width:900px) {
  .map-stat { margin-left:0; width:100% }
  .map-filter-row { gap:4px }
}
</style>
