<template>
  <div :class="['msg', role]">
    <div class="msg-bubble">{{ content }}</div>
    <div v-if="table" class="msg-table">
      <el-table :data="tableRows" size="small" border max-height="200">
        <el-table-column v-for="(col, ci) in table.columns" :key="ci" :prop="String(ci)" :label="col" />
      </el-table>
    </div>
    <div v-if="chartOption" class="msg-chart">
      <v-chart :option="chartOption" style="height:160px" autoresize />
    </div>
    <div v-if="stats && stats.length" class="msg-stats">
      <div v-for="s in stats" :key="s.method" class="stat-item">
        <span class="stat-method">{{ s.method }}</span>
        <span v-if="s.slope != null">斜率 {{ s.slope }} / {{ s.unit_per_decade }}/十年</span>
        <span v-if="s.r_squared != null">R²={{ s.r_squared }}</span>
        <span v-if="s.anomaly_count != null">{{ s.anomaly_count }} 异常 / {{ s.sample_count }} 样本</span>
      </div>
    </div>
    <div v-if="alerts && alerts.length" class="msg-alerts">
      <div v-for="a in alerts" :key="a.rule_id" :class="['alert-tag', a.severity]">
        {{ a.severity === 'red' ? '🔴' : a.severity === 'orange' ? '🟠' : '🟡' }} {{ a.evidence?.rule_name }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'; import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const props = defineProps({
  role: { type: String, default: 'assistant' },
  content: { type: String, default: '' },
  table: Object,
  chartOption: Object,
  stats: Array,
  alerts: Array,
})

const tableRows = computed(() => {
  if (!props.table?.rows) return []
  return props.table.rows.map((row, i) => {
    const o = { _key: i }
    props.table.columns.forEach((col, ci) => { o[String(ci)] = row[ci] })
    return o
  })
})
</script>

<style scoped>
.msg { margin-bottom: 6px; display: flex; }
.msg.user { justify-content: flex-end; }
.msg.assistant { flex-direction: column; }
.msg-bubble { max-width: 92%; padding: 8px 12px; border-radius: 10px; font-size: 15px; line-height: 1.45; white-space: pre-wrap; word-break: break-word; }
.msg.user .msg-bubble { background: var(--ci-primary); color: #fff; }
.msg.assistant .msg-bubble { background: #fff; color: var(--ci-text); box-shadow: 0 1px 3px rgb(0 0 0 / 6%); }
.msg-table, .msg-chart, .msg-stats, .msg-alerts { margin-top: 4px; }
.msg-stats { display: flex; flex-wrap: wrap; gap: 4px; }
.stat-item { font-size: 11px; padding: 2px 8px; background: rgb(58 103 79 / 8%); border-radius: 6px; color: var(--ci-text-muted); }
.stat-method { font-weight: 600; color: var(--ci-primary); margin-right: 6px; }
.msg-alerts { display: flex; flex-wrap: wrap; gap: 4px; }
.alert-tag { font-size: 12px; padding: 3px 10px; border-radius: 6px; font-weight: 600; }
.alert-tag.red { background: #ffdbce; color: #8b3713; }
.alert-tag.orange { background: #fff3e0; color: #c78b3c; }
.alert-tag.yellow { background: #fffde7; color: #8a7d14; }
</style>
