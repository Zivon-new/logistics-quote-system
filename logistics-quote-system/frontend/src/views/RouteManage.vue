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
        <el-table-column prop="货值" label="货值" width="120" align="right">
          <template #default="scope">
            ¥{{ scope.row.货值 }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="scope">
            <el-button type="primary" link size="small" @click="handleView(scope.row)">
              查看
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
        <el-row :gutter="20">
          <!-- 左侧：路线和货物信息 -->
          <el-col :span="12">
            <!-- 基本信息 -->
            <div class="detail-section">
              <h3>基本信息</h3>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="路线ID">{{ currentRoute.路线ID }}</el-descriptions-item>
                <el-descriptions-item label="起始地">{{ currentRoute.起始地 }}</el-descriptions-item>
                <el-descriptions-item label="目的地">{{ currentRoute.目的地 }}</el-descriptions-item>
                <el-descriptions-item label="途径地">{{ currentRoute.途径地 || '-' }}</el-descriptions-item>
                <el-descriptions-item label="交易开始日期">{{ currentRoute.交易开始日期 }}</el-descriptions-item>
                <el-descriptions-item label="交易结束日期">{{ currentRoute.交易结束日期 }}</el-descriptions-item>
                <el-descriptions-item label="实际重量">{{ currentRoute['实际重量(/kg)'] }} kg</el-descriptions-item>
                <el-descriptions-item label="计费重量">{{ currentRoute['计费重量(/kg)'] || '-' }} kg</el-descriptions-item>
                <el-descriptions-item label="总体积">{{ currentRoute['总体积(/cbm)'] || '-' }} cbm</el-descriptions-item>
                <el-descriptions-item label="货值">¥{{ currentRoute.货值 }}</el-descriptions-item>
                <el-descriptions-item v-if="currentRoute.货物名称" label="货物名称" :span="2">{{ currentRoute.货物名称 }}</el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- 货物信息（合并货物明细和整单货物） -->
            <div class="detail-section">
              <h3>货物信息</h3>
              
              <!-- 货物明细表格 -->
              <div v-if="currentRoute.goods_details?.length > 0" style="margin-bottom: 16px;">
                <p style="font-size: 14px; font-weight: 600; color: #595959; margin-bottom: 8px;">货物明细</p>
                <el-table 
                  :data="currentRoute.goods_details" 
                  border 
                  stripe
                  max-height="300"
                  size="small"
                >
                  <el-table-column prop="货物名称" label="货物名称" min-width="140" />
                  <el-table-column prop="货物种类" label="货物种类" width="90" />
                  <el-table-column label="是否新品" width="70" align="center">
                    <template #default="scope">
                      <el-tag :type="isNewProduct(scope.row.是否新品) ? 'success' : 'info'" size="small">
                        {{ isNewProduct(scope.row.是否新品) ? '是' : '否' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="数量" label="数量" width="60" align="right" />
                  <el-table-column label="重量" width="80" align="right">
                    <template #default="scope">
                      {{ scope.row['重量(/kg)'] || 0 }} kg
                    </template>
                  </el-table-column>
                  <el-table-column label="总重量" width="80" align="right">
                    <template #default="scope">
                      {{ scope.row['总重量(/kg)'] || 0 }} kg
                    </template>
                  </el-table-column>
                  <el-table-column label="单价" width="80" align="right">
                    <template #default="scope">
                      {{ scope.row.单价 || 0 }} {{ scope.row.币种 || '' }}
                    </template>
                  </el-table-column>
                  <el-table-column label="总价" width="90" align="right">
                    <template #default="scope">
                      ¥{{ (scope.row.总货值 || scope.row.总价 || 0)?.toFixed(2) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="备注" label="备注" min-width="100" show-overflow-tooltip />
                </el-table>
              </div>

              <!-- 整单货物汇总（在货物明细下方） -->
              <div v-if="currentRoute.goods_total?.length > 0">
                <p style="font-size: 14px; font-weight: 600; color: #595959; margin-bottom: 8px;">整单汇总</p>
                <div class="goods-summary">
                  <div v-for="goods in currentRoute.goods_total" :key="goods.整单货物ID" class="summary-item">
                    <span class="summary-label">{{ goods.货物名称 || '货物信息' }}:</span>
                    <span class="summary-value">
                      实际重量 {{ goods['实际重量(/kg)'] }} kg | 
                      货值 ¥{{ goods.货值?.toFixed(2) }} | 
                      体积 {{ goods['总体积(/cbm)'] }} cbm
                    </span>
                    <div v-if="goods.备注" style="margin-top: 4px;">
                      <span style="color: #909399; font-size: 12px;">备注：{{ goods.备注 }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 两者都没有时显示 -->
              <el-empty 
                v-if="(!currentRoute.goods_details || currentRoute.goods_details.length === 0) && 
                      (!currentRoute.goods_total || currentRoute.goods_total.length === 0)" 
                description="暂无货物信息" 
                :image-size="60" 
              />
            </div>
          </el-col>

          <!-- 右侧：代理商和费用信息 -->
          <el-col :span="12">
            <div v-if="currentRoute.agents?.length > 0">
              <!-- 遍历所有代理商 -->
              <div v-for="(agent, agentIndex) in currentRoute.agents" :key="agent.代理路线ID" class="agent-wrapper">
                <el-divider v-if="agentIndex > 0" />
                
                <!-- 代理商信息 -->
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
                    <el-descriptions-item v-if="agent.代理备注" label="代理备注" :span="2">
                      {{ agent.代理备注 }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>

                <!-- 费用明细（表格展示全部字段） -->
                <div class="detail-section">
                  <h3>费用明细</h3>
                  
                  <!-- 费用明细表 (fee_items) -->
                  <div v-if="agent.fee_items?.length > 0" style="margin-bottom: 16px;">
                    <p style="font-size: 13px; font-weight: 600; color: #595959; margin-bottom: 8px;">费用明细（{{ agent.fee_items.length }}条）</p>
                    <el-table :data="agent.fee_items" border stripe size="small">
                      <el-table-column prop="费用类型" label="费用类型" min-width="120" />
                      <el-table-column label="单价" width="100" align="right">
                        <template #default="scope">
                          {{ scope.row.单价 }}{{ scope.row.币种 }}{{ scope.row.单位 ? '/' + scope.row.单位.replace('/','') : '' }}
                        </template>
                      </el-table-column>
                      <el-table-column prop="数量" label="数量" width="70" align="right">
                        <template #default="scope">
                          {{ Number(scope.row.数量).toFixed(0) }}
                        </template>
                      </el-table-column>
                      <el-table-column label="原币金额" width="100" align="right">
                        <template #default="scope">
                          {{ scope.row.原币金额?.toFixed(2) }} {{ scope.row.币种 }}
                        </template>
                      </el-table-column>
                      <el-table-column label="人民币金额" width="100" align="right">
                        <template #default="scope">
                          <span style="color: #52c41a; font-weight: 500;">¥{{ scope.row.人民币金额?.toFixed(2) }}</span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="备注" label="备注" min-width="100" show-overflow-tooltip />
                    </el-table>
                  </div>
                  
                  <!-- 整单费用表 (fee_total) -->
                  <div v-if="agent.fee_total?.length > 0" style="margin-bottom: 16px;">
                    <p style="font-size: 13px; font-weight: 600; color: #595959; margin-bottom: 8px;">整单费用（{{ agent.fee_total.length }}条）</p>
                    <el-table :data="agent.fee_total" border stripe size="small">
                      <el-table-column prop="费用名称" label="费用名称" min-width="140" />
                      <el-table-column label="原币金额" width="120" align="right">
                        <template #default="scope">
                          {{ scope.row.原币金额?.toFixed(2) }} {{ scope.row.币种 }}
                        </template>
                      </el-table-column>
                      <el-table-column label="人民币金额" width="120" align="right">
                        <template #default="scope">
                          <span style="color: #52c41a; font-weight: 500;">¥{{ scope.row.人民币金额?.toFixed(2) }}</span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="备注" label="备注" min-width="100" show-overflow-tooltip />
                    </el-table>
                  </div>
                  
                  <el-empty 
                    v-if="(!agent.fee_items || agent.fee_items.length === 0) && (!agent.fee_total || agent.fee_total.length === 0)" 
                    description="暂无费用明细" 
                    :image-size="60" 
                  />
                </div>

                <!-- 汇总信息 -->
                <div v-if="agent.summary" class="detail-section">
                  <h3>费用汇总</h3>
                  <el-descriptions :column="2" border size="small">
                    <el-descriptions-item label="小计">¥{{ agent.summary.小计?.toFixed(2) }}</el-descriptions-item>
                    <el-descriptions-item label="税率">{{ (agent.summary.税率 * 100)?.toFixed(2) }}%</el-descriptions-item>
                    <el-descriptions-item label="税金">¥{{ agent.summary.税金?.toFixed(2) }}</el-descriptions-item>
                    <el-descriptions-item label="汇损率">{{ (agent.summary.汇损率 * 100)?.toFixed(4) }}%</el-descriptions-item>
                    <el-descriptions-item label="汇损">¥{{ agent.summary.汇损?.toFixed(2) }}</el-descriptions-item>
                    <el-descriptions-item label="总计" :span="2">
                      <span class="total-amount">¥{{ agent.summary.总计?.toFixed(2) }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item v-if="agent.summary.备注" label="备注" :span="2">
                      {{ agent.summary.备注 }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无代理商信息" :image-size="80" />
          </el-col>
        </el-row>
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
import { ref, reactive, onMounted, onActivated, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import { getRoutes, getRouteDetail, deleteRoute, updateRoute } from '@/api/route'
import { useUserStore } from '@/stores/user'
import RouteEditDialog from './NewRoute/components/RouteEditDialog.vue'  // ✅ 导入编辑对话框

const userStore = useUserStore()

const loading = ref(false)
const routeList = ref([])
const detailVisible = ref(false)
const currentRoute = ref(null)

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

// 获取代理商的所有费用（合并fee_items和fee_total）
const getAgentAllFees = (agent) => {
  const fees = []
  
  // 添加费用明细
  if (agent.fee_items) {
    agent.fee_items.forEach(fee => {
      fees.push({
        name: fee.费用类型,
        price: fee.单价,
        unit: fee.单位,
        currency: fee.币种,
        remark: fee.备注 || ''  // ✅ 添加备注
      })
    })
  }
  
  // 添加整单费用
  if (agent.fee_total) {
    agent.fee_total.forEach(fee => {
      fees.push({
        name: fee.费用名称,
        price: fee.原币金额,
        unit: '',
        currency: fee.币种,
        remark: fee.备注 || ''  // ✅ 添加备注
      })
    })
  }
  
  return fees
}

// 费用明细左栏
const getAgentLeftFees = (agent) => {
  const allFees = getAgentAllFees(agent)
  const mid = Math.ceil(allFees.length / 2)
  return allFees.slice(0, mid)
}

// 费用明细右栏
const getAgentRightFees = (agent) => {
  const allFees = getAgentAllFees(agent)
  const mid = Math.ceil(allFees.length / 2)
  return allFees.slice(mid)
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
const handleView = async (row) => {
  try {
    const res = await getRouteDetail(row.路线ID)
    // ✅ 修复：正确解析返回数据
    if (res.success && res.data) {
      currentRoute.value = res.data
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
}

.detail-section {
  margin-bottom: 20px;
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
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

/* 费用明细两栏布局 */
.fee-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  background: #ffffff;
}

.fee-column {
  padding: 0;
}

.fee-column:first-child {
  border-right: 1px solid #e5e7eb;
}

.fee-item {
  padding: 12px 16px;
}

.fee-item-border {
  border-bottom: 1px solid #e5e7eb;
}

.fee-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.fee-label {
  font-size: 14px;
  color: #262626;
}

.fee-value {
  font-size: 14px;
  color: #595959;
  font-weight: 500;
}

/* 总计样式 */
.total-amount {
  color: #f5222d;
  font-size: 18px;
  font-weight: 600;
}
</style>