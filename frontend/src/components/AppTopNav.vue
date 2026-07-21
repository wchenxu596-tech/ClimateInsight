<template>
  <nav class="topnav">
    <router-link to="/" class="topnav-brand">🌍 ClimateInsight</router-link>
    <div class="topnav-links" ref="navLinks">
      <router-link to="/" exact-active-class="nav-active" class="topnav-link">总览</router-link>
      <router-link to="/trend" active-class="nav-active" class="topnav-link">趋势</router-link>
      <router-link to="/ranking" active-class="nav-active" class="topnav-link">排名</router-link>
      <router-link to="/zones" active-class="nav-active" class="topnav-link">气候带</router-link>
    </div>
    <div class="topnav-right">
      <el-select :model-value="year" @update:model-value="$emit('update:year', $event)" size="small" style="width:100px">
        <el-option v-for="y in availableYears" :key="y" :label="y + '年'" :value="y" />
      </el-select>
      <!-- 移动端菜单按钮 -->
      <el-button class="menu-btn" @click="drawerOpen = true" :icon="'Menu'" size="small" text />
    </div>

    <!-- 移动端抽屉菜单 -->
    <el-drawer v-model="drawerOpen" direction="ltr" size="240px" title="导航">
      <div class="drawer-links">
        <router-link v-for="r in routes" :key="r.path" :to="r.path" class="drawer-link" @click="drawerOpen=false">{{ r.label }}</router-link>
      </div>
    </el-drawer>
  </nav>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  year: { type: Number, required: true },
  availableYears: { type: Array, required: true },
})
defineEmits(['update:year'])

const drawerOpen = ref(false)
const routes = [
  { path: '/', label: '📊 总览' },
  { path: '/trend', label: '📈 趋势' },
  { path: '/ranking', label: '🏆 排名' },
  { path: '/zones', label: '🗺️ 气候带' },
]
</script>

<style scoped>
.topnav {
  position: fixed; top:0; left:0; width:100%; z-index:50;
  display:flex; align-items:center; height:64px;
  padding:0 var(--ci-page-gutter);
  background: var(--ci-glass-strong);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgb(192 201 193 / 20%);
}
.topnav-brand {
  font-size:20px; font-weight:700; color:var(--ci-primary);
  text-decoration:none; margin-right:32px; white-space:nowrap; flex-shrink:0;
}
.topnav-links { display:flex; gap:4px; height:100%; align-items:center }
.topnav-link {
  color:var(--ci-text-muted); font-size:14px; font-weight:500;
  text-decoration:none; padding:8px 16px; border-radius:6px;
  transition:all .2s; white-space:nowrap;
}
.topnav-link:hover { color:var(--ci-primary); background:rgb(58 103 79 / 8%) }
.topnav-link.nav-active { color:var(--ci-primary); font-weight:600; border-bottom:2px solid var(--ci-primary); border-radius:0 }
.topnav-right { margin-left:auto; display:flex; align-items:center; gap:8px; flex-shrink:0 }
.menu-btn { display:none }

.drawer-links { display:flex; flex-direction:column; gap:8px; padding:16px }
.drawer-link { padding:12px 16px; border-radius:8px; text-decoration:none; color:var(--ci-text); font-size:15px }
.drawer-link:hover { background:var(--ci-surface-container) }

@media (max-width: 767px) {
  .topnav-links { display:none }
  .menu-btn { display:inline-flex }
}
</style>
