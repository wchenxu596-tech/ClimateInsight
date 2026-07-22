import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../components/HomePage.vue'

const routes = [
  { path: '/', name: 'Home', component: HomePage },
  { path: '/stations/:id', name: 'StationDetail', component: () => import('../views/StationDetail.vue') },
  { path: '/:pathMatch(.*)*', name: 'NotFound', redirect: '/' },
]

export default createRouter({ history: createWebHistory(), routes })
