<template>
  <div class="page-container">
    <h2 class="page-title">路线管理</h2>

    <!-- 搜索和操作栏 -->
    <el-card class="search-form">
      <el-form :model="searchForm" inline>
        <el-form-item label="起始地">
          <el-input v-model="searchForm.起始地" placeholder="请输入起始地" clearable style="width: 200px;" />
        </el-form-item>

        <el-form-item label="目的地">
          <el-input v-model="searchForm.目的地" placeholder="请输入目的地" clearable style="width: 200px;" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :icon="Search" @click="fetchRoutes">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          <el-button type="success" @click="$router.push('/route-manage/new')">新增路线</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 路线列表 -->
    <el-card class="result-container">
      <el-table 
        v-loading="loading"
        :data="routeList" 
        border 
        stripe
        style="width: 100%"
      >
        <el-table-column label="序号" width="80" align="center">
          <template #default="scope">
            {{ (pagination.page - 1) * pagination.page_size + scope.$index + 1 }}
          </template>
        </el-table-column>
        <el-table-column prop="起始地" label="起始地" width="120" />
        <el-table-column prop="途径地" label="途径地" width="120">
          <template #default="scope">
            {{ scope.row.途径地 || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="目的地" label="目的地" width="120" />
        <el-table-column label="交易日期" width="200">
          <template #default="scope">
            {{ scope.row.交易开始日期 }} 至 {{ scope.row.交易结束日期 }}
          </template>
        </el-table-column>
        <el-table-column prop="实际重量" label="实际重量(kg)" width="120" align="right">
          <template #default="scope">
            {{ scope.row['实际重量(/kg)'] }}
          </template>
        </el-table-column>
        <el-table-column prop="总体积" label="总体积(cbm)" width="120" align="right">
          <template #default="scope">
            {{ scope.row['总体积(/cbm)'] || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="货值" label="货值" width="130" align="right">
          <template #default="scope">
            {{ scope.row.货值币种 || 'RMB' }} {{ scope.row.货值 }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" align="center" fixed="right">
          <template #default="scope">
            <el-button type="primary" link size="small" @click="handleView(scope.row, (pagination.page - 1) * pagination.page_size + scope.$index + 1)">
              查看
            </el-button>
            <el-button
              v-if="userStore.userInfo.is_admin"
              type="success"
              link
              size="small"
              @click="handleCopy(scope.row)"
            >
              复制
            </el-button>
            <el-button
              v-if="userStore.userInfo.is_admin"
              type="warning"
              link
              size="small"
              @click="handleEdit(scope.row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="userStore.userInfo.is_admin"
              type="danger"
              link
              size="small"
              @click="handleDelete(scope.row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchRoutes"
          @current-change="fetchRoutes"
        />
      </div>
    </el-card>

    <!-- 全屏查看详情弹窗 -->
    <el-dialog 
      v-model="detailVisible" 
      title="路线详情" 
      fullscreen
      :close-on-click-modal="false"
      class="detail-dialog"
    >
      <div v-if="currentRoute" class="detail-container">

        <!-- ── 第一行：基本信息（左）+ 代理商基本信息（右） ── -->
        <el-row :gutter="20" style="margin-bottom:16px">
          <el-col :span="12">
            <div class="detail-section">
              <h3>基本信息</h3>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="路线序号">{{ currentSeqNo }}</el-descriptions-item>
                <el-descriptions-item label="起始地">{{ currentRoute.起始地 }}</el-descriptions-item>
                <el-descriptions-item label="目的地">{{ currentRoute.目的地 }}</el-descriptions-item>
                <el-descriptions-item label="途径地">{{ currentRoute.途径地 || '-' }}</el-descriptions-item>
                <el-descriptions-item label="交易开始日期">{{ currentRoute.交易开始日期 }}</el-descriptions-item>
                <el-descriptions-item label="交易结束日期">{{ currentRoute.交易结束日期 }}</el-descriptions-item>
                <el-descriptions-item label="实际重量">{{ currentRoute['实际重量(/kg)'] }} kg</el-descriptions-item>
                <el-descriptions-item label="计费重量">{{ currentRoute['计费重量(/kg)'] || '-' }} kg</el-descriptions-item>
                <el-descriptions-item label="总体积">{{ currentRoute['总体积(/cbm)'] || '-' }} cbm</el-descriptions-item>
                <el-descriptions-item label="货值">{{ currentRoute.货值币种 || 'RMB' }} {{ currentRoute.货值 }}</el-descriptions-item>
                <el-descriptions-item v-if="currentRoute.货物名称" label="货物名称" :span="2">{{ currentRoute.货物名称 }}</el-descriptions-item>
              </el-descriptions>
            </div>
          </el-col>

          <el-col :span="12">
            <div v-if="currentRoute.agents?.length > 0">
              <div v-for="(agent, agentIndex) in currentRoute.agents" :key="agent.代理路线ID">
                <el-divider v-if="agentIndex > 0" />
                <div class="detail-section">
                  <h3>代理商信息 {{ currentRoute.agents.length > 1 ? `(${agentIndex + 1}/${currentRoute.agents.length})` : '' }}</h3>
                  <el-descriptions :column="2" border size="small">
                    <el-descriptions-item label="代理商">{{ agent.代理商 }}</el-descriptions-item>
                    <el-descriptions-item label="运输方式">{{ agent.运输方式 }}</el-descriptions-item>
                    <el-descriptions-item label="贸易类型">{{ agent.贸易类型 }}</el-descriptions-item>
                    <el-descriptions-item label="时效">{{ agent.时效 }}</el-descriptions-item>
                    <el-descriptions-item label="时效备注" :span="2">{{ agent.时效备注 || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="不含" :span="2">{{ agent.不含 || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="是否赔付">
                      <el-tag :type="isCompensation(agent.是否赔付) ? 'success' : 'info'" size="small">
                        {{ isCompensation(agent.是否赔付) ? '是' : '否' }}
                      </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="赔付内容">{{ agent.赔付内容 || '-' }}</el-descriptions-item>
                    <el-descriptions-item v-if="agent.代理备注" label="代理备注" :span="2">{{ agent.代理备注 }}</el-descriptions-item>
                  </el-descriptions>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无代理商信息" :image-size="80" />
          </el-col>
        </el-row>

        <!-- ── 第二行：费用明细（全宽，每个代理商一块） ── -->
        <div v-if="currentRoute.agents?.length > 0">
          <div v-for="(agent, agentIndex) in currentRoute.agents" :key="`fees-${agent.代理路线ID}`" class="agent-fees-block">
            <div class="detail-section">
              <h3>
                费用明细
                <span v-if="currentRoute.agents.length > 1" class="agent-label">{{ agent.代理商 }}</span>
              </h3>

              <!-- 费用明细表 -->
              <div v-if="agent.fee_items?.length > 0" style="margin-bottom:16px">
                <p class="sub-table-title">明细费用（{{ agent.fee_items.filter(i => i.备注 !== '__GROUP_HEADER__').length }}条）</p>
                <el-table
                  :data="agent.fee_items"
                  border
                  size="small"
                  :span-method="feeItemsSpanMethod"
                  :row-class-name="({ row }) => row.备注 === '__GROUP_HEADER__' ? 'group-header-row' : (row.参与核算 === 0 || row.参与核算 === false ? 'excluded-view-row' : '')"
                >
                  <el-table-column label="费用类型" min-width="140">
                    <template #default="scope">
                      <div v-if="scope.row.备注 === '__GROUP_HEADER__'" class="group-header-cell">
                        <span class="group-header-icon">◆</span>
                        <span>{{ scope.row.费用类型 }}</span>
                      </div>
                      <span v-else>{{ scope.row.费用类型 }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="单价" width="130" align="right">
                    <template #default="scope">
                      {{ scope.row.单价 }}{{ scope.row.币种 }}{{ scope.row.单位 ? '/' + scope.row.单位.replace('/','') : '' }}
                    </template>
                  </el-table-column>
                  <el-table-column label="数量" width="80" align="right">
                    <template #default="scope">
                      {{ Number(scope.row.数量).toFixed(0) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="最低收费" width="120" align="right">
                    <template #default="scope">
                      <span v-if="scope.row.最低收费 && scope.row.备注 !== '__GROUP_HEADER__'" style="color:#8c8c8c;font-size:12px">
                        min {{ scope.row.最低收费 }} {{ scope.row.最低收费币种 || scope.row.币种 }}
                      </span>
                      <span v-else-if="scope.row.备注 !== '__GROUP_HEADER__'">—</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="原币金额" width="120" align="right">
                    <template #default="scope">
                      {{ scope.row.原币金额?.toFixed(2) }} {{ scope.row.币种 }}
                    </template>
                  </el-table-column>
                  <el-table-column label="人民币金额" width="120" align="right">
                    <template #default="scope">
                      <span style="color:#389e0d;font-weight:600">¥{{ scope.row.人民币金额?.toFixed(2) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="核算" width="70" align="center">
                    <template #default="scope">
                      <el-tag
                        v-if="scope.row.备注 !== '__GROUP_HEADER__' && (scope.row.参与核算 === 0 || scope.row.参与核算 === false)"
                        type="info" size="small" effect="plain"
                      >已排除</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="备注" min-width="200">
                    <template #default="scope">
                      <span v-if="scope.row.备注 && scope.row.备注 !== '__GROUP_HEADER__'" class="remark-text">
                        {{ scope.row.备注 }}
                      </span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <!-- 整单费用表 -->
              <div v-if="agent.fee_total?.length > 0">
                <p class="sub-table-title">整单费用（{{ agent.fee_total.filter(i => i.备注 !== '__GROUP_HEADER__').length }}条）</p>
                <el-table
                  :data="agent.fee_total"
                  border
                  size="small"
                  :span-method="feeTotalSpanMethod"
                  :row-class-name="({ row }) => row.备注 === '__GROUP_HEADER__' ? 'group-header-row' : (row.参与核算 === 0 || row.参与核算 === false ? 'excluded-view-row' : '')"
                >
                  <el-table-column label="费用名称" min-width="180">
                    <template #default="scope">
                      <div v-if="scope.row.备注 === '__GROUP_HEADER__'" class="group-header-cell">
                        <span class="group-header-icon">◆</span>
                        <span>{{ scope.row.费用名称 }}</span>
                      </div>
                      <span v-else>{{ scope.row.费用名称 }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="原币金额" width="150" align="right">
                    <template #default="scope">
                      {{ scope.row.原币金额?.toFixed(2) }} {{ scope.row.币种 }}
                    </template>
                  </el-table-column>
                  <el-table-column label="人民币金额" width="150" align="right">
                    <template #default="scope">
                      <span style="color:#389e0d;font-weight:600">¥{{ scope.row.人民币金额?.toFixed(2) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="核算" width="70" align="center">
                    <template #default="scope">
                      <el-tag
                        v-if="scope.row.备注 !== '__GROUP_HEADER__' && (scope.row.参与核算 === 0 || scope.row.参与核算 === false)"
                        type="info" size="small" effect="plain"
                      >已排除</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="备注" min-width="200">
                    <template #default="scope">
                      <span v-if="scope.row.备注 && scope.row.备注 !== '__GROUP_HEADER__'" class="remark-text">
                        {{ scope.row.备注 }}
                      </span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <el-empty
                v-if="!agent.fee_items?.length && !agent.fee_total?.length"
                description="暂无费用明细"
                :image-size="60"
              />
            </div>
          </div>
        </div>

        <!-- ── 第三行：货物信息（左）+ 费用汇总（右） ── -->
        <el-row :gutter="20" style="margin-bottom:16px">
          <!-- 货物信息 -->
          <el-col :span="10">
            <div class="detail-section">
              <h3>货物信息</h3>
              <div v-if="currentRoute.goods_details?.length > 0" style="margin-bottom:16px">
                <p class="sub-table-title">货物明细</p>
                <el-table :data="currentRoute.goods_details" border size="small" max-height="320">
                  <el-table-column prop="货物名称" label="货物名称" min-width="130" />
                  <el-table-column prop="货物种类" label="种类" width="80" />
                  <el-table-column label="新品" width="60" align="center">
                    <template #default="scope">
                      <el-tag :type="isNewProduct(scope.row.是否新品) ? 'success' : 'info'" size="small">
                        {{ isNewProduct(scope.row.是否新品) ? '是' : '否' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="数量" label="数量" width="55" align="right" />
                  <el-table-column label="总重" width="75" align="right">
                    <template #default="scope">{{ scope.row['总重量(/kg)'] || 0 }} kg</template>
                  </el-table-column>
                  <el-table-column label="总价" width="80" align="right">
                    <template #default="scope">¥{{ (scope.row.总货值 || scope.row.总价 || 0)?.toFixed(2) }}</template>
                  </el-table-column>
                  <el-table-column label="备注" min-width="100">
                    <template #default="scope">
                      <span v-if="scope.row.备注" class="remark-text">{{ scope.row.备注 }}</span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div v-if="currentRoute.goods_total?.length > 0">
                <p class="sub-table-title">整单货物</p>
                <div class="goods-summary">
                  <div v-for="goods in currentRoute.goods_total" :key="goods.整单货物ID" class="summary-item">
                    <span class="summary-label">{{ goods.货物名称 || '货物信息' }}:</span>
                    <span class="summary-value">
                      实重 {{ goods['实际重量(/kg)'] }} kg · 货值 {{ goods.货值币种 || 'RMB' }} {{ goods.货值?.toFixed(2) }} · 体积 {{ goods['总体积(/cbm)'] }} cbm
                    </span>
                    <p v-if="goods.备注" class="remark-text" style="margin:4px 0 0">{{ goods.备注 }}</p>
                  </div>
                </div>
              </div>
              <el-empty
                v-if="!currentRoute.goods_details?.length && !currentRoute.goods_total?.length"
                description="暂无货物信息"
                :image-size="60"
              />
            </div>
          </el-col>

          <!-- 费用汇总 -->
          <el-col :span="14">
            <div v-if="currentRoute.agents?.length > 0">
              <div v-for="(agent, agentIndex) in currentRoute.agents" :key="`sum-${agent.代理路线ID}`">
                <el-divider v-if="agentIndex > 0" />
                <div v-if="agent.summary" class="detail-section summary-section">
                  <h3>
                    费用汇总
                    <span v-if="currentRoute.agents.length > 1" class="agent-label">{{ agent.代理商 }}</span>
                  </h3>
                  <div class="summary-grid">
                    <div class="summary-row">
                      <div class="summary-cell">
                        <span class="s-label">运费小计</span>
                        <span class="s-value">
                          <span v-if="getAgentFeesCurrency(agent)" class="s-foreign">
                            {{ getAgentFeesCurrency(agent) }} {{ getAgentForeignSubtotal(agent, getAgentFeesCurrency(agent)).toFixed(2) }} →
                          </span>
                          ¥{{ agent.summary.小计?.toFixed(2) }}
                        </span>
                      </div>
                      <div class="summary-cell">
                        <span class="s-label">进口税率</span>
                        <span class="s-value">
                          <template v-if="parseTaxDetails(agent.summary.进口税率原文).length > 0">
                            <span v-for="(row, i) in parseTaxDetails(agent.summary.进口税率原文)" :key="i" style="display:block">
                              {{ row.货物名称 || ('货物'+(i+1)) }}：{{ row.税率说明 ? (row.税率说明 + ' ') : '' }}{{ row.综合税率 }}%
                            </span>
                          </template>
                          <template v-else>{{ agent.summary.税率 ? (agent.summary.税率 * 100).toFixed(2) + '%' : '—' }}</template>
                        </span>
                      </div>
                      <div class="summary-cell">
                        <span class="s-label">税金</span>
                        <span class="s-value">¥{{ agent.summary.税金?.toFixed(2) }}</span>
                      </div>
                      <div class="summary-cell">
                        <span class="s-label">汇损率</span>
                        <span class="s-value">{{ (agent.summary.汇损率 * 100)?.toFixed(4) }}%</span>
                      </div>
                      <div class="summary-cell">
                        <span class="s-label">汇损</span>
                        <span class="s-value">¥{{ agent.summary.汇损?.toFixed(2) }}</span>
                      </div>
                    </div>
                    <div class="summary-total-row">
                      <span class="s-total-label">综合成本总计</span>
                      <span class="s-total-value">
                        <span v-if="getAgentFeesCurrency(agent)" class="s-total-foreign">
                          {{ getAgentFeesCurrency(agent) }}
                          {{ (getAgentForeignSubtotal(agent, getAgentFeesCurrency(agent))
                            + (agent.summary.税金 || 0)
                            + (agent.summary.汇损 || 0)).toFixed(2) }} →
                        </span>
                        ¥{{ agent.summary.总计?.toFixed(2) }}
                      </span>
                    </div>
                    <div v-if="agent.summary.备注" class="summary-remark">
                      备注：{{ agent.summary.备注 }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>

        <!-- 附件管理 -->
        <div class="detail-section">
          <h3>附件管理</h3>
          <AttachmentPanel :route-id="currentRoute.路线ID" />
        </div>
      </div>
    </el-dialog>

    <!-- ✅ 编辑对话框 -->
    <RouteEditDialog
      v-if="editingRoute"
      v-model="editDialogVisible"
      :route-data="editingRoute"
      mode="edit"
      @success="handleEditSave"
      @cancel="editDialogVisible = false"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onActivated, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { getRoutes, getRouteDetail, deleteRoute, updateRoute } from '@/api/route'
import { useUserStore } from '@/stores/user'
import { useRouteCopyStore } from '@/stores/routeCopy'
import { transformForCopy } from '@/utils/routeCopyTransform'
import RouteEditDialog from './NewRoute/components/RouteEditDialog.vue'
import AttachmentPanel from '@/components/AttachmentPanel.vue'

const userStore     = useUserStore()
const routeCopyStore = useRouteCopyStore()
const router        = useRouter()

const loading = ref(false)
const routeList = ref([])
const detailVisible = ref(false)
const currentRoute = ref(null)
const currentSeqNo = ref(null)

// ✅ 添加：编辑对话框状态
const editDialogVisible = ref(false)
const editingRoute = ref(null)

const searchForm = reactive({
  起始地: '',
  目的地: ''
})

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const isIncluded = (i) => i.参与核算 !== 0 && i.参与核算 !== false

// 获取代理商费用的单一外币（仅看参与核算的费用，用于小计显示）
const getAgentFeesCurrency = (agent) => {
  const currencies = new Set()
  agent.fee_items?.filter(i => i.备注 !== '__GROUP_HEADER__' && isIncluded(i) && (i.原币金额 || 0) > 0)
    .forEach(i => currencies.add(i.币种 || 'RMB'))
  agent.fee_total?.filter(i => i.备注 !== '__GROUP_HEADER__' && isIncluded(i) && (i.原币金额 || 0) > 0)
    .forEach(i => currencies.add(i.币种 || 'RMB'))
  const arr = Array.from(currencies)
  return arr.length === 1 && arr[0] !== 'RMB' ? arr[0] : null
}

// 计算费用原币总额（仅计参与核算的费用）
const getAgentForeignSubtotal = (agent, currency) => {
  let total = 0
  agent.fee_items?.filter(i => i.备注 !== '__GROUP_HEADER__' && isIncluded(i) && i.币种 === currency)
    .forEach(i => { total += parseFloat(i.原币金额) || 0 })
  agent.fee_total?.filter(i => i.备注 !== '__GROUP_HEADER__' && isIncluded(i) && i.币种 === currency)
    .forEach(i => { total += parseFloat(i.原币金额) || 0 })
  return total
}

// 分组标题 span-method（费用明细表：7列 — 费用类型/单价/数量/原币/人民币/核算/备注）
const feeItemsSpanMethod = ({ row, columnIndex }) => {
  if (row.备注 === '__GROUP_HEADER__') {
    return columnIndex === 0 ? [1, 7] : [0, 0]
  }
  return [1, 1]
}

// 分组标题 span-method（整单费用表：5列 — 费用名称/原币/人民币/核算/备注）
const feeTotalSpanMethod = ({ row, columnIndex }) => {
  if (row.备注 === '__GROUP_HEADER__') {
    return columnIndex === 0 ? [1, 5] : [0, 0]
  }
  return [1, 1]
}

// 判断是否为新品（兼容多种数据类型）
const isNewProduct = (value) => {
  // 兼容：数字1、字符串"1"、布尔值true
  return value === 1 || value === '1' || value === true
}

// 判断是否赔付（兼容多种数据类型）
const isCompensation = (value) => {
  // 兼容：数字1、字符串"1"、布尔值true
  return value === 1 || value === '1' || value === true
}

const parseTaxDetails = (json) => {
  try { return JSON.parse(json || '[]') } catch { return [] }
}

// 获取路线列表
const fetchRoutes = async () => {
  loading.value = true

  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size
    }

    if (searchForm.起始地) params.起始地 = searchForm.起始地
    if (searchForm.目的地) params.目的地 = searchForm.目的地

    const res = await getRoutes(params)
    // ✅ 修复：正确解析返回数据
    if (res.success && res.data) {
      routeList.value = res.data.results
      pagination.total = res.data.total
    } else {
      routeList.value = []
      pagination.total = 0
    }
  } catch (error) {
    console.error('获取路线列表失败:', error)
    ElMessage.error('加载失败')
    routeList.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

// 重置搜索
const handleReset = () => {
  searchForm.起始地 = ''
  searchForm.目的地 = ''
  pagination.page = 1
  fetchRoutes()
}

// 查看详情
const handleView = async (row, seqNo) => {
  try {
    const res = await getRouteDetail(row.路线ID)
    if (res.success && res.data) {
      currentRoute.value = res.data
      currentSeqNo.value = seqNo
    } else {
      ElMessage.error('获取详情失败')
    }
    detailVisible.value = true
  } catch (error) {
    console.error('获取路线详情失败:', error)
    ElMessage.error('获取详情失败')
  }
}

// 新增路线
const handleAdd = () => {
  ElMessage.info('新增功能开发中...')
}

// 编辑路线
const handleEdit = async (row) => {
  try {
    console.log('📝 编辑路线:', row.路线ID)
    
    // 获取完整的路线数据
    const res = await getRouteDetail(row.路线ID)
    
    if (res.success && res.data) {
      editingRoute.value = {
        路线ID: res.data.路线ID,
        ...res.data
      }
      editDialogVisible.value = true
      console.log('✅ 编辑数据加载完成:', editingRoute.value)
    } else {
      ElMessage.error('获取路线数据失败')
    }
  } catch (error) {
    console.error('编辑路线失败:', error)
    ElMessage.error('编辑路线失败: ' + error.message)
  }
}

// 复制路线：克隆代理费用结构，导航到新建路线页
const handleCopy = async (row) => {
  try {
    const res = await getRouteDetail(row.路线ID)
    if (!res?.success || !res.data) {
      ElMessage.error('获取路线数据失败')
      return
    }
    routeCopyStore.setCopyTemplate(
      transformForCopy(res.data),
      `${res.data.起始地} → ${res.data.目的地}`
    )
    router.push('/route-manage/new')
  } catch {
    ElMessage.error('复制路线失败')
  }
}

// ✅ 添加：保存编辑结果
const handleEditSave = async () => {
  // ✅ ManualInput 已在内部调用 updateRoute 并显示成功提示
  // 这里只需关闭弹窗并刷新列表
  editDialogVisible.value = false
  await fetchRoutes()
}

// 删除路线
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除路线 "${row.起始地} → ${row.目的地}" 吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const res = await deleteRoute(row.路线ID)
    // ✅ 修复：检查返回结果
    if (res.success) {
      ElMessage.success('删除成功')
      fetchRoutes()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchRoutes()
})

// ✅ keep-alive 场景（或从编辑页返回）也强制刷新
onActivated(() => {
  fetchRoutes()
})
</script>

<style scoped>
.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* 全屏详情弹窗 */
.detail-dialog :deep(.el-dialog__body) {
  padding: 20px;
  height: calc(100vh - 120px);
  overflow-y: auto;
}

.detail-container {
  height: 100%;
}

.agent-wrapper {
  margin-bottom: 20px;
  border: 1px solid #e8f4ff;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(24, 144, 255, 0.06);
}

.detail-section {
  margin-bottom: 16px;
  padding: 14px 16px;
  background: #fafafa;
  border-radius: 6px;
}

.detail-section h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  padding-bottom: 8px;
  border-bottom: 2px solid #1890ff;
}

/* 整单货物汇总样式 */
.goods-summary {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 12px;
}

.summary-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.summary-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.summary-label {
  font-size: 14px;
  color: #595959;
  font-weight: 600;
  display: inline-block;
  min-width: 120px;
}

.summary-value {
  font-size: 14px;
  color: #262626;
}

/* 总计样式（保留兼容旧用法） */
.total-amount {
  color: #f5222d;
  font-size: 18px;
  font-weight: 600;
}

.agent-fees-block {
  margin-bottom: 16px;
}

.agent-label {
  font-size: 13px;
  font-weight: 400;
  color: #1890ff;
  margin-left: 10px;
  background: #e6f4ff;
  padding: 2px 8px;
  border-radius: 10px;
}

.sub-table-title {
  font-size: 13px;
  font-weight: 600;
  color: #595959;
  margin: 0 0 8px;
}

.remark-text {
  font-size: 13px;
  color: #434343;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}

:deep(.excluded-view-row) td {
  background-color: #fafafa !important;
  color: #bfbfbf !important;
  text-decoration: line-through;
}

/* ── 分组标题行 ─────────────────────────────────── */
:deep(.group-header-row) td {
  background: linear-gradient(90deg, #e6f0ff 0%, #f0f5ff 100%) !important;
  border-top: 2px solid #91caff !important;
  border-bottom: 2px solid #91caff !important;
  padding: 0 !important;
}

.group-header-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  font-weight: 700;
  font-size: 13px;
  color: #1677ff;
  letter-spacing: 0.5px;
}

.group-header-icon {
  font-size: 9px;
  color: #4096ff;
}

/* ── 费用汇总新样式 ──────────────────────────────── */
.summary-section .detail-section {
  background: #fff;
}

.summary-grid {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
}

.summary-row {
  display: flex;
  flex-wrap: wrap;
  border-bottom: 1px solid #e5e7eb;
}

.summary-cell {
  flex: 1;
  min-width: 90px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 8px;
  border-right: 1px solid #f0f0f0;
  gap: 4px;
}

.summary-cell:last-child {
  border-right: none;
}

.s-label {
  font-size: 11px;
  color: #8c8c8c;
}

.s-value {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.s-foreign {
  font-size: 11px;
  color: #1677ff;
  margin-right: 4px;
  font-weight: 500;
}

.summary-total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: linear-gradient(90deg, #fff7e6, #fffbe6);
}

.s-total-foreign {
  font-size: 13px;
  color: #1677ff;
  margin-right: 6px;
  font-weight: 600;
}

.s-total-label {
  font-size: 14px;
  font-weight: 600;
  color: #595959;
}

.s-total-value {
  font-size: 22px;
  font-weight: 700;
  color: #d4380d;
}

.summary-remark {
  padding: 6px 20px;
  font-size: 12px;
  color: #8c8c8c;
  background: #fafafa;
  border-top: 1px solid #f0f0f0;
}
</style>