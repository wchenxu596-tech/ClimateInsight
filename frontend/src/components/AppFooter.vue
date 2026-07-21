<template>
  <footer class="app-footer">
    <span>© 2024 ClimateInsight</span>
    <span>数据来源：NOAA GSOD</span>
  </footer>
</template>

<style scoped>
.app-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px var(--ci-page-gutter);
  color: var(--ci-text-muted); font-size: 12px;
}
@media (max-width: 767px) {
  .app-footer { flex-direction: column; gap: 4px; text-align: center }
}
</style>
