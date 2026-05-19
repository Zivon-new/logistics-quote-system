// composables/useFeeCalculation.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Stub external dependencies before importing the composable ──
vi.mock('element-plus', () => ({ ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() } }))
vi.mock('@/api/route', () => ({
  getExchangeRates: vi.fn().mockResolvedValue({ success: false }),
  refreshForexRates: vi.fn().mockResolvedValue({ success: false }),
}))

import { useFeeCalculation } from './useFeeCalculation'

// Minimal props stub
const makeProps = (overrides = {}) => ({
  routeValue: 1000,
  routeValueCurrency: 'USD',
  routeWeight: 100,
  routeVolume: 2,
  goodsList: [],
  modelValue: [],
  ...overrides,
})

// ── evalFormula (security-critical) ──────────────────────────────────────────

describe('evalFormula — security guard', () => {
  let applyFormula, activateFormula

  beforeEach(() => {
    const ctx = useFeeCalculation(makeProps())
    applyFormula = ctx.applyFormula
    activateFormula = ctx.activateFormula
  })

  it('evaluates valid arithmetic formula', () => {
    const row = { 单价: 0, 数量: 0, 原币金额: 0, 人民币金额: 0, 币种: 'RMB', 最低收费: null }
    activateFormula(row, '单价')
    row['_formula_单价'] = '=50 * 2'
    applyFormula(row, '单价')
    expect(row['单价']).toBe(100)
  })

  it('substitutes 货值 variable', () => {
    const props = makeProps({ routeValue: 5000 })
    const { activateFormula: af, applyFormula: apf } = useFeeCalculation(props)
    const row = { 单价: 0, 数量: 0, 原币金额: 0, 人民币金额: 0, 币种: 'RMB', 最低收费: null }
    af(row, '单价')
    row['_formula_单价'] = '=货值*0.04'
    apf(row, '单价')
    expect(row['单价']).toBeCloseTo(200)
  })

  it('blocks formula with non-numeric characters (injection attempt)', () => {
    // If the regex guard works, result should be null and the field stays unchanged
    const row = { 单价: 99, 数量: 0, 原币金额: 0, 人民币金额: 0, 币种: 'RMB', 最低收费: null }
    row['_formula_单价'] = '=process.exit(1)'
    // applyFormula should NOT update the field when result is null
    applyFormula(row, '单价')
    expect(row['单价']).toBe(99)
  })

  it('blocks formula with bracket access attempt', () => {
    const row = { 单价: 42, 数量: 0, 原币金额: 0, 人民币金额: 0, 币种: 'RMB', 最低收费: null }
    row['_formula_单价'] = '=globalThis["eval"]("1")'
    applyFormula(row, '单价')
    expect(row['单价']).toBe(42)
  })
})

// ── calcOriginalAmount ────────────────────────────────────────────────────────

describe('calcOriginalAmount', () => {
  const { calcOriginalAmount } = useFeeCalculation(makeProps())

  it('returns price * qty without min fee', () => {
    expect(calcOriginalAmount({ 单价: 50, 数量: 3, 最低收费: null })).toBe(150)
  })

  it('returns min fee when calculated amount is below it', () => {
    expect(calcOriginalAmount({ 单价: 10, 数量: 1, 最低收费: 50 })).toBe(50)
  })

  it('returns calculated amount when above min fee', () => {
    expect(calcOriginalAmount({ 单价: 30, 数量: 5, 最低收费: 50 })).toBe(150)
  })

  it('ignores min fee of zero', () => {
    expect(calcOriginalAmount({ 单价: 20, 数量: 2, 最低收费: 0 })).toBe(40)
  })

  it('handles undefined price and qty as zero', () => {
    expect(calcOriginalAmount({ 单价: undefined, 数量: undefined, 最低收费: null })).toBe(0)
  })
})

// ── calculateSubtotal ─────────────────────────────────────────────────────────

describe('calculateSubtotal', () => {
  it('sums fee_items and fee_total, skipping group headers', () => {
    const ctx = useFeeCalculation(makeProps())
    // Set exchange rate for USD to make RMB calculation predictable
    ctx.exchangeRates['USD'] = 7

    const agent = {
      fee_items: [
        { 原币金额: 100, 币种: 'RMB', 备注: '' },
        { 原币金额: 0, 币种: 'RMB', 备注: '__GROUP_HEADER__' }, // should be skipped
        { 原币金额: 200, 币种: 'USD', 备注: '' }, // 200 * 7 = 1400 RMB
      ],
      fee_total: [
        { 原币金额: 50, 币种: 'RMB' },
      ],
      summary: { 小计手动: false },
    }
    // 100 + 1400 + 50 = 1550
    expect(ctx.calculateSubtotal(agent)).toBeCloseTo(1550)
  })

  it('returns manual subtotal when 小计手动 is true', () => {
    const ctx = useFeeCalculation(makeProps())
    const agent = {
      fee_items: [{ 原币金额: 999, 币种: 'RMB', 备注: '' }],
      fee_total: [],
      summary: { 小计手动: true, 小计: 300 },
    }
    expect(ctx.calculateSubtotal(agent)).toBe(300)
  })
})
