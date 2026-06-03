// composables/useFeeCalculation.js
// Fee calculation logic extracted from Step3AgentsForm.vue.
// Accepts the parent's props object (reactive) so route-level values are always current.
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getExchangeRates, refreshForexRates } from '@/api/route'

export function useFeeCalculation(props) {
  // ── Forex ──────────────────────────────────────────────────

  const exchangeRates = reactive({
    RMB: 1.0, USD: 7.2, EUR: 7.8, GBP: 9.2,
    AUD: 4.7, CAD: 5.3, SGD: 5.3, HKD: 0.93,
    JPY: 0.05, MYR: 1.6,
  })
  const forexReferenceDate = ref('')
  const forexRefreshing = ref(false)

  const loadExchangeRates = async () => {
    try {
      const res = await getExchangeRates()
      if (res.success && res.data) {
        Object.assign(exchangeRates, res.data)
        if (res.reference_date) forexReferenceDate.value = res.reference_date
      }
    } catch {
      console.warn('⚠️ 获取汇率失败，使用默认值')
    }
  }

  const handleRefreshForex = async () => {
    forexRefreshing.value = true
    try {
      const res = await refreshForexRates()
      if (res.success && res.data) {
        Object.assign(exchangeRates, res.data)
        forexReferenceDate.value = new Date().toISOString().slice(0, 10)
        ElMessage.success(`汇率已更新，共同步 ${Object.keys(res.data).length} 种货币`)
      }
    } catch {
      ElMessage.error('汇率同步失败，请检查网络或联系管理员')
    } finally {
      forexRefreshing.value = false
    }
  }

  // ── Fee item calculations ──────────────────────────────────

  const calcOriginalAmount = (feeItem) => {
    const calculated = (feeItem.单价 || 0) * (feeItem.数量 || 0)
    const minFee = feeItem.最低收费 || 0
    if (minFee <= 0) return calculated
    const minCurrency = feeItem.最低收费币种 || feeItem.币种 || 'RMB'
    const itemCurrency = feeItem.币种 || 'RMB'
    if (minCurrency === itemCurrency) return Math.max(calculated, minFee)
    const convertedMin = minFee * (exchangeRates[minCurrency] || 1) / (exchangeRates[itemCurrency] || 1)
    return Math.max(calculated, convertedMin)
  }

  const updateFeeAmount = (feeItem) => {
    feeItem.原币金额 = calcOriginalAmount(feeItem)
    updateFeeRMB(feeItem)
  }

  const updateFeeRMB = (feeItem) => {
    feeItem.人民币金额 = feeItem.原币金额 * (exchangeRates[feeItem.币种] || 1)
  }

  const updateFeeTotalRMB = (feeItem) => {
    feeItem.人民币金额 = feeItem.原币金额 * (exchangeRates[feeItem.币种] || 1)
  }

  const calculateRMB = (feeItem) => {
    const originalAmount = feeItem.原币金额 ?? calcOriginalAmount(feeItem)
    return originalAmount * (exchangeRates[feeItem.币种] || 1)
  }

  // ── Subtotal / currency helpers ────────────────────────────

  const calculateSubtotalByCurrency = (agent) => {
    const byCurrency = {}
    const add = (currency, amount) => {
      if (!amount) return
      const cur = currency || 'RMB'
      byCurrency[cur] = (byCurrency[cur] || 0) + amount
    }
    if (agent.fee_items) {
      agent.fee_items
        .filter(item => item.备注 !== '__GROUP_HEADER__' && item.参与核算 !== false)
        .forEach(item => add(item.币种, item.原币金额 != null ? item.原币金额 : calcOriginalAmount(item)))
    }
    if (agent.fee_total) {
      agent.fee_total
        .filter(item => item.备注 !== '__GROUP_HEADER__' && item.参与核算 !== false)
        .forEach(item => add(item.币种, item.原币金额 || 0))
    }
    return byCurrency
  }

  const getFeesCurrency = (agent) => {
    const byCurrency = calculateSubtotalByCurrency(agent)
    const arr = Object.keys(byCurrency).filter(c => byCurrency[c] > 0)
    return arr.length === 1 && arr[0] !== 'RMB' ? arr[0] : null
  }

  const getCargoCurrency = () => {
    const currency = props.routeValueCurrency || 'RMB'
    return (parseFloat(props.routeValue) || 0) > 0 && currency !== 'RMB' ? currency : null
  }

  const getQuoteSingleCurrency = (agent) => {
    const byCurrency = calculateSubtotalByCurrency(agent)
    const allCurrencies = new Set(Object.keys(byCurrency).filter(c => byCurrency[c] > 0))
    const routeCurrency = props.routeValueCurrency || 'RMB'
    if ((parseFloat(props.routeValue) || 0) > 0) allCurrencies.add(routeCurrency)
    const arr = Array.from(allCurrencies)
    return arr.length === 1 && arr[0] !== 'RMB' ? arr[0] : null
  }

  const routeValueRMB = () => {
    const value = parseFloat(props.routeValue) || 0
    return value * (exchangeRates[props.routeValueCurrency] || 1)
  }

  const calculateSubtotal = (agent) => {
    if (agent.summary?.小计手动) return agent.summary.小计 || 0
    let total = 0
    if (agent.fee_items) {
      total += agent.fee_items
        .filter(item => item.备注 !== '__GROUP_HEADER__' && item.参与核算 !== false)
        .reduce((sum, item) => sum + calculateRMB(item), 0)
    }
    if (agent.fee_total) {
      total += agent.fee_total
        .filter(item => item.备注 !== '__GROUP_HEADER__' && item.参与核算 !== false)
        .reduce((sum, item) => sum + calculateRMB(item), 0)
    }
    return total
  }

  // ── Tax / loss calculations ────────────────────────────────

  const calcTaxDetailRowCNY = (row) => {
    const value = parseFloat(row.货值) || 0
    const rate = exchangeRates[row.货值币种] || 1
    const taxRate = (parseFloat(row.综合税率) || 0) / 100
    return value * rate * taxRate
  }

  const calcMultiTaxTotal = (agent) =>
    (agent.summary.税率明细 || []).reduce((sum, row) => sum + calcTaxDetailRowCNY(row), 0)

  const calculateTaxOriginal = (agent) => {
    if (agent.summary?.税率模式 === 'multi' && agent.summary.税率明细?.length) {
      const rate = exchangeRates[props.routeValueCurrency || 'RMB'] || 1
      return rate > 0 ? calcMultiTaxTotal(agent) / rate : 0
    }
    return (parseFloat(props.routeValue) || 0) * (parseFloat(agent.summary.税率) || 0)
  }

  const calculateLossOriginal = (agent) =>
    calculateTaxOriginal(agent) * (parseFloat(agent.summary.汇损率) || 0)

  const calculateTax = (agent) => {
    if (agent.summary?.税率模式 === 'multi' && agent.summary.税率明细?.length) {
      return calcMultiTaxTotal(agent)
    }
    return routeValueRMB() * (parseFloat(agent.summary.税率) || 0)
  }

  const calculateLoss = (agent) =>
    calculateTax(agent) * (parseFloat(agent.summary.汇损率) || 0)

  const calculateTotal = (agent) => {
    let taxRMB
    if (agent.summary?.税金手动) {
      const taxCur = agent.summary.税金币种 || 'RMB'
      taxRMB = (agent.summary.税金 || 0) * (exchangeRates[taxCur] || 1)
    } else {
      taxRMB = calculateTax(agent)
    }
    const lossRMB = agent.summary?.汇损手动 ? (agent.summary.汇损 || 0) : calculateLoss(agent)
    return calculateSubtotal(agent) + taxRMB + lossRMB
  }

  const updateSummary = (agent) => {
    if (!agent.summary) {
      agent.summary = {
        小计手动: false, 小计: 0, 税率: 0, 税金手动: false, 税金: 0, 税金币种: 'RMB',
        汇损率: 0, 汇损手动: false, 汇损: 0, 备注: '',
        税率模式: 'simple', 税率明细: [],
      }
    }
    if (!agent.summary.税金手动) agent.summary.税金 = calculateTax(agent)
    if (!agent.summary.汇损手动) agent.summary.汇损 = calculateLoss(agent)
    agent.summary.小计 = calculateSubtotal(agent)
    agent.summary.总计 = calculateTotal(agent)
  }

  // ── Group subtotals ───────────────────────────────────────
  // 按分组标题聚合 fee_items 原币小计
  // 返回 [{name: 'KUL-AMS', amounts: {USD: 1035.5}}, ...]
  const calcGroupSubtotals = (agent) => {
    const groups = []
    let cur = null
    for (const item of (agent.fee_items || [])) {
      if (item.备注 === '__GROUP_HEADER__') {
        if (cur) groups.push(cur)
        cur = { name: item.费用类型 || '未命名组', amounts: {} }
        continue
      }
      if (!cur) continue
      if (item.参与核算 === false || item.参与核算 === 0) continue
      const currency = item.币种 || 'RMB'
      const amt = calcOriginalAmount(item)
      if (amt > 0) cur.amounts[currency] = (cur.amounts[currency] || 0) + amt
    }
    if (cur) groups.push(cur)
    return groups.filter(g => Object.keys(g.amounts).length > 0)
  }

  // ── Multi-tax detail helpers ───────────────────────────────

  const addTaxDetail = (agent) => {
    if (!agent.summary.税率明细) agent.summary.税率明细 = []
    agent.summary.税率明细.push({
      货物名称: '', 货值: 0, 货值币种: props.routeValueCurrency || 'RMB',
      HS编码: '', 原产地: '', 税率说明: '', 综合税率: 10,
    })
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
          HS编码: '', 原产地: '', 税率说明: '', 综合税率: 10,
        })
      })
      ElMessage.success(`已导入 ${props.goodsList.length} 条货物信息`)
    } else if (parseFloat(props.routeValue) > 0) {
      agent.summary.税率明细.push({
        货物名称: '全部货物',
        货值: parseFloat(props.routeValue) || 0,
        货值币种: props.routeValueCurrency || 'RMB',
        HS编码: '', 原产地: '', 税率说明: '', 综合税率: 10,
      })
      ElMessage.success('已按路线总货值导入')
    } else {
      ElMessage.warning('暂无货值信息，请先在Step1填写货值，或在Step2填写整单货物')
    }
  }

  // ── Formula eval ──────────────────────────────────────────

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
    row[`_formula_${field}`] = `=${row[field] || 0}`
  }

  const clearFormula = (row, field) => {
    delete row[`_formula_${field}`]
  }

  const applyFormula = (row, field, isTotal = false) => {
    const formula = row[`_formula_${field}`]
    if (!formula) return
    const result = evalFormula(formula)
    if (result !== null && !isNaN(result)) {
      row[field] = Math.round(result * 100) / 100
      if (isTotal) updateFeeTotalRMB(row)
      else updateFeeAmount(row)
    } else {
      ElMessage.warning(`公式计算失败：${formula}`)
    }
  }

  // ── Tax rate display ↔ stored value ───────────────────────

  const taxRateToDisplay = (v) => +((parseFloat(v) || 0) * 100).toFixed(4)
  const taxRateFromDisplay = (v) => +((parseFloat(v) || 0) / 100).toFixed(8)

  // ── refreshSummariesWithValue (used in defineExpose) ───────

  const refreshSummariesWithValue = (agents, routeValue, routeValueCurrency) => {
    const rv   = parseFloat(routeValue) || 0
    const rc   = routeValueCurrency || 'RMB'
    const rvRMB = rv * (exchangeRates[rc] || 1)
    agents.forEach(agent => {
      if (!agent.summary) {
        agent.summary = {
          小计手动: false, 小计: 0, 税率: 0, 税金手动: false, 税金: 0, 税金币种: 'RMB',
          汇损率: 0, 汇损手动: false, 汇损: 0, 备注: '',
          税率模式: 'simple', 税率明细: [],
        }
      }
      if (!agent.summary.税金手动) {
        agent.summary.税金 = (agent.summary.税率模式 === 'multi' && agent.summary.税率明细?.length)
          ? calcMultiTaxTotal(agent)
          : rvRMB * (parseFloat(agent.summary.税率) || 0)
      }
      if (!agent.summary.汇损手动) {
        agent.summary.汇损 = (agent.summary.税金 || 0) * (parseFloat(agent.summary.汇损率) || 0)
      }
      if (!agent.summary.小计手动) agent.summary.小计 = calculateSubtotal(agent)
      const taxRMB = agent.summary.税金手动
        ? (agent.summary.税金 || 0) * (exchangeRates[agent.summary.税金币种 || 'RMB'] || 1)
        : (agent.summary.税金 || 0)
      agent.summary.总计 = (agent.summary.小计 || 0) + taxRMB + (agent.summary.汇损 || 0)
    })
  }

  return {
    exchangeRates, forexReferenceDate, forexRefreshing,
    loadExchangeRates, handleRefreshForex,
    calcOriginalAmount, updateFeeAmount, updateFeeRMB, updateFeeTotalRMB, calculateRMB,
    calculateSubtotalByCurrency, getFeesCurrency, getCargoCurrency,
    getQuoteSingleCurrency, routeValueRMB, calculateSubtotal,
    calcTaxDetailRowCNY, calcMultiTaxTotal,
    calculateTaxOriginal, calculateLossOriginal,
    calculateTax, calculateLoss, calculateTotal, updateSummary,
    calcGroupSubtotals,
    addTaxDetail, removeTaxDetail, importTaxFromGoods,
    evalFormula, activateFormula, clearFormula, applyFormula,
    taxRateToDisplay, taxRateFromDisplay,
    refreshSummariesWithValue,
  }
}
