/** 图表全屏/下载工具 */

/**
 * 全屏图表
 * @param {import('vue-echarts').default} chartRef - vue-echarts 组件 ref
 */
export function fullscreenChart(chartRef) {
  const dom = chartRef?.getEchartsInstance?.()?.getDom?.()
  if (dom?.requestFullscreen) {
    dom.requestFullscreen().catch(() => {})
  }
}

/**
 * 下载图表为 PNG
 * @param {import('vue-echarts').default} chartRef
 * @param {string} filename
 */
export function downloadChart(chartRef, filename = 'chart.png') {
  const instance = chartRef?.getEchartsInstance?.()
  if (!instance) return
  const url = instance.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#faf9f7' })
  const link = document.createElement('a')
  link.download = filename
  link.href = url
  link.click()
}
