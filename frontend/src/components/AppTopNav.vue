<template>
  <nav class="topnav">
    <router-link to="/" class="topnav-brand">🌍 ClimateInsight</router-link>
    <div class="topnav-links">
      <router-link to="/" exact-active-class="nav-active" class="topnav-link">总览</router-link>
      <router-link to="/trend" active-class="nav-active" class="topnav-link">趋势</router-link>
      <router-link to="/ranking" active-class="nav-active" class="topnav-link">排名</router-link>
      <router-link to="/zones" active-class="nav-active" class="topnav-link">气候带</router-link>
    </div>
    <div class="topnav-right">
      <el-button class="menu-btn" @click="drawerOpen = true" size="small" text>☰</el-button>
    </div>
    <el-drawer v-model="drawerOpen" direction="ltr" size="240px" title="导航">
      <div class="drawer-links">
        <router-link v-for="r in routes" :key="r.path" :to="r.path" class="drawer-link" @click="drawerOpen=false">{{ r.label }}</router-link>
      </div>
    </el-drawer>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
const drawerOpen = ref(false)
const routes = [
  { path: '/', label: '📊 总览' }, { path: '/trend', label: '📈 趋势' },
  { path: '/ranking', label: '🏆 排名' }, { path: '/zones', label: '🗺️ 气候带' },
]
</script>

<style scoped>
.topnav {
  position: fixed; top: 12px; left: 50%; transform: translateX(-50%);
  width: calc(100% - 48px); z-index: 50;
  display: flex; align-items: center; height: 56px; padding: 0 24px;
  background: rgb(250 249 247 / 82%); backdrop-filter: blur(20px) saturate(1.4);
  border: 1px solid rgb(255 255 255 / 45%); border-radius: 28px;
  box-shadow: 0 2px 24px rgb(0 0 0 / 6%), 0 0 0 1px rgb(255 255 255 / 30%) inset;
}
.topnav-brand { font-size: 20px; font-weight: 700; color: var(--ci-primary); text-decoration: none; margin-right: 32px; white-space: nowrap; flex-shrink: 0; }
.topnav-links { display: flex; gap: 4px; height: 100%; align-items: center; }
.topnav-link { color: var(--ci-text-muted); font-size: 14px; font-weight: 500; text-decoration: none; padding: 8px 16px; border-radius: 6px; transition: all .2s; white-space: nowrap; }
.topnav-link:hover { color: var(--ci-primary); background: rgb(58 103 79 / 8%); }
.topnav-link.nav-active { color: var(--ci-primary); font-weight: 600; border-bottom: 2px solid var(--ci-primary); border-radius: 0; }
.topnav-right { margin-left: auto; flex-shrink: 0; }
.menu-btn { display: none; font-size: 20px; }
.drawer-links { display: flex; flex-direction: column; gap: 8px; padding: 16px; }
.drawer-link { padding: 12px 16px; border-radius: 8px; text-decoration: none; color: var(--ci-text); font-size: 15px; }
.drawer-link:hover { background: var(--ci-surface-container); }
@media (max-width: 767px) { .topnav-links { display: none; } .menu-btn { display: inline-flex; } }
</style>
