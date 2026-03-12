# scripts/modules/extractors/fee_extractor.py
"""
费用提取器（智能路由）

同时提取：
1. fee_item - 单价费用（xx元/kg）
2. fee_total - 整单费用（操作费xx元）
"""

from typing import Dict, Any, List
from .fee_item_extractor import FeeItemExtractor, FeeItem
from .fee_total_extractor import FeeTotalExtractor, FeeTotal


class FeeExtractor:
    """费用提取器（智能路由）"""
    
    def __init__(self, logger=None, llm_client=None, enable_llm=True):
        self.logger = logger
        
        # 初始化两个子提取器
        self.item_extractor = FeeItemExtractor(logger, llm_client, enable_llm)
        self.total_extractor = FeeTotalExtractor(logger, llm_client, enable_llm)
    
    def extract(self, sheet, agent_col_idx: int = None, **kwargs) -> Dict[str, Any]:
        """
        提取费用信息
        
        参数：
            sheet: Excel sheet对象
            agent_col_idx: 代理商所在的列索引
        
        Returns:
            {
                'fee_items': List[FeeItem],
                'fee_totals': List[FeeTotal]
            }
        """
        if not agent_col_idx:
            if self.logger:
                self.logger.warning("  ⚠️  未提供agent_col_idx，无法提取费用")
            return {
                'fee_items': [],
                'fee_totals': []
            }
        
        if self.logger:
            self.logger.debug(f"  🔍 从第{agent_col_idx}列提取费用...")
        
        # ✅ 1. 提取单价费用
        fee_items = self.item_extractor.extract(sheet, agent_col_idx=agent_col_idx, **kwargs)
        
        # ✅ 2. 提取整单费用
        fee_totals = self.total_extractor.extract(sheet, agent_col_idx=agent_col_idx, **kwargs)
        
        if self.logger:
            self.logger.info(f"  ✅ 费用提取完成: {len(fee_items)}个单价费用, {len(fee_totals)}个整单费用")
        
        return {
            'fee_items': fee_items,
            'fee_totals': fee_totals
        }


__all__ = ['FeeExtractor']