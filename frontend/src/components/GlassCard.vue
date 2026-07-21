<template>
  <div class="glass-card">
    <slot />
  </div>
</template>

<style scoped>
.glass-card {
  background: var(--ci-glass);
  backdrop-filter: blur(12px);
  border: 1px solid rgb(192 201 193 / 30%);
  box-shadow: var(--ci-shadow);
  border-radius: var(--ci-radius-lg);
}
</style>
