/**
 * 把 getRouteDetail 的 res.data 转换成 ManualInput 的 initialData 格式。
 * 纯函数，无 Vue 依赖。
 */
export function transformForCopy(detail) {
  const renameGoods = g => ({
    货物名称: g.货物名称,
    实际重量: g['实际重量(/kg)'] ?? g.实际重量 ?? 0,
    数量:     g.数量 ?? 0,
    货值:     g.货值 ?? 0,
    货值币种: g.货值币种 || 'RMB',
    总体积:   g['总体积(/cbm)'] ?? g.总体积 ?? 0,
    备注:     g.备注 || ''
  })

  const renameDetail = g => ({
    货物名称: g.货物名称,
    是否新品: g.是否新品 ? 1 : 0,
    货物种类: g.货物种类,
    数量:     g.数量,
    单价:     g.单价,
    币种:     g.币种,
    重量:     g['重量(/kg)']    ?? g.重量    ?? 0,
    总重量:   g['总重量(/kg)']  ?? g.总重量  ?? 0,
    总价:     g.总价,
    备注:     g.备注 || ''
  })

  return {
    起始地:         detail.起始地,
    途径地:         detail.途径地,
    目的地:         detail.目的地,
    交易开始日期:   detail.交易开始日期,
    交易结束日期:   detail.交易结束日期,
    实际重量:       detail['实际重量(/kg)'],
    计费重量:       detail['计费重量(/kg)'],
    总体积:         detail['总体积(/cbm)'],
    货值:           detail.货值,
    货值币种:       detail.货值币种,

    goods_total:    (detail.goods_total   || []).map(renameGoods),
    goods_details:  (detail.goods_details || []).map(renameDetail),

    agents: (detail.agents || []).map(a => ({
      代理商:   a.代理商,
      运输方式: a.运输方式,
      贸易类型: a.贸易类型,
      时效:     a.时效,
      时效备注: a.时效备注,
      不含:     a.不含,
      是否赔付: String(a.是否赔付 ?? '0'),
      赔付内容: a.赔付内容,
      代理备注: a.代理备注,

      // 保留分组标题行（用户手工加的，后端正常存储），只剥掉自增 ID 和时间戳
      // eslint-disable-next-line no-unused-vars
      fee_items: (a.fee_items || []).map(({ 费用ID, 创建时间, ...rest }) => rest),

      // eslint-disable-next-line no-unused-vars
      fee_total: (a.fee_total || []).map(({ 整单费用ID, 创建时间, ...rest }) => rest),

      summary: {
        税率:         parseFloat(a.summary?.税率)   || 0,
        汇损率:       parseFloat(a.summary?.汇损率) || 0,
        // ManualInput line 351 从 进口税率原文 re-derive 税率明细
        进口税率原文: a.summary?.进口税率原文 || '',
        备注:         a.summary?.备注 || ''
        // 不复制 小计/税金/汇损/总计（Step3 计算引擎按新货物数据重算）
      }
    }))
  }
}
