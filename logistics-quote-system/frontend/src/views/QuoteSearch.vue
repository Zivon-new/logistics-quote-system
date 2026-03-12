<template>
  <div class="page-container">
    <h2 class="page-title">报价查询</h2>

    <!-- 搜索表单 -->
    <el-card class="search-form">
      <el-form :model="searchForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="起始地" required>
              <el-input v-model="searchForm.起始地" placeholder="支持模糊搜索，如：深圳" clearable />
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="目的地" required>
              <el-input v-model="searchForm.目的地" placeholder="支持模糊搜索，如：西班牙" clearable />
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="货物名称">
              <el-input v-model="searchForm.货物名称" placeholder="关键词搜索，如：服务器" clearable />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="代理商">
              <el-input v-model="searchForm.代理商" placeholder="支持模糊搜索" clearable />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="日期范围">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="-"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>

          <el-col :span="4" style="text-align: right;">
            <el-button type="primary" :icon="Search" :loading="loading" @click="handleSearch">
              查询报价
            </el-button>
            <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 查询结果 -->
    <el-card v-if="quoteResults.length > 0" class="result-container">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>查询结果（共 {{ total }} 条）</span>
          <el-button type="success" :icon="Download" size="small">导出Excel</el-button>
        </div>
      </template>

      <!-- 路线列表 -->
      <div v-for="route in quoteResults" :key="route.路线ID" class="route-item">
        <div class="route-header">
          <h3>{{ route.起始地 }} → {{ route.目的地 }}</h3>
          <el-tag v-if="route.途径地" type="info" size="small">途径: {{ route.途径地 }}</el-tag>
          <span class="route-date">
            {{ route.交易开始日期 }} 至 {{ route.交易结束日期 }}
          </span>
        </div>

        <div class="route-info">
          <el-descriptions :column="3" size="small" border>
            <el-descriptions-item label="实际重量">{{ route.实际重量 }} kg</el-descriptions-item>
            <el-descriptions-item label="总体积">{{ route.总体积 || '-' }} cbm</el-descriptions-item>
            <el-descriptions-item label="货值">¥{{ route.货值 }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 货物信息 -->
        <div v-if="route.goods_details && route.goods_details.length > 0" class="goods-info">
          <h4>货物信息</h4>
          <el-tag v-for="goods in route.goods_details" :key="goods.货物ID" type="success" style="margin-right: 8px;">
            {{ goods.货物名称 }}
          </el-tag>
        </div>

        <!-- 代理商列表 -->
        <div class="agents-container">
          <el-table :data="route.agents" border stripe>
            <el-table-column prop="代理商" label="代理商" width="150" />
            <el-table-column prop="运输方式" label="运输方式" width="100" />
            <el-table-column prop="时效" label="时效" width="120" />
            <el-table-column prop="总费用" label="总费用(CNY)" width="120" align="right">
              <template #default="scope">
                <span style="color: #f5222d; font-weight: 600;">
                  ¥{{ scope.row.总费用?.toFixed(2) || '0.00' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" align="center">
              <template #default="scope">
                <el-button type="primary" link size="small" @click="viewDetail(scope.row, route)">
                  查看详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="searchForm.page"
          v-model:page-size="searchForm.page_size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </el-card>

    <!-- 空状态 -->
    <el-empty v-else-if="!loading" description="请输入查询条件进行搜索" />

    <!-- 全屏详情弹窗 -->
    <el-dialog 
      v-model="detailVisible" 
      title="报价详情" 
      fullscreen
      :close-on-click-modal="false"
      class="detail-dialog"
    >
      <div v-if="currentAgent && currentRoute" class="detail-container">
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
                <el-descriptions-item label="实际重量">{{ currentRoute.实际重量 }} kg</el-descriptions-item>
                <el-descriptions-item label="计费重量">{{ currentRoute.计费重量 || '-' }} kg</el-descriptions-item>
                <el-descriptions-item label="总体积">{{ currentRoute.总体积 || '-' }} cbm</el-descriptions-item>
                <el-descriptions-item label="货值">¥{{ currentRoute.货值 }}</el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- 货物信息 -->
            <div class="detail-section">
              <h3>货物信息</h3>
              
              <!-- 货物明细表格 -->
              <div v-if="currentRoute.goods_details?.length > 0" style="margin-bottom: 16px;">
                <p style="font-size: 14px; font-weight: 600; color: #595959; margin-bottom: 8px;">货物明细</p>
                <el-table :data="currentRoute.goods_details" border stripe max-height="300" size="small">
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

              <!-- 整单货物汇总 -->
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
            <!-- 代理商信息 -->
            <div class="detail-section">
              <h3>代理商信息</h3>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="代理商">{{ currentAgent.代理商 }}</el-descriptions-item>
                <el-descriptions-item label="运输方式">{{ currentAgent.运输方式 }}</el-descriptions-item>
                <el-descriptions-item label="贸易类型">{{ currentAgent.贸易类型 }}</el-descriptions-item>
                <el-descriptions-item label="时效">{{ currentAgent.时效 }}</el-descriptions-item>
                <el-descriptions-item label="时效备注" :span="2">{{ currentAgent.时效备注 || '-' }}</el-descriptions-item>
                <el-descriptions-item label="不含" :span="2">{{ currentAgent.不含 || '-' }}</el-descriptions-item>
                <el-descriptions-item label="是否赔付">
                  <el-tag :type="isCompensation(currentAgent.是否赔付) ? 'success' : 'info'" size="small">
                    {{ isCompensation(currentAgent.是否赔付) ? '是' : '否' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="赔付内容">{{ currentAgent.赔付内容 || '-' }}</el-descriptions-item>
                <el-descriptions-item v-if="currentAgent.代理备注" label="代理备注" :span="2">
                  {{ currentAgent.代理备注 }}
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- 费用明细（表格展示全部字段） -->
            <div class="detail-section">
              <h3>费用明细</h3>
              
              <!-- 费用明细表 -->
              <div v-if="currentAgent.fee_items?.length > 0" style="margin-bottom: 16px;">
                <p style="font-size: 13px; font-weight: 600; color: #595959; margin-bottom: 8px;">费用明细（{{ currentAgent.fee_items.length }}条）</p>
                <el-table :data="currentAgent.fee_items" border stripe size="small">
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
              
              <!-- 整单费用表 -->
              <div v-if="currentAgent.fee_total?.length > 0" style="margin-bottom: 16px;">
                <p style="font-size: 13px; font-weight: 600; color: #595959; margin-bottom: 8px;">整单费用（{{ currentAgent.fee_total.length }}条）</p>
                <el-table :data="currentAgent.fee_total" border stripe size="small">
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
                v-if="(!currentAgent.fee_items || currentAgent.fee_items.length === 0) && (!currentAgent.fee_total || currentAgent.fee_total.length === 0)" 
                description="暂无费用明细" 
                :image-size="60" 
              />
            </div>

            <!-- 费用汇总 -->
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
                <el-descriptions-item v-if="currentAgent.summary.备注" label="备注" :span="2">
                  {{ currentAgent.summary.备注 }}
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
const detailVisible = ref(false)
const currentAgent = ref(null)
const currentRoute = ref(null)

const searchForm = reactive({
  起始地: '',
  目的地: '',
  货物名称: '',
  代理商: '',
  page: 1,
  page_size: 10
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

// 合并费用明细和整单费用
const allFees = computed(() => {
  if (!currentAgent.value) return []
  
  const fees = []
  
  // 添加费用明细
  if (currentAgent.value.fee_items) {
    currentAgent.value.fee_items.forEach(fee => {
      fees.push({
        name: fee.费用类型,
        price: fee.单价,
        unit: fee.单位,
        currency: fee.币种,
        remark: fee.备注 || ''  // ✅ 新增：备注
      })
    })
  }
  
  // 添加整单费用
  if (currentAgent.value.fee_total) {
    currentAgent.value.fee_total.forEach(fee => {
      fees.push({
        name: fee.费用名称,
        price: fee.原币金额,
        unit: '',
        currency: fee.币种,
        remark: fee.备注 || ''  // ✅ 新增：备注
      })
    })
  }
  
  return fees
})

// 费用明细左栏
const leftColumnFees = computed(() => {
  const mid = Math.ceil(allFees.value.length / 2)
  return allFees.value.slice(0, mid)
})

// 费用明细右栏
const rightColumnFees = computed(() => {
  const mid = Math.ceil(allFees.value.length / 2)
  return allFees.value.slice(mid)
})

// 查询报价
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
      page_size: searchForm.page_size
    }

    // 可选参数
    if (searchForm.货物名称) params.货物名称 = searchForm.货物名称
    if (searchForm.代理商) params.代理商 = searchForm.代理商
    if (dateRange.value?.length === 2) {
      params.交易开始日期 = dateRange.value[0]
      params.交易结束日期 = dateRange.value[1]
    }

    const res = await searchQuotes(params)
    quoteResults.value = res.results
    total.value = res.total

    ElMessage.success(`查询成功，找到 ${res.total} 条结果`)
  } catch (error) {
    console.error('查询失败:', error)
  } finally {
    loading.value = false
  }
}

// 重置表单
const handleReset = () => {
  searchForm.起始地 = ''
  searchForm.目的地 = ''
  searchForm.货物名称 = ''
  searchForm.代理商 = ''
  searchForm.page = 1
  dateRange.value = []
  quoteResults.value = []
  total.value = 0
}

// 查看详情
const viewDetail = (agent, route) => {
  currentAgent.value = agent
  currentRoute.value = route
  detailVisible.value = true
}
</script>

<style scoped>
.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 20px;
}

.route-item {
  margin-bottom: 30px;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
}

.route-item:last-child {
  margin-bottom: 0;
}

.route-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.route-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #262626;
  margin: 0;
}

.route-date {
  font-size: 14px;
  color: #8c8c8c;
  margin-left: auto;
}

.route-info {
  margin-bottom: 15px;
}

.goods-info {
  margin-bottom: 15px;
  padding: 10px;
  background: #f0f9ff;
  border-radius: 4px;
}

.goods-info h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #595959;
}

.agents-container {
  background: #ffffff;
  padding: 15px;
  border-radius: 4px;
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

.detail-section {
  margin-bottom: 24px;
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
.total-summary {
  padding: 16px;
  background: #ffffff;
  border-radius: 4px;
  text-align: right;
  font-size: 18px;
  font-weight: 600;
}

.total-amount {
  color: #f5222d;
  font-size: 20px;
  margin-left: 8px;
}
</style>