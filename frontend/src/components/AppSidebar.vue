<template>
  <nav class="sidebar">
    <div class="sb-label">年份</div>
    <div class="sb-scroll">
      <button v-for="y in availableYears" :key="y" :class="['sb-year', { active: y === year }]" @click="$emit('update:year', y)">{{ y }}</button>
    </div>
  </nav>
</template>

<script setup>
defineProps({ year: Number, availableYears: Array })
defineEmits(['update:year'])
</script>

<style scoped>
.sidebar {
  width: 68px; flex-shrink: 0; align-self: flex-start;
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 14px 8px; margin-top: 0;
  background: rgb(250 249 247 / 82%); backdrop-filter: blur(20px) saturate(1.4);
  border: 1px solid rgb(255 255 255 / 45%); border-radius: 20px;
  box-shadow: 0 2px 24px rgb(0 0 0 / 6%), 0 0 0 1px rgb(255 255 255 / 30%) inset;
}
.sb-label { font-size: 10px; font-weight: 500; color: var(--ci-text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; flex-shrink: 0; }
.sb-scroll {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  overflow-y: auto; max-height: 120px; width: 100%;
  scrollbar-width: thin; scrollbar-color: var(--ci-primary-soft, rgba(58,103,79,0.15)) transparent;
}
.sb-scroll::-webkit-scrollbar { width: 3px; }
.sb-scroll::-webkit-scrollbar-thumb { background: var(--ci-primary-soft, rgba(58,103,79,0.2)); border-radius: 4px; }
.sb-year { width: 52px; height: 36px; min-height: 36px; border: none; border-radius: 10px; background: transparent; color: var(--ci-text-muted); font-size: 15px; font-weight: 600; cursor: pointer; transition: all .2s; font-family: inherit; flex-shrink: 0; }
.sb-year:hover { background: rgb(58 103 79 / 10%); color: var(--ci-primary); }
.sb-year.active { background: var(--ci-primary); color: #fff; }
@media (max-width: 767px) { .sidebar { width: auto; flex-direction: row; padding: 8px 12px; gap: 4px; border-radius: 16px; } .sb-label { display: none; } .sb-scroll { flex-direction: row; overflow-y: visible; overflow-x: auto; } .sb-year { width: 44px; height: 32px; min-height: 32px; font-size: 14px; } }
</style>
