<template>
  <div class="risk-page">
    <div class="page-header">
      <h2>航线风险画像</h2>
      <p class="subtitle">基于 World Bank LPI 2023 数据，量化目的国物流能力与清关风险</p>
    </div>

    <el-row :gutter="16">
      <!-- 左侧：LPI 排行榜 + 航线查询 -->
      <el-col :span="8">

        <!-- 航线风险查询 -->
        <el-card class="query-card" shadow="never">
          <template #header>
            <div class="card-title"><el-icon><Compass /></el-icon> 航线风险查询</div>
          </template>
          <el-form :model="queryForm" label-width="60px" size="small">
            <el-form-item label="起始地">
              <el-input v-model="queryForm.origin" placeholder="如：深圳" clearable />
            </el-form-item>
            <el-form-item label="目的地">
              <el-input v-model="queryForm.destination" placeholder="如：新加坡" clearable />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loadingRoute" @click="queryRouteRisk" style="width:100%">
                生成风险画像
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 全球 LPI 排行榜 -->
        <el-card class="rank-card" shadow="never" v-loading="loadingList">
          <template #header>
            <div class="card-title"><el-icon><DataAnalysis /></el-icon> 全球LPI排行（{{ lpiList.length }}国）</div>
          </template>
          <div class="rank-list">
            <div
              v-for="(item, idx) in lpiList"
              :key="item.country_code"
              class="rank-item"
              :class="{ 'rank-active': selectedCountry === item.country_code }"
              @click="selectCountry(item)"
            >
              <span class="rank-no" :class="`rank-${idx < 3 ? idx + 1 : 'other'}`">{{ idx + 1 }}</span>
              <div class="rank-body">
                <span class="rank-name">{{ item.country_cn }}</span>
                <el-tag :type="riskTagType(item.risk_level)" size="small" style="margin-left:6px">{{ item.risk_level }}</el-tag>
              </div>
              <div class="rank-score-bar">
                <el-progress
                  :percentage="(item.lpi / 5) * 100"
                  :color="riskColor(item.risk_level)"
                  :show-text="false"
                  :stroke-width="6"
                  style="flex:1"
                />
                <span class="rank-score-val">{{ item.lpi }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：雷达图 + 详情 -->
      <el-col :span="16">

        <!-- 无数据提示 -->
        <el-card v-if="!activeCountry && !routeResult" shadow="never" class="empty-hint-card">
          <el-empty description="点击左侧国家查看LPI详情，或输入航线生成风险画像" :image-size="80" />
        </el-card>

        <!-- 航线风险画像（查询结果） -->
        <template v-if="routeResult">
          <el-card class="route-result-card" shadow="never">
            <template #header>
              <div class="card-title">
                <el-icon><Promotion /></el-icon>
                航线风险画像：{{ routeResult.origin }} → {{ routeResult.destination }}
              </div>
            </template>

            <!-- 报价统计 -->
            <el-row :gutter="12" class="route-stat-row">
              <el-col :span="8">
                <div class="mini-stat">
                  <div class="mini-num">{{ routeResult.quote_stats.route_count }}</div>
                  <div class="mini-label">历史路线数</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="mini-stat">
                  <div class="mini-num">{{ routeResult.quote_stats.agent_count }}</div>
                  <div class="mini-label">合作代理商</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="mini-stat">
                  <div class="mini-num">
                    {{ routeResult.quote_stats.min_days != null ? routeResult.quote_stats.min_days + ' 天' : '—' }}
                  </div>
                  <div class="mini-label">最快时效</div>
                </div>
              </el-col>
            </el-row>
            <el-row :gutter="12" class="route-stat-row" style="margin-top:8px">
              <el-col :span="8">
                <div class="mini-stat">
                  <div class="mini-num price">
                    {{ routeResult.quote_stats.min_price != null ? '¥' + routeResult.quote_stats.min_price.toLocaleString() : '—' }}
                  </div>
                  <div class="mini-label">最低报价</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="mini-stat">
                  <div class="mini-num">
                    {{ routeResult.quote_stats.avg_price != null ? '¥' + routeResult.quote_stats.avg_price.toLocaleString() : '—' }}
                  </div>
                  <div class="mini-label">平均报价</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="mini-stat">
                  <div class="mini-num">
                    {{ routeResult.quote_stats.max_price != null ? '¥' + routeResult.quote_stats.max_price.toLocaleString() : '—' }}
                  </div>
                  <div class="mini-label">最高报价</div>
                </div>
              </el-col>
            </el-row>

            <!-- 目的地港口 -->
            <div v-if="routeResult.ports.length" class="ports-row">
              <span class="ports-label">目的地港口：</span>
              <el-tag
                v-for="p in routeResult.ports"
                :key="p.unlocode"
                size="small"
                :type="p.risk === '低' ? 'success' : p.risk === '高' ? 'danger' : 'warning'"
                style="margin-right:6px"
              >
                {{ p.name }}（{{ p.type }}）
                {{ p.clearance_days != null ? '· 清关' + p.clearance_days + '天' : '' }}
              </el-tag>
            </div>

            <!-- 无 LPI 数据提示 -->
            <el-alert
              v-if="!routeResult.lpi"
              type="warning"
              show-icon
              :closable="false"
              title="未找到该目的地的LPI数据，雷达图无法显示"
              style="margin-top:12px"
            />
          </el-card>
        </template>

        <!-- LPI 雷达图 + 详情（单国家 或 航线目的国） -->
        <el-card v-if="activeCountry" class="radar-card" shadow="never">
          <template #header>
            <div class="card-title-row">
              <div class="card-title">
                <el-icon><PieChart /></el-icon>
                {{ activeCountry.country_cn }} LPI 六维雷达
              </div>
              <div class="risk-badge" :style="{ background: riskBg(activeCountry.risk_level), color: riskColor(activeCountry.risk_level) }">
                {{ activeCountry.risk_level }}风险
              </div>
            </div>
          </template>

          <el-row :gutter="16">
            <!-- 雷达图 -->
            <el-col :span="14">
              <div ref="radarRef" class="radar-chart"></div>
            </el-col>
            <!-- 六维得分表 -->
            <el-col :span="10">
              <div class="score-table">
                <div class="score-header">
                  <span>维度</span><span>评分 / 5.0</span>
                </div>
                <div
                  v-for="dim in dimensionRows"
                  :key="dim.key"
                  class="score-row"
                >
                  <span class="dim-name">{{ dim.label }}</span>
                  <div class="dim-bar-wrap">
                    <el-progress
                      :percentage="(activeCountry[dim.key] / 5) * 100"
                      :color="riskColor(activeCountry.risk_level)"
                      :show-text="false"
                      :stroke-width="8"
                      style="flex:1"
                    />
                    <span class="dim-score">{{ activeCountry[dim.key] ?? '—' }}</span>
                  </div>
                </div>

                <div class="score-summary">
                  <div class="summary-lpi">
                    <span>综合 LPI</span>
                    <span class="lpi-big" :style="{color: riskColor(activeCountry.risk_level)}">{{ activeCountry.lpi }}</span>
                    <span class="lpi-max">/ 5.0</span>
                  </div>
                  <div class="summary-rank" v-if="activeCountry.rank">
                    全球排名 <strong>#{{ activeCountry.rank }}</strong>
                  </div>
                  <div class="summary-year">{{ activeCountry.year }} 年数据</div>
                </div>
              </div>
            </el-col>
          </el-row>

          <!-- 风险解读 -->
          <div class="risk-explain">
            <div class="risk-explain-title">风险解读</div>
            <div class="risk-explain-body">
              <p>
                <strong>{{ activeCountry.country_cn }}</strong> 物流绩效指数（LPI）为
                <strong>{{ activeCountry.lpi }} / 5.0</strong>，全球排名
                <strong>{{ activeCountry.rank ? '#' + activeCountry.rank : '暂无' }}</strong>，
                综合风险评级为
                <span :style="{color: riskColor(activeCountry.risk_level), fontWeight: 600}">{{ activeCountry.risk_level }}风险</span>。
              </p>
              <p v-if="activeCountry.customs">
                海关效率 <strong>{{ activeCountry.customs }}</strong>，
                清关{{ activeCountry.customs >= 3.5 ? '流程相对顺畅' : '流程较为繁琐，建议预留充足清关时间' }}；
                基础设施评分 <strong>{{ activeCountry.infrastructure }}</strong>，
                {{ activeCountry.infrastructure >= 3.5 ? '港口和仓储条件较好' : '基础设施有限，可能影响货物中转效率' }}。
              </p>
              <p v-if="activeCountry.timeliness">
                时效性评分 <strong>{{ activeCountry.timeliness }}</strong>，
                货物追踪能力 <strong>{{ activeCountry.tracking }}</strong>，
                {{ activeCountry.timeliness >= 3.5 ? '货物交付准时率较高' : '时效稳定性一般，建议选择有保价服务的代理商' }}。
              </p>
            </div>
          </div>
        </el-card>

        <!-- 全国对比横向条形图 -->
        <el-card v-if="lpiList.length" class="compare-chart-card" shadow="never">
          <template #header>
            <div class="card-title"><el-icon><Histogram /></el-icon> 各国LPI综合评分对比</div>
          </template>
          <div ref="barRef" class="bar-chart"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis, Compass, Promotion, PieChart, Histogram } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getLpiList, getRouteRisk } from '@/api/risk'

const loadingList = ref(true)
const loadingRoute = ref(false)
const lpiList = ref([])
const selectedCountry = ref(null)
const activeCountry = ref(null)
const routeResult = ref(null)

const radarRef = ref(null)
const barRef = ref(null)
let radarChart = null
let barChart = null

const queryForm = reactive({ origin: '', destination: '' })

const dimensionRows = [
  { key: 'customs',               label: '通关效率' },
  { key: 'infrastructure',        label: '基础设施' },
  { key: 'international_shipments', label: '国际运输' },
  { key: 'logistics_competence',  label: '物流能力' },
  { key: 'tracking',              label: '货物追踪' },
  { key: 'timeliness',            label: '时效性' },
]

const riskTagType = (level) => {
  const map = { '低': 'success', '中低': 'success', '中': 'warning', '中高': 'warning', '高': 'danger' }
  return map[level] || 'info'
}
const riskColor = (level) => {
  const map = { '低': '#52c41a', '中低': '#73d13d', '中': '#faad14', '中高': '#fa8c16', '高': '#f5222d' }
  return map[level] || '#1890ff'
}
const riskBg = (level) => {
  const map = { '低': '#f6ffed', '中低': '#f6ffed', '中': '#fffbe6', '中高': '#fff7e6', '高': '#fff2f0' }
  return map[level] || '#f0f9ff'
}

const selectCountry = (item) => {
  selectedCountry.value = item.country_code
  activeCountry.value = item
  routeResult.value = null
  nextTick(() => renderRadar(item))
}

const renderRadar = (country) => {
  if (!radarRef.value) return
  if (!radarChart) {
    radarChart = echarts.init(radarRef.value)
  }
  const indicators = dimensionRows.map(d => ({ name: d.label, max: 5 }))
  const values = dimensionRows.map(d => country[d.key] ?? 0)
  const color = riskColor(country.risk_level)

  radarChart.setOption({
    radar: {
      indicator: indicators,
      radius: '65%',
      nameGap: 8,
      name: { textStyle: { color: '#595959', fontSize: 12 } },
      splitArea: { areaStyle: { color: ['rgba(24,144,255,0.03)', 'rgba(24,144,255,0.06)'] } },
      axisLine: { lineStyle: { color: '#e8e8e8' } },
      splitLine: { lineStyle: { color: '#e8e8e8' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        name: country.country_cn,
        areaStyle: { color: color + '33' },
        lineStyle: { color, width: 2 },
        itemStyle: { color },
        symbol: 'circle',
        symbolSize: 6,
        label: { show: true, formatter: ({ value }) => value.toFixed(2), fontSize: 11, color: '#595959' },
      }],
    }],
    tooltip: { trigger: 'item' },
  })
}

const renderBar = () => {
  if (!barRef.value || !lpiList.value.length) return
  if (!barChart) barChart = echarts.init(barRef.value)

  const sorted = [...lpiList.value].sort((a, b) => a.lpi - b.lpi)
  barChart.setOption({
    grid: { left: 90, right: 30, top: 10, bottom: 10, containLabel: false },
    xAxis: { type: 'value', max: 5, splitLine: { lineStyle: { color: '#f0f0f0' } }, axisLabel: { fontSize: 11 } },
    yAxis: { type: 'category', data: sorted.map(d => d.country_cn), axisLabel: { fontSize: 11 } },
    series: [{
      type: 'bar',
      data: sorted.map(d => ({
        value: d.lpi,
        itemStyle: { color: riskColor(d.risk_level), borderRadius: [0, 3, 3, 0] },
      })),
      label: { show: true, position: 'right', formatter: ({ value }) => value.toFixed(2), fontSize: 11 },
      barMaxWidth: 20,
    }],
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const d = sorted[params[0].dataIndex]
        return `${d.country_cn}<br/>LPI: ${d.lpi} &nbsp; ${d.risk_level}风险<br/>全球排名: #${d.rank ?? '—'}`
      }
    },
  })
}

const queryRouteRisk = async () => {
  if (!queryForm.origin || !queryForm.destination) {
    ElMessage.warning('请输入起始地和目的地')
    return
  }
  loadingRoute.value = true
  try {
    const res = await getRouteRisk(queryForm.origin, queryForm.destination)
    routeResult.value = res
    if (res.lpi) {
      selectedCountry.value = res.lpi.country_code
      activeCountry.value = res.lpi
      await nextTick()
      renderRadar(res.lpi)
    } else {
      activeCountry.value = null
    }
  } catch (e) {
    ElMessage.error('查询失败：' + (e.message || '未知错误'))
  } finally {
    loadingRoute.value = false
  }
}

onMounted(async () => {
  try {
    const data = await getLpiList()
    lpiList.value = data
    await nextTick()
    renderBar()
    // 默认选中第一个（最高分）
    if (data.length) selectCountry(data[0])
  } catch (e) {
    ElMessage.error('LPI数据加载失败')
  } finally {
    loadingList.value = false
  }
})
</script>

<style scoped>
.risk-page { padding: 0; }
.page-header { margin-bottom: 16px; }
.page-header h2 { font-size: 22px; font-weight: 600; color: #262626; margin: 0 0 4px; }
.subtitle { color: #8c8c8c; font-size: 13px; margin: 0; }

.card-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 14px; font-weight: 600; color: #262626;
}
.card-title-row {
  display: flex; align-items: center; justify-content: space-between;
}
.risk-badge {
  font-size: 12px; font-weight: 700; padding: 2px 10px;
  border-radius: 12px; border: 1px solid currentColor;
}

/* 左侧 */
.query-card { margin-bottom: 12px; border-radius: 8px; }
.rank-card { border-radius: 8px; }

.rank-list { display: flex; flex-direction: column; gap: 6px; max-height: 480px; overflow-y: auto; }
.rank-item {
  display: flex; flex-direction: column; gap: 4px;
  padding: 8px 10px; border-radius: 6px; cursor: pointer;
  transition: background .15s;
}
.rank-item:hover { background: #f5f5f5; }
.rank-active { background: #e6f4ff !important; }

.rank-no {
  font-size: 11px; font-weight: 700; width: 20px; height: 20px;
  border-radius: 50%; display: inline-flex; align-items: center;
  justify-content: center; flex-shrink: 0;
  background: #f0f0f0; color: #8c8c8c;
}
.rank-1 { background: #ffd700; color: #7c5800; }
.rank-2 { background: #c0c0c0; color: #555; }
.rank-3 { background: #cd7f32; color: #fff; }

.rank-body { display: flex; align-items: center; }
.rank-name { font-size: 13px; color: #262626; font-weight: 500; }
.rank-score-bar { display: flex; align-items: center; gap: 8px; }
.rank-score-val { font-size: 12px; color: #595959; width: 30px; text-align: right; flex-shrink: 0; }

/* 右侧 */
.empty-hint-card { border-radius: 8px; padding: 40px 0; }
.route-result-card { margin-bottom: 12px; border-radius: 8px; }
.radar-card { margin-bottom: 12px; border-radius: 8px; }
.compare-chart-card { border-radius: 8px; }

.route-stat-row .mini-stat {
  background: #fafafa; border-radius: 6px;
  padding: 10px 12px; text-align: center;
}
.mini-num { font-size: 20px; font-weight: 700; color: #262626; }
.mini-num.price { font-size: 16px; color: #d4380d; }
.mini-label { font-size: 12px; color: #8c8c8c; margin-top: 2px; }

.ports-row { margin-top: 12px; display: flex; align-items: center; flex-wrap: wrap; gap: 6px; font-size: 13px; }
.ports-label { color: #8c8c8c; flex-shrink: 0; }

.radar-chart { height: 300px; }
.bar-chart { height: 360px; }

/* 六维得分表 */
.score-table { display: flex; flex-direction: column; gap: 10px; }
.score-header { display: flex; justify-content: space-between; font-size: 12px; color: #8c8c8c; padding-bottom: 4px; border-bottom: 1px solid #f0f0f0; }
.score-row { display: flex; flex-direction: column; gap: 4px; }
.dim-name { font-size: 12px; color: #595959; }
.dim-bar-wrap { display: flex; align-items: center; gap: 8px; }
.dim-score { font-size: 12px; color: #262626; font-weight: 600; width: 28px; text-align: right; flex-shrink: 0; }

.score-summary {
  margin-top: 12px; padding-top: 12px;
  border-top: 1px solid #f0f0f0;
  text-align: center;
}
.summary-lpi { display: flex; align-items: baseline; justify-content: center; gap: 4px; margin-bottom: 4px; font-size: 13px; color: #8c8c8c; }
.lpi-big { font-size: 28px; font-weight: 700; }
.lpi-max { font-size: 13px; color: #bfbfbf; }
.summary-rank { font-size: 13px; color: #595959; }
.summary-rank strong { color: #1890ff; }
.summary-year { font-size: 12px; color: #bfbfbf; margin-top: 2px; }

/* 风险解读 */
.risk-explain {
  margin-top: 16px; padding: 14px 16px;
  background: #fafafa; border-radius: 6px;
  border-left: 3px solid #1890ff;
}
.risk-explain-title { font-size: 13px; font-weight: 600; color: #262626; margin-bottom: 8px; }
.risk-explain-body p { font-size: 13px; color: #595959; line-height: 1.8; margin: 0 0 6px; }
.risk-explain-body p:last-child { margin-bottom: 0; }
</style>
