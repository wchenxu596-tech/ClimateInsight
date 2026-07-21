<template>
  <!-- 折叠态：悬浮按钮 -->
  <div
    v-if="!isOpen"
    class="agent-fab"
    @click="isOpen = true"
    title="AI 分析助手"
  >
    <span class="fab-icon">🤖</span>
  </div>

  <!-- 展开态：可拖拽面板 -->
  <div
    v-else
    class="agent-panel"
    :style="{ left: pos.x + 'px', top: pos.y + 'px', width: size.w + 'px', height: size.h + 'px' }"
    @wheel.stop="onPanelWheel"
  >
    <!-- 拖拽标题栏 -->
    <div class="panel-header" @mousedown="onDragStart">
      <span>🤖 AI 分析助手</span>
      <el-button :icon="'Minus'" size="small" circle @click.stop="isOpen = false" />
    </div>

    <!-- 消息区 -->
    <div class="panel-messages" ref="msgBox">
      <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
        <div class="msg-content">
          {{ m.content }}
          <div v-if="m.table" style="margin-top:6px">
            <el-table :data="m.table.rows" size="small" border>
              <el-table-column v-for="(col, ci) in m.table.columns" :key="ci" :prop="String(ci)" :label="col" />
            </el-table>
          </div>
          <div v-if="m.chart" style="margin-top:6px">
            <v-chart :option="m.chartOption" style="height:200px" autoresize />
          </div>
        </div>
      </div>
      <div v-if="loading" class="msg assistant"><div class="msg-content">⏳ 分析中...</div></div>
    </div>

    <!-- 输入区 -->
    <div class="panel-input">
      <el-input
        v-model="question"
        placeholder="输入问题..."
        size="small"
        :disabled="loading"
        maxlength="300"
        @keyup.enter="send"
      />
      <el-button type="primary" size="small" :loading="loading" @click="send">发送</el-button>
    </div>

    <!-- 快捷问题 -->
    <div class="panel-quick">
      <el-tag
        v-for="q in quickQuestions"
        :key="q"
        size="small"
        @click="question = q; send()"
        style="cursor:pointer;margin:2px"
      >{{ q }}</el-tag>
    </div>

    <!-- 缩放拖拽手柄 -->
    <div class="resize-handle" @mousedown.stop="onResizeStart"></div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, watch, onBeforeUnmount, inject } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])
import { askAgent } from '../api'

const selectedYear = inject('selectedYear', ref(2024))

const isOpen = ref(false)
const question = ref('')
const loading = ref(false)
const msgBox = ref(null)

const messages = ref([{
  role: 'assistant',
  content: '👋 你好！我是气候智能分析助手。支持：全球均温、月度趋势、站点排名、气候带分布。'
}])

const quickQuestions = [
  '全球平均气温？', '最热的5个站点？', '各月温度变化？',
  '气候带分布？', '降水最多的站点？', '最冷的3个站点？',
]

// ── 暴露方法供外部调用 ──
defineExpose({ open: () => { isOpen.value = true } })

// ── 滚轮只作用于面板内，不穿透到外层页面 ──
function onPanelWheel(e) {
  const el = msgBox.value
  if (!el) return
  const { scrollTop, scrollHeight, clientHeight } = el
  const atTop = scrollTop <= 0
  const atBottom = scrollTop + clientHeight >= scrollHeight - 1
  // 到边界时阻止外层页面滚动
  if ((atTop && e.deltaY < 0) || (atBottom && e.deltaY > 0)) {
    e.preventDefault()
  }
}

// ── 拖拽 ──
const pos = reactive({ x: window.innerWidth - 440, y: 60 })
const size = reactive({ w: 380, h: 460 })
let dragging = false, startX = 0, startY = 0

function onDragStart(e) {
  if (e.target.tagName === 'BUTTON') return  // 不拦截按钮点击
  dragging = true
  startX = e.clientX - pos.x
  startY = e.clientY - pos.y
  document.addEventListener('mousemove', onDragMove)
  document.addEventListener('mouseup', onDragEnd)
}

function onDragMove(e) {
  if (!dragging) return
  pos.x = Math.max(0, Math.min(e.clientX - startX, window.innerWidth - 380))
  pos.y = Math.max(0, Math.min(e.clientY - startY, window.innerHeight - 60))
}

function onDragEnd() {
  dragging = false
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
}

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeEnd)
})

// ── 缩放 ──
let resizing = false, rezStartW = 0, rezStartH = 0, rezStartX = 0, rezStartY = 0

function onResizeStart(e) {
  resizing = true
  rezStartW = size.w; rezStartH = size.h
  rezStartX = e.clientX; rezStartY = e.clientY
  document.addEventListener('mousemove', onResizeMove)
  document.addEventListener('mouseup', onResizeEnd)
}

function onResizeMove(e) {
  if (!resizing) return
  size.w = Math.max(300, Math.min(rezStartW + e.clientX - rezStartX, 700))
  size.h = Math.max(260, Math.min(rezStartH + e.clientY - rezStartY, 700))
}

function onResizeEnd() {
  resizing = false
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeEnd)
}

// ── 打开时滚动到底部 ──
watch(isOpen, async (v) => {
  if (v) await nextTick(); scrollBottom()
})

function scrollBottom() {
  nextTick(() => {
    const el = msgBox.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

// ── 图表转换 ──
function chartToOption(c) {
  if (!c) return {}
  if (c.type === 'bar') return { tooltip: { trigger: 'axis', valueFormatter: v => typeof v === 'number' ? v.toFixed(2) : v }, xAxis: { type: 'category', data: c.x, axisLabel: { rotate: 25, fontSize: 10 } }, yAxis: { type: 'value', name: c.name }, series: [{ type: 'bar', data: c.y, itemStyle: { color: '#e53935' } }] }
  if (c.type === 'line') return { tooltip: { trigger: 'axis', valueFormatter: v => typeof v === 'number' ? v.toFixed(2) : v }, xAxis: { type: 'category', data: c.x }, yAxis: { type: 'value', name: c.name }, series: [{ type: 'line', data: c.y, smooth: true, itemStyle: { color: '#e53935' } }] }
  if (c.type === 'pie') return { tooltip: { trigger: 'item' }, series: [{ type: 'pie', radius: '55%', data: c.x.map((n, i) => ({ name: n, value: c.y[i] })) }] }
  return {}
}

function tableRows(table) {
  return table?.rows?.map((row, i) => {
    const o = {}; table.columns.forEach((col, ci) => { o[String(ci)] = row[ci] }); return o
  }) || []
}

// ── 发送消息 ──
async function send() {
  if (!question.value.trim() || loading.value) return
  const q = question.value.trim()
  messages.value.push({ role: 'user', content: q })
  question.value = ''
  loading.value = true
  scrollBottom()
  try {
    const res = await askAgent(q, selectedYear.value)
    const d = res.data?.data || {}
    const msg = { role: 'assistant', content: d.answer || '查询完成' }
    if (d.table) { msg.table = d.table; msg.table.rows = tableRows(d.table) }
    if (d.chart) { msg.chart = d.chart; msg.chartOption = chartToOption(d.chart) }
    if (d.limitations?.length) msg.content += '\n⚠️ ' + d.limitations.join('；')
    messages.value.push(msg)
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '分析助手暂不可用，请确认后端已启动。' })
  }
  loading.value = false
  scrollBottom()
}
</script>

<style scoped>
/* ── 悬浮按钮 ── */
.agent-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1a237e, #0d47a1);
  box-shadow: 0 4px 16px rgba(26, 35, 126, .4);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform .2s, box-shadow .2s;
  user-select: none;
}
.agent-fab:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 24px rgba(26, 35, 126, .55);
}
.fab-icon { font-size: 26px; }

/* ── 展开面板 ── */
.agent-panel {
  position: fixed;
  z-index: 9999;
  width: 380px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, .18);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: linear-gradient(135deg, #1a237e, #0d47a1);
  color: #fff;
  font-size: 14px;
  font-weight: bold;
  cursor: move;
  user-select: none;
}

.panel-messages {
  flex: 1;
  min-height: 120px;
  overflow-y: auto;
  padding: 10px;
  background: #f8f9fb;
}

.msg { margin-bottom: 8px; display: flex; }
.msg.user { justify-content: flex-end; }
.msg-content {
  max-width: 88%;
  padding: 7px 12px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
.msg.user .msg-content { background: #1a237e; color: #fff; }
.msg.assistant .msg-content { background: #fff; color: #333; box-shadow: 0 1px 3px rgba(0,0,0,.06); }

.panel-input {
  display: flex;
  gap: 6px;
  padding: 8px 10px;
  border-top: 1px solid #eee;
}

.panel-quick {
  padding: 4px 10px 8px;
  display: flex;
  flex-wrap: wrap;
}

.resize-handle {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 16px;
  height: 16px;
  cursor: nwse-resize;
  background: linear-gradient(135deg, transparent 50%, rgba(26,35,126,.25) 50%);
  border-radius: 0 0 12px 0;
}
</style>
