<template>
  <div class="home-root">
    <section data-section-id="map" id="section-map" class="home-section">
      <StationMap />
    </section>
    <section data-section-id="dashboard" id="section-dashboard" class="home-section">
      <Dashboard />
    </section>
    <section data-section-id="trend" id="section-trend" class="home-section">
      <TrendAnalysis />
    </section>
    <section data-section-id="ranking" id="section-ranking" class="home-section">
      <CityRanking />
    </section>
    <section data-section-id="zones" id="section-zones" class="home-section">
      <ClimateZones />
    </section>
    <section data-section-id="alert" id="section-alert" class="home-section">
      <AlertDashboard />
    </section>
  </div>
</template>

<script setup>
import StationMap from '../views/StationMap.vue'
import Dashboard from '../views/Dashboard.vue'
import TrendAnalysis from '../views/TrendAnalysis.vue'
import CityRanking from '../views/CityRanking.vue'
import ClimateZones from '../views/ClimateZones.vue'
import AlertDashboard from '../views/AlertDashboard.vue'
</script>

<style scoped>
.home-root { display: flex; flex-direction: column; width: 100%; }
.home-section { min-height: calc(100vh / 0.9); display: flex; flex-direction: column; transform: scale(0.9); transform-origin: top center; }
</style>
