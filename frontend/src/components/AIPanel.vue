<template>
  <div class="ai-root">
    <div class="ai-header">
      <span class="ai-title">🌿 AI 分析</span>
      <button class="ai-close" @click="$emit('close')">✕</button>
    </div>
    <div class="ai-body">
      <div class="ai-section">
        <div class="ai-section-title">📊 数据解读</div>
        <p class="ai-text">{{ insight }}</p>
      </div>
      <div class="ai-section">
        <div class="ai-section-title">⚠️ 异常提醒</div>
        <div v-if="alerts.length" class="ai-alerts">
          <div v-for="a in alerts" :key="a.station" class="ai-alert-item">
            <span class="ai-alert-icon">{{ a.icon }}</span>
            <span class="ai-alert-text">{{ a.station }}: {{ a.desc }}</span>
          </div>
        </div>
        <p v-else class="ai-text">当前无异常天气事件。</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, watch } from 'vue'
import { getKPI, getRanking } from '../api'

defineEmits(['close'])
const selectedYear = inject('selectedYear')

const insight = ref('加载中...')
const alerts = ref([])

watch(selectedYear, load, { immediate: true })

async function load() {
  try {
    const [kpiRes, hotRes] = await Promise.all([
      getKPI(selectedYear.value),
      getRanking(selectedYear.value, 'hottest', 3),
    ])
    const kpiData = kpiRes.data?.data || []
    const avgTemp = kpiData.find(k => k.kpi_name === 'global_avg_temp')?.kpi_value || '--'
    const stations = kpiData.find(k => k.kpi_name === 'total_stations')?.kpi_value || '--'
    const extreme = kpiData.find(k => k.kpi_name === 'extreme_event_pct')?.kpi_value || '--'

    insight.value = `${selectedYear.value} 年全球年均温 ${avgTemp}°C，覆盖 ${stations} 个气象站。极端天气占比 ${extreme}%。`

    const hotStations = hotRes.data?.data || []
    alerts.value = hotStations.slice(0, 5).map((s, i) => ({
      station: s.station_name?.substring(0, 12) || s.station_id,
      desc: `最高温 ${s.value}°C`,
      icon: i === 0 ? '🔥' : '🌡️',
    }))
  } catch {
    insight.value = '数据加载失败，请确认后端已启动。'
  }
}
</script>

<style scoped>
.ai-root {
  width: 280px; height: 100%;
  display: flex; flex-direction: column;
  background: rgb(250 249 247 / 92%); backdrop-filter: blur(16px);
  border-left: 1px solid rgb(192 201 193 / 40%);
  border-radius: 16px 0 0 16px;
  box-shadow: -4px 0 24px rgb(0 0 0 / 8%);
}
.ai-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 16px 10px; flex-shrink: 0;
  border-bottom: 1px solid var(--ci-outline-variant);
}
.ai-title { font-size: 16px; font-weight: 700; color: var(--ci-primary); }
.ai-close {
  background: none; border: none; font-size: 18px; color: var(--ci-text-muted);
  cursor: pointer; padding: 2px 6px; border-radius: 6px;
}
.ai-close:hover { background: var(--ci-surface-container); }
.ai-body { flex: 1; overflow-y: auto; padding: 12px 16px; }
.ai-section { margin-bottom: 16px; }
.ai-section-title { font-size: 14px; font-weight: 600; color: var(--ci-primary); margin-bottom: 8px; }
.ai-text { font-size: 13px; color: var(--ci-text-muted); line-height: 1.6; margin: 0; }
.ai-alerts { display: flex; flex-direction: column; gap: 8px; }
.ai-alert-item { display: flex; align-items: flex-start; gap: 8px; font-size: 12px; color: var(--ci-text); padding: 8px 10px; background: var(--ci-surface-container); border-radius: 8px; }
.ai-alert-icon { font-size: 16px; flex-shrink: 0; }
.ai-alert-text { line-height: 1.4; }
</style>
