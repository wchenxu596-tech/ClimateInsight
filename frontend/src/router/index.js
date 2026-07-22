import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/ranking', name: 'CityRanking', component: () => import('../views/CityRanking.vue') },
  { path: '/trend', name: 'TrendAnalysis', component: () => import('../views/TrendAnalysis.vue') },
  { path: '/zones', name: 'ClimateZones', component: () => import('../views/ClimateZones.vue') },
  { path: '/alert', name: 'AlertDashboard', component: () => import('../views/AlertDashboard.vue') },
  { path: '/map', name: 'StationMap', component: () => import('../views/StationMap.vue') },
  { path: '/stations/:id', name: 'StationDetail', component: () => import('../views/StationDetail.vue') },
  { path: '/:pathMatch(.*)*', name: 'NotFound', redirect: '/' },
]

export default createRouter({ history: createWebHistory(), routes })
