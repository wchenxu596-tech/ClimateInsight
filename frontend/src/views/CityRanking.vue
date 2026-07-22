<template>
  <div class="page-container">
    <PageState :loading="loading" :error="error" :empty="empty" empty-text="暂无排名数据" @retry="load">
      <div class="ranking-header">
        <div>
          <h1 class="page-h1">{{ selectedYear }} 年全球站点排名</h1>
          <p class="page-sub">基于 NOAA GSOD 年度聚合数据</p>
        </div>
        <div class="cat-tabs" role="tablist">
          <button v-for="cat in categories" :key="cat.key" role="tab" :aria-selected="category===cat.key"
            :class="['cat-btn',{active:category===cat.key}]" @click="category=cat.key;load()">{{ cat.label }}</button>
        </div>
      </div>

      <div class="ranking-body">
        <ChartPanel :title="meta.title" :subtitle="'单位：' + meta.unit" style="flex:1;min-height:0">
          <v-chart v-if="hasData" :option="chartOption" autoresize />
          <el-empty v-else description="暂无数据" />
        </ChartPanel>

        <GlassCard class="table-card">
          <div class="table-hd">详细数据</div>
          <div class="table-card-wrap"><el-table :data="tableData" border stripe size="small" style="width:100%">
            <el-table-column prop="rank_num" label="#" width="50" align="center">
              <template #default="{row}"><span :style="{fontWeight:row.rank_num===1?'bold':'',color:row.rank_num===1?'var(--ci-tertiary)':''}">{{ row.rank_num }}</span></template>
            </el-table-column>
            <el-table-column label="站点" min-width="140">
              <template #default="{row}">{{ stationCN(row.station_name||'') }}</template>
            </el-table-column>
            <el-table-column :label="meta.label+'('+meta.unit+')'" width="120" align="right">
              <template #default="{row}">{{ safeNumber(row.value)?.toFixed(2)??'--' }}</template>
            </el-table-column>
          </el-table></div>
        </GlassCard>
      </div>
    </PageState>
  </div>
</template>

<script setup>
import { ref, reactive, inject, watch, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'; import { CanvasRenderer } from 'echarts/renderers'; import { BarChart } from 'echarts/charts'; import { GridComponent, TooltipComponent } from 'echarts/components'
use([CanvasRenderer, BarChart, GridComponent, TooltipComponent])
import { getRanking } from '../api'; import { stationCN } from '../utils/stationNames'
import PageState from '../components/PageState.vue'; import GlassCard from '../components/GlassCard.vue'; import ChartPanel from '../components/ChartPanel.vue'
import { chartColors, baseTooltip, safeNumber } from '../composables/useDashboardTheme'

const selectedYear = inject('selectedYear')
const loading=ref(true); const error=ref(''); const empty=ref(false); const hasData=ref(false); let requestId=0

const category=ref('hottest')
const categories=[{key:'hottest',label:'🔥 最高温'},{key:'coldest',label:'❄️ 最低温'},{key:'rainiest',label:'🌧️ 最多降水'},{key:'most_extreme',label:'⚠️ 极端天气'}]
const metaMap={hottest:{label:'最高温',unit:'°C',title:'最高温站点 TOP 15'},coldest:{label:'最低温',unit:'°C',title:'最低温站点 TOP 15'},rainiest:{label:'最多降水',unit:'mm',title:'最多降水站点 TOP 15'},most_extreme:{label:'极端天气',unit:'天',title:'极端天气站点 TOP 15'}}
const meta=computed(()=>metaMap[category.value])

const chartOption=reactive({tooltip:baseTooltip(),grid:{left:'3%',right:'4%',top:'5%',bottom:'8%',containLabel:true},xAxis:{type:'category',data:[],axisLabel:{color:chartColors.text,fontSize:11,rotate:20,width:60,overflow:'truncate'},axisLine:{lineStyle:{color:chartColors.outline}}},yAxis:{type:'value',name:'',axisLabel:{color:chartColors.text,fontSize:11},splitLine:{lineStyle:{color:chartColors.grid}}},series:[{type:'bar',data:[],barMaxWidth:36,itemStyle:{borderRadius:[6,6,0,0],color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:chartColors.primary},{offset:1,color:chartColors.teal}]}}}]})
const tableData=ref([])

async function load(){
  const id=++requestId; loading.value=true; error.value=''; empty.value=false; hasData.value=false
  try{
    const res=await getRanking(selectedYear.value,category.value,15); if(id!==requestId) return
    const rows=(res.data?.data||[]).sort((a,b)=>a.rank_num-b.rank_num)
    if(!rows.length){empty.value=true;loading.value=false;return}
    hasData.value=true
    const values = rows.map(r=>safeNumber(r.value))
    const vmin = Math.min(...values.filter(Number.isFinite))
    const vmax = Math.max(...values.filter(Number.isFinite))
    const range = vmax - vmin || 1

    chartOption.xAxis.data = rows.map(r=>stationCN(r.station_name||r.station_id).substring(0,10))
    chartOption.yAxis.name = meta.value.unit

    // Y轴范围
    if (category.value === 'hottest') {
      chartOption.yAxis.min = 30; chartOption.yAxis.max = 50
    } else {
      delete chartOption.yAxis.min; delete chartOption.yAxis.max
    }

    // 按值映射单色
    const isColdest = category.value === 'coldest'
    chartOption.series[0].data = values.map(v => {
      const ratio = Number.isFinite(v) ? (v - vmin) / (range || 1) : 0.5
      const t = Math.max(0, Math.min(1, ratio))

      // 颜色插值函数
      const lerp = (a, b, r) => Math.round(a + (b - a) * r)
      const hex = (r, g, b) => '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('')

      let color
      if (category.value === 'hottest')       // 黄→橙→深红
        color = hex(lerp(0xff,0x8b,t), lerp(0xdb,0x37,t), lerp(0xce,0x13,t))
      else if (category.value === 'coldest')   // 深蓝→浅蓝（最冷=深蓝）
        color = hex(lerp(0x1e,0xbb,t), lerp(0x88,0xde,t), lerp(0xe5,0xfb,t))
      else if (category.value === 'rainiest')  // 浅青→深绿
        color = hex(lerp(0xba,0x39,t), lerp(0xe8,0x65,t), lerp(0xef,0x6b,t))
      else                                     // 浅粉→深橙
        color = hex(lerp(0xff,0x8b,t), lerp(0xdb,0x37,t), lerp(0xce,0x13,t))

      return {
        value: v,
        itemStyle: {
          color,
          borderRadius: isColdest ? [0, 0, 6, 6] : [6, 6, 0, 0],
        }
      }
    })
    tableData.value = rows
  }catch(e){if(id===requestId){error.value='数据加载失败，请确认后端已启动';console.error(e)}}
  finally{if(id===requestId)loading.value=false}
}
watch(selectedYear,load,{immediate:true})
</script>

<style scoped>
.page-sub { color:var(--ci-text-muted); font-size:16px; margin-bottom:8px }
.ranking-header { display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:10px; flex-shrink:0 }
.cat-tabs { display:flex; gap:4px; background:var(--ci-surface-container); border-radius:8px; padding:4px }
.cat-btn { padding:8px 16px; border:none; border-radius:8px; background:transparent; color:var(--ci-text-muted); font-size:15px; font-weight:500; cursor:pointer; transition:all .2s; white-space:nowrap }
.cat-btn:hover { background:rgb(58 103 79 / 8%) }
.cat-btn.active { background:var(--ci-primary); color:#fff }

.ranking-body { display:grid; grid-template-columns: minmax(0, 7fr) minmax(260px, 5fr); gap:12px; flex:1; min-height:0; overflow:hidden }
.table-card { display:flex; flex-direction:column; overflow:hidden; padding:19px }
.table-card-wrap { flex:1; min-height:0; overflow-y:auto; scrollbar-width:none; overscroll-behavior:contain }
.table-card-wrap::-webkit-scrollbar { display:none }
.table-hd { font-size:17px; font-weight:600; color:var(--ci-primary); margin-bottom:10px; flex-shrink:0 }

@media (max-width: 767px) {
  .ranking-header { flex-direction:column; align-items:flex-start }
  .cat-tabs { overflow-x:auto; width:100% }
  .ranking-body { grid-template-columns:1fr }
}
</style>
