import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('../components/HomePage.vue') },
  { path: '/stations/:id', name: 'StationDetail', component: () => import('../views/StationDetail.vue') },
  { path: '/:pathMatch(.*)*', name: 'NotFound', redirect: '/' },
]

export default createRouter({ history: createWebHistory(), routes })
