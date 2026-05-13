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
            <div style="display:flex; gap:8px;">
              <el-button
                type="default"
                size="small"
                @click="addGroupHeader(agentIndex)"
              >
                + 分组标题
              </el-button>
              <el-button
                type="primary"
                size="small"
                :icon="Plus"
                @click="addFeeItem(agentIndex)"
              >
                添加费用
              </el-button>
            </div>
          </div>

          <div @keydown="handleFeeKeydown($event, agentIndex, 'fi')">
          <el-table
            v-if="agent.fee_items && agent.fee_items.length > 0"
            :ref="el => onFeeItemTableRef(el, agentIndex)"
            :data="agent.fee_items"
            :row-key="getRowKey"
            border
            size="small"
            class="fee-table"
            :span-method="feeItemSpanMethod"
            :row-class-name="({ row }) => row.备注 === '__GROUP_HEADER__' ? 'group-header-row' : ''"
          >
            <el-table-column width="32" align="center">
              <template #default>
                <span class="drag-handle">⠿</span>
              </template>
            </el-table-column>
            <el-table-column label="费用类型" min-width="140">
              <template #default="scope">
                <template v-if="scope.row.备注 === '__GROUP_HEADER__'">
                  <div class="group-header-cell">
                    <span class="group-header-icon">▶</span>
                    <el-input
                      v-model="scope.row.费用类型"
                      placeholder="分组名称，如：DFW出口"
                      size="small"
                    />
                  </div>
                </template>
                <el-input
                  v-else
                  v-model="scope.row.费用类型"
                  placeholder="如：空运费"
                  size="small"
                />
              </template>
            </el-table-column>

            <el-table-column label="单价" width="130">
              <template #default="scope">
                <div v-if="scope.row._formula_单价 !== undefined" class="formula-wrap">
                  <el-input
                    v-model="scope.row._formula_单价"
                    size="small"
                    placeholder="=货值*0.038"
                    @blur="applyFormula(scope.row, '单价')"
                    @keydown.enter.prevent="applyFormula(scope.row, '单价')"
                  >
                    <template #prefix><span class="formula-prefix">f</span></template>
                  </el-input>
                  <el-button link size="small" class="formula-clear" @click="clearFormula(scope.row, '单价')">×</el-button>
                </div>
                <div v-else class="price-wrap">
                  <el-input-number :controls="false"
                    v-model="scope.row.单价"
                    :precision="2"
                    :min="0"
                    size="small"
                    @change="updateFeeAmount(scope.row)"
                  />
                  <el-tooltip content="公式（如 =货值*0.038）" placement="top">
                    <el-button link size="small" class="formula-btn" @click="activateFormula(scope.row, '单价')">=</el-button>
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="单位" width="130">
              <template #default="scope">
                <el-autocomplete
                  v-model="scope.row.单位"
                  :fetch-suggestions="queryUnits"
                  size="small"
                  placeholder="选择或手动输入"
                  :trigger-on-focus="true"
                  style="width:100%"
                  @select="() => handleUnitChange(scope.row)"
                  @change="() => handleUnitChange(scope.row)"
                />
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

            <el-table-column label="最低收费" width="110">
              <template #default="scope">
                <el-input-number :controls="false"
                  v-if="scope.row.备注 !== '__GROUP_HEADER__'"
                  v-model="scope.row.最低收费"
                  :precision="2"
                  :min="0"
                  placeholder="选填"
                  size="small"
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
                  <el-option label="HKD" value="HKD" />
                </el-select>
              </template>
            </el-table-column>

            <el-table-column label="原币金额" width="110">
              <template #default="scope">
                <el-tooltip
                  v-if="scope.row.最低收费 > 0 && (scope.row.单价 * scope.row.数量) < scope.row.最低收费"
                  content="已应用最低收费"
                  placement="top"
                >
                  <span style="color: #fa8c16; font-weight: 600;">
                    {{ calcOriginalAmount(scope.row).toFixed(2) }}
                    <el-icon style="font-size:11px;vertical-align:-1px"><InfoFilled /></el-icon>
                  </span>
                </el-tooltip>
                <span v-else style="color: #1890ff; font-weight: 500;">
                  {{ calcOriginalAmount(scope.row).toFixed(2) }}
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

            <el-table-column label="操作" width="70" align="center">
              <template #default="scope">
                <el-button
                  type="danger"
                  size="small"
                  link
                  @click="removeFeeItem(agentIndex, scope.$index)"
                >删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty
            v-else
            description="暂无费用明细，点击上方按钮添加"
            :image-size="60"
          />
          </div><!-- /keydown wrapper fi -->
        </div>

        <el-divider />

        <!-- 整单费用（可选） -->
        <div class="section">
          <div class="section-header">
            <h4 class="section-title">整单费用（可选）</h4>
            <div style="display:flex; gap:8px;">
              <el-button
                type="default"
                size="small"
                @click="addFeeTotalGroupHeader(agentIndex)"
              >
                + 分组标题
              </el-button>
              <el-button
                type="primary"
                size="small"
                :icon="Plus"
                @click="addFeeTotal(agentIndex)"
              >
                添加整单费用
              </el-button>
            </div>
          </div>

          <div @keydown="handleFeeKeydown($event, agentIndex, 'ft')">
          <el-table
            v-if="agent.fee_total && agent.fee_total.length > 0"
            :ref="el => onFeeTotalTableRef(el, agentIndex)"
            :data="agent.fee_total"
            :row-key="getRowKey"
            border
            size="small"
            class="fee-table"
            :span-method="feeTotalSpanMethod"
            :row-class-name="({ row }) => row.备注 === '__GROUP_HEADER__' ? 'group-header-row' : ''"
          >
            <el-table-column width="32" align="center">
              <template #default>
                <span class="drag-handle">⠿</span>
              </template>
            </el-table-column>
            <el-table-column label="费用名称" min-width="180">
              <template #default="scope">
                <template v-if="scope.row.备注 === '__GROUP_HEADER__'">
                  <div class="group-header-cell">
                    <span class="group-header-icon">▶</span>
                    <el-input
                      v-model="scope.row.费用名称"
                      placeholder="分组名称，如：新加坡进口"
                      size="small"
                    />
                  </div>
                </template>
                <el-input
                  v-else
                  v-model="scope.row.费用名称"
                  placeholder="如：报关费"
                  size="small"
                />
              </template>
            </el-table-column>

            <el-table-column label="原币金额" width="160">
              <template #default="scope">
                <div v-if="scope.row._formula_原币金额 !== undefined" class="formula-wrap">
                  <el-input
                    v-model="scope.row._formula_原币金额"
                    size="small"
                    placeholder="=货值*0.038"
                    @blur="applyFormula(scope.row, '原币金额', true)"
                    @keydown.enter.prevent="applyFormula(scope.row, '原币金额', true)"
                  >
                    <template #prefix><span class="formula-prefix">f</span></template>
                  </el-input>
                  <el-button link size="small" class="formula-clear" @click="clearFormula(scope.row, '原币金额')">×</el-button>
                </div>
                <div v-else class="price-wrap">
                  <el-input-number :controls="false"
                    v-model="scope.row.原币金额"
                    :precision="2"
                    :min="0"
                    size="small"
                    @change="updateFeeTotalRMB(scope.row)"
                  />
                  <el-tooltip content="公式（如 =货值*0.038）" placement="top">
                    <el-button link size="small" class="formula-btn" @click="activateFormula(scope.row, '原币金额')">=</el-button>
                  </el-tooltip>
                </div>
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
                  <el-option label="HKD" value="HKD" />
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
          </div><!-- /keydown wrapper ft -->
        </div>

        <el-divider />

        <!-- 费用汇总 -->
        <div class="section">
          <h4 class="section-title">
            费用汇总
            <span v-if="forexReferenceDate" class="forex-date-tip">
              （汇率参考日期：{{ forexReferenceDate }}）
            </span>
            <el-button
              size="small"
              :loading="forexRefreshing"
              style="margin-left:10px;font-weight:400"
              @click="handleRefreshForex"
            >
              {{ forexRefreshing ? '同步中...' : '刷新汇率' }}
            </el-button>
          </h4>
          <el-form :model="agent.summary" label-width="120px" class="summary-form">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="小计">
                  <div class="manual-override-row">
                    <el-tooltip content="切换为手动填写小计" placement="top">
                      <el-switch
                        v-model="agent.summary.小计手动"
                        size="small"
                        style="margin-right:8px;flex-shrink:0"
                        @change="updateSummary(agent)"
                      />
                    </el-tooltip>
                    <el-input-number
                      v-if="agent.summary.小计手动"
                      :controls="false"
                      v-model="agent.summary.小计"
                      :precision="2"
                      :min="0"
                      style="width:130px"
                      @change="updateSummary(agent)"
                    />
                    <div v-else class="amount-display">
                      <span v-if="getFeesCurrency(agent)" class="original-amount">
                        {{ getFeesCurrency(agent) }} {{ calculateSubtotalByCurrency(agent)[getFeesCurrency(agent)]?.toFixed(2) }} →
                      </span>
                      <span class="rmb-amount">¥{{ calculateSubtotal(agent).toFixed(2) }}</span>
                    </div>
                  </div>
                </el-form-item>
              </el-col>

              <el-col :span="12">
                <el-form-item label="税率模式">
                  <el-radio-group
                    v-model="agent.summary.税率模式"
                    size="small"
                    @change="updateSummary(agent)"
                  >
                    <el-radio-button value="simple">单一税率</el-radio-button>
                    <el-radio-button value="multi">多货物税率</el-radio-button>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 单一税率模式 -->
            <el-row v-if="!agent.summary.税率模式 || agent.summary.税率模式 === 'simple'" :gutter="16">
              <el-col :span="12">
                <el-form-item label="税率">
                  <div style="display:flex;align-items:center;gap:4px;width:100%;">
                    <el-input-number :controls="false"
                      v-model="agent.summary.税率Display"
                      :precision="4"
                      :min="0"
                      style="flex:1;"
                      @change="v => { agent.summary.税率 = (v || 0) / 100; updateSummary(agent) }"
                    />
                    <span style="color:#606266;font-size:14px;white-space:nowrap;">%</span>
                  </div>
                  <span class="unit-label">（如 9 表示 9%，支持小数如 9.15）</span>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 多货物税率模式 -->
            <div v-else class="multi-tax-section">
              <div class="multi-tax-header">
                <span class="multi-tax-title">货物税率明细</span>
                <div style="display:flex;gap:8px">
                  <el-button size="small" @click="importTaxFromGoods(agent, agentIndex)">
                    从货物信息导入
                  </el-button>
                  <el-button size="small" type="primary" @click="addTaxDetail(agent)">
                    + 添加行
                  </el-button>
                </div>
              </div>
              <el-table
                :data="agent.summary.税率明细 || []"
                border size="small"
                class="tax-detail-table"
              >
                <el-table-column label="货物名称" min-width="120">
                  <template #default="scope">
                    <el-input v-model="scope.row.货物名称" size="small" placeholder="货物描述" />
                  </template>
                </el-table-column>
                <el-table-column label="货值" width="100">
                  <template #default="scope">
                    <el-input-number
                      :controls="false" v-model="scope.row.货值"
                      :precision="2" :min="0" size="small"
                      @change="updateSummary(agent)"
                    />
                  </template>
                </el-table-column>
                <el-table-column label="币种" width="80">
                  <template #default="scope">
                    <el-select v-model="scope.row.货值币种" size="small" @change="updateSummary(agent)">
                      <el-option label="RMB" value="RMB" />
                      <el-option label="USD" value="USD" />
                      <el-option label="EUR" value="EUR" />
                      <el-option label="SGD" value="SGD" />
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="HS编码" width="120">
                  <template #default="scope">
                    <el-input v-model="scope.row.HS编码" size="small" placeholder="如8517620090" />
                  </template>
                </el-table-column>
                <el-table-column label="原产地" width="80">
                  <template #default="scope">
                    <el-input v-model="scope.row.原产地" size="small" placeholder="如中国" />
                  </template>
                </el-table-column>
                <el-table-column label="税率说明" min-width="140">
                  <template #default="scope">
                    <el-input
                      v-model="scope.row.税率说明"
                      size="small"
                      placeholder="如 关税25%+增值税10%"
                    />
                  </template>
                </el-table-column>
                <el-table-column label="综合税率%" width="100">
                  <template #default="scope">
                    <el-input-number
                      :controls="false" v-model="scope.row.综合税率"
                      :precision="2" :min="0" :max="999" size="small"
                      @change="updateSummary(agent)"
                    />
                  </template>
                </el-table-column>
                <el-table-column label="税金CNY" width="100" align="right">
                  <template #default="scope">
                    <span class="rmb-amount">
                      ¥{{ calcTaxDetailRowCNY(scope.row).toFixed(2) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="60" align="center">
                  <template #default="scope">
                    <el-button type="danger" link size="small" @click="removeTaxDetail(agent, scope.$index)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <div class="multi-tax-total">
                汇总税金：<span class="total-amount">¥{{ calcMultiTaxTotal(agent).toFixed(2) }}</span>
                <span class="unit-label">（已自动写入税金）</span>
              </div>
            </div>

            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="税金">
                  <div class="manual-override-row">
                    <el-tooltip content="切换为手动填写" placement="top">
                      <el-switch
                        v-model="agent.summary.税金手动"
                        size="small"
                        style="margin-right:8px;flex-shrink:0"
                        @change="updateSummary(agent)"
                      />
                    </el-tooltip>
                    <el-input-number
                      v-if="agent.summary.税金手动"
                      :controls="false"
                      v-model="agent.summary.税金"
                      :precision="2"
                      :min="0"
                      style="width:120px"
                      @change="updateSummary(agent)"
                    />
                    <div v-else class="amount-display">
                      <span v-if="getCargoCurrency()" class="original-amount">
                        {{ getCargoCurrency() }} {{ calculateTaxOriginal(agent).toFixed(2) }} →
                      </span>
                      <span class="rmb-amount">¥{{ calculateTax(agent).toFixed(2) }}</span>
                    </div>
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
                  <div class="manual-override-row">
                    <el-tooltip content="切换为手动填写" placement="top">
                      <el-switch
                        v-model="agent.summary.汇损手动"
                        size="small"
                        style="margin-right:8px;flex-shrink:0"
                        @change="updateSummary(agent)"
                      />
                    </el-tooltip>
                    <el-input-number
                      v-if="agent.summary.汇损手动"
                      :controls="false"
                      v-model="agent.summary.汇损"
                      :precision="2"
                      :min="0"
                      style="width:120px"
                      @change="updateSummary(agent)"
                    />
                    <div v-else class="amount-display">
                      <span v-if="getCargoCurrency()" class="original-amount">
                        {{ getCargoCurrency() }} {{ calculateLossOriginal(agent).toFixed(2) }} →
                      </span>
                      <span class="rmb-amount">¥{{ calculateLoss(agent).toFixed(2) }}</span>
                    </div>
                  </div>
                </el-form-item>
              </el-col>

              <el-col :span="12">
                <el-form-item label="总计">
                  <div class="amount-display">
                    <span v-if="getQuoteSingleCurrency(agent)" class="original-amount">
                      {{ getQuoteSingleCurrency(agent) }}
                      {{ (
                        (calculateSubtotalByCurrency(agent)[getQuoteSingleCurrency(agent)] || 0)
                        + calculateTaxOriginal(agent)
                        + calculateLossOriginal(agent)
                      ).toFixed(2) }} →
                    </span>
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

        <!-- 代理商附件（路线保存后可上传） -->
        <template v-if="savedRouteId">
          <el-divider />
          <div class="section">
            <h4 class="section-title">附件</h4>
            <AttachmentPanel :route-id="savedRouteId" :agent-index="agentIndex" />
          </div>
        </template>
        <div v-else class="section attachment-placeholder">
          <span>提交路线后可在此上传代理商附件</span>
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
import { ref, reactive, watch, onBeforeUnmount, nextTick } from 'vue'
import { Plus, Delete, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import Sortable from 'sortablejs'
import AttachmentPanel from '@/components/AttachmentPanel.vue'

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
  },
  goodsList: {
    type: Array,
    default: () => []
  },
  savedRouteId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

// ── 行唯一 key（row-key 必须，否则 Vue 用位置 diff 会和 Sortable 的 DOM 移动冲突）
let _idCnt = 0
const _genId = () => `_r${++_idCnt}_${Date.now()}`
// 用 WeakMap 给没有 _id 的行（后端老数据）分配临时 key，不污染数据对象
const _rowKeyMap = new WeakMap()
const getRowKey = (row) => {
  if (row._id) return String(row._id)
  if (!_rowKeyMap.has(row)) _rowKeyMap.set(row, _genId())
  return _rowKeyMap.get(row)
}

// 汇率表（从后端获取，带默认兜底值）
const exchangeRates = reactive({
  'RMB': 1.0,
  'USD': 7.2,
  'SGD': 5.3,
  'EUR': 7.8,
  'JPY': 0.05,
  'MYR': 1.6,
  'HKD': 0.93
})
const forexReferenceDate = ref('')  // 汇率参考日期

// ── 拖拽排序 ──────────────────────────────────────────────
const sortableMap = new Map() // key: 'fi-{agentIndex}' | 'ft-{agentIndex}'

const createSortable = (key, tableEl, items) => {
  if (sortableMap.has(key)) {
    try { sortableMap.get(key).destroy() } catch {}
    sortableMap.delete(key)
  }
  if (!tableEl?.$el) return
  const tbody = tableEl.$el.querySelector('table.el-table__body > tbody')
    || tableEl.$el.querySelector('.el-table__body-wrapper tbody')
    || tableEl.$el.querySelector('tbody')
  if (!tbody) return

  try {
    sortableMap.set(key, Sortable.create(tbody, {
      handle: '.drag-handle',
      draggable: '.el-table__row',
      animation: 0,
      ghostClass: 'sortable-ghost',
      onEnd ({ oldDraggableIndex, newDraggableIndex }) {
        if (oldDraggableIndex == null || newDraggableIndex == null) return
        if (oldDraggableIndex === newDraggableIndex) return
        const [moved] = items.splice(oldDraggableIndex, 1)
        items.splice(newDraggableIndex, 0, moved)
        nextTick(() => createSortable(key, tableEl, items))
      }
    }))
  } catch (e) {
    console.warn('[Sortable] 初始化失败:', e)
    sortableMap.delete(key)
  }
}

const onFeeItemTableRef = (el, agentIndex) => {
  if (el) nextTick(() => createSortable(`fi-${agentIndex}`, el, props.modelValue[agentIndex].fee_items))
  else {
    try { sortableMap.get(`fi-${agentIndex}`)?.destroy() } catch {}
    sortableMap.delete(`fi-${agentIndex}`)
  }
}

const onFeeTotalTableRef = (el, agentIndex) => {
  if (el) nextTick(() => createSortable(`ft-${agentIndex}`, el, props.modelValue[agentIndex].fee_total))
  else {
    try { sortableMap.get(`ft-${agentIndex}`)?.destroy() } catch {}
    sortableMap.delete(`ft-${agentIndex}`)
  }
}

onBeforeUnmount(() => {
  sortableMap.forEach(s => { try { s.destroy() } catch {} })
  sortableMap.clear()
})

// 整单费用 span-method（7列，含拖拽列，分组标题行横跨列1-5）
const feeTotalSpanMethod = ({ row, columnIndex }) => {
  if (row.备注 === '__GROUP_HEADER__') {
    if (columnIndex === 1) return [1, 5]
    if (columnIndex > 1 && columnIndex < 6) return [0, 0]
  }
  return [1, 1]
}

// 页面加载时从后端获取最新汇率
import { getExchangeRates, refreshForexRates } from '@/api/route'
const loadExchangeRates = async () => {
  try {
    const res = await getExchangeRates()
    if (res.success && res.data) {
      Object.assign(exchangeRates, res.data)
      if (res.reference_date) forexReferenceDate.value = res.reference_date
    }
  } catch (e) {
    console.warn('⚠️ 获取汇率失败，使用默认值')
  }
}
loadExchangeRates()

const forexRefreshing = ref(false)
const handleRefreshForex = async () => {
  forexRefreshing.value = true
  try {
    const res = await refreshForexRates()
    if (res.success && res.data) {
      Object.assign(exchangeRates, res.data)
      forexReferenceDate.value = new Date().toISOString().slice(0, 10)
      ElMessage.success(`汇率已更新，共同步 ${Object.keys(res.data).length} 种货币`)
    }
  } catch (e) {
    ElMessage.error('汇率同步失败，请检查网络或联系管理员')
  } finally {
    forexRefreshing.value = false
  }
}

// 计费重量变化时，同步所有 /kg 行的数量
watch(() => props.routeWeight, (newWeight) => {
  if (!newWeight) return
  props.modelValue.forEach(agent => {
    (agent.fee_items || []).forEach(item => {
      if (item.单位 === '/kg' && item.备注 !== '__GROUP_HEADER__') {
        item.数量 = newWeight
        updateFeeAmount(item)
      }
    })
  })
})

// 体积变化时，同步所有 /cbm 行的数量
watch(() => props.routeVolume, (newVol) => {
  if (!newVol) return
  props.modelValue.forEach(agent => {
    (agent.fee_items || []).forEach(item => {
      if (item.单位 === '/cbm' && item.备注 !== '__GROUP_HEADER__') {
        item.数量 = newVol
        updateFeeAmount(item)
      }
    })
  })
})

// 货值或货值币种变化时，重新计算所有代理商的税金和汇损
watch([() => props.routeValue, () => props.routeValueCurrency], () => {
  props.modelValue.forEach(agent => {
    updateSummary(agent)
  })
})

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
      小计手动: false,
      小计: 0,
      税率: 0,
      税率Display: 0,
      税金手动: false,
      税金: 0,
      汇损率: 0,
      汇损手动: false,
      汇损: 0,
      备注: '',
      税率模式: 'simple',
      税率明细: []
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

// 费用明细表格 span-method：11列，含拖拽列，分组标题行横跨列1-9
const feeItemSpanMethod = ({ row, columnIndex }) => {
  if (row.备注 === '__GROUP_HEADER__') {
    if (columnIndex === 1) return [1, 9]
    if (columnIndex > 1 && columnIndex < 10) return [0, 0]
  }
  return [1, 1]
}

// 添加分组标题行
const addGroupHeader = (agentIndex) => {
  if (!props.modelValue[agentIndex].fee_items) {
    props.modelValue[agentIndex].fee_items = []
  }
  props.modelValue[agentIndex].fee_items.push({
    _id: _genId(),
    费用类型: '',
    单价: 0,
    单位: '',
    数量: 0,
    最低收费: null,
    币种: 'RMB',
    原币金额: 0,
    人民币金额: 0,
    备注: '__GROUP_HEADER__'
  })
}

// 添加费用明细
const addFeeItem = (agentIndex) => {
  if (!props.modelValue[agentIndex].fee_items) {
    props.modelValue[agentIndex].fee_items = []
  }

  props.modelValue[agentIndex].fee_items.push({
    _id: _genId(),
    费用类型: '',
    单价: 0,
    单位: '/kg',
    数量: props.routeWeight || 0,
    最低收费: null,
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

// 添加整单费用分组标题行
const addFeeTotalGroupHeader = (agentIndex) => {
  if (!props.modelValue[agentIndex].fee_total) {
    props.modelValue[agentIndex].fee_total = []
  }
  props.modelValue[agentIndex].fee_total.push({
    _id: _genId(),
    费用名称: '',
    原币金额: 0,
    币种: 'RMB',
    人民币金额: 0,
    备注: '__GROUP_HEADER__'
  })
}

// 添加整单费用
const addFeeTotal = (agentIndex) => {
  if (!props.modelValue[agentIndex].fee_total) {
    props.modelValue[agentIndex].fee_total = []
  }

  props.modelValue[agentIndex].fee_total.push({
    _id: _genId(),
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

// 单位建议列表（el-autocomplete 数据源）
const UNIT_OPTIONS = [
  '/kg', '/cbm', '/票', '/件', '/个', '/箱', '/板', '/套', '/人', '/次', '/天',
  '/kg/天', '/cbm/天', '/票/天', '/kg/周', '/cbm/周'
]
const queryUnits = (query, cb) => {
  const q = (query || '').trim()
  const results = q
    ? UNIT_OPTIONS.filter(u => u.includes(q)).map(u => ({ value: u }))
    : UNIT_OPTIONS.map(u => ({ value: u }))
  cb(results)
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

// 计算实际原币金额（应用最低收费）
const calcOriginalAmount = (feeItem) => {
  const calculated = (feeItem.单价 || 0) * (feeItem.数量 || 0)
  const minFee = feeItem.最低收费 || 0
  return minFee > 0 ? Math.max(calculated, minFee) : calculated
}

// 更新费用原币金额
const updateFeeAmount = (feeItem) => {
  feeItem.原币金额 = calcOriginalAmount(feeItem)
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

// 计算人民币金额（含最低收费逻辑）
const calculateRMB = (feeItem) => {
  const rate = exchangeRates[feeItem.币种] || 1
  const originalAmount = feeItem.原币金额 || calcOriginalAmount(feeItem)
  return originalAmount * rate
}

// 按币种统计原币小计（用于展示），跳过分组标题行
const calculateSubtotalByCurrency = (agent) => {
  const byCurrency = {}
  const add = (currency, amount) => {
    if (!amount) return
    currency = currency || 'RMB'
    byCurrency[currency] = (byCurrency[currency] || 0) + amount
  }
  if (agent.fee_items) {
    agent.fee_items
      .filter(item => item.备注 !== '__GROUP_HEADER__')
      .forEach(item => {
        // 必须用 calcOriginalAmount（含最低收费），而非裸的单价×数量
        const amount = item.原币金额 != null ? item.原币金额 : calcOriginalAmount(item)
        add(item.币种, amount)
      })
  }
  if (agent.fee_total) {
    agent.fee_total.forEach(item => add(item.币种, item.原币金额 || 0))
  }
  return byCurrency
}

// 仅看费用（fee_items + fee_total）的单一外币，用于「小计」行显示
const getFeesCurrency = (agent) => {
  const byCurrency = calculateSubtotalByCurrency(agent)
  const arr = Object.keys(byCurrency).filter(c => byCurrency[c] > 0)
  return arr.length === 1 && arr[0] !== 'RMB' ? arr[0] : null
}

// 货值的外币，用于「税金/汇损」行显示
const getCargoCurrency = () => {
  const currency = props.routeValueCurrency || 'RMB'
  return (parseFloat(props.routeValue) || 0) > 0 && currency !== 'RMB' ? currency : null
}

// 费用+货值全部是同一外币时返回该币种，用于「总计」行显示
const getQuoteSingleCurrency = (agent) => {
  const byCurrency = calculateSubtotalByCurrency(agent)
  const allCurrencies = new Set(Object.keys(byCurrency).filter(c => byCurrency[c] > 0))
  const routeCurrency = props.routeValueCurrency || 'RMB'
  if ((parseFloat(props.routeValue) || 0) > 0) allCurrencies.add(routeCurrency)
  const arr = Array.from(allCurrencies)
  return arr.length === 1 && arr[0] !== 'RMB' ? arr[0] : null
}

// 计算小计（人民币合计），跳过分组标题行；手动模式时直接用 summary.小计
const calculateSubtotal = (agent) => {
  if (agent.summary?.小计手动) return agent.summary.小计 || 0
  let total = 0
  if (agent.fee_items) {
    total += agent.fee_items
      .filter(item => item.备注 !== '__GROUP_HEADER__')
      .reduce((sum, item) => sum + calculateRMB(item), 0)
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
  // 多税率模式：原币税金 = CNY税金 ÷ 汇率（避免读旧的 summary.税率）
  if (agent.summary?.税率模式 === 'multi' && agent.summary.税率明细?.length) {
    const rate = exchangeRates[props.routeValueCurrency || 'RMB'] || 1
    return rate > 0 ? calcMultiTaxTotal(agent) / rate : 0
  }
  return (parseFloat(props.routeValue) || 0) * (parseFloat(agent.summary.税率) || 0)
}
const calculateLossOriginal = (agent) => {
  // 汇损 = 税金原币 × 汇损率
  return calculateTaxOriginal(agent) * (parseFloat(agent.summary.汇损率) || 0)
}

// 计算税金（人民币）
const calculateTax = (agent) => {
  if (agent.summary?.税率模式 === 'multi' && agent.summary.税率明细?.length) {
    return calcMultiTaxTotal(agent)
  }
  return routeValueRMB() * (parseFloat(agent.summary.税率) || 0)
}

// 计算汇损（人民币）= 税金 × 汇损率
const calculateLoss = (agent) => {
  return calculateTax(agent) * (parseFloat(agent.summary.汇损率) || 0)
}

// 计算总计（手动模式时使用 summary 中已存的值）
const calculateTotal = (agent) => {
  const tax = agent.summary?.税金手动 ? (agent.summary.税金 || 0) : calculateTax(agent)
  const loss = agent.summary?.汇损手动 ? (agent.summary.汇损 || 0) : calculateLoss(agent)
  return calculateSubtotal(agent) + tax + loss
}

const updateSummary = (agent) => {
  if (!agent.summary) {
    agent.summary = { 小计手动: false, 小计: 0, 税率: 0, 税金手动: false, 税金: 0, 汇损率: 0, 汇损手动: false, 汇损: 0, 备注: '', 税率模式: 'simple', 税率明细: [] }
  }
  if (!agent.summary.税金手动) {
    agent.summary.税金 = calculateTax(agent)
  }
  if (!agent.summary.汇损手动) {
    agent.summary.汇损 = calculateLoss(agent)
  }
  agent.summary.小计 = calculateSubtotal(agent)
  agent.summary.总计 = calculateSubtotal(agent) + (agent.summary.税金 || 0) + (agent.summary.汇损 || 0)
}

// ── 多货物税率明细 ──────────────────────────────────────────

const calcTaxDetailRowCNY = (row) => {
  const value = parseFloat(row.货值) || 0
  const rate = exchangeRates[row.货值币种] || 1
  const taxRate = (parseFloat(row.综合税率) || 0) / 100
  return value * rate * taxRate
}

const calcMultiTaxTotal = (agent) => {
  return (agent.summary.税率明细 || []).reduce((sum, row) => sum + calcTaxDetailRowCNY(row), 0)
}

const addTaxDetail = (agent) => {
  if (!agent.summary.税率明细) agent.summary.税率明细 = []
  agent.summary.税率明细.push({ 货物名称: '', 货值: 0, 货值币种: props.routeValueCurrency || 'RMB', HS编码: '', 原产地: '', 税率说明: '', 综合税率: 10 })
}

const removeTaxDetail = (agent, index) => {
  agent.summary.税率明细.splice(index, 1)
  updateSummary(agent)
}

const importTaxFromGoods = (agent) => {
  if (!agent.summary.税率明细) agent.summary.税率明细 = []
  if (props.goodsList?.length > 0) {
    props.goodsList.forEach(g => {
      agent.summary.税率明细.push({
        货物名称: g.货物名称 || '',
        货值: parseFloat(g.货值) || 0,
        货值币种: g.货值币种 || props.routeValueCurrency || 'RMB',
        HS编码: '',
        原产地: '',
        税率说明: '',
        综合税率: 10
      })
    })
    ElMessage.success(`已导入 ${props.goodsList.length} 条货物信息`)
  } else if (parseFloat(props.routeValue) > 0) {
    agent.summary.税率明细.push({
      货物名称: '全部货物',
      货值: parseFloat(props.routeValue) || 0,
      货值币种: props.routeValueCurrency || 'RMB',
      HS编码: '',
      原产地: '',
      税率说明: '',
      综合税率: 10
    })
    ElMessage.success('已按路线总货值导入')
  } else {
    ElMessage.warning('暂无货值信息，请先在Step1填写货值，或在Step2填写整单货物')
  }
}

// ── 公式求值 ──────────────────────────────────────────────

const evalFormula = (expr) => {
  let s = expr.startsWith('=') ? expr.slice(1) : expr
  s = s
    .replace(/货值/g, String(parseFloat(props.routeValue) || 0))
    .replace(/重量/g, String(parseFloat(props.routeWeight) || 0))
    .replace(/体积/g, String(parseFloat(props.routeVolume) || 0))
  if (!/^[\d\s+\-*/().,]+$/.test(s)) return null
  try { return Function('"use strict";return(' + s + ')')() } catch { return null }
}

const activateFormula = (row, field) => {
  const formulaKey = `_formula_${field}`
  row[formulaKey] = `=${row[field] || 0}`
}

const clearFormula = (row, field) => {
  const formulaKey = `_formula_${field}`
  delete row[formulaKey]
}

const applyFormula = (row, field, isTotal = false) => {
  const formulaKey = `_formula_${field}`
  const formula = row[formulaKey]
  if (!formula) return
  const result = evalFormula(formula)
  if (result !== null && !isNaN(result)) {
    row[field] = Math.round(result * 100) / 100
    if (isTotal) updateFeeTotalRMB(row)
    else { updateFeeAmount(row) }
  } else {
    ElMessage.warning(`公式计算失败：${formula}`)
  }
}

// ── 键盘导航 ──────────────────────────────────────────────

const handleFeeKeydown = (e, agentIndex, tableType) => {
  if (!['Enter', 'ArrowDown', 'ArrowUp', 'ArrowLeft', 'ArrowRight'].includes(e.key)) return
  const target = e.target
  if (!target || target.tagName !== 'INPUT') return
  const tr = target.closest('tr.el-table__row')
  if (!tr) return
  const td = target.closest('td')
  if (!td) return
  const tbody = tr.closest('tbody')
  if (!tbody) return

  // Left / Right: navigate between inputs in the same row
  if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
    const allInputs = [...tr.querySelectorAll('input')]
    const curIdx = allInputs.indexOf(target)
    if (curIdx < 0) return
    const next = e.key === 'ArrowRight' ? allInputs[curIdx + 1] : allInputs[curIdx - 1]
    if (next) { e.preventDefault(); next.focus(); next.select() }
    return
  }

  e.preventDefault()

  const allRows = [...tbody.querySelectorAll('tr.el-table__row')]
  const rowIdx = allRows.indexOf(tr)
  const allTds = [...tr.querySelectorAll('td')]
  const colIdx = allTds.indexOf(td)

  if (e.key === 'ArrowUp') {
    if (rowIdx <= 0) return
    focusCell(allRows, rowIdx - 1, colIdx)
    return
  }

  // Enter / ArrowDown → next row
  if (rowIdx + 1 >= allRows.length) {
    if (tableType === 'fi') addFeeItem(agentIndex)
    else addFeeTotal(agentIndex)
    nextTick(() => {
      const newRows = [...tbody.querySelectorAll('tr.el-table__row')]
      focusCell(newRows, newRows.length - 1, colIdx)
    })
  } else {
    focusCell(allRows, rowIdx + 1, colIdx)
  }
}

const focusCell = (rows, rowIdx, colIdx) => {
  const tr = rows[rowIdx]
  if (!tr) return
  const tds = [...tr.querySelectorAll('td')]
  const td = tds[Math.min(colIdx, tds.length - 1)]
  const inp = td?.querySelector('input')
  if (inp) { inp.focus(); inp.select() }
}

// 税率 显示/存储 转换（存储为小数 0.09，显示为百分比 9）
const taxRateToDisplay = (v) => +((parseFloat(v) || 0) * 100).toFixed(4)
const taxRateFromDisplay = (v) => +((parseFloat(v) || 0) / 100).toFixed(8)

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
  validate,
  refreshSummaries: () => {
    props.modelValue.forEach(agent => updateSummary(agent))
  },
  // 用明确的货值参数刷新所有代理商汇总（绕过 stale props.routeValue，供 handleSubmit 提交前调用）
  refreshSummariesWithValue: (routeValue, routeValueCurrency) => {
    const rv = parseFloat(routeValue) || 0
    const rc = routeValueCurrency || 'RMB'
    const rvRMB = rv * (exchangeRates[rc] || 1)

    props.modelValue.forEach(agent => {
      if (!agent.summary) {
        agent.summary = { 小计手动: false, 小计: 0, 税率: 0, 税金手动: false, 税金: 0, 汇损率: 0, 汇损手动: false, 汇损: 0, 备注: '', 税率模式: 'simple', 税率明细: [] }
      }
      if (!agent.summary.税金手动) {
        agent.summary.税金 = (agent.summary.税率模式 === 'multi' && agent.summary.税率明细?.length)
          ? calcMultiTaxTotal(agent)
          : rvRMB * (parseFloat(agent.summary.税率) || 0)
      }
      if (!agent.summary.汇损手动) {
        agent.summary.汇损 = (agent.summary.税金 || 0) * (parseFloat(agent.summary.汇损率) || 0)
      }
      if (!agent.summary.小计手动) {
        agent.summary.小计 = calculateSubtotal(agent)
      }
      agent.summary.总计 = (agent.summary.小计 || 0) + (agent.summary.税金 || 0) + (agent.summary.汇损 || 0)
    })
  },
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

.forex-date-tip {
  font-size: 12px;
  font-weight: 400;
  color: #8c8c8c;
  margin-left: 8px;
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

.fee-table :deep(.group-header-row) td {
  background-color: #f0f5ff !important;
}

.drag-handle {
  cursor: grab;
  color: #bbb;
  font-size: 15px;
  user-select: none;
  display: block;
}

.drag-handle:active {
  cursor: grabbing;
}

.group-header-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.group-header-icon {
  color: #1890ff;
  font-size: 11px;
  flex-shrink: 0;
}

:deep(.sortable-ghost) {
  opacity: 0.4;
  background: #d6e4ff !important;
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

.price-wrap {
  display: flex;
  align-items: center;
  gap: 2px;
}

.formula-wrap {
  display: flex;
  align-items: center;
  gap: 2px;
}

.formula-btn {
  padding: 0 2px;
  min-width: 14px;
  color: #8c8c8c;
  font-size: 12px;
  font-style: italic;
}

.formula-btn:hover { color: #1890ff; }

.formula-clear {
  padding: 0 2px;
  min-width: 14px;
  color: #bfbfbf;
  font-size: 14px;
}

.formula-clear:hover { color: #f5222d; }

.formula-prefix {
  color: #52c41a;
  font-size: 11px;
  font-style: italic;
  font-weight: 600;
}

.multi-tax-section {
  padding: 12px 0 8px;
  margin-bottom: 8px;
}

.multi-tax-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.multi-tax-title {
  font-size: 13px;
  font-weight: 600;
  color: #262626;
}

.tax-detail-table {
  margin-bottom: 8px;
}

.multi-tax-total {
  text-align: right;
  font-size: 13px;
  color: #595959;
  padding: 6px 4px 0;
}

.manual-override-row {
  display: flex;
  align-items: center;
  padding: 4px 0;
  min-height: 32px;
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

.attachment-placeholder {
  padding: 12px 0 4px;
  color: #bfbfbf;
  font-size: 13px;
}
</style>