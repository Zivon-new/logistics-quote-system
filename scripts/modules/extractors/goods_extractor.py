# scripts/modules/extractors/goods_extractor.py
"""
货物提取器（智能路由）- 重写版

【核心修复】
✅ 先检测details（无表头固定格式）
✅ 再检测total（不规范格式）
✅ details优先级更高（因为格式更规整）
"""

from typing import Dict, Any, List
from .goods_details_extractor import GoodsDetailsExtractor, GoodsDetail
from .goods_total_extractor import GoodsTotalExtractor, GoodsTotal


class GoodsExtractor:
    """货物提取器（智能路由）- 重写版"""
    
    def __init__(self, logger=None, llm_client=None, enable_llm=True):
        self.logger = logger
        
        # 初始化两个子提取器
        self.details_extractor = GoodsDetailsExtractor(logger, llm_client, enable_llm)
        self.total_extractor = GoodsTotalExtractor(logger, llm_client, enable_llm)
    
    def extract(self, sheet, **kwargs) -> Dict[str, Any]:
        """
        提取货物信息
        
        ✅ 修改：Details优先（因为无表头固定格式更容易识别）
        
        Returns:
            {
                'type': 'details' | 'total' | None,
                'goods_details': List[GoodsDetail] | None,
                'goods_total': List[GoodsTotal] | None
            }
        """
        if self.logger:
            self.logger.debug(f"  🔍 检测货物格式...")
        
        # ✅ 1. 先尝试提取details（无表头固定格式，第1列是"新"/"旧"）
        goods_details = self.details_extractor.extract(sheet, **kwargs)
        
        if goods_details and len(goods_details) > 0:
            if self.logger:
                self.logger.info(f"  ✅ 检测为details格式，提取到{len(goods_details)}个货物")
            return {
                'type': 'details',
                'goods_details': goods_details,
                'goods_total': None
            }
        
        # ✅ 2. 如果没有details，再尝试提取total（不规范格式）
        goods_total_list = self.total_extractor.extract(sheet, **kwargs)
        
        # 过滤无效货物
        if goods_total_list:
            valid_goods = [
                g for g in goods_total_list 
                if g.货物名称 and g.货物名称 != "未提取"
            ]
            
            if valid_goods:
                if self.logger:
                    self.logger.info(f"  ✅ 检测为total格式，提取到{len(valid_goods)}个货物")
                return {
                    'type': 'total',
                    'goods_details': None,
                    'goods_total': valid_goods
                }
        
        # ✅ 3. 都没有
        if self.logger:
            self.logger.debug(f"  ⚠️  未检测到货物信息")
        
        return {
            'type': None,
            'goods_details': None,
            'goods_total': None
        }


__all__ = ['GoodsExtractor']