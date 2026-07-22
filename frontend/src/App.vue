<template>
  <div class="app-shell">
    <div class="app-background" :class="{ 'app-background--fallback': !bgLoaded }" aria-hidden="true">
      <img v-show="bgLoaded" :src="bgSrc" @load="bgLoaded = true" @error="bgLoaded = false" />
    </div>
    <main class="app-main">
      <AppSidebar v-model:year="selectedYear" :available-years="availableYears" @select-page="activePage = $event" />
      <div class="main-content">
        <AppTopNav />
        <router-view v-slot="{ Component }">
          <component :is="Component" :key="$route.path" :active-page="activePage" />
        </router-view>
      </div>
      <RightNav :active-page="activePage" @select="activePage = $event" @toggle-ai="agentOpen = !agentOpen" />
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
import HomePage from './components/HomePage.vue'
import AppFooter from './components/AppFooter.vue'
import BIAgent from './views/BIAgent.vue'
import bgImage from './assets/images/climate-landscape.webp'

const availableYears = [2024, 2023, 2022]
const selectedYear = ref(2024)
provide('selectedYear', selectedYear)

const activePage = ref('dashboard')
provide('activePage', activePage)

const agentOpen = ref(false)

const bgLoaded = ref(false)
const bgSrc = bgImage
</script>
