<template>
  <div class="app-shell">
    <div class="app-background" :class="{ 'app-background--fallback': !bgLoaded }" aria-hidden="true">
      <img v-show="bgLoaded" :src="bgSrc" @load="bgLoaded = true" @error="bgLoaded = false" />
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
import { ref, provide } from 'vue'
import AppTopNav from './components/AppTopNav.vue'
import AppSidebar from './components/AppSidebar.vue'
import RightNav from './components/RightNav.vue'
import AIPanel from './components/AIPanel.vue'
import bgImage from './assets/images/climate-landscape.webp'

const availableYears = Array.from({length: 16}, (_, i) => 2010 + i)
const selectedYear = ref(2024)
provide('selectedYear', selectedYear)

const activePage = ref('dashboard')
provide('activePage', activePage)

const aiOpen = ref(false)
const panelWidth = ref(400)
provide('panelWidth', panelWidth)

function onNavSelect(id) {
  if (id === 'ai') { aiOpen.value = !aiOpen.value; return }
  activePage.value = id
}

const bgLoaded = ref(false)
const bgSrc = bgImage
</script>
