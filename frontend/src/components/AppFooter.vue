<template>
  <footer class="app-footer">
    <span>© 2024 ClimateInsight</span>
    <span>数据来源：NOAA GSOD</span>
  </footer>
</template>

<style scoped>
.app-footer {
  width: 100%; padding: 32px var(--ci-page-gutter);
  display: flex; justify-content: space-between; align-items: center;
  background: var(--ci-glass-strong); backdrop-filter: blur(12px);
  border-top: 1px solid rgb(192 201 193 / 30%);
  color: var(--ci-text-muted); font-size: 14px;
}
@media (max-width: 767px) {
  .app-footer { flex-direction: column; gap: 8px; text-align: center }
}
</style>
