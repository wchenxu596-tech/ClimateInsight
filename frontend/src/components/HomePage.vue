<template>
  <div class="home-root">
    <Transition name="page" mode="out-in">
      <component :is="currentComponent" :key="activePage" />
    </Transition>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import StationMap from '../views/StationMap.vue'
import Dashboard from '../views/Dashboard.vue'
import TrendAnalysis from '../views/TrendAnalysis.vue'
import CityRanking from '../views/CityRanking.vue'
import ClimateZones from '../views/ClimateZones.vue'
import AlertDashboard from '../views/AlertDashboard.vue'

const props = defineProps({ activePage: { type: String, default: 'dashboard' } })

const pageMap = {
  map: StationMap,
  dashboard: Dashboard,
  trend: TrendAnalysis,
  ranking: CityRanking,
  zones: ClimateZones,
  alert: AlertDashboard,
}
const currentComponent = computed(() => pageMap[props.activePage] || Dashboard)
</script>

<style scoped>
.home-root { width: 100%; height: 100%; overflow: hidden; }
</style>
