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
          <div class="stat-icon" style="background:#e6f7ff"><el-icon style="color:#096dd9;font-size:22px"><Money /></el-icon></div>
          <div class="stat-body">
            <div class="stat-num" style="font-size:18px">
              {{ latestUsdRate ? latestUsdRate.toFixed(4) : '—' }}
            </div>
            <div class="stat-label">
              USD/CNY
              <span v-if="latestForexDate" style="font-size:11px;color:#bbb;display:block">{{ latestForexDate }}</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-card">
          <div class="stat-icon" style="background:#fff7e6"><el-icon style="color:#d46b08;font-size:22px"><Odometer /></el-icon></div>
          <div class="stat-body">
            <div class="stat-num" style="font-size:18px">
              {{ latestFuelPrice ? '¥' + latestFuelPrice.toFixed(1) : '—' }}
            </div>
            <div class="stat-label">
              原油SC0（元/桶）
              <span v-if="latestFuelDate" style="font-size:11px;color:#bbb;display:block">{{ latestFuelDate }}</span>
            </div>
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

    <!-- 第四行：汇率走势（全宽） -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="24">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <span class="card-title">外汇汇率走势</span>
            <div style="float:right;display:flex;align-items:center;gap:12px">
              <el-checkbox-group v-model="selectedCurrencies" size="small" @change="loadForexHistory">
                <el-checkbox-button v-for="c in allCurrencies" :key="c" :value="c">{{ c }}</el-checkbox-button>
              </el-checkbox-group>
              <el-radio-group v-model="forexDays" size="small" @change="loadForexHistory">
                <el-radio-button :value="30">近30天</el-radio-button>
                <el-radio-button :value="90">近90天</el-radio-button>
                <el-radio-button :value="180">近180天</el-radio-button>
              </el-radio-group>
              <el-button size="small" :loading="forexSyncing" @click="handleForexSync">
                {{ forexSyncing ? '同步中...' : '同步今日' }}
              </el-button>
              <el-button v-if="isAdmin" size="small" :loading="forexBackfilling" @click="handleForexBackfill">
                {{ forexBackfilling ? '回填中...' : '回填30天' }}
              </el-button>
            </div>
          </template>
          <div v-if="forexEmpty" class="market-empty">
            <el-empty description="暂无汇率历史数据" :image-size="60" />
            <p class="empty-tip">点击「刷新汇率」按钮同步一次，之后每天 09:30 自动积累</p>
          </div>
          <v-chart v-else :option="forexChartOption" style="height:320px" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- 第五行：布伦特原油参考价 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="24">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <span class="card-title">上海原油期货参考价格（SC888，元/桶）</span>
            <div style="float:right;display:flex;align-items:center;gap:12px">
              <el-tag type="info" size="small">上期所原油期货·空运/海运燃油附加费参考基准</el-tag>
              <el-radio-group v-model="fuelDays" size="small" @change="loadFuelHistory">
                <el-radio-button :value="30">近30天</el-radio-button>
                <el-radio-button :value="90">近90天</el-radio-button>
                <el-radio-button :value="180">近180天</el-radio-button>
              </el-radio-group>
              <el-button
                v-if="isAdmin"
                size="small"
                :loading="fuelBackfilling"
                @click="handleFuelBackfill"
              >回填历史数据</el-button>
            </div>
          </template>
          <div v-if="fuelEmpty" class="market-empty">
            <el-empty description="暂无燃油价格数据" :image-size="60" />
            <p class="empty-tip">管理员点击「回填历史数据」拉取近30条原油价格（数据来源：新浪财经 SC0）</p>
          </div>
          <v-chart v-else :option="fuelChartOption" style="height:300px" autoresize />
        </el-card>
      </el-col>
    </el-row>
    <!-- 代理商年度报价分析 -->
    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="24">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <span class="card-title">代理商年度报价分析</span>
            <div style="display:flex;gap:8px;align-items:center">
              <el-input v-model="agentQuery.代理商" placeholder="代理商名称，如：融讯" clearable style="width:180px" />
              <el-input-number v-model="agentQuery.year" :min="2020" :max="2030" placeholder="年份" style="width:110px" />
              <el-button type="primary" size="small" @click="loadAgentReport" :loading="agentLoading">查询</el-button>
            </div>
          </template>

          <div v-if="agentReport">
            <div style="margin-bottom:12px;color:#595959;font-size:13px">
              共 <b>{{ agentReport.路线数 }}</b> 条路线，
              <span style="color:#f5222d;font-weight:600">{{ agentReport.异常路线数 }}</span> 条涨幅超15%（标红）
            </div>
            <el-table :data="agentReport.routes" border size="small" row-key="路线"
              :row-class-name="({ row }) => row.异常标记 ? 'agent-suspicious-row' : ''">
              <el-table-column prop="路线" label="路线" min-width="160" />
              <el-table-column prop="记录数" label="报价次数" width="90" align="center" />
              <el-table-column prop="最早日期" label="首次日期" width="110" align="center" />
              <el-table-column prop="最新日期" label="最新日期" width="110" align="center" />
              <el-table-column label="首次报价(¥)" width="110" align="right">
                <template #default="{ row }">{{ row.首次报价 != null ? '¥' + row.首次报价.toFixed(2) : '—' }}</template>
              </el-table-column>
              <el-table-column label="最新报价(¥)" width="110" align="right">
                <template #default="{ row }">{{ row.最新报价 != null ? '¥' + row.最新报价.toFixed(2) : '—' }}</template>
              </el-table-column>
              <el-table-column label="涨幅" width="90" align="center">
                <template #default="{ row }">
                  <span v-if="row.涨幅百分比 != null"
                    :style="{ color: row.涨幅百分比 > 15 ? '#f5222d' : row.涨幅百分比 > 0 ? '#fa8c16' : '#52c41a', fontWeight: '600' }">
                    {{ row.涨幅百分比 > 0 ? '+' : '' }}{{ row.涨幅百分比 }}%
                  </span>
                  <span v-else style="color:#bfbfbf">—</span>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="80" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.异常标记" type="danger" size="small">异常</el-tag>
                  <el-tag v-else type="success" size="small">正常</el-tag>
                </template>
              </el-table-column>
              <el-table-column type="expand" width="50">
                <template #default="{ row }">
                  <el-table :data="row.明细" size="small" border style="margin:8px 16px">
                    <el-table-column prop="交易开始日期" label="日期" width="110" />
                    <el-table-column prop="运输方式" label="运输方式" width="90" />
                    <el-table-column prop="时效" label="时效" width="80" />
                    <el-table-column prop="小计" label="小计(¥)" width="100" align="right">
                      <template #default="{ row: r }">{{ r.小计 > 0 ? '¥' + r.小计.toFixed(2) : '—' }}</template>
                    </el-table-column>
                    <el-table-column prop="总计" label="总计(¥)" width="100" align="right">
                      <template #default="{ row: r }">{{ r.总计 > 0 ? '¥' + r.总计.toFixed(2) : '—' }}</template>
                    </el-table-column>
                  </el-table>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-empty v-else-if="!agentLoading" description="输入代理商名称并点击查询" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart, LineChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, GridComponent,
  LegendComponent, DataZoomComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { Document, User, Location, TrendCharts, Bottom, Top, Money, Odometer } from '@element-plus/icons-vue'
import {
  getOverview, getRouteUsage, getRouteAgentDist, getTrend, getByAgent, getPriceDistribution,
  getForexHistory, getFuelHistory, triggerFuelBackfill, triggerForexBackfill
} from '@/api/analytics'
import request from '@/utils/request'
import { refreshForexRates } from '@/api/route'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

use([CanvasRenderer, BarChart, PieChart, LineChart,
  TitleComponent, TooltipComponent, GridComponent, LegendComponent, DataZoomComponent])

// ── 数据 ──────────────────────────────────────────────────
// 代理商年度分析
const agentQuery = ref({ 代理商: '', year: new Date().getFullYear() })
const agentReport = ref(null)
const agentLoading = ref(false)
const loadAgentReport = async () => {
  if (!agentQuery.value.代理商) return
  agentLoading.value = true
  try {
    const params = { 代理商: agentQuery.value.代理商 }
    if (agentQuery.value.year) params.year = agentQuery.value.year
    agentReport.value = await request.get('/v1/analytics/agent-report', { params })
  } catch (e) {
    ElMessage.error('查询失败：' + (e.message || '未知错误'))
  } finally {
    agentLoading.value = false
  }
}

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

// ── 市场行情数据 ───────────────────────────────────────────
const userStore = useUserStore()
const isAdmin = computed(() => userStore.userInfo?.is_admin)

const allCurrencies = ['USD', 'EUR', 'SGD', 'HKD', 'MYR', 'JPY']
const selectedCurrencies = ref(['USD', 'EUR', 'SGD'])  // JPY量级(0.05)与其他差异太大，默认不选
const forexDays = ref(90)
const forexHistoryData = ref({})
const forexEmpty = computed(() => Object.values(forexHistoryData.value).every(arr => !arr?.length))

const fuelDays = ref(90)
const fuelHistoryData = ref([])
const fuelEmpty = computed(() => !fuelHistoryData.value.length)
const fuelBackfilling = ref(false)
const forexSyncing = ref(false)
const forexBackfilling = ref(false)

// ── 市场行情最新值（用于顶部卡片）─────────────────────────
const latestUsdRate = computed(() => {
  const arr = forexHistoryData.value['USD']
  return arr?.length ? arr[arr.length - 1].rate : null
})
const latestForexDate = computed(() => {
  const arr = forexHistoryData.value['USD']
  return arr?.length ? arr[arr.length - 1].date : null
})
const latestFuelPrice = computed(() => {
  const arr = fuelHistoryData.value
  return arr?.length ? arr[arr.length - 1].price : null
})
const latestFuelDate = computed(() => {
  const arr = fuelHistoryData.value
  return arr?.length ? arr[arr.length - 1].date : null
})

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

const handleForexBackfill = async () => {
  forexBackfilling.value = true
  try {
    const res = await triggerForexBackfill(30)
    if (res.success) {
      ElMessage.success(res.message)
      await loadForexHistory()
    }
  } catch {
    ElMessage.error('汇率历史回填失败，请检查网络')
  } finally {
    forexBackfilling.value = false
  }
}

const handleForexSync = async () => {
  forexSyncing.value = true
  try {
    const res = await refreshForexRates()
    if (res.success) {
      ElMessage.success(`汇率已同步，今日记录已写入历史`)
      await loadForexHistory()
    }
  } catch {
    ElMessage.error('汇率同步失败，请检查网络')
  } finally {
    forexSyncing.value = false
  }
}

const loadForexHistory = async () => {
  try {
    const res = await getForexHistory(forexDays.value, selectedCurrencies.value.join(','))
    if (res.success) forexHistoryData.value = res.data
  } catch { /* 数据暂无时静默处理 */ }
}

const loadFuelHistory = async () => {
  try {
    const res = await getFuelHistory(fuelDays.value)
    if (res.success) fuelHistoryData.value = res.data
  } catch { /* 数据暂无时静默处理 */ }
}

const handleFuelBackfill = async () => {
  fuelBackfilling.value = true
  try {
    const res = await triggerFuelBackfill(30)
    if (res.success) {
      ElMessage.success(res.message)
      await loadFuelHistory()
    }
  } catch {
    ElMessage.error('回填失败，请检查网络后重试')
  } finally {
    fuelBackfilling.value = false
  }
}

const loadAll = async () => {
  loadingOverview.value = true
  selectedRoute.value = null
  const [ov, routes, agent, dist] = await Promise.all([
    getOverview(), getRouteUsage(), getByAgent(), getPriceDistribution()
  ])
  overview.value = ov
  loadingOverview.value = false
  routeUsageData.value = routes
  agentData.value = agent
  distData.value = dist
  await Promise.all([loadTrend(), loadAgentDist(), loadForexHistory(), loadFuelHistory()])
}

onMounted(loadAll)
onActivated(loadAll)

// ── 路线点击 ───────────────────────────────────────────────
const onRouteBarClick = (params) => {
  const item = routeUsageData.value[routeUsageData.value.length - 1 - params.dataIndex]
  if (!item) return
  selectedRoute.value = {
    origin: item.起始地,
    dest: item.目的地,
    label: `${item.起始地}→${item.目的地}`,
  }
  loadAgentDist({ origin: item.起始地, dest: item.目的地 })
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

// ── 汇率走势折线图 ─────────────────────────────────────────
const CURRENCY_COLORS = { USD: '#1890ff', EUR: '#52c41a', SGD: '#fa8c16', JPY: '#722ed1', MYR: '#eb2f96', HKD: '#13c2c2' }

const forexChartOption = computed(() => {
  const dates = new Set()
  Object.values(forexHistoryData.value).forEach(arr => arr?.forEach(p => dates.add(p.date)))
  const sortedDates = [...dates].sort()

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const date = params[0]?.axisValue || ''
        return `<b>${date}</b><br/>` + params.map(p => `${p.marker}${p.seriesName}：<b>${p.value?.toFixed(4)}</b>`).join('<br/>')
      }
    },
    legend: { top: 4, data: selectedCurrencies.value },
    grid: { left: 16, right: 24, top: 36, bottom: 40, containLabel: true },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 20, bottom: 4 }],
    xAxis: { type: 'category', data: sortedDates, axisLabel: { rotate: 30, fontSize: 11 } },
    yAxis: {
      type: 'value', name: 'CNY', scale: true,
      axisLabel: { formatter: v => v.toFixed(2) }
    },
    series: selectedCurrencies.value.map(currency => ({
      name: currency,
      type: 'line',
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2 },
      itemStyle: { color: CURRENCY_COLORS[currency] || '#1890ff' },
      data: sortedDates.map(d => {
        const point = forexHistoryData.value[currency]?.find(p => p.date === d)
        return point ? point.rate : null
      }),
      connectNulls: false
    }))
  }
})

// ── 布伦特原油折线图 ───────────────────────────────────────
const fuelChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params) => {
      const p = params[0]
      return `<b>${p.axisValue}</b><br/>${p.marker}SC888收盘：<b>¥${p.value?.toFixed(2)}/桶</b>`
    }
  },
  grid: { left: 16, right: 24, top: 16, bottom: 40, containLabel: true },
  dataZoom: [{ type: 'inside' }, { type: 'slider', height: 20, bottom: 4 }],
  xAxis: { type: 'category', data: fuelHistoryData.value.map(d => d.date), axisLabel: { rotate: 30, fontSize: 11 } },
  yAxis: { type: 'value', name: '元/桶', axisLabel: { formatter: v => '¥' + v } },
  series: [{
    name: '原油SC888',
    type: 'line',
    smooth: true,
    symbol: 'none',
    lineStyle: { width: 2, color: '#1890ff' },
    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(24,144,255,0.3)' }, { offset: 1, color: 'rgba(24,144,255,0.02)' }] } },
    data: fuelHistoryData.value.map(d => d.price),
    markLine: {
      silent: true,
      lineStyle: { color: '#ff4d4f', type: 'dashed' },
      data: [{ type: 'average', name: '均价' }]
    }
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
.market-empty { padding: 24px 0; text-align: center; }
.empty-tip { font-size: 12px; color: #8c8c8c; margin-top: 8px; }
:deep(.agent-suspicious-row) td { background-color: #fff1f0 !important; }
</style>
