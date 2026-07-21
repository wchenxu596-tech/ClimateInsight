<template>
  <GlassCard :style="{ minHeight: minHeight }">
    <div class="cp-header">
      <div>
        <div class="cp-title">{{ title }}</div>
        <div v-if="subtitle" class="cp-subtitle">{{ subtitle }}</div>
      </div>
      <slot name="actions" />
    </div>
    <div v-if="loading" style="height:200px;display:flex;align-items:center;justify-content:center">
      <el-icon class="is-loading"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="3" stroke-dasharray="31.4" stroke-dashoffset="10"/></svg></el-icon>
    </div>
    <el-empty v-else-if="empty" :description="emptyText || '暂无数据'" />
    <div v-else class="cp-body">
      <slot />
    </div>
  </GlassCard>
</template>

<script setup>
import GlassCard from './GlassCard.vue'
defineProps({
  title: String,
  subtitle: String,
  loading: Boolean,
  empty: Boolean,
  emptyText: String,
  minHeight: { type: String, default: '320px' },
})
</script>

<style scoped>
.cp-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px; padding:20px 20px 0 }
.cp-title { font-size:18px; font-weight:600; color:var(--ci-primary) }
.cp-subtitle { font-size:13px; color:var(--ci-text-muted); margin-top:4px }
.cp-body { padding: 0 20px 20px; min-height: 260px }
</style>
