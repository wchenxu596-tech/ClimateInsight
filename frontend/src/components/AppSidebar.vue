<template>
  <nav class="sidebar">
    <div class="sb-logo" title="ClimateInsight">🌍</div>
    <div class="sb-label">年份</div>
    <div class="sb-scroll">
      <button v-for="y in availableYears" :key="y" :class="['sb-year', { active: y === year }]" @click="$emit('update:year', y)">{{ y }}</button>
    </div>
  </nav>
</template>

<script setup>
import { onMounted, nextTick, ref } from 'vue'
const props = defineProps({ year: Number, availableYears: Array })
defineEmits(['update:year'])
const scrollEl = ref(null)
onMounted(() => {
  nextTick(() => {
    const el = document.querySelector('.sb-year.active')
    if (el) el.scrollIntoView({ block: 'center' })
  })
})
</script>

<style scoped>
.sidebar {
  width: 100%; min-width: 0; align-self: center;
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 12px 6px;
  background: rgb(250 249 247 / 70%); backdrop-filter: blur(12px) saturate(1.4);
  border: 1px solid rgb(255 255 255 / 45%); border-radius: 16px;
  box-shadow: 0 2px 8px rgb(0 0 0 / 5%);
}
.sb-logo { font-size: 26px; line-height: 1; margin-bottom: 6px; flex-shrink: 0; }
.sb-label { font-size: 11px; font-weight: 500; color: var(--ci-text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; flex-shrink: 0; }
.sb-scroll {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  overflow-y: auto; max-height: 260px; width: 100%;
  scrollbar-width: none;
}
.sb-scroll::-webkit-scrollbar { display: none; }
.sb-year { width: 64px; height: 34px; min-height: 34px; border: none; border-radius: 10px; background: transparent; color: var(--ci-text-muted); font-size: 16px; font-weight: 600; cursor: pointer; font-family: inherit; flex-shrink: 0; position: relative; }
.sb-year:hover { background: rgb(58 103 79 / 10%); color: var(--ci-primary); }
.sb-year.active { background: var(--ci-primary); color: #fff; animation: pulse-glow 3s ease-in-out infinite; }
@media (max-width: 900px) { .sidebar { width: auto; flex-direction: row; padding: 6px 10px; gap: 6px; border-radius: 14px; align-self: stretch; } .sb-logo { font-size: 16px; margin-bottom: 0; } .sb-label { display: none; } .sb-scroll { flex-direction: row; overflow-y: visible; overflow-x: auto; max-height: none; } .sb-year { width: 40px; height: 28px; min-height: 28px; font-size: 12px; } }
</style>
