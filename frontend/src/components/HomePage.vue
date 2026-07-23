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
const scrollTarget = ref(null) // 导航点击目标，精确追踪避免中途 snap 干扰

const sections = [
  { id: 'map', comp: StationMap },
  { id: 'dashboard', comp: Dashboard },
  { id: 'trend', comp: TrendAnalysis },
  { id: 'zones', comp: ClimateZones },
  { id: 'ranking', comp: CityRanking },
  { id: 'alert', comp: AlertDashboard },
]
const idxMap = Object.fromEntries(sections.map((s, i) => [s.id, i]))
function isAdjacent(id) {
  const cur = idxMap[activePage.value]
  const target = idxMap[id]
  return Math.abs(target - cur) <= 1
}

function onScroll() {
  const el = homeRoot.value
  if (!el) return
  // 导航点击导致的滚动：抑制中途 snap 检测，等目标到位
  if (scrollTarget.value) {
    const targetEl = document.getElementById('sec-' + scrollTarget.value)
    if (targetEl) {
      const rect = targetEl.getBoundingClientRect()
      const containerTop = el.getBoundingClientRect().top
      if (Math.abs(rect.top - containerTop) < 8) {
        // 目标到位，切换 activePage
        if (activePage.value !== scrollTarget.value) {
          activePage.value = scrollTarget.value
        }
        scrollTarget.value = null
      }
    } else {
      scrollTarget.value = null
    }
    return
  }
  // 手动滚轮/触控：正常 snap 检测
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
  scrollTarget.value = id
  el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// 监听右侧导航点击 → 滚动到对应 section
watch(() => activePage.value, (newId) => {
  if (scrollTarget.value) return
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
