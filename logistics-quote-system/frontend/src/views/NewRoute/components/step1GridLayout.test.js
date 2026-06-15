import { describe, it, expect } from 'vitest'
import { ROW_LAYOUT, LAST_CELL, getTargetCell } from './step1GridLayout'

describe('ROW_LAYOUT', () => {
  it('matches the documented 2/3/2/3 topology', () => {
    expect(ROW_LAYOUT).toEqual([
      ['起始地', '途径地'],
      ['目的地', '交易日期开始', '交易日期结束'],
      ['实际重量', '计费重量'],
      ['总体积', '货值', '货值币种'],
    ])
  })
})

describe('LAST_CELL', () => {
  it('is the last cell of the last row', () => {
    expect(LAST_CELL).toBe('货值币种')
  })
})

describe('getTargetCell — ArrowLeft/ArrowRight', () => {
  it('moves within a row', () => {
    expect(getTargetCell('起始地', 'ArrowRight')).toBe('途径地')
    expect(getTargetCell('途径地', 'ArrowLeft')).toBe('起始地')
    expect(getTargetCell('目的地', 'ArrowRight')).toBe('交易日期开始')
    expect(getTargetCell('交易日期开始', 'ArrowRight')).toBe('交易日期结束')
    expect(getTargetCell('交易日期结束', 'ArrowLeft')).toBe('交易日期开始')
  })

  it('does not wrap at row start/end', () => {
    expect(getTargetCell('起始地', 'ArrowLeft')).toBeNull()
    expect(getTargetCell('途径地', 'ArrowRight')).toBeNull()
    expect(getTargetCell('目的地', 'ArrowLeft')).toBeNull()
    expect(getTargetCell('交易日期结束', 'ArrowRight')).toBeNull()
    expect(getTargetCell('总体积', 'ArrowLeft')).toBeNull()
    expect(getTargetCell('货值币种', 'ArrowRight')).toBeNull()
  })
})

describe('getTargetCell — ArrowUp/ArrowDown', () => {
  it('is index-aligned to the adjacent row', () => {
    expect(getTargetCell('起始地', 'ArrowDown')).toBe('目的地')
    expect(getTargetCell('途径地', 'ArrowDown')).toBe('交易日期开始')
    expect(getTargetCell('目的地', 'ArrowUp')).toBe('起始地')
    expect(getTargetCell('交易日期开始', 'ArrowUp')).toBe('途径地')
  })

  it('clamps to the last cell when the adjacent row is shorter', () => {
    expect(getTargetCell('交易日期结束', 'ArrowDown')).toBe('计费重量')
    expect(getTargetCell('计费重量', 'ArrowDown')).toBe('货值')
  })

  it('is a no-op on row 1 (Up) and row 4 (Down)', () => {
    expect(getTargetCell('起始地', 'ArrowUp')).toBeNull()
    expect(getTargetCell('途径地', 'ArrowUp')).toBeNull()
    expect(getTargetCell('总体积', 'ArrowDown')).toBeNull()
    expect(getTargetCell('货值', 'ArrowDown')).toBeNull()
    expect(getTargetCell('货值币种', 'ArrowDown')).toBeNull()
  })
})

describe('getTargetCell — Enter', () => {
  it('behaves the same as ArrowDown', () => {
    expect(getTargetCell('起始地', 'Enter')).toBe('目的地')
    expect(getTargetCell('交易日期结束', 'Enter')).toBe('计费重量')
  })

  it('is a no-op on row 4', () => {
    expect(getTargetCell('总体积', 'Enter')).toBeNull()
    expect(getTargetCell('货值币种', 'Enter')).toBeNull()
  })
})

describe('getTargetCell — edge cases', () => {
  it('returns null for an unknown cell id', () => {
    expect(getTargetCell('不存在', 'ArrowDown')).toBeNull()
  })

  it('returns null for keys without a mapping', () => {
    expect(getTargetCell('起始地', 'Tab')).toBeNull()
    expect(getTargetCell('起始地', 'a')).toBeNull()
  })
})
