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

    <!-- 第一行图表：目的地价格对比 + 运输方式分布 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="16">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <span class="card-title">各目的地报价对比</span>
            <el-radio-group v-model="destMetric" size="small" style="float:right">
              <el-radio-button value="平均总价">均价</el-radio-button>
              <el-radio-button value="最低总价">最低</el-radio-button>
              <el-radio-button value="最高总价">最高</el-radio-button>
            </el-radio-group>
          </template>
          <v-chart :option="destChartOption" style="height:300px" autoresize />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" class="chart-card">
          <template #header><span class="card-title">运输方式分布</span></template>
          <v-chart :option="transportPieOption" style="height:300px" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- 第二行图表：代理商对比 + 价格区间分布 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="14">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <span class="card-title">代理商报价对比</span>
            <el-radio-group v-model="agentMetric" size="small" style="float:right">
              <el-radio-button value="报价次数">报价次数</el-radio-button>
              <el-radio-button value="平均总价">平均总价</el-radio-button>
            </el-radio-group>
          </template>
          <v-chart :option="agentChartOption" style="height:320px" autoresize />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never" class="chart-card">
          <template #header><span class="card-title">报价金额区间分布</span></template>
          <v-chart :option="distChartOption" style="height:320px" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- 第三行：运输方式均价 + 数据明细表 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="10">
        <el-card shadow="never" class="chart-card">
          <template #header><span class="card-title">各运输方式平均报价</span></template>
          <v-chart :option="transportBarOption" style="height:280px" autoresize />
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card shadow="never" class="chart-card">
          <template #header><span class="card-title">目的地报价明细</span></template>
          <el-table :data="destData" size="small" stripe>
            <el-table-column prop="目的地" label="目的地" min-width="100" />
            <el-table-column prop="报价次数" label="报价次数" width="90" align="center" />
            <el-table-column label="平均报价" width="120" align="right">
              <template #default="{ row }">¥{{ formatNum(row.平均总价) }}</template>
            </el-table-column>
            <el-table-column label="最低" width="110" align="right">
              <template #default="{ row }"><span style="color:#52c41a">¥{{ formatNum(row.最低总价) }}</span></template>
            </el-table-column>
            <el-table-column label="最高" width="110" align="right">
              <template #default="{ row }"><span style="color:#f5222d">¥{{ formatNum(row.最高总价) }}</span></template>
            </el-table-column>
            <el-table-column label="价格范围" min-width="140">
              <template #default="{ row }">
                <el-progress
                  :percentage="100"
                  :format="() => ''"
                  :stroke-width="6"
                  :color="[{ color: '#1890ff', percentage: 100 }]"
                  style="margin-top:4px"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, GridComponent,
  LegendComponent, DataZoomComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { Document, User, Location, TrendCharts, Bottom, Top } from '@element-plus/icons-vue'
import {
  getOverview, getByDestination, getByTransport, getByAgent, getPriceDistribution
} from '@/api/analytics'

use([CanvasRenderer, BarChart, PieChart,
  TitleComponent, TooltipComponent, GridComponent, LegendComponent, DataZoomComponent])

const loadingOverview = ref(true)
const overview = ref({ total_routes: 0, total_agents: 0, total_destinations: 0, avg_price: 0, min_price: 0, max_price: 0 })
const destData = ref([])
const transportData = ref([])
const agentData = ref([])
const distData = ref([])

const destMetric = ref('平均总价')
const agentMetric = ref('报价次数')

const formatNum = (n) => {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + 'W'
  return n.toLocaleString()
}

onMounted(async () => {
  const [ov, dest, trans, agent, dist] = await Promise.all([
    getOverview(), getByDestination(), getByTransport(), getByAgent(), getPriceDistribution()
  ])
  overview.value = ov
  loadingOverview.value = false
  destData.value = dest
  transportData.value = trans
  agentData.value = agent
  distData.value = dist
})

// 目的地柱状图
const destChartOption = computed(() => ({
  tooltip: { trigger: 'axis', formatter: (p) => `${p[0].name}<br/>¥${p[0].value?.toLocaleString()}` },
  grid: { left: 16, right: 16, bottom: 60, top: 16, containLabel: true },
  xAxis: {
    type: 'category',
    data: destData.value.map(d => d.目的地),
    axisLabel: { rotate: 30, fontSize: 11 }
  },
  yAxis: { type: 'value', axisLabel: { formatter: v => v >= 10000 ? (v/10000)+'W' : v } },
  series: [{
    type: 'bar', barMaxWidth: 40,
    data: destData.value.map(d => d[destMetric.value]),
    itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#1890ff' }, { offset: 1, color: '#096dd9' }] } },
    label: { show: true, position: 'top', formatter: p => p.value >= 10000 ? (p.value/10000).toFixed(1)+'W' : p.value, fontSize: 11 }
  }]
}))

// 运输方式饼图
const transportPieOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c}次 ({d}%)' },
  legend: { bottom: 0, type: 'scroll' },
  series: [{
    type: 'pie', radius: ['40%', '68%'], center: ['50%', '45%'],
    data: transportData.value.map(d => ({ name: d.运输方式, value: d.报价次数 })),
    label: { formatter: '{b}\n{c}次' },
    emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' } }
  }]
}))

// 运输方式均价柱状图
const transportBarOption = computed(() => ({
  tooltip: { trigger: 'axis', formatter: p => `${p[0].name}<br/>均价 ¥${p[0].value?.toLocaleString()}` },
  grid: { left: 16, right: 16, bottom: 16, top: 16, containLabel: true },
  xAxis: { type: 'category', data: transportData.value.map(d => d.运输方式) },
  yAxis: { type: 'value', axisLabel: { formatter: v => v >= 10000 ? (v/10000)+'W' : v } },
  series: [{
    type: 'bar', barMaxWidth: 40,
    data: transportData.value.map(d => d.平均总价),
    itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#52c41a' }, { offset: 1, color: '#389e0d' }] } },
    label: { show: true, position: 'top', formatter: p => p.value >= 10000 ? (p.value/10000).toFixed(1)+'W' : p.value, fontSize: 11 }
  }]
}))

// 代理商图表
const agentChartOption = computed(() => {
  const sorted = [...agentData.value].sort((a, b) => b[agentMetric.value] - a[agentMetric.value]).slice(0, 12)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 16, right: 16, bottom: 60, top: 16, containLabel: true },
    xAxis: {
      type: 'category',
      data: sorted.map(d => d.代理商.length > 8 ? d.代理商.slice(0, 8) + '…' : d.代理商),
      axisLabel: { rotate: 35, fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: v => agentMetric.value === '平均总价' ? (v >= 10000 ? (v/10000).toFixed(1)+'W' : v) : v }
    },
    series: [{
      type: 'bar', barMaxWidth: 36,
      data: sorted.map(d => d[agentMetric.value]),
      itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#722ed1' }, { offset: 1, color: '#531dab' }] } },
      label: { show: true, position: 'top', fontSize: 10,
        formatter: p => agentMetric.value === '平均总价' && p.value >= 10000 ? (p.value/10000).toFixed(1)+'W' : p.value }
    }]
  }
})

// 价格区间分布
const distChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
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
.analytics-page { padding: 20px; max-width: 1400px; margin: 0 auto; }
.page-header { margin-bottom: 20px; }
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
.chart-card :deep(.el-card__header) { padding: 12px 16px; font-size: 14px; }
.card-title { font-weight: 600; color: #262626; }
</style>
