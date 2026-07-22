<template>
  <nav class="topnav">
    <span class="topnav-brand">🌍 ClimateInsight</span>
    <span class="topnav-subtitle">全球气候智能分析平台</span>
  </nav>
</template>

<script setup>
</script>

<style scoped>
.topnav {
  display: flex; align-items: center; gap: 12px; height: 48px; padding: 0 20px; margin-bottom: 8px;
  background: rgb(250 249 247 / 70%); backdrop-filter: blur(20px) saturate(1.4);
  border: 1px solid rgb(255 255 255 / 45%); border-radius: 24px;
  box-shadow: 0 2px 8px rgb(0 0 0 / 5%);
  flex-shrink: 0;
}
.topnav-brand { font-size: 20px; font-weight: 700; color: var(--ci-primary); white-space: nowrap; }
.topnav-subtitle { font-size: 13px; color: var(--ci-text-muted); white-space: nowrap; opacity: .7; }
@media (max-width: 767px) { .topnav-subtitle { display: none; } .topnav { height: 42px; padding: 0 14px; border-radius: 18px; } .topnav-brand { font-size: 17px; } }
</style>
