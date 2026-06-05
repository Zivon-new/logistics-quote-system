/**
 * 按分组标题聚合 fee_items + fee_total 原币小计
 * 返回 [{name: '路线名', amounts: {USD: 1035.5}}, ...]
 *
 * 适用于只读视图（RouteManage、QuoteSearch）——所有 item 都已存库，
 * 原币金额已计算，直接读取即可。
 *
 * 编辑态（Step3AgentsForm）由 useFeeCalculation.js 内的版本处理，
 * 后者会在 原币金额 未设置时回退 calcOriginalAmount(单价×数量)。
 */
export function calcGroupSubtotalsReadOnly(agent) {
  const groupMap = new Map()
  const groupOrder = []

  const processItems = (items) => {
    let curName = null
    for (const item of (items || [])) {
      if (item.备注 === '__GROUP_HEADER__') {
        curName = item.费用类型 || item.费用名称 || '未命名组'
        if (!groupMap.has(curName)) {
          groupMap.set(curName, {})
          groupOrder.push(curName)
        }
        continue
      }
      if (!curName) continue
      if (item.参与核算 === false || item.参与核算 === 0) continue
      const currency = item.币种 || 'RMB'
      const amt = parseFloat(item.原币金额) || 0
      if (amt > 0) {
        const amounts = groupMap.get(curName)
        amounts[currency] = (amounts[currency] || 0) + amt
      }
    }
  }

  processItems(agent.fee_items)
  processItems(agent.fee_total)

  return groupOrder
    .map(name => ({ name, amounts: groupMap.get(name) }))
    .filter(g => Object.keys(g.amounts).length > 0)
}
