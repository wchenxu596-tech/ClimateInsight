<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="暂无月度数据" @retry="load">
      <div class="trend-layout">
        <aside class="trend-sidebar">
          <GlassCard class="sb-card">
            <div class="sb-label">数据范围</div>
            <div class="sb-value">全球 / {{ selectedYear }} 年</div>
            <div class="sb-note">数据来源：NOAA GSOD</div>
          </GlassCard>
          <GlassCard class="sb-card">
            <div class="sb-label">年度峰值平均气温</div>
            <div class="sb-value highlight">{{ peakTemp != null ? peakTemp.toFixed(2) + '°C' : '--' }}</div>
            <div class="sb-note">{{ peakMonth ? peakMonth + '月记录' : '暂无数据' }}</div>
          </GlassCard>
          <GlassCard class="sb-card">
            <div class="sb-label">全年平均气温</div>
            <div class="sb-value">{{ annualAvg != null ? annualAvg.toFixed(2) + '°C' : '--' }}</div>
          </GlassCard>
          <GlassCard class="sb-card">
            <div class="sb-label">年度最高平均气温</div>
            <div class="sb-value">{{ peakMax != null ? peakMax.toFixed(2) + '°C' : '--' }}</div>
          </GlassCard>
        </aside>

        <ChartPanel :title="'月度气温变化'" :subtitle="'全球月度平均、平均最高与平均最低气温'" style="flex:1;min-height:0;min-width:0">
          <v-chart ref="chartRef" :option="option" autoresize />
        </ChartPanel>
      </div>
    </PageState>
  </div>
</template>

<script setup>
import { ref, reactive, inject, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

import { getMonthly } from '../api'
import PageState from '../components/PageState.vue'
import GlassCard from '../components/GlassCard.vue'
import ChartPanel from '../components/ChartPanel.vue'
import { chartColors, baseTooltip, monthLabels, safeNumber } from '../composables/useDashboardTheme'

const selectedYear = inject('selectedYear')
const loading = ref(true); const error = ref(''); const empty = ref(false)
let requestId = 0; const chartRef = ref(null)

const option = reactive({ tooltip: {...baseTooltip(),axisPointer:{type:'cross'}}, legend:{data:['均温','均最高','均最低'],textStyle:{color:chartColors.text,fontSize:11},top:0,itemWidth:14,itemHeight:8}, grid:{left:'3%',right:'4%',top:'14%',bottom:'3%',containLabel:true}, xAxis:{type:'category',boundaryGap:false,data:monthLabels,axisLabel:{color:chartColors.text,fontSize:11},axisLine:{lineStyle:{color:chartColors.outline}}}, yAxis:{type:'value',name:'气温（°C）',axisLabel:{color:chartColors.text,fontSize:11},splitLine:{lineStyle:{color:chartColors.grid}}}, series:[] })

const peakTemp = ref(null); const peakMonth = ref(null); const annualAvg = ref(null); const peakMax = ref(null)

async function load(){
  const id=++requestId; loading.value=true; error.value=''; empty.value=false
  try{
    const res=await getMonthly(selectedYear.value); if(id!==requestId) return
    const rows=(res.data?.data||[]).sort((a,b)=>a.obs_month-b.obs_month)
    if(!rows.length){empty.value=true;loading.value=false;return}
    const temps=rows.map(r=>safeNumber(r.avg_temp)), maxs=rows.map(r=>safeNumber(r.avg_max)), mins=rows.map(r=>safeNumber(r.avg_min))
    option.series=[
      {name:'均温',type:'line',data:temps,smooth:true,symbolSize:6,itemStyle:{color:chartColors.green},areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(58,103,79,0.12)'},{offset:1,color:'rgba(58,103,79,0)'}]}},markPoint:{data:[{type:'max',name:'峰值',itemStyle:{color:chartColors.orange},label:{color:'#fff',fontSize:10}}]}},
      {name:'均最高',type:'line',data:maxs,smooth:true,symbolSize:6,itemStyle:{color:chartColors.orange},areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(139,55,19,0.1)'},{offset:1,color:'rgba(139,55,19,0)'}]}}},
      {name:'均最低',type:'line',data:mins,smooth:true,symbolSize:6,itemStyle:{color:chartColors.teal}},
    ]
    const vt=temps.filter(Number.isFinite); annualAvg.value=vt.length?vt.reduce((a,b)=>a+b,0)/vt.length:null
    const vm=maxs.filter(Number.isFinite); peakMax.value=vm.length?Math.max(...vm):null
    let bv=-Infinity,bi=-1; temps.forEach((v,i)=>{if(v!=null&&v>bv){bv=v;bi=i}})
    peakTemp.value=bi>=0?bv:null; peakMonth.value=bi>=0?rows[bi].obs_month:null
  }catch(e){if(id===requestId){error.value='数据加载失败，请确认后端已启动';console.error(e)}}
  finally{if(id===requestId)loading.value=false}
}
watch(selectedYear,load,{immediate:true})
</script>

<style scoped>
.trend-layout { display:grid; grid-template-columns:200px minmax(0,1fr); gap:12px; flex:1; min-height:0; overflow:hidden }
.trend-sidebar { display:flex; flex-direction:column; gap:8px; overflow-y:auto }
.sb-card { padding:10px 12px; flex-shrink:0 }
.sb-label { font-size:11px; font-weight:500; text-transform:uppercase; letter-spacing:0.05em; color:var(--ci-text-muted); margin-bottom:4px }
.sb-value { font-size:20px; font-weight:700; color:var(--ci-text) }
.sb-value.highlight { color:var(--ci-tertiary) }
.sb-note { font-size:12px; color:var(--ci-text-muted); margin-top:2px }

@media (max-width: 767px) {
  .trend-layout { grid-template-columns:1fr }
  .trend-sidebar { flex-direction:row; overflow-x:auto; gap:8px }
  .sb-card { min-width:140px }
}
</style>
