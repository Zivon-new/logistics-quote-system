<template>
  <div class="step4-container">
    <h3 class="step-title">预览确认</h3>
    
    <el-alert 
      title="请仔细核对以下信息，确认无误后提交" 
      type="warning"
      :closable="false"
      show-icon
      class="alert-tip"
    />

    <!-- 路线信息 -->
    <el-card class="preview-section">
      <template #header>
        <div class="section-header">
          <span class="section-title">路线信息</span>
        </div>
      </template>
      
      <el-descriptions :column="3" border>
        <el-descriptions-item label="起始地">
          {{ formData.route.起始地 }}
        </el-descriptions-item>
        <el-descriptions-item label="途径地">
          {{ formData.route.途径地 || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="目的地">
          {{ formData.route.目的地 }}
        </el-descriptions-item>
        <el-descriptions-item label="交易日期" :span="3">
          {{ formData.route.交易开始日期 }} 至 {{ formData.route.交易结束日期 }}
        </el-descriptions-item>
        <el-descriptions-item label="实际重量">
          {{ formData.route.实际重量 }} kg
        </el-descriptions-item>
        <el-descriptions-item label="计费重量">
          {{ formData.route.计费重量 }} kg
        </el-descriptions-item>
        <el-descriptions-item label="总体积">
          {{ formData.route.总体积 }} cbm
        </el-descriptions-item>
        <el-descriptions-item label="货值" :span="2">
          {{ formData.route.货值币种 || 'RMB' }} {{ formData.route.货值?.toFixed(2) }}
          <span v-if="formData.route.货值币种 && formData.route.货值币种 !== 'RMB'" style="color:#999; font-size:12px; margin-left:8px;">
            ≈ ¥{{ routeValueRMB().toFixed(2) }}
          </span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 货物信息 -->
    <el-card class="preview-section">
      <template #header>
        <div class="section-header">
          <span class="section-title">货物信息</span>
        </div>
      </template>
      
      <!-- 货物明细 -->
      <div v-if="formData.goodsDetails && formData.goodsDetails.length > 0">
        <h4>货物明细（{{ formData.goodsDetails.length }}条）</h4>
        <el-table :data="formData.goodsDetails" border size="small">
          <el-table-column prop="货物名称" label="货物名称" min-width="130" />
          <el-table-column prop="货物种类" label="货物种类" width="90" />
          <el-table-column label="是否新品" width="70" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.是否新品 === 1 ? 'success' : 'info'" size="small">
                {{ scope.row.是否新品 === 1 ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="数量" label="数量" width="60" align="right" />
          <el-table-column label="单价" width="80" align="right">
            <template #default="scope">
              {{ scope.row.单价 || 0 }} {{ scope.row.币种 || '' }}
            </template>
          </el-table-column>
          <el-table-column label="重量" width="80" align="right">
            <template #default="scope">
              {{ scope.row.重量 || 0 }} kg
            </template>
          </el-table-column>
          <el-table-column label="总重量" width="80" align="right">
            <template #default="scope">
              {{ scope.row.总重量 || 0 }} kg
            </template>
          </el-table-column>
          <el-table-column label="总价" width="90" align="right">
            <template #default="scope">
              ¥{{ (scope.row.总价 || 0)?.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="备注" label="备注" min-width="80" show-overflow-tooltip />
        </el-table>
      </div>
      
      <!-- 整单货物（支持多条） -->
      <div v-if="formData.goodsTotal && formData.goodsTotal.length > 0">
        <h4>整单货物（{{ formData.goodsTotal.length }}条）</h4>
        <el-table :data="formData.goodsTotal" border size="small">
          <el-table-column prop="货物名称" label="货物名称" min-width="140" />
          <el-table-column label="实际重量" width="110" align="right">
            <template #default="scope">
              {{ scope.row.实际重量 || 0 }} kg
            </template>
          </el-table-column>
          <el-table-column label="货值" width="110" align="right">
            <template #default="scope">
              ¥{{ (scope.row.货值 || 0)?.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="总体积" width="110" align="right">
            <template #default="scope">
              {{ scope.row.总体积 || 0 }} cbm
            </template>
          </el-table-column>
          <el-table-column prop="备注" label="备注" min-width="100" show-overflow-tooltip />
        </el-table>
      </div>
      
      <el-empty 
        v-if="(!formData.goodsDetails || formData.goodsDetails.length === 0) && 
              (!formData.goodsTotal || formData.goodsTotal.length === 0)"
        description="暂无货物信息"
        :image-size="60"
      />
    </el-card>

    <!-- 代理商信息 -->
    <el-card 
      v-for="(agent, index) in formData.agents" 
      :key="index"
      class="preview-section agent-section"
    >
      <template #header>
        <div class="section-header">
          <span class="section-title">
            代理商 {{ index + 1 }}: {{ agent.代理商 }}
          </span>
          <el-tag :type="getTransportTypeColor(agent.运输方式)" size="small">
            {{ agent.运输方式 }}
          </el-tag>
        </div>
      </template>
      
      <!-- 代理商基本信息 -->
      <el-descriptions :column="3" border size="small" class="agent-info">
        <el-descriptions-item label="代理商">{{ agent.代理商 }}</el-descriptions-item>
        <el-descriptions-item label="运输方式">{{ agent.运输方式 }}</el-descriptions-item>
        <el-descriptions-item label="贸易类型">{{ agent.贸易类型 || '-' }}</el-descriptions-item>
        <el-descriptions-item label="时效">{{ agent.时效 || '-' }}</el-descriptions-item>
        <el-descriptions-item label="时效备注" :span="2">{{ agent.时效备注 || '-' }}</el-descriptions-item>
        <el-descriptions-item label="不含" :span="3">{{ agent.不含 || '-' }}</el-descriptions-item>
        <el-descriptions-item label="是否赔付">
          <el-tag :type="agent.是否赔付 === '1' ? 'success' : 'info'" size="small">
            {{ agent.是否赔付 === '1' ? '是' : '否' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="赔付内容" :span="2">
          {{ agent.赔付内容 || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 费用明细 -->
      <div v-if="agent.fee_items && agent.fee_items.length > 0" class="fee-section">
        <h4>费用明细（{{ agent.fee_items.length }}条）</h4>
        <el-table :data="agent.fee_items" border size="small">
          <el-table-column prop="费用类型" label="费用类型" min-width="140" />
          <el-table-column label="单价" width="100" align="right">
            <template #default="scope">
              {{ scope.row.单价?.toFixed(2) }}{{ scope.row.币种 }}{{ scope.row.单位 }}
            </template>
          </el-table-column>
          <el-table-column prop="数量" label="数量" width="100" align="right">
            <template #default="scope">
              {{ scope.row.数量?.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="原币金额" width="120" align="right">
            <template #default="scope">
              {{ (scope.row.单价 * scope.row.数量)?.toFixed(2) }} {{ scope.row.币种 }}
            </template>
          </el-table-column>
          <el-table-column label="人民币金额" width="120" align="right">
            <template #default="scope">
              <span style="color: #52c41a; font-weight: 600;">
                ¥{{ calculateRMB(scope.row)?.toFixed(2) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 整单费用 -->
      <div v-if="agent.fee_total && agent.fee_total.length > 0" class="fee-section">
        <h4>整单费用（{{ agent.fee_total.length }}条）</h4>
        <el-table :data="agent.fee_total" border size="small">
          <el-table-column prop="费用名称" label="费用名称" min-width="180" />
          <el-table-column label="原币金额" width="150" align="right">
            <template #default="scope">
              {{ scope.row.原币金额?.toFixed(2) }} {{ scope.row.币种 }}
            </template>
          </el-table-column>
          <el-table-column label="人民币金额" width="150" align="right">
            <template #default="scope">
              <span style="color: #52c41a; font-weight: 600;">
                ¥{{ calculateRMB(scope.row)?.toFixed(2) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 汇总信息 -->
      <div class="summary-section">
        <h4>费用汇总</h4>
        <el-descriptions :column="2" border size="small" class="summary-info">
          <el-descriptions-item label="小计">
            <template v-for="(amount, currency) in calculateSubtotalByCurrency(agent)" :key="currency">
              <span v-if="currency !== 'RMB'" style="color:#1890ff; font-size:12px; margin-right:6px;">
                {{ currency }} {{ amount.toFixed(2) }} →
              </span>
            </template>
            <span class="amount-value">¥{{ calculateSubtotal(agent)?.toFixed(2) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="税率">
            {{ (agent.summary.税率 * 100).toFixed(2) }}%
          </el-descriptions-item>
          <el-descriptions-item label="税金">
            <span v-if="formData.route.货值币种 && formData.route.货值币种 !== 'RMB'" style="color:#1890ff; font-size:12px; margin-right:6px;">
              {{ formData.route.货值币种 }} {{ (parseFloat(formData.route.货值) * (agent.summary.税率 || 0)).toFixed(2) }} →
            </span>
            <span class="amount-value">¥{{ calculateTax(agent)?.toFixed(2) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="汇损率">
            {{ (agent.summary.汇损率 * 100).toFixed(4) }}%
          </el-descriptions-item>
          <el-descriptions-item label="汇损">
            <span v-if="formData.route.货值币种 && formData.route.货值币种 !== 'RMB'" style="color:#1890ff; font-size:12px; margin-right:6px;">
              {{ formData.route.货值币种 }} {{ (parseFloat(formData.route.货值) * (agent.summary.税率 || 0) * (agent.summary.汇损率 || 0)).toFixed(2) }} →
            </span>
            <span class="amount-value">¥{{ calculateLoss(agent)?.toFixed(2) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="总计">
            <span class="total-amount">¥{{ calculateTotal(agent)?.toFixed(2) }}</span>
          </el-descriptions-item>
          <el-descriptions-item v-if="agent.summary.备注" label="备注" :span="2">
            {{ agent.summary.备注 }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getExchangeRates } from '@/api/route'

const props = defineProps({
  formData: {
    type: Object,
    required: true
  }
})

// 汇率表（从后端获取，带默认兜底值）
const exchangeRates = reactive({
  'RMB': 1.0,
  'USD': 7.2,
  'SGD': 5.3,
  'EUR': 7.8,
  'JPY': 0.05,
  'MYR': 1.6
})

onMounted(async () => {
  try {
    const res = await getExchangeRates()
    if (res.success && res.data) {
      Object.assign(exchangeRates, res.data)
    }
  } catch (e) {
    console.warn('⚠️ 获取汇率失败，使用默认值')
  }
})

// 获取运输方式颜色
const getTransportTypeColor = (type) => {
  const colorMap = {
    '空运': 'primary',
    '海运': 'success',
    '陆运': 'warning',
    '快递': 'danger',
    '专线': 'info'
  }
  return colorMap[type] || 'info'
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

// 计算小计
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

// 货值转换为人民币（考虑货值币种的汇率）
const routeValueRMB = () => {
  const value = parseFloat(props.formData.route.货值) || 0
  const currency = props.formData.route.货值币种 || 'RMB'
  const rate = exchangeRates[currency] || 1
  return value * rate
}

// 计算税金 - 使用货值（换算为人民币后）计算
const calculateTax = (agent) => {
  return routeValueRMB() * (agent.summary.税率 || 0)
}

// 计算汇损 = 税金 × 汇损率
const calculateLoss = (agent) => {
  return calculateTax(agent) * (agent.summary.汇损率 || 0)
}

// 计算总计
const calculateTotal = (agent) => {
  return calculateSubtotal(agent) + calculateTax(agent) + calculateLoss(agent)
}
</script>

<style scoped>
.step4-container {
  max-width: 1200px;
  margin: 0 auto;
}

.step-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 2px solid #1890ff;
}

.alert-tip {
  margin-bottom: 24px;
}

.preview-section {
  margin-bottom: 24px;
}

.agent-section {
  border: 2px solid #e5e7eb;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
}

.agent-info {
  margin-bottom: 20px;
}

.fee-section {
  margin-top: 20px;
}

.fee-section h4 {
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
}

.summary-section {
  margin-top: 20px;
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
}

.summary-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
}

.summary-info {
  background: #fff;
}

.amount-value {
  color: #1890ff;
  font-weight: 500;
}

.total-amount {
  color: #f5222d;
  font-weight: 600;
  font-size: 16px;
}
</style>