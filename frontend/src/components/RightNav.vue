<template>
  <nav class="right-nav">
    <button v-for="item in navItems" :key="item.id"
      :class="['rn-item', { active: activeId === item.id }]"
      @click="scrollTo(item.id)" :title="item.label">
      <span class="rn-icon">{{ item.icon }}</span>
      <span class="rn-label">{{ item.label }}</span>
    </button>
    <div class="rn-spacer"></div>
    <button class="rn-ai-btn" @click="$emit('toggleAi')" title="AI 分析助手">
      <span class="rn-icon">🌿</span>
      <span class="rn-label">AI</span>
    </button>
  </nav>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

defineEmits(['toggleAi'])

const navItems = [
  { id: 'map', icon: '🗺️', label: '地图' },
  { id: 'dashboard', icon: '📊', label: '总览' },
  { id: 'trend', icon: '📈', label: '趋势' },
  { id: 'ranking', icon: '🏆', label: '排名' },
  { id: 'zones', icon: '🌍', label: '气候带' },
  { id: 'alert', icon: '⚠️', label: '预警' },
]

const activeId = ref('map')

function scrollTo(id) {
  const el = document.getElementById('section-' + id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function onScroll() {
  const root = document.querySelector('.main-content')
  if (!root) return
  const scrollTop = root.scrollTop
  let current = navItems[0].id
  for (const item of navItems) {
    const el = document.getElementById('section-' + item.id)
    if (el && el.offsetTop <= scrollTop + 60) {
      current = item.id
    }
  }
  activeId.value = current
}

onMounted(() => {
  const root = document.querySelector('.main-content')
  if (root) {
    root.addEventListener('scroll', onScroll, { passive: true })
    onScroll() // 初始化
  }
})

onUnmounted(() => {
  const root = document.querySelector('.main-content')
  if (root) root.removeEventListener('scroll', onScroll)
})
</script>

<style scoped>
.right-nav {
  width: 64px; flex-shrink: 0; align-self: flex-start;
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 12px 6px 10px;
  background: rgb(250 249 247 / 82%); backdrop-filter: blur(20px) saturate(1.4);
  border: 1px solid rgb(255 255 255 / 45%); border-radius: 20px;
  box-shadow: 0 2px 24px rgb(0 0 0 / 6%), 0 0 0 1px rgb(255 255 255 / 30%) inset;
}
.rn-item {
  width: 48px; height: 52px; border: none; border-radius: 14px;
  background: transparent; color: var(--ci-text-muted);
  cursor: pointer; transition: all .25s;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px;
  font-family: inherit;
}
.rn-item:hover { background: rgb(58 103 79 / 10%); color: var(--ci-primary); }
.rn-item.active { background: var(--ci-primary); color: #fff; }
.rn-icon { font-size: 16px; line-height: 1; }
.rn-label { font-size: 9px; font-weight: 500; line-height: 1; }
.rn-spacer { flex: 1; min-height: 4px; }
.rn-ai-btn {
  width: 48px; height: 44px; border: none; border-radius: 14px;
  background: var(--ci-primary-soft); color: var(--ci-primary);
  cursor: pointer; transition: all .25s;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px;
  font-family: inherit;
}
.rn-ai-btn:hover { background: var(--ci-primary); color: #fff; }
@media (max-width: 767px) { .right-nav { display: none; } }
</style>
