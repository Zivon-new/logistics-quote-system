# scripts/modules/extractors/goods_details_extractor.py
"""
货物明细提取器 - 重写版

【核心功能】
✅ 支持无表头固定格式（第1列是"新"/"旧"）
✅ 支持标准表头格式
✅ 按固定列位置提取数据
✅ 绝对的正确率
"""

import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

from .base_extractor import BaseExtractor


@dataclass
class GoodsDetail:
    """货物明细数据类"""
    货物名称: Optional[str] = None
    是否新品: int = 0
    货物种类: Optional[str] = None
    数量: Optional[float] = None
    单价: Optional[float] = None
    币种: str = 'RMB'
    重量: Optional[float] = None
    总重量: Optional[float] = None
    总价: Optional[float] = None
    备注: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


class GoodsDetailsExtractor(BaseExtractor):
    """货物明细提取器（重写版）"""
    
    QUALITY_THRESHOLD = 0.5
    
    def __init__(self, logger=None, llm_client=None, enable_llm=True):
        super().__init__(logger, llm_client, enable_llm)
        
        # 标准表头关键词
        self.header_keywords = {
            '是否新品': ['新', '旧', '新旧', '状态'],
            '货物种类': ['品类', '类别', '种类', '分类'],
            '货物名称': ['品名', '货物名称', '产品名称', '名称', '货物', '产品'],
            '数量': ['数量', '件数', '个数'],
            '单价': ['单价', '价格'],
            '总价': ['总价', '金额', '总金额'],
            '重量': ['实际重量', '单重', '重量'],
            '总重量': ['计费重量', '总重', '总重量'],
        }
        
        self.currency_map = {
            '￥': 'RMB', '¥': 'RMB', '元': 'RMB', 'RMB': 'RMB', 'CNY': 'RMB',
            '$': 'USD', 'USD': 'USD',
            '€': 'EUR', 'EUR': 'EUR',
            '£': 'GBP', 'GBP': 'GBP',
            'SGD': 'SGD', 'MYR': 'MYR', 'HKD': 'HKD',
        }
    
    def _extract_with_rules(self, sheet, **kwargs) -> List[GoodsDetail]:
        """
        规则提取
        
        ✅ 策略1：检测无表头固定格式（优先）
        ✅ 策略2：查找标准表头
        """
        # ✅ 策略1：检测无表头固定格式（第1列是"新"/"旧"）
        start_row = self._detect_headerless_table(sheet)
        if start_row:
            if self.logger:
                self.logger.info(f"  ✅ 检测到无表头固定格式，起始行{start_row}")
            goods_list = self._extract_headerless_data(sheet, start_row)
            if goods_list:
                if self.logger:
                    self.logger.info(f"  📦 提取到 {len(goods_list)} 个货物明细")
                return goods_list
        
        # ✅ 策略2：查找标准表头
        header_row_idx, header_map = self._find_standard_header(sheet)
        if header_row_idx and header_map:
            if self.logger:
                self.logger.info(f"  ✅ 找到标准表头: 行{header_row_idx}")
            goods_list = self._extract_data_rows(sheet, header_row_idx, header_map)
            if goods_list:
                if self.logger:
                    self.logger.info(f"  📦 提取到 {len(goods_list)} 个货物明细")
                return goods_list
        
        if self.logger:
            self.logger.debug("  ⚠️  未找到货物明细表格")
        return []
    
    def _detect_headerless_table(self, sheet) -> Optional[int]:
        """
        检测无表头的固定格式表格
        
        特征：
        - 第3列（C列）是"新"或"旧"  ✅ 修复：检测C列
        - 至少有8列
        
        Returns:
            数据起始行号，如果没找到返回None
        """
        max_scan_rows = min(20, sheet.max_row)
        
        for row_idx in range(1, max_scan_rows + 1):
            # ✅ 修复：检查第3列（C列）是否是"新"/"旧"
            third_col = self._get_cell_value(sheet, row_idx, 3)
            
            # 第3列必须是"新"或"旧"
            if third_col and third_col.strip() in ['新', '旧']:
                # 检查列数（至少8列）
                col_count = self._count_non_empty_columns(sheet, row_idx)
                if col_count >= 8:
                    if self.logger:
                        self.logger.debug(f"    无表头表格检测成功：行{row_idx}，{col_count}列，第3列={third_col}")
                    return row_idx
        
        return None
    
    def _extract_headerless_data(self, sheet, start_row: int) -> List[GoodsDetail]:
        """
        按固定列位置提取无表头数据
        
        ✅ 修复后的列位置（基于实际Excel）：
        1. 第1列（A）：跳过（可能为空）
        2. 第2列（B）：库房信息（跳过）
        3. 第3列（C）：新/旧（是否新品）
        4. 第4列（D）：货物种类
        5. 第5列（E）：货物名称（已包含型号）
        6. 第6列（F）：数量 ✅
        7. 第7列（G）：单价 ✅
        8. 第8列（H）：总价 ✅
        9. 第9列（I）：单重 ✅
        10. 第10列（J）：总重 ✅
        """
        goods_list = []
        
        for row_idx in range(start_row, sheet.max_row + 1):
            # ✅ 检查第3列（C列）是否是"新"/"旧"
            third_col = self._get_cell_value(sheet, row_idx, 3)
            
            # 如果第3列不是"新"/"旧"，跳过或结束
            if not third_col or third_col.strip() not in ['新', '旧']:
                # 连续3行都不是，就结束
                if row_idx - start_row > 2:
                    break
                continue
            
            goods = GoodsDetail()
            
            # ✅ 第3列（C）：是否新品
            goods.是否新品 = 1 if third_col.strip() == '新' else 0
            
            # ✅ 第4列（D）：货物种类
            goods.货物种类 = self._get_cell_value(sheet, row_idx, 4)
            
            # ✅ 第5列（E）：货物名称（已包含型号，不需要再合并）
            goods.货物名称 = self._get_cell_value(sheet, row_idx, 5)
            
            # 如果没有货物名称，跳过
            if not goods.货物名称:
                continue
            
            # ✅ 第6列（F）：数量
            goods.数量 = self._extract_number(sheet, row_idx, 6)
            
            # ✅ 第7列（G）：单价
            price, currency = self._extract_price_with_currency(sheet, row_idx, 7)
            goods.单价 = price
            if currency:
                goods.币种 = currency
            
            # ✅ 第8列（H）：总价
            goods.总价 = self._extract_number(sheet, row_idx, 8)
            
            # ✅ 第9列（I）：单重
            goods.重量 = self._extract_number(sheet, row_idx, 9)
            
            # ✅ 第10列（J）：总重
            goods.总重量 = self._extract_number(sheet, row_idx, 10)
            
            # 如果有数量和单重但没有总重，计算总重
            if goods.数量 and goods.重量 and not goods.总重量:
                goods.总重量 = round(goods.数量 * goods.重量, 2)
            
            # ✅ 验证数据有效性
            if self._is_valid_goods(goods):
                goods_list.append(goods)
                if self.logger:
                    self.logger.debug(f"    行{row_idx}: {goods.货物名称} x {goods.数量}")
        
        return goods_list
    
    def _find_standard_header(self, sheet) -> tuple:
        """
        查找标准表头
        
        必须有明确的"品名"、"数量"等关键词
        """
        max_row = min(30, sheet.max_row)
        
        for row_idx in range(1, max_row + 1):
            row_values = []
            for col_idx in range(1, min(20, sheet.max_column + 1)):
                cell = sheet.cell(row=row_idx, column=col_idx)
                if cell.value:
                    row_values.append((col_idx, str(cell.value).strip()))
            
            header_map = self._match_headers(row_values)
            
            # 严格要求：必须有货物名称 + 数量
            has_name = '货物名称' in header_map
            has_quantity = '数量' in header_map
            
            if has_name and has_quantity:
                return row_idx, header_map
        
        return None, {}
    
    def _match_headers(self, row_values: List[tuple]) -> Dict[str, int]:
        """匹配标准表头"""
        header_map = {}
        
        for col_idx, cell_value in row_values:
            cell_value_clean = cell_value.lower().strip()
            
            for field_name, keywords in self.header_keywords.items():
                if field_name in header_map:
                    continue
                
                for keyword in keywords:
                    if keyword.lower() in cell_value_clean:
                        header_map[field_name] = col_idx
                        break
        
        return header_map
    
    def _extract_data_rows(self, sheet, header_row_idx: int, header_map: Dict[str, int]) -> List[GoodsDetail]:
        """提取数据行（标准表头模式）"""
        goods_list = []
        
        start_row = header_row_idx + 1
        max_row = min(start_row + 100, sheet.max_row + 1)
        
        for row_idx in range(start_row, max_row):
            goods = self._extract_single_row(sheet, row_idx, header_map)
            
            if goods and goods.货物名称:
                if self._is_valid_goods(goods):
                    goods_list.append(goods)
            elif self._is_empty_row(sheet, row_idx):
                break
        
        return goods_list
    
    def _extract_single_row(self, sheet, row_idx: int, header_map: Dict[str, int]) -> Optional[GoodsDetail]:
        """提取单行（标准表头模式）"""
        goods = GoodsDetail()
        
        # 是否新品
        if '是否新品' in header_map:
            col_idx = header_map['是否新品']
            cell_value = self._get_cell_value(sheet, row_idx, col_idx)
            goods.是否新品 = 1 if cell_value and '新' in cell_value else 0
        
        # 货物种类
        if '货物种类' in header_map:
            col_idx = header_map['货物种类']
            goods.货物种类 = self._get_cell_value(sheet, row_idx, col_idx)
        
        # 货物名称
        if '货物名称' in header_map:
            col_idx = header_map['货物名称']
            goods.货物名称 = self._get_cell_value(sheet, row_idx, col_idx)
        
        if not goods.货物名称 and goods.货物种类:
            goods.货物名称 = goods.货物种类
        
        if not goods.货物名称:
            return None
        
        # 数量
        if '数量' in header_map:
            col_idx = header_map['数量']
            goods.数量 = self._extract_number(sheet, row_idx, col_idx)
        
        # 单价
        if '单价' in header_map:
            col_idx = header_map['单价']
            price, currency = self._extract_price_with_currency(sheet, row_idx, col_idx)
            goods.单价 = price
            if currency:
                goods.币种 = currency
        
        # 总价
        if '总价' in header_map:
            col_idx = header_map['总价']
            goods.总价 = self._extract_number(sheet, row_idx, col_idx)
        
        # 重量
        if '重量' in header_map:
            col_idx = header_map['重量']
            goods.重量 = self._extract_number(sheet, row_idx, col_idx)
        
        # 总重量
        if '总重量' in header_map:
            col_idx = header_map['总重量']
            goods.总重量 = self._extract_number(sheet, row_idx, col_idx)
        
        # 计算总重量
        if goods.数量 and goods.重量 and not goods.总重量:
            goods.总重量 = round(goods.数量 * goods.重量, 2)
        
        return goods
    
    def _is_valid_goods(self, goods: GoodsDetail) -> bool:
        """
        验证货物是否有效
        
        过滤规则：
        1. 必须有货物名称和数量
        2. 货物名称不能太长（>100字符）
        3. 货物名称不能包含无效关键词
        """
        if not goods.货物名称:
            return False
        
        if not goods.数量:
            return False
        
        # 长度限制
        if len(goods.货物名称) > 100:
            if self.logger:
                self.logger.debug(f"    过滤：货物名称太长 {goods.货物名称[:20]}...")
            return False
        
        # 无效关键词
        invalid_keywords = [
            '按', '合计', '小计', '总计', '不含', '尾端', '派送',
            '提货费', '保险费', '包装费', '存储费', '卡车', '停车费',
            '实报实销', '天左右', '受天气', '晚开船', '查验', '赔付',
            '时效', '专线', '运费', '操作费', '物流费', '仓储费',
            '代理', '协议', '合作', '费用', '明细',
            '物流', '指定', '地址', '库房', '机房'  # ✅ 新增
        ]
        
        for keyword in invalid_keywords:
            if keyword in goods.货物名称:
                if self.logger:
                    self.logger.debug(f"    过滤：包含无效关键词'{keyword}' {goods.货物名称[:20]}...")
                return False
        
        return True
    
    def _count_non_empty_columns(self, sheet, row_idx: int) -> int:
        """统计非空列数"""
        count = 0
        for col_idx in range(1, min(20, sheet.max_column + 1)):
            cell = sheet.cell(row=row_idx, column=col_idx)
            if cell.value:
                count += 1
        return count
    
    def _get_cell_value(self, sheet, row_idx: int, col_idx: int) -> Optional[str]:
        """获取单元格值"""
        try:
            cell = sheet.cell(row=row_idx, column=col_idx)
            if cell.value:
                return str(cell.value).strip()
        except:
            pass
        return None
    
    def _extract_number(self, sheet, row_idx: int, col_idx: int) -> Optional[float]:
        """提取数字"""
        cell_value = self._get_cell_value(sheet, row_idx, col_idx)
        if not cell_value:
            return None
        
        # 移除货币符号、逗号、空格
        cleaned = re.sub(r'[￥$€£,，\s¥]', '', cell_value)
        
        try:
            return float(cleaned)
        except:
            return None
    
    def _extract_price_with_currency(self, sheet, row_idx: int, col_idx: int) -> tuple:
        """提取价格和币种"""
        cell_value = self._get_cell_value(sheet, row_idx, col_idx)
        if not cell_value:
            return None, None
        
        # 检测币种
        currency = 'RMB'
        for symbol, curr in self.currency_map.items():
            if symbol in cell_value:
                currency = curr
                break
        
        price = self._extract_number(sheet, row_idx, col_idx)
        
        return price, currency
    
    def _is_empty_row(self, sheet, row_idx: int) -> bool:
        """判断是否为空行"""
        for col_idx in range(1, min(20, sheet.max_column + 1)):
            cell = sheet.cell(row=row_idx, column=col_idx)
            if cell.value:
                return False
        return True
    
    # ========== BaseExtractor 必需方法 ==========
    
    def _evaluate_quality(self, result: List[GoodsDetail], sheet, **kwargs) -> float:
        if not result or len(result) == 0:
            return 0.0
        
        score = 0.4
        has_name = sum(1 for g in result if g.货物名称) / len(result)
        score += has_name * 0.2
        has_quantity = sum(1 for g in result if g.数量) / len(result)
        score += has_quantity * 0.2
        has_price = sum(1 for g in result if g.单价 or g.总价) / len(result)
        score += has_price * 0.2
        
        return score
    
    def _build_enhancement_prompt(self, result: List[GoodsDetail], sheet, **kwargs) -> str:
        return ""
    
    def _merge_results(self, rule_result: List[GoodsDetail], llm_result) -> List[GoodsDetail]:
        return rule_result
    
    def _extract_with_llm(self, sheet, **kwargs) -> List[GoodsDetail]:
        return []
    
    def _is_valid(self, result: List[GoodsDetail]) -> bool:
        return result and len(result) > 0
    
    def _get_default(self) -> List[GoodsDetail]:
        return []


__all__ = ['GoodsDetailsExtractor', 'GoodsDetail']