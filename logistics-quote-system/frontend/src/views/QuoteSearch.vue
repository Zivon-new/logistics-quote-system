<template>
  <div class="page-container">
    <h2 class="page-title">报价查询</h2>

    <!-- 搜索表单 -->
    <el-card class="search-form">
      <el-form :model="searchForm" label-width="80px">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-form-item label="起始地" required>
              <el-input v-model="searchForm.起始地" placeholder="如：深圳" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="目的地" required>
              <el-input v-model="searchForm.目的地" placeholder="如：新加坡" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="货物名称">
              <el-input v-model="searchForm.货物名称" placeholder="关键词，如：服务器" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="代理商">
              <el-input v-model="searchForm.代理商" placeholder="代理商名称" clearable />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="10">
            <el-form-item label="日期范围">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="-"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="14" style="display:flex; align-items:flex-end; gap:8px; padding-bottom:18px">
            <el-button type="primary" :icon="Search" :loading="loading" @click="handleSearch">
              查询报价
            </el-button>
            <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 结果区 -->
    <template v-if="quoteResults.length > 0">

      <!-- 目的国 LPI 信息条 -->
      <div v-if="Object.keys(destLpiInfo).length" class="lpi-bar">
        <span class="lpi-bar-label">目的国物流指数（LPI）：</span>
        <span
          v-for="(info, dest) in destLpiInfo"
          :key="dest"
          class="lpi-bar-item"
        >
          <strong>{{ dest }}</strong>
          <template v-if="info.LPI">
            （{{ info.国家中文名 }}）&nbsp;
            <span class="lpi-score">{{ info.LPI }} / 5.0</span>&nbsp;
            <el-tag :type="riskTagType(info.风险等级)" size="small">{{ info.风险等级 }}风险</el-tag>
          </template>
          <template v-else>
            <el-tag type="info" size="small">暂无LPI数据</el-tag>
          </template>
        </span>
        <span class="lpi-bar-tip">· LPI越高物流越成熟，综合评分已将其纳入计算</span>
      </div>

      <!-- 排序 + 结果统计 -->
      <div class="result-toolbar">
        <span class="result-count">共 <strong>{{ total }}</strong> 条结果</span>
        <div class="sort-controls">
          <span class="sort-label">排序：</span>
          <el-radio-group v-model="sortBy" size="small">
            <el-radio-button value="score">综合评分</el-radio-button>
            <el-radio-button value="time">时效优先</el-radio-button>
            <el-radio-button value="price">价格优先</el-radio-button>
            <el-radio-button value="date">最新日期</el-radio-button>
          </el-radio-group>
        </div>
        <el-button type="success" :icon="Download" size="small">导出Excel</el-button>
      </div>

      <!-- 路线列表 -->
      <el-card
        v-for="route in sortedRoutes"
        :key="route.路线ID"
        class="route-card"
        shadow="never"
      >
        <!-- 路线头部 -->
        <div class="route-header">
          <span class="route-title">{{ route.起始地 }} → {{ route.目的地 }}</span>
          <el-tag v-if="route.途径地" type="info" size="small">途径 {{ route.途径地 }}</el-tag>
          <el-tag v-if="route.货物名称" type="success" size="small" class="goods-tag">
            {{ route.货物名称.length > 20 ? route.货物名称.slice(0, 20) + '…' : route.货物名称 }}
          </el-tag>
          <span class="route-date">{{ route.交易开始日期 }} 至 {{ route.交易结束日期 }}</span>
          <span class="route-weight">
            实重 {{ route.实际重量 }} kg
            <template v-if="route.计费重量">· 计费重 {{ route.计费重量 }} kg</template>
          </span>
        </div>

        <!-- 代理商表格 -->
        <el-table :data="sortedAgents(route.agents)" border stripe size="small">
          <!-- 评分列 -->
          <el-table-column label="推荐评分" width="90" align="center" sortable>
            <template #default="{ row }">
              <el-tooltip
                v-if="row.综合评分 != null"
                placement="right"
                :content="`时效:${row.各项得分?.时效得分} · 价格:${row.各项得分?.价格得分} · LPI:${row.各项得分?.LPI得分} · 信用:${row.各项得分?.信用得分}`"
              >
                <el-tag
                  :type="scoreTagType(row.综合评分)"
                  size="small"
                  style="font-weight:600; cursor:help"
                >
                  {{ row.综合评分 }}
                </el-tag>
              </el-tooltip>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>

          <el-table-column prop="代理商" label="代理商" min-width="130" />
          <el-table-column prop="运输方式" label="运输方式" width="90" />

          <!-- 时效 -->
          <el-table-column label="时效" width="100">
            <template #default="{ row }">
              <span :class="{ 'fast-time': row.时效天数 && row.时效天数 <= 10 }">
                {{ row.时效天数 ? row.时效天数 + ' 天' : (row.时效 || '—') }}
              </span>
            </template>
          </el-table-column>

          <!-- 小计（费用合计，不含税汇损） -->
          <el-table-column label="小计 (CNY)" width="120" align="right">
            <template #default="{ row }">
              <span class="price-text">
                {{ row.总费用 > 0 ? '¥ ' + row.总费用.toFixed(2) : '—' }}
              </span>
            </template>
          </el-table-column>

          <!-- 总计（含税+汇损的最终金额） -->
          <el-table-column label="总计 (CNY)" width="120" align="right">
            <template #default="{ row }">
              <span class="total-price" v-if="row.summary?.总计 > 0">
                ¥ {{ row.summary.总计.toFixed(2) }}
              </span>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>

          <!-- 赔付 -->
          <el-table-column label="赔付" width="66" align="center">
            <template #default="{ row }">
              <el-tag
                :type="isCompensation(row.是否赔付) ? 'success' : 'info'"
                size="small"
              >
                {{ isCompensation(row.是否赔付) ? '有' : '无' }}
              </el-tag>
            </template>
          </el-table-column>

          <!-- 操作 -->
          <el-table-column label="操作" width="90" align="center">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="viewDetail(row, route)">
                费用详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="searchForm.page"
          v-model:page-size="searchForm.page_size"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </template>

    <el-empty v-else-if="!loading" description="请输入起始地和目的地查询" />

    <!-- 费用详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="费用详情"
      fullscreen
      :close-on-click-modal="false"
      class="detail-dialog"
    >
      <div v-if="currentAgent && currentRoute" class="detail-container">
        <el-row :gutter="20">
          <!-- 左：路线 + 货物 + 智能评分 -->
          <el-col :span="12">
            <div class="detail-section">
              <h3>基本信息</h3>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="路线">{{ currentRoute.起始地 }} → {{ currentRoute.目的地 }}</el-descriptions-item>
                <el-descriptions-item label="途径地">{{ currentRoute.途径地 || '—' }}</el-descriptions-item>
                <el-descriptions-item label="交易日期">{{ currentRoute.交易开始日期 }} 至 {{ currentRoute.交易结束日期 }}</el-descriptions-item>
                <el-descriptions-item label="货物名称">{{ currentRoute.货物名称 || '—' }}</el-descriptions-item>
                <el-descriptions-item label="实际重量">{{ currentRoute.实际重量 }} kg</el-descriptions-item>
                <el-descriptions-item label="计费重量">{{ currentRoute.计费重量 || '—' }} kg</el-descriptions-item>
                <el-descriptions-item label="总体积">{{ currentRoute.总体积 || '—' }} cbm</el-descriptions-item>
                <el-descriptions-item label="货值">¥{{ currentRoute.货值 }}</el-descriptions-item>
              </el-descriptions>
            </div>

            <div class="detail-section" v-if="currentRoute.goods_details?.length || currentRoute.goods_total?.length">
              <h3>货物信息</h3>
              <el-table v-if="currentRoute.goods_details?.length" :data="currentRoute.goods_details" border stripe size="small" style="margin-bottom:12px">
                <el-table-column prop="货物名称" label="货物名称" min-width="140" />
                <el-table-column prop="货物种类" label="种类" width="90" />
                <el-table-column label="新品" width="60" align="center">
                  <template #default="{ row }">
                    <el-tag :type="isNewProduct(row.是否新品) ? 'success' : 'info'" size="small">
                      {{ isNewProduct(row.是否新品) ? '是' : '否' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="数量" label="数量" width="60" align="right" />
                <el-table-column label="总重(kg)" width="80" align="right">
                  <template #default="{ row }">{{ row['总重量(/kg)'] || 0 }}</template>
                </el-table-column>
                <el-table-column label="总价" width="90" align="right">
                  <template #default="{ row }">¥{{ (row.总货值 || row.总价 || 0).toFixed?.(2) }}</template>
                </el-table-column>
                <el-table-column prop="备注" label="备注" min-width="80" show-overflow-tooltip />
              </el-table>
              <div v-if="currentRoute.goods_total?.length" class="goods-total-list">
                <div v-for="g in currentRoute.goods_total" :key="g.整单货物ID" class="goods-total-item">
                  <span>{{ g.货物名称 || '整单' }}</span>
                  <span>实重 {{ g['实际重量(/kg)'] }} kg · 货值 ¥{{ g.货值?.toFixed(2) }} · 体积 {{ g['总体积(/cbm)'] }} cbm</span>
                  <span v-if="g.备注" class="dim">备注：{{ g.备注 }}</span>
                </div>
              </div>
            </div>

            <!-- 智能评分放在左侧底部 -->
            <div class="detail-section score-section" v-if="currentAgent.综合评分 != null">
              <h3>智能评分</h3>
              <div class="score-overview">
                <div class="score-circle-wrap">
                  <el-progress
                    type="circle"
                    :percentage="currentAgent.综合评分"
                    :color="scoreColor(currentAgent.综合评分)"
                    :width="80"
                    :stroke-width="7"
                  >
                    <template #default>
                      <span class="score-big">{{ currentAgent.综合评分 }}</span>
                    </template>
                  </el-progress>
                  <div class="dim" style="font-size:12px;margin-top:4px">综合评分</div>
                </div>
                <div class="score-dims">
                  <div v-for="dim in [
                    {label:'时效', val: currentAgent.各项得分?.时效得分, tip:'时效天数越短越高'},
                    {label:'价格', val: currentAgent.各项得分?.价格得分, tip:'报价越低越高'},
                    {label:'LPI',  val: currentAgent.各项得分?.LPI得分,  tip:'目的国物流绩效指数'},
                    {label:'信用', val: currentAgent.各项得分?.信用得分, tip:'代理商信用评分'},
                  ]" :key="dim.label" class="dim-row">
                    <el-tooltip :content="`${dim.label}得分（${dim.tip}）`" placement="top">
                      <span class="dim-label">{{ dim.label }}</span>
                    </el-tooltip>
                    <el-progress
                      :percentage="dim.val ?? 0"
                      :color="scoreColor(dim.val ?? 0)"
                      :show-text="false"
                      :stroke-width="6"
                      style="flex:1"
                    />
                    <span class="dim-val">{{ dim.val ?? '—' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </el-col>

          <!-- 右：代理商 + 费用明细 + 汇总 -->
          <el-col :span="12">
            <div class="detail-section">
              <h3>代理商信息</h3>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="代理商">{{ currentAgent.代理商 }}</el-descriptions-item>
                <el-descriptions-item label="运输方式">{{ currentAgent.运输方式 }}</el-descriptions-item>
                <el-descriptions-item label="贸易类型">{{ currentAgent.贸易类型 }}</el-descriptions-item>
                <el-descriptions-item label="时效">{{ currentAgent.时效 }}</el-descriptions-item>
                <el-descriptions-item label="时效备注" :span="2">{{ currentAgent.时效备注 || '—' }}</el-descriptions-item>
                <el-descriptions-item label="不含" :span="2">{{ currentAgent.不含 || '—' }}</el-descriptions-item>
                <el-descriptions-item label="是否赔付">
                  <el-tag :type="isCompensation(currentAgent.是否赔付) ? 'success' : 'info'" size="small">
                    {{ isCompensation(currentAgent.是否赔付) ? '有赔付' : '无赔付' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="赔付内容">{{ currentAgent.赔付内容 || '—' }}</el-descriptions-item>
                <el-descriptions-item v-if="currentAgent.代理备注" label="备注" :span="2">
                  {{ currentAgent.代理备注 }}
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <div class="detail-section">
              <h3>费用明细</h3>
              <el-table v-if="currentAgent.fee_items?.length" :data="currentAgent.fee_items" border stripe size="small" style="margin-bottom:12px">
                <el-table-column prop="费用类型" label="费用类型" min-width="110" />
                <el-table-column label="单价" width="120" align="right">
                  <template #default="{ row }">
                    {{ row.单价 }}{{ row.币种 }}{{ row.单位 ? '/' + row.单位.replace('/','') : '' }}
                  </template>
                </el-table-column>
                <el-table-column label="数量" width="60" align="right">
                  <template #default="{ row }">{{ Number(row.数量).toFixed(0) }}</template>
                </el-table-column>
                <el-table-column label="原币金额" width="100" align="right">
                  <template #default="{ row }">{{ row.原币金额?.toFixed(2) }} {{ row.币种 }}</template>
                </el-table-column>
                <el-table-column label="人民币" width="90" align="right">
                  <template #default="{ row }">
                    <span class="rmb-amount">¥{{ row.人民币金额?.toFixed(2) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="备注" label="备注" min-width="80" show-overflow-tooltip />
              </el-table>

              <el-table v-if="currentAgent.fee_total?.length" :data="currentAgent.fee_total" border stripe size="small">
                <el-table-column prop="费用名称" label="整单费用" min-width="130" />
                <el-table-column label="原币金额" width="120" align="right">
                  <template #default="{ row }">{{ row.原币金额?.toFixed(2) }} {{ row.币种 }}</template>
                </el-table-column>
                <el-table-column label="人民币" width="90" align="right">
                  <template #default="{ row }">
                    <span class="rmb-amount">¥{{ row.人民币金额?.toFixed(2) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="备注" label="备注" min-width="80" show-overflow-tooltip />
              </el-table>

              <el-empty v-if="!currentAgent.fee_items?.length && !currentAgent.fee_total?.length"
                description="暂无费用明细" :image-size="60" />
            </div>

            <div v-if="currentAgent.summary" class="detail-section">
              <h3>费用汇总</h3>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="小计">¥{{ currentAgent.summary.小计?.toFixed(2) }}</el-descriptions-item>
                <el-descriptions-item label="税率">{{ (currentAgent.summary.税率 * 100)?.toFixed(2) }}%</el-descriptions-item>
                <el-descriptions-item label="税金">¥{{ currentAgent.summary.税金?.toFixed(2) }}</el-descriptions-item>
                <el-descriptions-item label="汇损率">{{ (currentAgent.summary.汇损率 * 100)?.toFixed(4) }}%</el-descriptions-item>
                <el-descriptions-item label="汇损">¥{{ currentAgent.summary.汇损?.toFixed(2) }}</el-descriptions-item>
                <el-descriptions-item label="总计" :span="2">
                  <span class="total-amount">¥{{ currentAgent.summary.总计?.toFixed(2) }}</span>
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Download } from '@element-plus/icons-vue'
import { searchQuotes } from '@/api/quote'

const loading = ref(false)
const dateRange = ref([])
const quoteResults = ref([])
const total = ref(0)
const destLpiInfo = ref({})
const sortBy = ref('score')
const detailVisible = ref(false)
const currentAgent = ref(null)
const currentRoute = ref(null)

const searchForm = reactive({
  起始地: '', 目的地: '', 货物名称: '', 代理商: '',
  page: 1, page_size: 10
})

const isNewProduct = (v) => v === 1 || v === '1' || v === true
const isCompensation = (v) => v === 1 || v === '1' || v === true

const scoreTagType = (score) => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'primary'
  if (score >= 40) return 'warning'
  return 'danger'
}

const scoreColor = (score) => {
  if (score >= 80) return '#52c41a'
  if (score >= 60) return '#1890ff'
  if (score >= 40) return '#faad14'
  return '#ff4d4f'
}

const riskTagType = (level) => {
  const map = { '低': 'success', '中低': 'success', '中': 'warning', '中高': 'warning', '高': 'danger' }
  return map[level] || 'info'
}

// 每张路线卡的"代表值"（用于卡片间排序）
const routeSortKey = (route) => {
  const agents = route.agents || []
  if (sortBy.value === 'score') {
    const scores = agents.map(a => a.综合评分 ?? -1)
    return -Math.max(...scores, -1)           // 降序：最高分排前
  } else if (sortBy.value === 'time') {
    const times = agents.map(a => a.时效天数).filter(t => t != null)
    return times.length ? Math.min(...times) : 9999   // 升序：最快排前
  } else if (sortBy.value === 'price') {
    const prices = agents.map(a => a.总费用).filter(p => p > 0)
    return prices.length ? Math.min(...prices) : 9999999  // 升序：最低价排前
  } else {  // date
    return route.交易开始日期 ? -new Date(route.交易开始日期).getTime() : 0  // 降序：最新排前
  }
}

// 路线卡排序（返回排序后的路线列表）
const sortedRoutes = computed(() => {
  return [...quoteResults.value].sort((a, b) => routeSortKey(a) - routeSortKey(b))
})

// 路线内代理商始终按综合评分降序（方便对比同一路线）
const sortedAgents = (agents) => {
  if (!agents) return []
  return [...agents].sort((a, b) => (b.综合评分 ?? -1) - (a.综合评分 ?? -1))
}

const handleSearch = async () => {
  if (!searchForm.起始地 || !searchForm.目的地) {
    ElMessage.warning('请输入起始地和目的地')
    return
  }
  loading.value = true
  try {
    const params = {
      起始地: searchForm.起始地,
      目的地: searchForm.目的地,
      page: searchForm.page,
      page_size: searchForm.page_size,
    }
    if (searchForm.货物名称) params.货物名称 = searchForm.货物名称
    if (searchForm.代理商) params.代理商 = searchForm.代理商
    if (dateRange.value?.length === 2) {
      params.交易开始日期 = dateRange.value[0]
      params.交易结束日期 = dateRange.value[1]
    }
    const res = await searchQuotes(params)
    quoteResults.value = res.results
    total.value = res.total
    destLpiInfo.value = res.dest_lpi_info || {}
    if (res.total === 0) ElMessage.warning('未找到匹配结果')
    else ElMessage.success(`找到 ${res.total} 条结果`)
  } catch (e) {
    ElMessage.error('查询失败：' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  searchForm.起始地 = ''
  searchForm.目的地 = ''
  searchForm.货物名称 = ''
  searchForm.代理商 = ''
  searchForm.page = 1
  dateRange.value = []
  quoteResults.value = []
  total.value = 0
  destLpiInfo.value = {}
}

const viewDetail = (agent, route) => {
  currentAgent.value = agent
  currentRoute.value = route
  detailVisible.value = true
}
</script>

<style scoped>
.page-title { font-size: 22px; font-weight: 600; color: #262626; margin-bottom: 16px; }

.search-form { margin-bottom: 12px; border-radius: 8px; }
.search-form :deep(.el-form-item) { margin-bottom: 12px; }

/* LPI 信息条 */
.lpi-bar {
  display: flex; align-items: center; flex-wrap: wrap; gap: 12px;
  background: #f0f9ff; border: 1px solid #bae7ff;
  border-radius: 8px; padding: 10px 16px;
  font-size: 13px; margin-bottom: 10px;
}
.lpi-bar-label { color: #096dd9; font-weight: 600; }
.lpi-bar-item { display: flex; align-items: center; gap: 6px; }
.lpi-score { color: #1890ff; font-weight: 600; }
.lpi-bar-tip { color: #8c8c8c; font-size: 12px; margin-left: auto; }

/* 工具栏 */
.result-toolbar {
  display: flex; align-items: center; gap: 16px;
  margin-bottom: 12px; flex-wrap: wrap;
}
.result-count { font-size: 14px; color: #595959; }
.result-count strong { color: #1890ff; }
.sort-controls { display: flex; align-items: center; gap: 8px; }
.sort-label { font-size: 13px; color: #8c8c8c; }

/* 路线卡片 */
.route-card { margin-bottom: 12px; border-radius: 8px; }

.route-header {
  display: flex; align-items: center; flex-wrap: wrap;
  gap: 10px; margin-bottom: 12px;
}
.route-title { font-size: 16px; font-weight: 600; color: #262626; }
.goods-tag { max-width: 200px; overflow: hidden; text-overflow: ellipsis; }
.route-date { font-size: 12px; color: #8c8c8c; margin-left: auto; }
.route-weight { font-size: 12px; color: #8c8c8c; }

/* 表格内样式 */
.price-text { color: #595959; font-weight: 500; }
.total-price { color: #d4380d; font-weight: 700; }
.fast-time { color: #52c41a; font-weight: 600; }
.days-badge {
  display: inline-block; background: #e6f7ff; color: #1890ff;
  font-size: 11px; border-radius: 3px; padding: 0 4px; margin-left: 4px;
}
.dim { color: #bfbfbf; }

.pagination-container { margin-top: 16px; display: flex; justify-content: center; }

/* 详情弹窗 */
.detail-dialog :deep(.el-dialog__body) {
  padding: 20px; height: calc(100vh - 120px); overflow-y: auto;
}
.detail-section {
  margin-bottom: 20px; padding: 16px;
  background: #fafafa; border-radius: 6px;
}
.detail-section h3 {
  margin: 0 0 12px; font-size: 15px; font-weight: 600; color: #262626;
  padding-bottom: 8px; border-bottom: 2px solid #1890ff;
}

/* 评分区 */
.score-section { background: #f0f9ff; border: 1px solid #bae7ff; }
.score-overview { display: flex; gap: 24px; align-items: center; }
.score-circle-wrap { display: flex; flex-direction: column; align-items: center; flex-shrink: 0; }
.score-big { font-size: 18px; font-weight: 700; }
.score-dims { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.dim-row { display: flex; align-items: center; gap: 8px; }
.dim-label { font-size: 12px; color: #595959; width: 26px; flex-shrink: 0; cursor: help; }
.dim-val { font-size: 12px; color: #595959; width: 30px; text-align: right; flex-shrink: 0; }

.goods-total-list { display: flex; flex-direction: column; gap: 8px; }
.goods-total-item {
  display: flex; flex-direction: column; gap: 2px;
  padding: 8px 12px; background: #fff;
  border: 1px solid #f0f0f0; border-radius: 4px; font-size: 13px;
}

.rmb-amount { color: #52c41a; font-weight: 500; }
.total-amount { color: #f5222d; font-size: 18px; font-weight: 700; }
</style>
