<template>
  <div>
    <h2 class="page-title">🤖 AI 分析助手</h2>
    <div class="chat-box">
      <div class="messages" ref="msgBox">
        <div v-for="(m,i) in messages" :key="i" :class="['msg', m.role]">
          <div class="msg-content">
            {{ m.content }}
            <div v-if="m.table" style="margin-top:8px">
              <el-table :data="m.table.rows" size="small" border>
                <el-table-column v-for="(col,ci) in m.table.columns" :key="ci" :prop="String(ci)" :label="col" />
              </el-table>
            </div>
            <div v-if="m.chart" style="margin-top:8px">
              <v-chart :option="m.chartOption" style="height:250px" autoresize />
            </div>
          </div>
        </div>
        <div v-if="loading" class="msg assistant"><div class="msg-content">⏳ 分析中...</div></div>
      </div>
      <div class="input-row">
        <el-input v-model="question" placeholder="如：2024年最热的10个站点？" @keyup.enter="send" size="large" :disabled="loading" maxlength="300" />
        <el-button type="primary" @click="send" size="large" :loading="loading">发送</el-button>
      </div>
      <div class="quick-qs">
        <el-tag v-for="q in quickQuestions" :key="q" @click="question=q;send()" style="cursor:pointer;margin:4px" :disable-transitions="false">{{ q }}</el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])
import { askAgent } from '../api'

const question = ref('')
const messages = ref([{ role:'assistant', content:'👋 你好！我是气候智能分析助手。当前支持：全球均温查询、月度气温趋势、站点排名（最热/最冷/降水/极端天气）、气候带分布。' }])
const loading = ref(false)

const quickQuestions = [
  '2024年全球平均气温？', '最热的10个站点？', '各月温度变化？',
  '气候带分布？', '降水最多的站点？', '最冷的5个站点？',
]

function chartToOption(c) {
  if (!c) return {}
  if (c.type === 'bar') return { tooltip:{trigger:'axis'}, xAxis:{type:'category',data:c.x,axisLabel:{rotate:30}}, yAxis:{type:'value',name:c.name}, series:[{type:'bar',data:c.y,itemStyle:{color:'#e53935'}}] }
  if (c.type === 'line') return { tooltip:{trigger:'axis'}, xAxis:{type:'category',data:c.x}, yAxis:{type:'value',name:c.name}, series:[{type:'line',data:c.y,smooth:true,itemStyle:{color:'#e53935'}}] }
  if (c.type === 'pie') return { tooltip:{trigger:'item'}, series:[{type:'pie',radius:'60%',data:c.x.map((n,i)=>({name:n,value:c.y[i]}))}] }
  return {}
}

function tableRows(table) {
  return table?.rows?.map((row,i) => {
    const o = {}; table.columns.forEach((col,ci) => { o[String(ci)] = row[ci] }); return o
  }) || []
}

async function send() {
  if (!question.value.trim() || loading.value) return
  const q = question.value.trim()
  messages.value.push({ role:'user', content: q })
  question.value = ''
  loading.value = true; await nextTick()
  try {
    const res = await askAgent(q, 2024)
    const d = res.data?.data || {}
    const msg = { role:'assistant', content: d.answer || '查询完成' }
    if (d.table) { msg.table = d.table; msg.table.rows = tableRows(d.table) }
    if (d.chart) { msg.chart = d.chart; msg.chartOption = chartToOption(d.chart) }
    if (d.limitations?.length) msg.content += '\n⚠️ ' + d.limitations.join('；')
    messages.value.push(msg)
  } catch(e) {
    messages.value.push({ role:'assistant', content:'分析助手暂不可用，请确认后端已启动或使用导航栏查看预置看板。' })
  }
  loading.value = false
}
</script>

<style scoped>
.page-title{font-size:22px;font-weight:bold;color:#1a237e;margin-bottom:20px}
.chat-box{background:#fff;border-radius:10px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.messages{max-height:480px;overflow-y:auto;margin-bottom:16px}
.msg{margin-bottom:12px;display:flex}
.msg.user{justify-content:flex-end}
.msg-content{max-width:80%;padding:10px 16px;border-radius:12px;font-size:14px;line-height:1.6;white-space:pre-wrap}
.msg.user .msg-content{background:#1a237e;color:#fff}
.msg.assistant .msg-content{background:#f0f2f5;color:#333}
.input-row{display:flex;gap:10px}
.quick-qs{margin-top:12px}
</style>
