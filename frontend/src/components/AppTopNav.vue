<template>
  <nav class="topnav">
    <router-link to="/" class="topnav-brand">🌍 ClimateInsight</router-link>
    <div class="topnav-right">
      <el-button class="menu-btn" @click="drawerOpen = true" size="small" text>☰</el-button>
    </div>
    <el-drawer v-model="drawerOpen" direction="ltr" size="240px" title="导航">
      <div class="drawer-links">
        <button v-for="item in navItems" :key="item.id" class="drawer-link" @click="scrollTo(item.id); drawerOpen=false">{{ item.icon }} {{ item.label }}</button>
      </div>
    </el-drawer>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
const drawerOpen = ref(false)
const navItems = [
  { id: 'map', icon: '🗺️', label: '地图' },
  { id: 'dashboard', icon: '📊', label: '总览' },
  { id: 'trend', icon: '📈', label: '趋势' },
  { id: 'ranking', icon: '🏆', label: '排名' },
  { id: 'zones', icon: '🌍', label: '气候带' },
  { id: 'alert', icon: '⚠️', label: '预警' },
]
function scrollTo(id) {
  const el = document.getElementById('section-' + id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<style scoped>
.topnav {
  display: flex; align-items: center; height: 56px; padding: 0 24px; margin-bottom: 0;
  background: rgb(250 249 247 / 82%); backdrop-filter: blur(20px) saturate(1.4);
  border: 1px solid rgb(255 255 255 / 45%); border-radius: 28px;
  box-shadow: 0 2px 24px rgb(0 0 0 / 6%), 0 0 0 1px rgb(255 255 255 / 30%) inset;
  flex-shrink: 0;
}
.topnav-brand { font-size: 20px; font-weight: 700; color: var(--ci-primary); text-decoration: none; white-space: nowrap; flex-shrink: 0; }
.topnav-right { margin-left: auto; flex-shrink: 0; }
.menu-btn { display: none; font-size: 20px; }
.drawer-links { display: flex; flex-direction: column; gap: 8px; padding: 16px; }
.drawer-link { padding: 12px 16px; border-radius: 8px; text-decoration: none; color: var(--ci-text); font-size: 15px; cursor: pointer; background: none; border: none; text-align: left; font-family: inherit; transition: background .2s; }
.drawer-link:hover { background: var(--ci-surface-container); }
@media (max-width: 767px) { .menu-btn { display: inline-flex; } }
</style>
