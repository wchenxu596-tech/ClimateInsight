<template>
  <GlassCard class="cp-root">
    <div class="cp-header">
      <div>
        <div class="cp-title">{{ title }}</div>
        <div v-if="subtitle" class="cp-subtitle">{{ subtitle }}</div>
      </div>
      <slot name="actions" />
    </div>
    <el-empty v-if="empty" :description="emptyText || '暂无数据'" style="flex:1;min-height:0" />
    <div v-else class="cp-body">
      <slot />
    </div>
  </GlassCard>
</template>

<script setup>
import GlassCard from './GlassCard.vue'
defineProps({ title:String, subtitle:String, empty:Boolean, emptyText:String })
</script>

<style scoped>
.cp-root { display:flex; flex-direction:column; overflow:visible }
.cp-header { display:flex; justify-content:space-between; align-items:flex-start; padding:10px 14px 0; flex-shrink:0 }
.cp-title { font-size:14px; font-weight:600; color:var(--ci-primary) }
.cp-subtitle { font-size:11px; color:var(--ci-text-muted); margin-top:2px }
.cp-body { flex:1; min-height:0; padding:4px 12px 10px; overflow:hidden }
</style>
