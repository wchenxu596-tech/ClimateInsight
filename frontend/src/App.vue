<template>
  <div class="app-shell">
    <!-- 背景层 -->
    <div class="app-background" :class="{ 'app-background--fallback': !bgLoaded }" aria-hidden="true">
      <img v-show="bgLoaded" :src="bgSrc" @load="bgLoaded = true" @error="bgLoaded = false" />
    </div>

    <AppTopNav v-model:year="selectedYear" :available-years="availableYears" />
    <main class="app-main"><router-view /></main>
    <AppFooter />
    <BIAgent />
  </div>
</template>

<script setup>
import { ref, provide } from 'vue'
import AppTopNav from './components/AppTopNav.vue'
import AppFooter from './components/AppFooter.vue'
import BIAgent from './views/BIAgent.vue'
import bgImage from './assets/images/climate-landscape.webp'

const availableYears = [2022, 2023, 2024]
const selectedYear = ref(2024)
provide('selectedYear', selectedYear)

const bgLoaded = ref(false)
const bgSrc = bgImage
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  position: relative;
  color: var(--ci-text);
  background-color: var(--ci-surface);
}
</style>
