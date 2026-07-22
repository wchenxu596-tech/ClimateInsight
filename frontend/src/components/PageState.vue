<template>
  <div v-if="loading" class="ps-loading">
    <div class="ps-spinner">🌍</div>
    <div class="ps-text">加载中...</div>
  </div>
  <el-alert v-else-if="error" :title="error" type="error" show-icon closable @close="$emit('retry')">
    <el-button type="primary" size="small" @click="$emit('retry')">重试</el-button>
  </el-alert>
  <el-empty v-else-if="empty" :description="emptyText || '暂无数据'" />
  <slot v-else />
</template>

<script setup>
defineProps({
  loading: Boolean,
  error: { type: String, default: '' },
  empty: Boolean,
  emptyText: { type: String, default: '' },
})
defineEmits(['retry'])
</script>

<style scoped>
.ps-loading {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  flex: 1; gap: 12px; min-height: 200px;
}
.ps-spinner {
  font-size: 48px; animation: ps-spin 1.5s linear infinite;
  opacity: .8;
}
@keyframes ps-spin {
  0% { transform: rotate(0deg) scale(1); }
  50% { transform: rotate(180deg) scale(1.15); }
  100% { transform: rotate(360deg) scale(1); }
}
.ps-text { font-size: 15px; color: var(--ci-text-muted); }
</style>
