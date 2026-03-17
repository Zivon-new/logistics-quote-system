<template>
  <div class="step3-container">
    <h3 class="step-title">代理商及费用信息</h3>

    <!-- 代理商列表 -->
    <div 
      v-for="(agent, agentIndex) in modelValue" 
      :key="agentIndex"
      class="agent-card-wrapper"
    >
      <el-card class="agent-card" shadow="hover">
        <!-- 卡片头部 -->
        <template #header>
          <div class="card-header">
            <span class="card-title">
              代理商 {{ agentIndex + 1 }}
              <el-tag v-if="modelValue.length > 1" size="small" type="info">
                共{{ modelValue.length }}个
              </el-tag>
            </span>
            <el-button 
              v-if="modelValue.length > 1"
              type="danger" 
              size="small"
              :icon="Delete"
              @click="removeAgent(agentIndex)"
            >
              删除此代理商
            </el-button>
          </div>
        </template>

        <!-- 代理商基本信息 -->
        <div class="section">
          <h4 class="section-title">基本信息</h4>
          <el-form :model="agent" label-width="110px">
            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="代理商名称" required>
                  <el-input 
                    v-model="agent.代理商"
                    placeholder="如：融迅"
                  />
                </el-form-item>
              </el-col>

              <el-col :span="8">
                <el-form-item label="运输方式" required>
                  <el-select v-model="agent.运输方式" placeholder="请选择">
                    <el-option label="空运" value="空运" />
                    <el-option label="海运" value="海运" />
                    <el-option label="陆运" value="陆运" />
                    <el-option label="快递" value="快递" />
                    <el-option label="专线" value="专线" />
                  </el-select>
                </el-form-item>
              </el-col>

              <el-col :span="8">
                <el-form-item label="贸易类型">
                  <el-select v-model="agent.贸易类型" placeholder="请选择" clearable>
                    <el-option label="一般贸易" value="一般贸易" />
                    <el-option label="专线" value="专线" />
                    <el-option label="正清 " value="正清" />
                    <el-option label="双清 " value="双清" />
                    <el-option label="贸易代理" value="贸易代理" />
                    <el-option label="跨境电商" value="跨境电商" />
                    <el-option label="保税仓" value="保税仓" />
                    <el-option label="转口贸易" value="转口贸易" />
                    <el-option label="样品/展品" value="样品/展品" />
                    <el-option label="其他" value="其他" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="时效">
                  <el-input 
                    v-model="agent.时效"
                    placeholder="如：5-7天"
                  />
                </el-form-item>
              </el-col>

              <el-col :span="16">
                <el-form-item label="时效备注">
                  <el-input 
                    v-model="agent.时效备注"
                    placeholder="时效相关说明"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row>
              <el-col :span="24">
                <el-form-item label="不含">
                  <el-input 
                    type="textarea"
                    v-model="agent.不含"
                    :rows="2"
                    placeholder="如：国内提货费，保险费，二次包装费等"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="是否赔付">
                  <el-radio-group v-model="agent.是否赔付">
                    <el-radio label="1">是</el-radio>
                    <el-radio label="0">否</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>

              <el-col :span="16">
                <el-form-item 
                  v-if="agent.是否赔付 === '1'" 
                  label="赔付内容"
                >
                  <el-input 
                    v-model="agent.赔付内容"
                    placeholder="赔付标准和内容"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row>
              <el-col :span="24">
                <el-form-item label="代理备注">
                  <el-input 
                    type="textarea"
                    v-model="agent.代理备注"
                    :rows="2"
                    placeholder="其他备注信息"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>

        <el-divider />

        <!-- 费用明细 -->
        <div class="section">
          <div class="section-header">
            <h4 class="section-title">费用明细</h4>
            <el-button 
              type="primary" 
              size="small"
              :icon="Plus"
              @click="addFeeItem(agentIndex)"
            >
              添加费用
            </el-button>
          </div>

          <el-table 
            v-if="agent.fee_items && agent.fee_items.length > 0"
            :data="agent.fee_items"
            border
            size="small"
            class="fee-table"
          >
            <el-table-column label="费用类型" min-width="140">
              <template #default="scope">
                <el-input 
                  v-model="scope.row.费用类型"
                  placeholder="如：空运费"
                  size="small"
                />
              </template>
            </el-table-column>

            <el-table-column label="单价" width="110">
              <template #default="scope">
                <el-input-number :controls="false" 
                  v-model="scope.row.单价"
                  :precision="2"
                  :min="0"
                  size="small"
                  controls-position="right"
                  @change="updateFeeAmount(scope.row)"
                />
              </template>
            </el-table-column>

            <el-table-column label="单位" width="100">
              <template #default="scope">
                <el-select 
                  v-model="scope.row.单位"
                  size="small"
                  @change="handleUnitChange(scope.row)"
                >
                  <el-option label="/kg" value="/kg" />
                  <el-option label="/cbm" value="/cbm" />
                  <el-option label="/个" value="/个" />
                  <el-option label="/票" value="/票" />
                </el-select>
              </template>
            </el-table-column>

            <el-table-column label="数量" width="100">
              <template #default="scope">
                <el-tooltip
                  v-if="isAutoQuantity(scope.row.单位)"
                  content="已按计费重量/体积自动填入，可手动修改"
                  placement="top"
                >
                  <el-input-number :controls="false"
                    v-model="scope.row.数量"
                    :precision="2"
                    :min="0"
                    size="small"
                    controls-position="right"
                    @change="updateFeeAmount(scope.row)"
                  />
                </el-tooltip>
                <el-input-number :controls="false"
                  v-else
                  v-model="scope.row.数量"
                  :precision="2"
                  :min="0"
                  size="small"
                  controls-position="right"
                  @change="updateFeeAmount(scope.row)"
                />
              </template>
            </el-table-column>

            <el-table-column label="币种" width="90">
              <template #default="scope">
                <el-select 
                  v-model="scope.row.币种"
                  size="small"
                  @change="updateFeeRMB(scope.row)"
                >
                  <el-option label="RMB" value="RMB" />
                  <el-option label="USD" value="USD" />
                  <el-option label="SGD" value="SGD" />
                  <el-option label="EUR" value="EUR" />
                  <el-option label="JPY" value="JPY" />
                  <el-option label="MYR" value="MYR" />
                </el-select>
              </template>
            </el-table-column>

            <el-table-column label="原币金额" width="110">
              <template #default="scope">
                <span style="color: #1890ff; font-weight: 500;">
                  {{ (scope.row.单价 * scope.row.数量).toFixed(2) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column label="人民币金额" width="120">
              <template #default="scope">
                <span style="color: #52c41a; font-weight: 600;">
                  ¥{{ calculateRMB(scope.row).toFixed(2) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column label="备注" min-width="120">
              <template #default="scope">
                <el-input 
                  v-model="scope.row.备注"
                  placeholder="可选"
                  size="small"
                />
              </template>
            </el-table-column>

            <el-table-column label="操作" width="70" align="center" fixed="right">
              <template #default="scope">
                <el-button 
                  type="danger" 
                  size="small"
                  link
                  @click="removeFeeItem(agentIndex, scope.$index)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty 
            v-else
            description="暂无费用明细，点击上方按钮添加"
            :image-size="60"
          />
        </div>

        <el-divider />

        <!-- 整单费用（可选） -->
        <div class="section">
          <div class="section-header">
            <h4 class="section-title">整单费用（可选）</h4>
            <el-button 
              type="primary" 
              size="small"
              :icon="Plus"
              @click="addFeeTotal(agentIndex)"
            >
              添加整单费用
            </el-button>
          </div>

          <el-table 
            v-if="agent.fee_total && agent.fee_total.length > 0"
            :data="agent.fee_total"
            border
            size="small"
            class="fee-table"
          >
            <el-table-column label="费用名称" min-width="180">
              <template #default="scope">
                <el-input 
                  v-model="scope.row.费用名称"
                  placeholder="如：报关费"
                  size="small"
                />
              </template>
            </el-table-column>

            <el-table-column label="原币金额" width="140">
              <template #default="scope">
                <el-input-number :controls="false" 
                  v-model="scope.row.原币金额"
                  :precision="2"
                  :min="0"
                  size="small"
                  controls-position="right"
                  @change="updateFeeTotalRMB(scope.row)"
                />
              </template>
            </el-table-column>

            <el-table-column label="币种" width="100">
              <template #default="scope">
                <el-select 
                  v-model="scope.row.币种"
                  size="small"
                  @change="updateFeeTotalRMB(scope.row)"
                >
                  <el-option label="RMB" value="RMB" />
                  <el-option label="USD" value="USD" />
                  <el-option label="SGD" value="SGD" />
                  <el-option label="EUR" value="EUR" />
                </el-select>
              </template>
            </el-table-column>

            <el-table-column label="人民币金额" width="140">
              <template #default="scope">
                <span style="color: #52c41a; font-weight: 600;">
                  ¥{{ calculateRMB(scope.row).toFixed(2) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column label="备注" min-width="120">
              <template #default="scope">
                <el-input 
                  v-model="scope.row.备注"
                  placeholder="可选"
                  size="small"
                />
              </template>
            </el-table-column>

            <el-table-column label="操作" width="80" align="center">
              <template #default="scope">
                <el-button 
                  type="danger" 
                  size="small"
                  link
                  @click="removeFeeTotal(agentIndex, scope.$index)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty 
            v-else
            description="暂无整单费用"
            :image-size="60"
          />
        </div>

        <el-divider />

        <!-- 费用汇总 -->
        <div class="section">
          <h4 class="section-title">费用汇总</h4>
          <el-form :model="agent.summary" label-width="120px" class="summary-form">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="小计">
                  <div class="amount-display">
                    <template v-for="(amount, currency) in calculateSubtotalByCurrency(agent)" :key="currency">
                      <span v-if="currency !== 'RMB'" class="original-amount">
                        {{ currency }} {{ amount.toFixed(2) }} →
                      </span>
                    </template>
                    <span class="rmb-amount">¥{{ calculateSubtotal(agent).toFixed(2) }}</span>
                  </div>
                </el-form-item>
              </el-col>

              <el-col :span="12">
                <el-form-item label="税率">
                  <el-input-number :controls="false" 
                    v-model="agent.summary.税率"
                    :precision="2"
                    :min="0"
                    :max="1"
                    controls-position="right"
                    style="width: 100%;"
                    @change="updateSummary(agent)"
                  />
                  <span class="unit-label">（如0.09表示9%）</span>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="税金">
                  <div class="amount-display">
                    <span v-if="routeValueCurrency !== 'RMB'" class="original-amount">
                      {{ routeValueCurrency }} {{ calculateTaxOriginal(agent).toFixed(2) }} →
                    </span>
                    <span class="rmb-amount">¥{{ calculateTax(agent).toFixed(2) }}</span>
                  </div>
                </el-form-item>
              </el-col>

              <el-col :span="12">
                <el-form-item label="汇损率">
                  <el-input-number :controls="false" 
                    v-model="agent.summary.汇损率"
                    :precision="4"
                    :min="0"
                    :max="1"
                    controls-position="right"
                    style="width: 100%;"
                    @change="updateSummary(agent)"
                  />
                  <span class="unit-label">（如0.04表示4%）</span>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="汇损">
                  <div class="amount-display">
                    <span v-if="routeValueCurrency !== 'RMB'" class="original-amount">
                      {{ routeValueCurrency }} {{ calculateLossOriginal(agent).toFixed(2) }} →
                    </span>
                    <span class="rmb-amount">¥{{ calculateLoss(agent).toFixed(2) }}</span>
                  </div>
                </el-form-item>
              </el-col>

              <el-col :span="12">
                <el-form-item label="总计">
                  <div class="amount-display">
                    <span class="total-amount">¥{{ calculateTotal(agent).toFixed(2) }}</span>
                  </div>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row>
              <el-col :span="24">
                <el-form-item label="备注">
                  <el-input 
                    type="textarea"
                    v-model="agent.summary.备注"
                    :rows="2"
                    placeholder="费用汇总相关备注"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </el-card>
    </div>

    <!-- 添加代理商按钮 -->
    <div class="add-agent-section">
      <el-button 
        type="success" 
        :icon="Plus"
        size="large"
        @click="addAgent"
      >
        添加另一个代理商
      </el-button>
      <span class="tip-text">（一条路线可以有多个代理商报价）</span>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Array,
    required: true
  },
  routeWeight: {
    type: Number,
    default: 0
  },
  routeVolume: {
    type: Number,
    default: 0
  },
  routeValue: {
    type: Number,
    default: 0
  },
  routeValueCurrency: {
    type: String,
    default: 'RMB'
  }
})

const emit = defineEmits(['update:modelValue'])

// 汇率表（从后端获取，带默认兜底值）
const exchangeRates = reactive({
  'RMB': 1.0,
  'USD': 7.2,
  'SGD': 5.3,
  'EUR': 7.8,
  'JPY': 0.05,
  'MYR': 1.6
})

// 页面加载时从后端获取最新汇率
import { getExchangeRates } from '@/api/route'
const loadExchangeRates = async () => {
  try {
    const res = await getExchangeRates()
    if (res.success && res.data) {
      Object.assign(exchangeRates, res.data)
      console.log('✅ 汇率已从后端加载:', exchangeRates)
    }
  } catch (e) {
    console.warn('⚠️ 获取汇率失败，使用默认值')
  }
}
loadExchangeRates()

// 添加代理商
const addAgent = () => {
  props.modelValue.push({
    代理商: '',
    运输方式: '',
    贸易类型: '',
    时效: '',
    时效备注: '',
    不含: '',
    是否赔付: '0',
    赔付内容: '',
    代理备注: '',
    fee_items: [],
    fee_total: [],
    summary: {
      税率: 0,
      汇损率: 0,
      备注: ''
    }
  })
}

// 删除代理商
const removeAgent = (index) => {
  if (props.modelValue.length === 1) {
    ElMessage.warning('至少需要保留一个代理商')
    return
  }
  props.modelValue.splice(index, 1)
}

// 添加费用明细
const addFeeItem = (agentIndex) => {
  if (!props.modelValue[agentIndex].fee_items) {
    props.modelValue[agentIndex].fee_items = []
  }
  
  props.modelValue[agentIndex].fee_items.push({
    费用类型: '',
    单价: 0,
    单位: '/kg',
    数量: props.routeWeight || 0,
    币种: 'RMB',
    原币金额: 0,
    人民币金额: 0,
    备注: ''
  })
}

// 删除费用明细
const removeFeeItem = (agentIndex, feeIndex) => {
  props.modelValue[agentIndex].fee_items.splice(feeIndex, 1)
}

// 添加整单费用
const addFeeTotal = (agentIndex) => {
  if (!props.modelValue[agentIndex].fee_total) {
    props.modelValue[agentIndex].fee_total = []
  }
  
  props.modelValue[agentIndex].fee_total.push({
    费用名称: '',
    原币金额: 0,
    币种: 'RMB',
    人民币金额: 0,
    备注: ''
  })
}

// 删除整单费用
const removeFeeTotal = (agentIndex, feeIndex) => {
  props.modelValue[agentIndex].fee_total.splice(feeIndex, 1)
}

// 判断是否自动计算数量
const isAutoQuantity = (unit) => {
  return unit === '/kg' || unit === '/cbm'
}

// 处理单位变化
const handleUnitChange = (feeItem) => {
  if (feeItem.单位 === '/kg') {
    feeItem.数量 = props.routeWeight || 0
  } else if (feeItem.单位 === '/cbm') {
    feeItem.数量 = props.routeVolume || 0
  } else {
    feeItem.数量 = 1
  }
  updateFeeAmount(feeItem)
}

// 更新费用原币金额
const updateFeeAmount = (feeItem) => {
  feeItem.原币金额 = feeItem.单价 * feeItem.数量
  updateFeeRMB(feeItem)
}

// 更新费用人民币金额
const updateFeeRMB = (feeItem) => {
  const rate = exchangeRates[feeItem.币种] || 1
  feeItem.人民币金额 = feeItem.原币金额 * rate
}

// 更新整单费用人民币金额
const updateFeeTotalRMB = (feeItem) => {
  const rate = exchangeRates[feeItem.币种] || 1
  feeItem.人民币金额 = feeItem.原币金额 * rate
}

// 计算人民币金额
const calculateRMB = (feeItem) => {
  const rate = exchangeRates[feeItem.币种] || 1
  const originalAmount = feeItem.原币金额 || (feeItem.单价 * feeItem.数量) || 0
  return originalAmount * rate
}

// 按币种统计原币小计（用于展示）
const calculateSubtotalByCurrency = (agent) => {
  const byCurrency = {}
  const add = (currency, amount) => {
    currency = currency || 'RMB'
    byCurrency[currency] = (byCurrency[currency] || 0) + amount
  }
  if (agent.fee_items) {
    agent.fee_items.forEach(item => add(item.币种, (item.单价 || 0) * (item.数量 || 0)))
  }
  if (agent.fee_total) {
    agent.fee_total.forEach(item => add(item.币种, item.原币金额 || 0))
  }
  return byCurrency
}

// 计算小计（人民币合计）
const calculateSubtotal = (agent) => {
  let total = 0
  if (agent.fee_items) {
    total += agent.fee_items.reduce((sum, item) => sum + calculateRMB(item), 0)
  }
  if (agent.fee_total) {
    total += agent.fee_total.reduce((sum, item) => sum + calculateRMB(item), 0)
  }
  return total
}

// 货值换算为人民币
const routeValueRMB = () => {
  const value = parseFloat(props.routeValue) || 0
  const rate = exchangeRates[props.routeValueCurrency] || 1
  return value * rate
}

// 税金/汇损原币金额（换汇前，用于展示原币部分）
const calculateTaxOriginal = (agent) => {
  return (parseFloat(props.routeValue) || 0) * (parseFloat(agent.summary.税率) || 0)
}
const calculateLossOriginal = (agent) => {
  // 汇损 = 税金原币 × 汇损率
  return calculateTaxOriginal(agent) * (parseFloat(agent.summary.汇损率) || 0)
}

// 计算税金（人民币）
const calculateTax = (agent) => {
  return routeValueRMB() * (parseFloat(agent.summary.税率) || 0)
}

// 计算汇损（人民币）= 税金 × 汇损率
const calculateLoss = (agent) => {
  return calculateTax(agent) * (parseFloat(agent.summary.汇损率) || 0)
}

// 计算总计
const calculateTotal = (agent) => {
  return calculateSubtotal(agent) + calculateTax(agent) + calculateLoss(agent)
}

// ✅ 更新税金、汇损和总计
const updateSummary = (agent) => {
  if (!agent.summary) {
    agent.summary = {
      税率: 0,
      税金: 0,
      汇损率: 0,
      汇损: 0,
      备注: ''
    }
  }
  
  const taxRate = parseFloat(agent.summary.税率) || 0
  const lossRate = parseFloat(agent.summary.汇损率) || 0

  // 更新税金（人民币）；汇损 = 税金 × 汇损率
  agent.summary.税金 = routeValueRMB() * taxRate
  agent.summary.汇损 = agent.summary.税金 * lossRate
  
  // 更新小计和总计
  agent.summary.小计 = calculateSubtotal(agent)
  agent.summary.总计 = calculateTotal(agent)
  
  console.log('✅ 更新summary:', {
    税率: taxRate,
    税金: agent.summary.税金,
    汇损率: lossRate,
    汇损: agent.summary.汇损,
    总计: agent.summary.总计
  })
}

// 验证
const validate = () => {
  // 检查每个代理商是否有代理商名称和运输方式
  for (const agent of props.modelValue) {
    if (!agent.代理商) {
      ElMessage.error('请填写代理商名称')
      return Promise.resolve(false)
    }
    if (!agent.运输方式) {
      ElMessage.error('请选择运输方式')
      return Promise.resolve(false)
    }
  }
  return Promise.resolve(true)
}

defineExpose({
  validate
})
</script>

<style scoped>
.step3-container {
  max-width: 1400px;
  margin: 0 auto;
}

.step-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 2px solid #1890ff;
}

.agent-card-wrapper {
  margin-bottom: 24px;
}

.agent-card {
  border: 2px solid #e5e7eb;
}

.agent-card:hover {
  border-color: #1890ff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}

.section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #262626;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.fee-table {
  margin-top: 12px;
}

.summary-form {
  background: #fafafa;
  padding: 20px;
  border-radius: 4px;
}

.unit-label {
  margin-left: 8px;
  color: #8c8c8c;
  font-size: 13px;
}

.total-label {
  color: #f5222d;
  font-weight: 600;
}

:deep(.total-input .el-input-number__decrease),
:deep(.total-input .el-input-number__increase) {
  display: none;
}

:deep(.total-input input) {
  color: #f5222d;
  font-weight: 600;
  font-size: 16px;
}

.add-agent-section {
  text-align: center;
  padding: 40px 0;
}

.tip-text {
  margin-left: 12px;
  color: #8c8c8c;
  font-size: 14px;
}

.amount-display {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 0;
  font-size: 14px;
}

.original-amount {
  color: #1890ff;
  font-size: 12px;
}

.rmb-amount {
  color: #52c41a;
  font-weight: 600;
  font-size: 14px;
}

.total-amount {
  color: #f5222d;
  font-weight: 700;
  font-size: 16px;
}
</style>