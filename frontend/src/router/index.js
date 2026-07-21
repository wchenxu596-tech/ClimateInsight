import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/ranking', name: 'CityRanking', component: () => import('../views/CityRanking.vue') },
  { path: '/trend', name: 'TrendAnalysis', component: () => import('../views/TrendAnalysis.vue') },
  { path: '/zones', name: 'ClimateZones', component: () => import('../views/ClimateZones.vue') },
  { path: '/ai', name: 'BIAgent', component: () => import('../views/BIAgent.vue') },
  { path: '/:pathMatch(.*)*', name: 'NotFound', redirect: '/' },
]

export default createRouter({ history: createWebHistory(), routes })
