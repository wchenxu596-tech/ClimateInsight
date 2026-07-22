<template>
  <div v-if="loading" class="ps-loading" />
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
.ps-loading { flex: 1; min-height: 0; }
</style>
