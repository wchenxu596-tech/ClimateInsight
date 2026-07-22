<template>
  <div class="home-root" ref="homeRoot" @scroll="onScroll">
    <section v-for="s in sections" :key="s.id" :id="'sec-' + s.id" class="snap-section">
      <KeepAlive :max="3">
        <component v-if="activePage === s.id || isAdjacent(s.id)" :is="s.comp" />
      </KeepAlive>
    </section>
  </div>
</template>

<script setup>
import { ref, inject, watch, computed } from 'vue'
import StationMap from '../views/StationMap.vue'
import Dashboard from '../views/Dashboard.vue'
import TrendAnalysis from '../views/TrendAnalysis.vue'
import CityRanking from '../views/CityRanking.vue'
import ClimateZones from '../views/ClimateZones.vue'
import AlertDashboard from '../views/AlertDashboard.vue'

const activePage = inject('activePage')
const homeRoot = ref(null)
let ignoreScroll = false

const sections = [
  { id: 'map', comp: StationMap },
  { id: 'dashboard', comp: Dashboard },
  { id: 'trend', comp: TrendAnalysis },
  { id: 'ranking', comp: CityRanking },
  { id: 'zones', comp: ClimateZones },
  { id: 'alert', comp: AlertDashboard },
]
const idxMap = Object.fromEntries(sections.map((s, i) => [s.id, i]))
function isAdjacent(id) {
  const cur = idxMap[activePage.value]
  const target = idxMap[id]
  return Math.abs(target - cur) <= 1
}

function onScroll() {
  if (ignoreScroll) return
  const el = homeRoot.value
  if (!el) return
  const top = el.scrollTop
  const h = el.clientHeight
  const idx = Math.round(top / h)
  const sec = sections[idx]
  if (sec && activePage.value !== sec.id) {
    activePage.value = sec.id
  }
}

function scrollToPage(id) {
  const el = document.getElementById('sec-' + id)
  if (!el) return
  ignoreScroll = true
  el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  setTimeout(() => { ignoreScroll = false }, 600)
}

// 监听右侧导航点击 → 滚动到对应 section
watch(() => activePage.value, (newId) => {
  if (ignoreScroll) return
  scrollToPage(newId)
})

defineExpose({ scrollToPage })
</script>

<style scoped>
.home-root {
  position: absolute; inset: 0;
  overflow-y: scroll; overflow-x: hidden;
  scroll-snap-type: y mandatory;
  scroll-behavior: smooth; overscroll-behavior: contain;
  scrollbar-width: none;
}
.home-root::-webkit-scrollbar { display: none; }
.snap-section {
  height: 100%; min-width: 0; scroll-snap-align: start; box-sizing: border-box;
  display: flex; flex-direction: column;
  padding: 10px 0 20px;
}
</style>
