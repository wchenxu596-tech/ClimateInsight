<template>
  <nav class="right-nav">
    <button v-for="item in navItems" :key="item.id"
      :class="['rn-item', { active: activePage === item.id }]"
      @click="$emit('select', item.id)" :title="item.label">
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
defineProps({ activePage: { type: String, default: 'dashboard' } })
defineEmits(['select', 'toggleAi'])

const navItems = [
  { id: 'map', icon: '🗺️', label: '地图' },
  { id: 'dashboard', icon: '📊', label: '总览' },
  { id: 'trend', icon: '📈', label: '趋势' },
  { id: 'ranking', icon: '🏆', label: '排名' },
  { id: 'zones', icon: '🌍', label: '气候带' },
  { id: 'alert', icon: '⚠️', label: '预警' },
]
</script>

<style scoped>
.right-nav {
  width: 100%; min-width: 0; align-self: center;
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 14px 6px;
  background: rgb(250 249 247 / 82%); backdrop-filter: blur(20px) saturate(1.4);
  border: 1px solid rgb(255 255 255 / 45%); border-radius: 20px;
  box-shadow: 0 2px 8px rgb(0 0 0 / 5%);
}
.rn-item {
  width: 84px; height: 54px; border: none; border-radius: 12px;
  background: transparent; color: var(--ci-text-muted);
  cursor: pointer; transition: all .25s;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px;
  font-family: inherit;
}
.rn-item:hover { background: rgb(58 103 79 / 10%); color: var(--ci-primary); }
.rn-item.active { background: var(--ci-primary); color: #fff; box-shadow: 0 4px 16px rgb(20 66 45 / 30%); }
.rn-icon { font-size: 18px; line-height: 1; }
.rn-label { font-size: 10px; font-weight: 600; line-height: 1; }
.rn-spacer { flex: 1; min-height: 4px; }
.rn-ai-btn {
  width: 84px; height: 46px; border: none; border-radius: 12px;
  background: var(--ci-primary-soft); color: var(--ci-primary);
  cursor: pointer; transition: all .25s;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px;
  font-family: inherit;
}
.rn-ai-btn:hover { background: var(--ci-primary); color: #fff; }
@media (max-width: 767px) { .right-nav { display: none; } }
</style>
