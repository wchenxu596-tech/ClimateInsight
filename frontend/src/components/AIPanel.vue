<template>
  <div class="ai-root">
    <div class="ai-resize-handle" @mousedown="startResize" title="拖动调整宽度"></div>
    <div class="ai-header">
      <span>🌿 AI 分析助手</span>
      <button class="ai-close" @click="$emit('close')">✕</button>
    </div>

    <div class="ai-msgs" ref="msgBox">
      <div v-for="(m,i) in messages" :key="i" :class="['msg', m.role]">
        <div class="msg-bubble">{{ m.content }}</div>
        <div v-if="m.table" class="msg-table">
          <el-table :data="m.table.rows" size="small" border>
            <el-table-column v-for="(col,ci) in m.table.columns" :key="ci" :prop="String(ci)" :label="col" />
          </el-table>
        </div>
        <div v-if="m.chart" class="msg-chart">
          <v-chart :option="m.chartOption" style="height:150px" autoresize />
        </div>
      </div>
      <div v-if="loading" class="msg assistant"><div class="msg-bubble">⏳ 分析中...</div></div>
    </div>

    <div class="ai-input">
      <el-input v-model="question" placeholder="输入问题..." size="small" :disabled="loading" maxlength="300" @keyup.enter="send" />
      <el-button type="primary" size="small" :loading="loading" @click="send">发送</el-button>
    </div>

    <div class="ai-quick">
      <el-tag v-for="q in quickQuestions" :key="q" size="small" @click="question=q;send()" style="cursor:pointer;margin:2px">{{ q }}</el-tag>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, nextTick, onUnmounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'; import { CanvasRenderer } from 'echarts/renderers'; import { BarChart, LineChart, PieChart } from 'echarts/charts'; import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])
import { askAgent } from '../api'
import { chartColors, baseTooltip, baseGrid } from '../composables/useDashboardTheme'

defineEmits(['close'])
const selectedYear = inject('selectedYear', ref(2024))
const panelWidth = inject('panelWidth')
const question = ref('')
const loading = ref(false)
const msgBox = ref(null)
const messages = ref([{ role:'assistant', content:'🌿 你好！我是气候智能分析助手。支持：全球均温、月度趋势、站点排名、气候带分布、多年对比。' }])
const quickQuestions = ['全球平均气温？','最热的5个站点？','各月温度变化？','气候带分布？','2022和2023哪个更热？']

// 面板宽度拖拽
const MIN_W = 400, MAX_W = 500
let dragging = false, startX = 0, startW = 0

function startResize(e) {
  dragging = true; startX = e.clientX; startW = panelWidth.value
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'; document.body.style.userSelect = 'none'
}
function onDrag(e) {
  if (!dragging) return
  const dx = startX - e.clientX  // 向左拖 = 增大宽度
  const w = Math.min(MAX_W, Math.max(MIN_W, startW + dx))
  panelWidth.value = w
}
function stopResize() {
  dragging = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''; document.body.style.userSelect = ''
}
onUnmounted(stopResize)

function scrollBottom(){ nextTick(()=>{ const el=msgBox.value; if(el) el.scrollTop=el.scrollHeight }) }

function chartToOption(c){
  if(!c) return {}
  const t = baseTooltip()
  const g = baseGrid()
  if(c.type==='bar') return { tooltip:t, grid:g, xAxis:{type:'category',data:c.x,axisLabel:{rotate:25,fontSize:9,color:chartColors.text},axisLine:{lineStyle:{color:chartColors.outline}}}, yAxis:{type:'value',name:c.name,axisLabel:{color:chartColors.text,fontSize:9},splitLine:{lineStyle:{color:chartColors.grid}}}, series:[{type:'bar',data:c.y,barMaxWidth:20,itemStyle:{borderRadius:[4,4,0,0],color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:chartColors.primary},{offset:1,color:chartColors.teal}]}}}] }
  if(c.type==='line') return { tooltip:{...t,axisPointer:{type:'cross'}}, grid:g, xAxis:{type:'category',boundaryGap:false,data:c.x,axisLabel:{color:chartColors.text,fontSize:9},axisLine:{lineStyle:{color:chartColors.outline}}}, yAxis:{type:'value',name:c.name,axisLabel:{color:chartColors.text,fontSize:9},splitLine:{lineStyle:{color:chartColors.grid}}}, series:[{type:'line',data:c.y,smooth:true,symbolSize:6,itemStyle:{color:chartColors.green},areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(58,103,79,0.12)'},{offset:1,color:'rgba(58,103,79,0)'}]}}}] }
  if(c.type==='pie') return { tooltip:{...t,trigger:'item'}, series:[{type:'pie',radius:'50%',data:c.x.map((n,i)=>({name:n,value:c.y[i]}))}] }
  return {}
}
function tableRows(table){ return table?.rows?.map((row,i)=>{ const o={}; table.columns.forEach((col,ci)=>{ o[String(ci)]=row[ci] }); return o }) || [] }

async function send(){
  if(!question.value.trim()||loading.value) return
  const q=question.value.trim()
  messages.value.push({ role:'user', content:q })
  question.value=''; loading.value=true; scrollBottom()
  try{
    const res=await askAgent(q, selectedYear.value)
    const d=res.data?.data||{}
    const msg={ role:'assistant', content: d.answer||'查询完成' }
    if(d.table){ msg.table=d.table; msg.table.rows=tableRows(d.table) }
    if(d.chart){ msg.chart=d.chart; msg.chartOption=chartToOption(d.chart) }
    if(d.limitations?.length) msg.content+='\n'+d.limitations.join('；')
    messages.value.push(msg)
  }catch(e){ messages.value.push({ role:'assistant', content:'分析助手暂不可用，请确认后端已启动。' }) }
  loading.value=false; scrollBottom()
}
</script>

<style scoped>
.ai-root {
  position: absolute; inset: 0; overflow: hidden;
  display: flex; flex-direction: column;
  background: var(--ci-glass-strong); backdrop-filter: blur(16px);
  border-radius: 12px;
  box-shadow: -2px 0 16px rgb(0 0 0 / 6%);
}
.ai-resize-handle {
  position: absolute; left: 0; top: 0; bottom: 0; width: 6px;
  cursor: col-resize; z-index: 10;
  background: transparent;
  transition: background .2s;
}
.ai-resize-handle:hover { background: rgb(20 66 45 / 8%); }
.ai-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; background: var(--ci-primary); color: #fff;
  font-size: 17px; font-weight: 600; flex-shrink: 0; border-radius: 12px 12px 0 0;
}
.ai-close { background: none; border: none; color: #fff; cursor: pointer; font-size: 20px; padding: 2px 8px; border-radius: 4px; }
.ai-close:hover { background: rgb(255 255 255 / 15%); }

.ai-msgs { flex: 1; overflow-y: auto; padding: 10px; background: rgb(250 249 247 / 60%); min-height: 0; scrollbar-width: none; overscroll-behavior: contain; }
.ai-msgs::-webkit-scrollbar { display: none; }
.msg { margin-bottom: 6px; display: flex; }
.msg.user { justify-content: flex-end; }
.msg.assistant { flex-direction: column; }
.msg-bubble { max-width: 92%; padding: 8px 12px; border-radius: 10px; font-size: 15px; line-height: 1.45; white-space: pre-wrap; word-break: break-word; }
.msg.user .msg-bubble { background: var(--ci-primary); color: #fff; }
.msg.assistant .msg-bubble { background: #fff; color: var(--ci-text); box-shadow: 0 1px 3px rgb(0 0 0 / 6%); }
.msg-table, .msg-chart { margin-top: 4px; }
.ai-input { display: flex; gap: 4px; padding: 8px 10px; border-top: 1px solid var(--ci-outline-variant); flex-shrink: 0; }
.ai-quick { padding: 4px 10px 20px; display: flex; flex-wrap: wrap; flex-shrink: 0; }
</style>
