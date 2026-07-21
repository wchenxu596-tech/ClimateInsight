/** ECharts 统一主题工具 */

export const chartColors = {
  green: '#3a674f',
  teal: '#39656b',
  orange: '#8b3713',
  orangeSoft: '#ffdbce',
  error: '#ba1a1a',
  text: '#414943',
  outline: '#c0c9c1',
  grid: '#e3e2e0',
  primary: '#14422d',
}

/** 标准 tooltip 配置 */
export function baseTooltip() {
  return {
    trigger: 'axis',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: chartColors.outline,
    textStyle: { color: chartColors.text, fontSize: 13 },
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
    valueFormatter: (v) => (typeof v === 'number' ? v.toFixed(2) : v),
  }
}

/** 标准 grid 配置 */
export function baseGrid() {
  return { left: '3%', right: '4%', bottom: '3%', containLabel: true }
}

/** 12个月标签 */
export const monthLabels = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']

/** 安全数字：null/NaN/Infinity → null，不伪装成0 */
export function safeNumber(value) {
  if (value === null || value === undefined || value === '') return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

/** 气候带颜色映射 */
export const zoneColors = {
  tropical: '#8b3713',
  temperate: '#3a674f',
  arid: '#bdeaf2',
  continental: '#39656b',
  polar: '#c0c9c1',
}

/** 气候带中文名 */
export const zoneCN = {
  tropical: '热带', temperate: '温带', continental: '大陆性', polar: '寒带', arid: '干旱',
}
