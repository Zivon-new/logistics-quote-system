# scripts/modules/extractors/fee_extractor.py
"""
费用提取器（智能路由）

同时提取：
1. fee_item - 单价费用（xx元/kg）
2. fee_total - 整单费用（操作费xx元）
"""

from typing import Dict, Any, List, Optional
from .fee_item_extractor import FeeItemExtractor, FeeItem
from .fee_total_extractor import FeeTotalExtractor, FeeTotal
from .agent_extractor_v2 import FEE_ANCHORS


class FeeExtractor:
    """费用提取器（智能路由）v2.4：支持锚点降级提取"""

    def __init__(self, logger=None, llm_client=None, enable_llm=True):
        self.logger = logger

        self.item_extractor = FeeItemExtractor(logger, llm_client, enable_llm)
        self.total_extractor = FeeTotalExtractor(logger, llm_client, enable_llm)

    def extract(self, sheet, agent_col_idx: int = None, **kwargs) -> Dict[str, Any]:
        """
        提取费用信息

        参数：
            sheet: Excel sheet对象
            agent_col_idx: 代理商所在的列索引（None 时尝试锚点自动定位）

        Returns:
            {'fee_items': List[FeeItem], 'fee_totals': List[FeeTotal]}
        """
        if agent_col_idx is None:
            # 锚点降级：尝试自动定位费用列
            agent_col_idx = self._detect_fee_column_from_anchors(sheet)
            if agent_col_idx is None:
                if self.logger:
                    self.logger.warning("  ⚠️  未提供 agent_col_idx 且锚点定位失败，无法提取费用")
                return {'fee_items': [], 'fee_totals': []}
            if self.logger:
                self.logger.debug(f"  🔍 锚点定位费用列: {agent_col_idx}")

        if self.logger:
            self.logger.debug(f"  🔍 从第{agent_col_idx}列提取费用...")

        fee_items = self.item_extractor.extract(sheet, agent_col_idx=agent_col_idx, **kwargs)
        fee_totals = self.total_extractor.extract(sheet, agent_col_idx=agent_col_idx, **kwargs)

        if self.logger:
            self.logger.info(f"  ✅ 费用提取完成: {len(fee_items)}个单价费用, {len(fee_totals)}个整单费用")

        return {'fee_items': fee_items, 'fee_totals': fee_totals}

    def _detect_fee_column_from_anchors(self, sheet) -> Optional[int]:
        """
        从费用锚点行找数字所在列，用作费用列的降级定位。
        与 agent_extractor_v2.FEE_ANCHORS 保持同一份关键词列表。
        """
        for row_idx in range(3, min(30, sheet.max_row + 1)):
            label = str(sheet.cell(row=row_idx, column=1).value or '').strip()
            if any(a in label for a in FEE_ANCHORS):
                for col_idx in range(2, min(sheet.max_column + 1, 8)):
                    val = sheet.cell(row=row_idx, column=col_idx).value
                    if val:
                        s = str(val).strip().replace(',', '')
                        try:
                            float(s)
                            return col_idx
                        except ValueError:
                            continue
        return None


__all__ = ['FeeExtractor']