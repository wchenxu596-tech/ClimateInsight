<template>
  <div class="app-shell">
    <div class="app-background" :class="{ 'app-background--fallback': !bgLoaded }" aria-hidden="true">
      <img v-show="bgLoaded" :src="bgSrc" @load="bgLoaded = true" @error="bgLoaded = false" />
    </div>
    <main class="app-main">
      <AppSidebar v-model:year="selectedYear" :available-years="availableYears" />
      <div class="main-content">
        <AppTopNav />
        <router-view :key="$route.path" />
      </div>
      <RightNav @toggle-ai="agentOpen = !agentOpen" />
    </main>
    <BIAgent :visible="agentOpen" @toggle="agentOpen = !agentOpen" />
    <AppFooter />
  </div>
</template>

<script setup>
import { ref, provide } from 'vue'
import AppTopNav from './components/AppTopNav.vue'
import AppSidebar from './components/AppSidebar.vue'
import RightNav from './components/RightNav.vue'
import AppFooter from './components/AppFooter.vue'
import BIAgent from './views/BIAgent.vue'
import bgImage from './assets/images/climate-landscape.webp'

const availableYears = Array.from({length: 16}, (_, i) => 2010 + i)
const selectedYear = ref(2024)
provide('selectedYear', selectedYear)

const agentOpen = ref(false)

const bgLoaded = ref(false)
const bgSrc = bgImage
</script>
