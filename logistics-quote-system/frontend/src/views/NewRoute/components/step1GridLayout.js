// Step1's cell grid topology (4 rows, uneven cell counts), per
// docs/adr/0001-grid-cell-navigation-edit-mode.md.
export const ROW_LAYOUT = [
  ['起始地', '途径地'],
  ['目的地', '交易日期开始', '交易日期结束'],
  ['实际重量', '计费重量'],
  ['总体积', '货值', '货值币种'],
]

// The last cell in reading order — Tab here has no effect (no wrap-around).
export const LAST_CELL = ROW_LAYOUT[ROW_LAYOUT.length - 1].at(-1)

const findCell = (cellId) => {
  for (let row = 0; row < ROW_LAYOUT.length; row++) {
    const col = ROW_LAYOUT[row].indexOf(cellId)
    if (col >= 0) return { row, col }
  }
  return null
}

/**
 * Maps (current cell, key) to the target cell id, per ADR-0001's Step1 topology:
 * - ArrowLeft/Right: move within the row, no wrap at row start/end (null)
 * - ArrowUp: index-aligned to the previous row, null on row 1
 * - ArrowDown/Enter: index-aligned to the next row, null on row 4
 * - Anything else / unknown cellId: null
 */
export function getTargetCell(cellId, key) {
  const pos = findCell(cellId)
  if (!pos) return null
  const { row, col } = pos

  switch (key) {
    case 'ArrowLeft':
      return col > 0 ? ROW_LAYOUT[row][col - 1] : null
    case 'ArrowRight':
      return col < ROW_LAYOUT[row].length - 1 ? ROW_LAYOUT[row][col + 1] : null
    case 'ArrowUp': {
      if (row === 0) return null
      const targetRow = ROW_LAYOUT[row - 1]
      return targetRow[Math.min(col, targetRow.length - 1)]
    }
    case 'ArrowDown':
    case 'Enter': {
      if (row === ROW_LAYOUT.length - 1) return null
      const targetRow = ROW_LAYOUT[row + 1]
      return targetRow[Math.min(col, targetRow.length - 1)]
    }
    default:
      return null
  }
}
