// Focuses the input in a given (row, col) cell of an el-table-style grid,
// clamping the column to the last available cell in shorter rows (e.g. group-header rows).
// For radio-group cells (e.g. 是否新品), focuses the checked radio rather than
// always the first one.
export function focusCell(rows, rowIdx, colIdx) {
  const tr = rows[rowIdx]
  if (!tr) return
  const tds = [...tr.querySelectorAll('td')]
  const td = tds[Math.min(colIdx, tds.length - 1)]
  const inp = td?.querySelector('input:checked') || td?.querySelector('input')
  if (inp) { inp.focus(); inp.select() }
}
