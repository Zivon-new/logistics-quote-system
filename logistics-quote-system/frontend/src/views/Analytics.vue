<template>
  <div class="analytics-page">
    <div class="page-header">
      <h2>价格分析看板</h2>
      <p class="subtitle">基于历史报价数据的多维度可视化分析</p>
    </div>

    <!-- 概览数字卡片 -->
    <el-row :gutter="16" class="overview-row" v-loading="loadingOverview">
      <el-col :span="4">
        <div class="stat-card">
          <div class="stat-icon" style="background:#e6f4ff"><el-icon style="color:#1890ff;font-size:22px"><Document /></el-icon></div>
          <div class="stat-body">
            <div class="stat-num">{{ overview.total_routes }}</div>
            <div class="stat-label">历史路线</div>
          </div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-card">
          <div class="stat-icon" style="background:#f6ffed"><el-icon style="color:#52c41a;font-size:22px"><User /></el-icon></div>
          <div class="stat-body">
            <div class="stat-num">{{ overview.total_agents }}</div>
            <div class="stat-label">合作代理商</div>
          </div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-card">
          <div class="stat-icon" style="background:#fff7e6"><el-icon style="color:#fa8c16;font-size:22px"><Location /></el-icon></div>
          <div class="stat-body">
            <div class="stat-num">{{ overview.total_destinations }}</div>
            <div class="stat-label">覆盖目的地</div>
          </div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-card">
          <div class="stat-icon" style="background:#fff0f6"><el-icon style="color:#eb2f96;font-size:22px"><TrendCharts /></el-icon></div>
          <div class="stat-body">
            <div class="stat-num">¥{{ formatNum(overview.avg_price) }}</div>
            <div class="stat-label">平均报价</div>
          </div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-card">
          <div class="stat-icon" style="background:#f6ffed"><el-icon style="color:#52c41a;font-size:22px"><Bottom /></el-icon></div>
          <div class="stat-body">
            <div class="stat-num">¥{{ formatNum(overview.min_price) }}</div>
            <div class="stat-label">最低报价</div>
          </div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-card">
          <div class="stat-icon" style="background:#fff1f0"><el-icon style="color:#f5222d;font-size:22px"><Top /></el-icon></div>
          <div class="stat-body">
            <div class="stat-num">¥{{ formatNum(overview.max_price) }}</div>
            <div class="stat-label">最高报价</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 第一行：热门路线 + 线路代理分布 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="14">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <span class="card-title">热门路线排行 TOP15</span>
            <span class="card-hint">点击柱条查看该路线代理分布</span>
          </template>
          <v-chart
            :option="routeUsageOption"
            style="height:340px"
            autoresize
            @click="onRouteBarClick"
          />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <span class="card-title">线路代理选择分布</span>
            <el-tag
              v-if="selectedRoute"
              size="small"
              closable
              @close="clearRoute"
              style="float:right;max-width:160px;overflow:hidden;text-overflow:ellipsis"
            >{{ selectedRoute.label }}</el-tag>
            <span v-else class="card-hint" style="float:right">全部路线汇总</span>
          </template>
          <v-chart :option="agentDistOption" style="height:340px" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- 第二行：报价趋势（全宽） -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="24">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <span class="card-title">报价趋势分析</span>
            <div style="float:right;display:flex;align-items:center;gap:12px">
              <el-radio-group v-model="trendMetric" size="small">
                <el-radio-button value="总报价额">总报价额</el-radio-button>
                <el-radio-button value="平均报价">平均报价</el-radio-button>
                <el-radio-button value="路线数">路线数</el-radio-button>
              </el-radio-group>
              <el-radio-group v-model="trendGranularity" size="small" @change="loadTrend">
                <el-radio-button value="week">按周</el-radio-button>
                <el-radio-button value="month">按月</el-radio-button>
                <el-radio-button value="quarter">按季度</el-radio-button>
                <el-radio-button value="year">按年</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <v-chart :option="trendOption" style="height:300px" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- 第三行：代理商活跃度 + 价格区间分布 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="10">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <span class="card-title">代理商活跃度</span>
            <el-radio-group v-model="agentMetric" size="small" style="float:right">
              <el-radio-button value="报价次数">报价次数</el-radio-button>
              <el-radio-button value="平均总价">平均总价</el-radio-button>
            </el-radio-group>
          </template>
          <v-chart :option="agentBarOption" style="height:300px" autoresize />
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card shadow="never" class="chart-card">
          <template #header><span class="card-title">报价金额区间分布</span></template>
          <v-chart :option="distChartOption" style="height:300px" autoresize />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart, LineChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, GridComponent,
  LegendComponent, DataZoomComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { Document, User, Location, TrendCharts, Bottom, Top } from '@element-plus/icons-vue'
import {
  getOverview, getRouteUsage, getRouteAgentDist, getTrend, getByAgent, getPriceDistribution
} from '@/api/analytics'

use([CanvasRenderer, BarChart, PieChart, LineChart,
  TitleComponent, TooltipComponent, GridComponent, LegendComponent, DataZoomComponent])

// ── 数据 ──────────────────────────────────────────────────
const loadingOverview = ref(true)
const overview = ref({ total_routes: 0, total_agents: 0, total_destinations: 0, avg_price: 0, min_price: 0, max_price: 0 })
const routeUsageData = ref([])
const agentDistData = ref([])
const trendData = ref([])
const agentData = ref([])
const distData = ref([])

const selectedRoute = ref(null)   // { origin, dest, transport, label }
const trendGranularity = ref('month')
const trendMetric = ref('总报价额')
const agentMetric = ref('报价次数')

// ── 工具 ──────────────────────────────────────────────────
const formatNum = (n) => {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + 'W'
  return n.toLocaleString()
}

// ── 加载数据 ───────────────────────────────────────────────
const loadTrend = async () => {
  trendData.value = await getTrend(trendGranularity.value)
}

const loadAgentDist = async (params = {}) => {
  agentDistData.value = await getRouteAgentDist(params)
}

onMounted(async () => {
  const [ov, routes, agent, dist] = await Promise.all([
    getOverview(), getRouteUsage(), getByAgent(), getPriceDistribution()
  ])
  overview.value = ov
  loadingOverview.value = false
  routeUsageData.value = routes
  agentData.value = agent
  distData.value = dist
  await Promise.all([loadTrend(), loadAgentDist()])
})

// ── 路线点击 ───────────────────────────────────────────────
const onRouteBarClick = (params) => {
  const item = routeUsageData.value[params.dataIndex]
  if (!item) return
  selectedRoute.value = {
    origin: item.起始地,
    dest: item.目的地,
    transport: item.运输方式,
    label: `${item.起始地}→${item.目的地} ${item.运输方式}`,
  }
  loadAgentDist({ origin: item.起始地, dest: item.目的地, transport: item.运输方式 })
}

const clearRoute = () => {
  selectedRoute.value = null
  loadAgentDist()
}

// ── 热门路线横向柱状图 ─────────────────────────────────────
const routeUsageOption = computed(() => {
  const data = [...routeUsageData.value].reverse()
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (p) => {
        const item = routeUsageData.value[routeUsageData.value.length - 1 - p[0].dataIndex]
        if (!item) return ''
        return `<b>${item.起始地} → ${item.目的地}</b><br/>
          运输方式：${item.运输方式}<br/>
          代理报价数：<b>${item.代理报价数}</b><br/>
          涉及代理商：${item.代理商数} 家<br/>
          平均报价：¥${item.平均报价?.toLocaleString()}`
      }
    },
    grid: { left: 16, right: 60, top: 10, bottom: 10, containLabel: true },
    xAxis: { type: 'value', minInterval: 1, axisLabel: { formatter: v => v + '次' } },
    yAxis: {
      type: 'category',
      data: data.map(d => `${d.起始地}→${d.目的地}`),
      axisLabel: { fontSize: 12 }
    },
    series: [{
      type: 'bar',
      barMaxWidth: 28,
      data: data.map(d => ({
        value: d.代理报价数,
        itemStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [{ offset: 0, color: '#096dd9' }, { offset: 1, color: '#69b1ff' }]
          }
        }
      })),
      label: {
        show: true, position: 'right',
        formatter: p => p.value + '次', fontSize: 11, color: '#595959'
      }
    }]
  }
})

// ── 线路代理分布饼图 ───────────────────────────────────────
const COLORS = ['#1890ff','#52c41a','#faad14','#f5222d','#722ed1','#13c2c2','#fa8c16','#eb2f96','#a0d911','#2f54eb']
const agentDistOption = computed(() => {
  if (!agentDistData.value.length) {
    return {
      title: { text: '暂无数据', left: 'center', top: 'center', textStyle: { color: '#bfbfbf', fontSize: 14 } }
    }
  }
  const top10 = agentDistData.value.slice(0, 10)
  return {
    tooltip: {
      trigger: 'item',
      formatter: (p) => `${p.name}<br/>报价次数：${p.value}<br/>占比：${p.percent}%`
    },
    legend: { bottom: 0, type: 'scroll', textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie',
      radius: ['36%', '65%'],
      center: ['50%', '44%'],
      data: top10.map((d, i) => ({
        name: d.代理商,
        value: d.报价次数,
        itemStyle: { color: COLORS[i % COLORS.length] }
      })),
      label: { formatter: '{b}\n{c}次', fontSize: 11 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' } }
    }]
  }
})

// ── 报价趋势图（柱+线双轴） ────────────────────────────────
const trendOption = computed(() => {
  const times = trendData.value.map(d => d.时间)
  const isCountMetric = trendMetric.value === '路线数'

  // 计算同比变化标注
  const values = trendData.value.map(d => d[trendMetric.value])

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const p = params[0]
        const idx = p.dataIndex
        const prev = idx > 0 ? values[idx - 1] : null
        const curr = values[idx]
        let yoyStr = ''
        if (prev && prev > 0) {
          const pct = (((curr - prev) / prev) * 100).toFixed(1)
          const arrow = pct >= 0 ? '↑' : '↓'
          const color = pct >= 0 ? '#f5222d' : '#52c41a'
          yoyStr = `<br/>环比：<span style="color:${color}">${arrow}${Math.abs(pct)}%</span>`
        }
        const valStr = isCountMetric ? `${curr} 条` : `¥${curr?.toLocaleString()}`
        return `<b>${p.name}</b><br/>${trendMetric.value}：${valStr}${yoyStr}`
      }
    },
    grid: { left: 16, right: 16, top: 20, bottom: 50, containLabel: true },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 20, bottom: 8 }],
    xAxis: {
      type: 'category',
      data: times,
      axisLabel: { rotate: times.length > 8 ? 30 : 0, fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: v => isCountMetric ? v + '条' : (v >= 10000 ? (v / 10000).toFixed(0) + 'W' : v)
      }
    },
    series: [{
      name: trendMetric.value,
      type: isCountMetric ? 'bar' : 'line',
      smooth: true,
      data: values,
      barMaxWidth: 36,
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: {
        color: isCountMetric
          ? { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#1890ff' }, { offset: 1, color: '#096dd9' }] }
          : '#fa8c16'
      },
      lineStyle: { color: '#fa8c16', width: 2 },
      areaStyle: isCountMetric ? undefined : { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(250,140,22,0.3)' }, { offset: 1, color: 'rgba(250,140,22,0)' }] } },
      label: {
        show: values.length <= 12,
        position: isCountMetric ? 'top' : 'top',
        fontSize: 11,
        formatter: p => isCountMetric ? p.value + '条' : (p.value >= 10000 ? (p.value / 10000).toFixed(1) + 'W' : p.value)
      }
    }]
  }
})

// ── 代理商活跃度 ──────────────────────────────────────────
const agentBarOption = computed(() => {
  const sorted = [...agentData.value].sort((a, b) => b[agentMetric.value === '报价次数' ? '报价次数' : '平均总价'] - a[agentMetric.value === '报价次数' ? '报价次数' : '平均总价']).slice(0, 12)
  const isCount = agentMetric.value === '报价次数'
  return {
    tooltip: {
      trigger: 'axis',
      formatter: p => {
        const d = agentData.value.find(a => a.代理商 === (sorted[p[0].dataIndex]?.代理商))
        if (!d) return ''
        return `<b>${d.代理商}</b><br/>报价次数：${d.报价次数}<br/>覆盖路线：${d.路线数} 条<br/>平均报价：¥${d.平均总价?.toLocaleString()}`
      }
    },
    grid: { left: 16, right: 16, bottom: 60, top: 10, containLabel: true },
    xAxis: {
      type: 'category',
      data: sorted.map(d => d.代理商.length > 6 ? d.代理商.slice(0, 6) + '…' : d.代理商),
      axisLabel: { rotate: 35, fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: v => isCount ? v : (v >= 10000 ? (v / 10000).toFixed(1) + 'W' : v) }
    },
    series: [{
      type: 'bar', barMaxWidth: 32,
      data: sorted.map(d => isCount ? d.报价次数 : d.平均总价),
      itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#722ed1' }, { offset: 1, color: '#531dab' }] } },
      label: {
        show: true, position: 'top', fontSize: 10,
        formatter: p => isCount ? p.value : (p.value >= 10000 ? (p.value / 10000).toFixed(1) + 'W' : p.value)
      }
    }]
  }
})

// ── 价格区间分布 ──────────────────────────────────────────
const distChartOption = computed(() => ({
  tooltip: { trigger: 'axis', formatter: p => `${p[0].name}：${p[0].value} 笔` },
  grid: { left: 16, right: 16, bottom: 16, top: 16, containLabel: true },
  xAxis: { type: 'category', data: distData.value.map(d => d.区间) },
  yAxis: { type: 'value', minInterval: 1 },
  series: [{
    type: 'bar', barMaxWidth: 48,
    data: distData.value.map(d => d.数量),
    itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#fa8c16' }, { offset: 1, color: '#d46b08' }] } },
    label: { show: true, position: 'top', formatter: p => p.value + '笔' }
  }]
}))
</script>

<style scoped>
.analytics-page { padding: 0; max-width: 1400px; margin: 0 auto; }
.page-header { margin-bottom: 16px; }
.page-header h2 { font-size: 20px; font-weight: 600; margin: 0 0 4px; color: #262626; }
.subtitle { color: #8c8c8c; font-size: 13px; margin: 0; }

.overview-row { margin-bottom: 16px; }
.stat-card {
  background: #fff; border-radius: 8px; padding: 16px 20px;
  display: flex; align-items: center; gap: 14px;
  border: 1px solid #f0f0f0;
  transition: box-shadow 0.2s;
}
.stat-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
.stat-icon { width: 44px; height: 44px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.stat-num { font-size: 20px; font-weight: 700; color: #262626; line-height: 1.2; }
.stat-label { font-size: 12px; color: #8c8c8c; margin-top: 2px; }

.chart-row { margin-bottom: 16px; }
.chart-card { border-radius: 8px; }
.chart-card :deep(.el-card__header) { padding: 10px 16px; font-size: 14px; display: flex; align-items: center; justify-content: space-between; }
.card-title { font-weight: 600; color: #262626; }
.card-hint { font-size: 12px; color: #bfbfbf; margin-left: 8px; }
</style>
