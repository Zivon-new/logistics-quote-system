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
            :row-class-name="({ row }) => row.备注 === '__GROUP_HEADER__' ? 'group-header-row' : (row.参与核算 === false ? 'excluded-row' : '')"
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

            <el-table-column label="数量" width="120">
              <template #default="scope">
                <div v-if="scope.row._formula_数量 !== undefined" class="formula-wrap">
                  <el-input
                    v-model="scope.row._formula_数量"
                    size="small"
                    placeholder="如 462*3"
                    @blur="applyFormula(scope.row, '数量')"
                    @keydown.enter.prevent="applyFormula(scope.row, '数量')"
                  >
                    <template #prefix><span class="formula-prefix">f</span></template>
                  </el-input>
                  <el-button link size="small" class="formula-clear" @click="clearFormula(scope.row, '数量')">×</el-button>
                </div>
                <div v-else class="price-wrap">
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
                      @change="updateFeeAmount(scope.row)"
                    />
                  </el-tooltip>
                  <el-input-number v-else :controls="false"
                    v-model="scope.row.数量"
                    :precision="2"
                    :min="0"
                    size="small"
                    @change="updateFeeAmount(scope.row)"
                  />
                  <el-tooltip content="输入表达式（如 462*3）" placement="top">
                    <el-button link size="small" class="formula-btn" @click="activateFormula(scope.row, '数量')">=</el-button>
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="最低收费" width="185">
              <template #default="scope">
                <div v-if="scope.row.备注 !== '__GROUP_HEADER__'" class="min-fee-wrap">
                  <el-input-number :controls="false"
                    v-model="scope.row.最低收费"
                    :precision="2"
                    :min="0"
                    placeholder="选填"
                    size="small"
                    style="width:105px"
                    @change="updateFeeAmount(scope.row)"
                  />
                  <CurrencySelect
                    v-model="scope.row.最低收费币种"
                    size="small"
                    style="width:75px"
                    @change="updateFeeAmount(scope.row)"
                  />
                </div>
              </template>
            </el-table-column>

            <el-table-column label="币种" width="90">
              <template #default="scope">
                <CurrencySelect v-model="scope.row.币种" size="small" @change="updateFeeRMB(scope.row)" />
              </template>
            </el-table-column>

            <el-table-column label="原币金额" width="110">
              <template #default="scope">
                <el-tooltip
                  v-if="scope.row.最低收费 > 0 && calcOriginalAmount(scope.row) > (scope.row.单价 * scope.row.数量)"
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

            <el-table-column label="核算" width="58" align="center">
              <template #default="scope">
                <el-tooltip
                  v-if="scope.row.备注 !== '__GROUP_HEADER__'"
                  :content="scope.row.参与核算 !== false ? '参与核算（点击排除）' : '已排除（点击恢复）'"
                  placement="top"
                >
                  <el-switch
                    :model-value="scope.row.参与核算 !== false"
                    size="small"
                    @change="val => { scope.row.参与核算 = val; updateFeeAmount(scope.row) }"
                  />
                </el-tooltip>
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
            :row-class-name="({ row }) => row.备注 === '__GROUP_HEADER__' ? 'group-header-row' : (row.参与核算 === false ? 'excluded-row' : '')"
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
                <CurrencySelect v-model="scope.row.币种" size="small" @change="updateFeeTotalRMB(scope.row)" />
              </template>
            </el-table-column>

            <el-table-column label="人民币金额" width="140">
              <template #default="scope">
                <span style="color: #52c41a; font-weight: 600;">
                  ¥{{ calculateRMB(scope.row).toFixed(2) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column label="核算" width="58" align="center">
              <template #default="scope">
                <el-tooltip
                  v-if="scope.row.备注 !== '__GROUP_HEADER__'"
                  :content="scope.row.参与核算 !== false ? '参与核算（点击排除）' : '已排除（点击恢复）'"
                  placement="top"
                >
                  <el-switch
                    :model-value="scope.row.参与核算 !== false"
                    size="small"
                    @change="val => { scope.row.参与核算 = val; updateSummary(props.modelValue[agentIndex]) }"
                  />
                </el-tooltip>
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
            <!-- 分组小计（仅当 fee_items 中存在分组标题时显示） -->
            <template v-if="calcGroupSubtotals(agent).length > 0">
              <div class="group-subtotals-block">
                <div
                  v-for="grp in calcGroupSubtotals(agent)"
                  :key="grp.name"
                  class="group-subtotal-row"
                >
                  <span class="group-subtotal-label">{{ grp.name }}</span>
                  <span class="group-subtotal-amounts">
                    <span
                      v-for="(amt, cur) in grp.amounts"
                      :key="cur"
                      class="group-subtotal-item"
                    >{{ cur }} {{ amt.toFixed(2) }}</span>
                  </span>
                </div>
              </div>
              <el-divider style="margin:6px 0 10px" />
            </template>
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
                <div style="display:flex;gap:8px;flex-wrap:wrap">
                  <!-- 同步按钮：只在有其他已填写税率明细的代理时显示 -->
                  <template v-if="taxSyncSources(agentIndex).length === 1">
                    <el-button
                      size="small"
                      @click="syncTaxFrom(agent, taxSyncSources(agentIndex)[0].agent)"
                    >
                      从{{ taxSyncSources(agentIndex)[0].label }}同步
                    </el-button>
                  </template>
                  <template v-else-if="taxSyncSources(agentIndex).length > 1">
                    <el-dropdown @command="src => syncTaxFrom(agent, src)">
                      <el-button size="small">
                        从其他代理同步<el-icon class="el-icon--right"><arrow-down /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item
                            v-for="src in taxSyncSources(agentIndex)"
                            :key="src.index"
                            :command="src.agent"
                          >{{ src.label }}</el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </template>
                  <el-button size="small" @click="importTaxFromGoods(agent, agentIndex)">
                    从货物信息导入
                  </el-button>
                  <el-button size="small" type="primary" @click="addTaxDetail(agent)">
                    + 添加行
                  </el-button>
                </div>
              </div>
              <div @keydown="handleTaxKeydown($event, agent)">
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
                    <CurrencySelect v-model="scope.row.货值币种" size="small" @change="updateSummary(agent)" />
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
                      :min="0" :max="999" size="small"
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
              </div><!-- /keydown wrapper tax -->
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
                    <template v-if="agent.summary.税金手动">
                      <el-input-number
                        :controls="false"
                        v-model="agent.summary.税金"
                        :precision="2"
                        :min="0"
                        style="width:90px"
                        @change="updateSummary(agent)"
                      />
                      <CurrencySelect
                        v-model="agent.summary.税金币种"
                        size="small"
                        style="width:85px;margin-left:4px"
                        @change="updateSummary(agent)"
                      />
                    </template>
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
import { ref, watch, onBeforeUnmount, nextTick } from 'vue'
import { Plus, Delete, InfoFilled, ArrowDown } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import Sortable from 'sortablejs'
import AttachmentPanel from '@/components/AttachmentPanel.vue'
import CurrencySelect from '@/components/CurrencySelect.vue'
import { useFeeCalculation } from '@/composables/useFeeCalculation'

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

// ── Fee calculation composable ─────────────────────────────
const {
  exchangeRates, forexReferenceDate, forexRefreshing,
  loadExchangeRates, handleRefreshForex,
  calcOriginalAmount, updateFeeAmount, updateFeeRMB, updateFeeTotalRMB, calculateRMB,
  calculateSubtotalByCurrency, getFeesCurrency, getCargoCurrency,
  getQuoteSingleCurrency, calculateSubtotal,
  calcGroupSubtotals,
  calcTaxDetailRowCNY, calcMultiTaxTotal,
  calculateTaxOriginal, calculateLossOriginal,
  calculateTax, calculateLoss, calculateTotal, updateSummary,
  addTaxDetail, removeTaxDetail, importTaxFromGoods,
  activateFormula, clearFormula, applyFormula,
  taxRateToDisplay, taxRateFromDisplay,
  refreshSummariesWithValue,
} = useFeeCalculation(props)

loadExchangeRates()

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

// exchangeRates / forexReferenceDate / forexRefreshing — from useFeeCalculation composable

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

// 整单费用 span-method（8列，含拖拽列，分组标题行横跨列1-6）
const feeTotalSpanMethod = ({ row, columnIndex }) => {
  if (row.备注 === '__GROUP_HEADER__') {
    if (columnIndex === 1) return [1, 6]
    if (columnIndex > 1 && columnIndex < 7) return [0, 0]
  }
  return [1, 1]
}

// loadExchangeRates / handleRefreshForex — from useFeeCalculation composable

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
      税金币种: 'RMB',
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

// 费用明细表格 span-method：12列（含拖拽列），分组标题行横跨列1-10，操作列（11）保留以显示删除按钮
const feeItemSpanMethod = ({ row, columnIndex }) => {
  if (row.备注 === '__GROUP_HEADER__') {
    if (columnIndex === 1) return [1, 10]
    if (columnIndex > 1 && columnIndex < 11) return [0, 0]
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
    最低收费币种: 'RMB',
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
    最低收费币种: 'RMB',
    币种: 'RMB',
    原币金额: 0,
    人民币金额: 0,
    备注: '',
    参与核算: true,
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
    备注: '',
    参与核算: true,
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

// Calculation functions — from useFeeCalculation composable

// ── 键盘导航 ──────────────────────────────────────────────

// 返回当前代理以外、已有多货物税率明细的代理列表，用于同步来源选择
const taxSyncSources = (currentAgentIndex) => {
  return props.modelValue
    .map((a, i) => ({ agent: a, index: i, label: `代理${i + 1}（${a.代理商 || '未命名'}）` }))
    .filter(({ agent, index }) =>
      index !== currentAgentIndex &&
      agent.summary?.税率模式 === 'multi' &&
      agent.summary?.税率明细?.length > 0
    )
}

// 从来源代理同步税率明细到目标代理（完全覆盖）
const syncTaxFrom = (targetAgent, sourceAgent) => {
  targetAgent.summary.税率明细 = JSON.parse(JSON.stringify(sourceAgent.summary.税率明细))
  updateSummary(targetAgent)
  ElMessage.success('税率明细已同步')
}

// 税率明细表格的键盘导航（Enter/方向键，与费用明细一致）
const handleTaxKeydown = (e, agent) => {
  if (!['Enter', 'ArrowDown', 'ArrowUp', 'ArrowLeft', 'ArrowRight'].includes(e.key)) return
  const target = e.target
  if (!target || target.tagName !== 'INPUT') return
  const tr = target.closest('tr.el-table__row')
  if (!tr) return
  const td = target.closest('td')
  if (!td) return
  const tbody = tr.closest('tbody')
  if (!tbody) return

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

  if (rowIdx + 1 >= allRows.length) {
    addTaxDetail(agent)
    nextTick(() => {
      const newRows = [...tbody.querySelectorAll('tr.el-table__row')]
      focusCell(newRows, newRows.length - 1, colIdx)
    })
  } else {
    focusCell(allRows, rowIdx + 1, colIdx)
  }
}

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

// taxRateToDisplay / taxRateFromDisplay — from useFeeCalculation composable

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
  refreshSummaries: () => props.modelValue.forEach(agent => updateSummary(agent)),
  refreshSummariesWithValue: (routeValue, routeValueCurrency) =>
    refreshSummariesWithValue(props.modelValue, routeValue, routeValueCurrency),
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

.fee-table :deep(.excluded-row) td {
  opacity: 0.45;
}

.min-fee-wrap {
  display: flex;
  align-items: center;
  gap: 2px;
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
.group-subtotals-block {
  padding: 4px 0 4px 120px;
}
.group-subtotal-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #595959;
  padding: 2px 0;
}
.group-subtotal-label {
  font-weight: 500;
  min-width: 80px;
}
.group-subtotal-amounts {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.group-subtotal-item {
  color: #1890ff;
  font-weight: 600;
}
</style>