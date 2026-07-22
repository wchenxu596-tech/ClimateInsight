<template>
  <div class="app-shell">
    <div class="app-background" aria-hidden="true">
      <Grainient
        :color1="bgColors[0]"
        :color2="bgColors[1]"
        :color3="bgColors[2]"
        :time-speed="0.4"
        :grain-amount="0.04"
        :zoom="0.85"
        :contrast="0.9"
      />
    </div>
    <main class="app-main">
      <AppSidebar v-model:year="selectedYear" :available-years="availableYears" />
      <div class="center-area">
        <div class="main-content">
          <AppTopNav />
          <div class="content-body">
            <router-view v-slot="{ Component }">
              <component :is="Component" :key="$route.path" :active-page="activePage" />
            </router-view>
          </div>
        </div>
        <Transition name="ai-slide">
          <div v-if="aiOpen" class="ai-panel" :style="{ width: panelWidth + 'px' }">
            <AIPanel @close="aiOpen = false" />
          </div>
        </Transition>
      </div>
      <RightNav :active-page="activePage" @select="onNavSelect" @toggle-ai="aiOpen = !aiOpen" />
    </main>
  </div>
</template>

<script setup>
import { ref, provide, watch } from 'vue'
import { Grainient } from '@bg-effects/grainient'
import AppTopNav from './components/AppTopNav.vue'
import AppSidebar from './components/AppSidebar.vue'
import RightNav from './components/RightNav.vue'
import AIPanel from './components/AIPanel.vue'

// 主题色系：绿 → 青蓝 → 暖橙
const bgColors = ['#bceecf', '#bae8ef', '#ffdbce']

const availableYears = [2015, 2016, 2017, 2021, 2022, 2023, 2024, 2025]
const selectedYear = ref(2024)
provide('selectedYear', selectedYear)

const activePage = ref('map')
provide('activePage', activePage)

const aiOpen = ref(false)
const panelWidth = ref(400)
provide('panelWidth', panelWidth)
provide('aiOpen', aiOpen)

// AI 面板开关时触发 ECharts 重绘
watch(aiOpen, () => {
  setTimeout(() => window.dispatchEvent(new Event('resize')), 420)
})
watch(panelWidth, () => {
  setTimeout(() => window.dispatchEvent(new Event('resize')), 100)
})

function onNavSelect(id) {
  if (id === 'ai') { aiOpen.value = !aiOpen.value; return }
  activePage.value = id
}
</script>
