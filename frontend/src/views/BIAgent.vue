<template>
  <div class="agent-root" :class="{ 'agent-root--open': isOpen }">
    <!-- 收回态 -->
    <Transition name="fab">
      <button v-if="!isOpen" class="agent-fab" @click="isOpen = true" title="AI 分析助手">🌿</button>
    </Transition>

    <!-- 展开态 -->
    <Transition name="panel">
      <aside v-if="isOpen" class="agent-sidebar">
      <div class="agent-hd">
        <span>🌿 AI 分析助手</span>
        <button class="agent-toggle" @click="isOpen = false" title="收起">◀</button>
      </div>

      <div class="agent-msgs" ref="msgBox">
        <div v-for="(m,i) in messages" :key="i" :class="['msg', m.role]">
          <div class="msg-bubble">{{ m.content }}</div>
          <div v-if="m.table" class="msg-table">
            <el-table :data="m.table.rows" size="small" border>
              <el-table-column v-for="(col,ci) in m.table.columns" :key="ci" :prop="String(ci)" :label="col" />
            </el-table>
          </div>
          <div v-if="m.chart" class="msg-chart">
            <v-chart :option="m.chartOption" style="height:180px" autoresize />
          </div>
        </div>
        <div v-if="loading" class="msg assistant"><div class="msg-bubble">⏳ 分析中...</div></div>
      </div>

      <div class="agent-input">
        <el-input v-model="question" placeholder="输入问题..." size="small" :disabled="loading" maxlength="300" @keyup.enter="send" />
        <el-button type="primary" size="small" :loading="loading" @click="send">发送</el-button>
      </div>

      <div class="agent-quick">
        <el-tag v-for="q in quickQuestions" :key="q" size="small" @click="question=q;send()" style="cursor:pointer;margin:2px">{{ q }}</el-tag>
      </div>
    </aside>
    </Transition>
  </div>
</template>

<script setup>
import { ref, inject, nextTick, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'; import { CanvasRenderer } from 'echarts/renderers'; import { BarChart, LineChart, PieChart } from 'echarts/charts'; import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])
import { askAgent } from '../api'
import { chartColors, baseTooltip, baseGrid } from '../composables/useDashboardTheme'

const selectedYear = inject('selectedYear', ref(2024))
const isOpen = ref(false)
const question = ref('')
const loading = ref(false)
const msgBox = ref(null)
const messages = ref([{ role:'assistant', content:'🌿 你好！我是气候智能分析助手。支持：全球均温、月度趋势、站点排名、气候带分布、多年对比。' }])
const quickQuestions = ['全球平均气温？','最热的5个站点？','各月温度变化？','气候带分布？','2022和2023哪个更热？']

defineExpose({ open:()=>{ isOpen.value=true }, toggle:()=>{ isOpen.value=!isOpen.value } })

watch(isOpen, async(v) => {
  if (v) { await nextTick(); scrollBottom() }
  // 等CSS过渡完成后再触发resize
  setTimeout(() => window.dispatchEvent(new Event('resize')), 500)
})
function scrollBottom(){ nextTick(()=>{ const el=msgBox.value; if(el) el.scrollTop=el.scrollHeight }) }

function chartToOption(c){
  if(!c) return {}
  const t = baseTooltip()
  const g = baseGrid()
  if(c.type==='bar') return { tooltip:t, grid:g, xAxis:{type:'category',data:c.x,axisLabel:{rotate:25,fontSize:9,color:chartColors.text},axisLine:{lineStyle:{color:chartColors.outline}}}, yAxis:{type:'value',name:c.name,axisLabel:{color:chartColors.text,fontSize:9},splitLine:{lineStyle:{color:chartColors.grid}}}, series:[{type:'bar',data:c.y,barMaxWidth:24,itemStyle:{borderRadius:[4,4,0,0],color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:chartColors.primary},{offset:1,color:chartColors.teal}]}}}] }
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
.agent-root {
  width: 320px; min-width: 0; overflow: hidden; flex-shrink: 0;
  display: flex; flex-direction: column;
}
.agent-root:not(:has(.agent-sidebar)) {
  width: 0;
}
.agent-sidebar {
  width: 320px; flex-shrink: 0; flex-grow: 1;
  display: flex; flex-direction: column;
  background: var(--ci-glass-strong); backdrop-filter: blur(16px);
  border: 1px solid rgb(192 201 193 / 30%); border-radius: 16px;
  box-shadow: var(--ci-shadow); overflow: hidden;
}

/* 过渡动画 */
.panel-enter-active { transition: all .35s cubic-bezier(.4, 0, .2, 1); }
.panel-leave-active { transition: all .25s cubic-bezier(.4, 0, 1, 1); }
.panel-enter-from { opacity: 0; transform: translateX(40px); }
.panel-leave-to { opacity: 0; transform: translateX(40px); }

.fab-enter-active { transition: all .35s cubic-bezier(.4, 0, .2, 1) .15s; }
.fab-leave-active { transition: all .2s cubic-bezier(.4, 0, 1, 1); }
.fab-enter-from, .fab-leave-to { opacity: 0; transform: scale(.5) translateY(16px); }
.agent-hd {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px; background: var(--ci-primary); color: #fff;
  font-size: 14px; font-weight: 600; flex-shrink: 0; white-space: nowrap;
}
.agent-toggle { background: none; border: none; color: #fff; cursor: pointer; font-size: 14px; padding: 2px 6px; border-radius: 4px; }
.agent-toggle:hover { background: rgb(255 255 255 / 15%); }

/* 收回态按钮 */
.agent-fab {
  position: fixed; bottom: 24px; right: 24px; z-index: 100;
  width: 56px; height: 56px; border-radius: 50%; border: none;
  background: var(--ci-primary-container); color: #fff;
  box-shadow: 0 4px 16px rgb(20 66 45 / 35%);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all .2s; font-size: 24px;
}
.agent-fab:hover { background: var(--ci-primary); transform: translateY(-2px); box-shadow: 0 8px 24px rgb(20 66 45 / 50%); }

.agent-msgs { flex: 1; overflow-y: auto; padding: 10px; background: rgb(250 249 247 / 60%); min-height: 0; }
.msg { margin-bottom: 6px; display: flex; }
.msg.user { justify-content: flex-end; }
.msg.assistant { flex-direction: column; }
.msg-bubble { max-width: 90%; padding: 7px 12px; border-radius: 10px; font-size: 12px; line-height: 1.45; white-space: pre-wrap; word-break: break-word; }
.msg.user .msg-bubble { background: var(--ci-primary); color: #fff; }
.msg.assistant .msg-bubble { background: #fff; color: var(--ci-text); box-shadow: 0 1px 3px rgb(0 0 0 / 6%); }
.msg-table, .msg-chart { margin-top: 4px; }
.agent-input { display: flex; gap: 4px; padding: 8px 10px; border-top: 1px solid var(--ci-outline-variant); flex-shrink: 0; }
.agent-quick { padding: 4px 10px 6px; display: flex; flex-wrap: wrap; flex-shrink: 0; }

@media (max-width: 767px) {
  .agent-sidebar { width: 100%!important; max-width: 100%!important; min-width: 100%!important; position: fixed; inset: 0; z-index: 200; border-radius: 0; }
}
</style>
