<template>
  <!-- 折叠态 -->
  <button v-if="!isOpen" class="agent-fab" @click="isOpen=true" aria-label="打开 AI 气候分析助手">
    <span>🤖</span>
  </button>

  <!-- 展开态 -->
  <div v-else class="agent-panel" :style="{ left:pos.x+'px', top:pos.y+'px', width:size.w+'px', height:size.h+'px' }" @wheel.stop="onPanelWheel">
    <!-- 标题栏 -->
    <div class="panel-hd" @mousedown="onDragStart">
      <div class="panel-hd-left">
        <span class="panel-icon">🤖</span>
        <div>
          <div class="panel-title">AI 气候分析助手</div>
          <div class="panel-sub">可根据当前 {{ selectedYear }} 年数据回答</div>
        </div>
      </div>
      <el-button size="small" text @click.stop="isOpen=false" style="color:#fff">−</el-button>
    </div>

    <!-- 消息区 -->
    <div class="panel-msgs" ref="msgBox">
      <div v-for="(m,i) in messages" :key="i" :class="['msg', m.role]">
        <div class="msg-bubble">{{ m.content }}</div>
        <div v-if="m.table" class="msg-table">
          <el-table :data="m.table.rows" size="small" border>
            <el-table-column v-for="(col,ci) in m.table.columns" :key="ci" :prop="String(ci)" :label="col" />
          </el-table>
        </div>
        <div v-if="m.chart" class="msg-chart">
          <v-chart :option="m.chartOption" style="height:200px" autoresize />
        </div>
      </div>
      <div v-if="loading" class="msg assistant"><div class="msg-bubble">⏳ 分析中...</div></div>
    </div>

    <!-- 输入 -->
    <div class="panel-input">
      <el-input v-model="question" placeholder="输入问题..." size="small" :disabled="loading" maxlength="300" @keyup.enter="send" />
      <el-button type="primary" size="small" :loading="loading" @click="send">发送</el-button>
    </div>
    <div class="panel-quick">
      <el-tag v-for="q in quickQuestions" :key="q" size="small" @click="question=q;send()" style="cursor:pointer;margin:2px">{{ q }}</el-tag>
    </div>

    <!-- 缩放 -->
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
import { chartColors, baseTooltip } from '../composables/useDashboardTheme'

const selectedYear = inject('selectedYear', ref(2024))
const isOpen = ref(false)
const question = ref('')
const loading = ref(false)
const msgBox = ref(null)
const messages = ref([{ role:'assistant', content:'👋 你好！我是气候智能分析助手。支持：全球均温、月度趋势、站点排名、气候带分布。' }])

const quickQuestions = ['全球平均气温？','最热的5个站点？','各月温度变化？','气候带分布？','降水最多的站点？','最冷的3个站点？']

defineExpose({ open:()=>{ isOpen.value=true } })

// 拖拽
const pos = reactive({ x: window.innerWidth-420, y: 80 })
const size = reactive({ w: 380, h: 460 })
let dragging=false, startX=0, startY=0

function onDragStart(e){ if(e.target.tagName==='BUTTON') return; dragging=true; startX=e.clientX-pos.x; startY=e.clientY-pos.y; document.addEventListener('mousemove',onDragMove); document.addEventListener('mouseup',onDragEnd) }
function onDragMove(e){ if(!dragging) return; pos.x=Math.max(0,Math.min(e.clientX-startX,window.innerWidth-size.w)); pos.y=Math.max(0,Math.min(e.clientY-startY,window.innerHeight-60)) }
function onDragEnd(){ dragging=false; document.removeEventListener('mousemove',onDragMove); document.removeEventListener('mouseup',onDragEnd) }

let resizing=false, rzW=0, rzH=0, rzX=0, rzY=0
function onResizeStart(e){ resizing=true; rzW=size.w; rzH=size.h; rzX=e.clientX; rzY=e.clientY; document.addEventListener('mousemove',onResizeMove); document.addEventListener('mouseup',onResizeEnd) }
function onResizeMove(e){ if(!resizing) return; size.w=Math.max(300,Math.min(rzW+e.clientX-rzX,700)); size.h=Math.max(260,Math.min(rzH+e.clientY-rzY,700)) }
function onResizeEnd(){ resizing=false; document.removeEventListener('mousemove',onResizeMove); document.removeEventListener('mouseup',onResizeEnd) }

onBeforeUnmount(()=>{ document.removeEventListener('mousemove',onDragMove); document.removeEventListener('mouseup',onDragEnd); document.removeEventListener('mousemove',onResizeMove); document.removeEventListener('mouseup',onResizeEnd) })

function onPanelWheel(e){ const el=msgBox.value; if(!el) return; const{scrollTop,scrollHeight,clientHeight}=el; if((scrollTop<=0&&e.deltaY<0)||(scrollTop+clientHeight>=scrollHeight-1&&e.deltaY>0)) e.preventDefault() }

watch(isOpen, async(v)=>{ if(v) await nextTick(); scrollBottom() })
function scrollBottom(){ nextTick(()=>{ const el=msgBox.value; if(el) el.scrollTop=el.scrollHeight }) }

// 图表转换
function chartToOption(c){
  if(!c) return {}
  const t = baseTooltip()
  if(c.type==='bar') return { tooltip:t, xAxis:{type:'category',data:c.x,axisLabel:{rotate:25,fontSize:10}}, yAxis:{type:'value',name:c.name}, series:[{type:'bar',data:c.y,itemStyle:{color:chartColors.orange}}] }
  if(c.type==='line') return { tooltip:t, xAxis:{type:'category',data:c.x}, yAxis:{type:'value',name:c.name}, series:[{type:'line',data:c.y,smooth:true,itemStyle:{color:chartColors.green}}] }
  if(c.type==='pie') return { tooltip:{ ...t, trigger:'item' }, series:[{type:'pie',radius:'55%',data:c.x.map((n,i)=>({name:n,value:c.y[i]}))}] }
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
    if(d.limitations?.length) msg.content+='\n⚠️ '+d.limitations.join('；')
    messages.value.push(msg)
  }catch(e){ messages.value.push({ role:'assistant', content:'分析助手暂不可用，请确认后端已启动。' }) }
  loading.value=false; scrollBottom()
}
</script>

<style scoped>
.agent-fab {
  position:fixed; bottom:24px; right:24px; z-index:100;
  width:64px; height:64px; border-radius:50%; border:none;
  background:var(--ci-primary-container); color:#fff;
  box-shadow:0 4px 16px rgb(20 66 45 / 35%);
  display:flex; align-items:center; justify-content:center;
  cursor:pointer; transition:all .2s; font-size:28px;
}
.agent-fab:hover { background:var(--ci-primary); transform:translateY(-2px); box-shadow:0 8px 24px rgb(20 66 45 / 50%) }

.agent-panel {
  position:fixed; z-index:100;
  background:var(--ci-glass-strong); backdrop-filter:blur(16px);
  border:1px solid rgb(192 201 193 / 30%); border-radius:12px;
  box-shadow:0 8px 32px rgb(0 0 0 / 12%);
  display:flex; flex-direction:column; overflow:hidden;
}
.panel-hd {
  display:flex; justify-content:space-between; align-items:center;
  padding:12px 16px; background:var(--ci-primary);
  color:#fff; cursor:move; user-select:none;
}
.panel-hd-left { display:flex; align-items:center; gap:10px }
.panel-icon { font-size:22px }
.panel-title { font-size:14px; font-weight:600 }
.panel-sub { font-size:11px; opacity:.8 }
.panel-msgs { flex:1; min-height:120px; overflow-y:auto; padding:12px; background:rgb(250 249 247 / 60%) }
.msg { margin-bottom:8px; display:flex }
.msg.user { justify-content:flex-end }
.msg-bubble { max-width:88%; padding:8px 14px; border-radius:12px; font-size:13px; line-height:1.5; white-space:pre-wrap; word-break:break-word }
.msg.user .msg-bubble { background:var(--ci-primary); color:#fff }
.msg.assistant .msg-bubble { background:#fff; color:var(--ci-text); box-shadow:0 1px 3px rgb(0 0 0 / 6%) }
.msg-table, .msg-chart { margin-top:6px }
.panel-input { display:flex; gap:6px; padding:8px 12px; border-top:1px solid var(--ci-outline-variant) }
.panel-quick { padding:4px 12px 8px; display:flex; flex-wrap:wrap }
.resize-handle { position:absolute; bottom:0; right:0; width:16px; height:16px; cursor:nwse-resize; background:linear-gradient(135deg,transparent 50%,var(--ci-outline-variant) 50%); border-radius:0 0 12px 0 }

@media (max-width: 639px) {
  .agent-fab { width:56px; height:56px; bottom:16px; right:16px; font-size:24px }
  .agent-panel { width:calc(100vw - 32px)!important; max-height:calc(100vh - 112px); left:16px!important }
}
</style>
