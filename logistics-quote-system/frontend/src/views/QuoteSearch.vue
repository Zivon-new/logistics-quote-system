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
        <el-badge :value="selectedAgents.length" :hidden="selectedAgents.length < 2" type="primary">
          <el-button
            type="warning"
            :icon="Histogram"
            size="small"
            :disabled="selectedAgents.length < 2"
            @click="compareVisible = true"
          >
            对比报价{{ selectedAgents.length >= 2 ? `（${selectedAgents.length}家）` : '' }}
          </el-button>
        </el-badge>
        <el-button v-if="selectedAgents.length > 0" size="small" @click="selectedAgents = []">清空选择</el-button>
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

          <!-- 航线预警 badge -->
          <el-popover
            v-if="destWarnings[route.目的地]?.length"
            placement="bottom-start"
            :width="380"
            trigger="hover"
          >
            <template #reference>
              <el-tag
                :type="destWarnings[route.目的地][0].风险等级 >= 3 ? 'danger' : 'warning'"
                size="small"
                class="warning-tag"
              >
                <el-icon style="vertical-align:-2px"><Warning /></el-icon>
                {{ destWarnings[route.目的地][0].风险等级 >= 3 ? '高风险预警' : '风险提示' }}
                （{{ destWarnings[route.目的地].length }}条）
              </el-tag>
            </template>
            <div class="warning-popover">
              <div
                v-for="w in destWarnings[route.目的地]"
                :key="w.预警ID"
                class="warning-item"
                :class="w.风险等级 >= 3 ? 'warning-high' : 'warning-mid'"
              >
                <div class="warning-item-title">
                  <el-tag :type="w.风险等级 >= 3 ? 'danger' : 'warning'" size="small" style="margin-right:6px">
                    {{ w.风险等级文字 }}
                  </el-tag>
                  <strong>{{ w.预警标题 }}</strong>
                </div>
                <div class="warning-item-type">{{ w.风险类型 }} · 生效 {{ w.生效日期 }}</div>
                <div class="warning-item-detail">{{ w.预警详情 }}</div>
              </div>
            </div>
          </el-popover>

          <span class="route-date">{{ route.交易开始日期 }} 至 {{ route.交易结束日期 }}</span>
          <span class="route-weight">
            实重 {{ route.实际重量 }} kg
            <template v-if="route.计费重量">· 计费重 {{ route.计费重量 }} kg</template>
          </span>
        </div>

        <!-- 代理商表格 -->
        <el-table :data="sortedAgents(route.agents)" border stripe size="small">
          <!-- 选择列 -->
          <el-table-column width="46" align="center">
            <template #header>
              <el-icon style="color:#8c8c8c;font-size:13px" title="勾选后可横向对比"><Tickets /></el-icon>
            </template>
            <template #default="{ row }">
              <el-checkbox
                :model-value="isSelected(row, route)"
                @change="toggleSelect(row, route)"
                :disabled="!isSelected(row, route) && selectedAgents.length >= 6"
              />
            </template>
          </el-table-column>
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

    <!-- 报价对比弹窗 -->
    <el-dialog
      v-model="compareVisible"
      title="报价横向对比"
      width="90%"
      :close-on-click-modal="false"
      class="compare-dialog"
    >
      <div v-if="compareVisible" class="compare-container">
        <el-alert type="info" :closable="false" style="margin-bottom:12px">
          <template #title>
            共对比 <strong>{{ selectedAgents.length }}</strong> 家代理商方案；
            <span style="color:#52c41a">绿色</span>为最优值，<span style="color:#f5222d">红色</span>为最差值（同类可比项）
          </template>
        </el-alert>

        <div class="compare-scroll">
          <table class="compare-table">
            <thead>
              <tr>
                <th class="metric-col">指标</th>
                <th v-for="(item, idx) in selectedAgents" :key="idx" class="agent-col">
                  <div class="agent-col-header">
                    <div class="agent-name">{{ item.agent.代理商 }}</div>
                    <div class="agent-route">{{ item.route.起始地 }} → {{ item.route.目的地 }}</div>
                    <el-tag v-if="item.agent.综合评分 != null" :type="scoreTagType(item.agent.综合评分)" size="small" style="margin-top:4px">
                      综合 {{ item.agent.综合评分 }}
                    </el-tag>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in compareRows" :key="row.key" :class="{ 'section-header': row.isSection }">
                <td v-if="row.isSection" :colspan="selectedAgents.length + 1" class="section-title">{{ row.label }}</td>
                <template v-else>
                  <td class="metric-label">{{ row.label }}</td>
                  <td
                    v-for="(item, idx) in selectedAgents"
                    :key="idx"
                    class="metric-value"
                    :class="getCellClass(row, item)"
                  >
                    <span v-html="row.render(item)"></span>
                  </td>
                </template>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <template #footer>
        <el-button @click="compareVisible = false">关闭</el-button>
        <el-button type="danger" plain @click="selectedAgents = []; compareVisible = false">清空选择并关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Download, Histogram, Tickets, Warning } from '@element-plus/icons-vue'
import { searchQuotes } from '@/api/quote'

const route = useRoute()
const loading = ref(false)
const dateRange = ref([])
const quoteResults = ref([])
const total = ref(0)
const destLpiInfo = ref({})
const destWarnings = ref({})   // { 目的地: [预警列表] }
const sortBy = ref('score')
const detailVisible = ref(false)
const currentAgent = ref(null)
const currentRoute = ref(null)

// 报价对比
const selectedAgents = ref([])  // [{agent, route}]
const compareVisible = ref(false)

const agentKey = (agent, route) => `${route.路线ID}-${agent.代理商}-${agent.运输方式}`

const isSelected = (agent, route) =>
  selectedAgents.value.some(x => agentKey(x.agent, x.route) === agentKey(agent, route))

const toggleSelect = (agent, route) => {
  const key = agentKey(agent, route)
  const idx = selectedAgents.value.findIndex(x => agentKey(x.agent, x.route) === key)
  if (idx >= 0) {
    selectedAgents.value.splice(idx, 1)
  } else {
    if (selectedAgents.value.length >= 6) {
      ElMessage.warning('最多同时对比6家代理商')
      return
    }
    selectedAgents.value.push({ agent, route })
  }
}

// 对比表行定义
const compareRows = computed(() => [
  { key: 's1', isSection: true, label: '基本信息' },
  { key: '运输方式', label: '运输方式', render: ({ agent }) => agent.运输方式 || '—' },
  { key: '贸易类型', label: '贸易类型', render: ({ agent }) => agent.贸易类型 || '—' },
  {
    key: '时效天数', label: '时效', numeric: true, lowerBetter: true,
    getValue: ({ agent }) => agent.时效天数,
    render: ({ agent }) => agent.时效天数 ? `${agent.时效天数} 天` : (agent.时效 || '—'),
  },
  { key: '是否赔付', label: '赔付保障', render: ({ agent }) => isCompensation(agent.是否赔付) ? '<span style="color:#52c41a;font-weight:600">✔ 有赔付</span>' : '<span style="color:#bfbfbf">✘ 无赔付</span>' },
  { key: '赔付内容', label: '赔付说明', render: ({ agent }) => agent.赔付内容 || '—' },
  { key: '不含', label: '不含项目', render: ({ agent }) => agent.不含 || '—' },

  { key: 's2', isSection: true, label: '综合评分' },
  {
    key: '综合评分', label: '综合评分', numeric: true, lowerBetter: false,
    getValue: ({ agent }) => agent.综合评分,
    render: ({ agent }) => agent.综合评分 != null ? `<strong>${agent.综合评分}</strong> / 100` : '—',
  },
  {
    key: '时效得分', label: '时效得分', numeric: true, lowerBetter: false,
    getValue: ({ agent }) => agent.各项得分?.时效得分,
    render: ({ agent }) => agent.各项得分?.时效得分 ?? '—',
  },
  {
    key: '价格得分', label: '价格得分', numeric: true, lowerBetter: false,
    getValue: ({ agent }) => agent.各项得分?.价格得分,
    render: ({ agent }) => agent.各项得分?.价格得分 ?? '—',
  },
  {
    key: 'LPI得分', label: 'LPI得分', numeric: true, lowerBetter: false,
    getValue: ({ agent }) => agent.各项得分?.LPI得分,
    render: ({ agent }) => agent.各项得分?.LPI得分 ?? '—',
  },
  {
    key: '信用得分', label: '信用得分', numeric: true, lowerBetter: false,
    getValue: ({ agent }) => agent.各项得分?.信用得分,
    render: ({ agent }) => agent.各项得分?.信用得分 ?? '—',
  },

  { key: 's3', isSection: true, label: '费用（CNY）' },
  {
    key: '总费用', label: '小计（不含税汇损）', numeric: true, lowerBetter: true,
    getValue: ({ agent }) => agent.总费用 > 0 ? agent.总费用 : null,
    render: ({ agent }) => agent.总费用 > 0 ? `¥ ${agent.总费用.toFixed(2)}` : '—',
  },
  {
    key: '总计', label: '总计（含税汇损）', numeric: true, lowerBetter: true,
    getValue: ({ agent }) => agent.summary?.总计 > 0 ? agent.summary.总计 : null,
    render: ({ agent }) => agent.summary?.总计 > 0 ? `¥ ${agent.summary.总计.toFixed(2)}` : '—',
  },
  { key: '税率', label: '税率', render: ({ agent }) => agent.summary?.税率 != null ? (agent.summary.税率 * 100).toFixed(2) + '%' : '—' },
  { key: '汇损率', label: '汇损率', render: ({ agent }) => agent.summary?.汇损率 != null ? (agent.summary.汇损率 * 100).toFixed(4) + '%' : '—' },

  { key: 's4', isSection: true, label: '路线信息' },
  { key: '路线', label: '路线', render: ({ route }) => `${route.起始地} → ${route.目的地}` },
  { key: '途径地', label: '途径地', render: ({ route }) => route.途径地 || '—' },
  { key: '货物名称', label: '货物名称', render: ({ route }) => route.货物名称 || '—' },
  { key: '交易日期', label: '报价日期', render: ({ route }) => `${route.交易开始日期 || '—'} 至 ${route.交易结束日期 || '—'}` },
  { key: '实际重量', label: '实际重量', render: ({ route }) => route.实际重量 ? `${route.实际重量} kg` : '—' },
])

// 获取某行的最优/最差值集合（用于高亮）
const getRowExtremes = (row) => {
  if (!row.numeric) return {}
  const vals = selectedAgents.value
    .map(item => row.getValue(item))
    .filter(v => v != null && !isNaN(v))
  if (vals.length < 2) return {}
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  return { min, max }
}

const getCellClass = (row, item) => {
  if (!row.numeric) return ''
  const val = row.getValue(item)
  if (val == null || isNaN(val)) return ''
  const { min, max } = getRowExtremes(row)
  if (min === max) return ''
  if (row.lowerBetter) {
    if (val === min) return 'cell-best'
    if (val === max) return 'cell-worst'
  } else {
    if (val === max) return 'cell-best'
    if (val === min) return 'cell-worst'
  }
  return ''
}

const searchForm = reactive({
  起始地: '', 目的地: '', 货物名称: '', 代理商: '',
  page: 1, page_size: 10
})

// 支持从港口地图跳转时预填目的地（?dest=国家名）
onMounted(() => {
  if (route.query.dest) {
    searchForm.目的地 = route.query.dest
    handleSearch()
  }
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
    destWarnings.value = res.dest_warnings || {}
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
  destWarnings.value = {}
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

/* 对比弹窗 */
.compare-container { min-height: 300px; }

.compare-scroll { overflow-x: auto; }

.compare-table {
  width: 100%; border-collapse: collapse;
  font-size: 13px; table-layout: auto;
}
.compare-table th, .compare-table td {
  border: 1px solid #e8e8e8;
  padding: 8px 12px;
  text-align: center;
  vertical-align: middle;
}
.compare-table thead th {
  background: #fafafa;
  font-weight: 600;
}
.metric-col { width: 120px; min-width: 120px; background: #fafafa; }
.agent-col { min-width: 160px; }
.agent-col-header { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.agent-name { font-weight: 700; font-size: 14px; color: #262626; }
.agent-route { font-size: 12px; color: #8c8c8c; }

.metric-label {
  text-align: left; color: #595959; background: #fafafa;
  font-weight: 500; white-space: nowrap;
}
.metric-value { color: #262626; }

.section-title {
  background: #f0f5ff; color: #2f54eb;
  font-weight: 700; font-size: 13px;
  text-align: left; padding: 6px 12px;
  border-top: 2px solid #adc6ff;
}

.cell-best { background: #f6ffed; color: #389e0d; font-weight: 700; }
.cell-worst { background: #fff2f0; color: #cf1322; }

/* 预警 */
.warning-tag { cursor: pointer; }
.warning-popover { max-height: 400px; overflow-y: auto; }
.warning-item { padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
.warning-item:last-child { border-bottom: none; }
.warning-item-title { display: flex; align-items: center; margin-bottom: 4px; font-size: 13px; }
.warning-item-type { font-size: 11px; color: #8c8c8c; margin-bottom: 4px; }
.warning-item-detail { font-size: 12px; color: #595959; line-height: 1.7; }
.warning-high .warning-item-title { color: #cf1322; }
.warning-mid .warning-item-title { color: #d46b08; }
</style>
