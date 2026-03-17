# scripts/modules/extractors/fee_item_extractor.py
"""
单价费用提取器 - 重写版

【提取规则】
1. 格式：XX元/kg、XX元/cbm
2. 没有标注 = 默认"海运费"
3. 数量从货物重量/体积来，不在这里提取

【数据库字段】
- 费用类型（不是费用名称！）
- 单价
- 单位（kg, cbm, KG, CBM）
- 币种
"""

import re
from typing import List, Optional
from dataclasses import dataclass, asdict

from .base_extractor import BaseExtractor


@dataclass
class FeeItem:
    """单价费用数据类"""
    费用类型: str = "海运费"  # 费用类型！不是费用名称！
    单价: Optional[float] = None
    单位: Optional[str] = None  # kg, cbm, KG, CBM
    数量: Optional[float] = None  # ✅ 新增：数量（从货物重量/体积来）
    币种: str = 'RMB'
    备注: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


class FeeItemExtractor(BaseExtractor):
    """单价费用提取器 - 重写版"""
    
    QUALITY_THRESHOLD = 0.4
    
    def __init__(self, logger=None, llm_client=None, enable_llm=True):
        super().__init__(logger, llm_client, enable_llm)
        
        # 币种映射
        self.currency_map = {
            'CNY': 'RMB', 'RMB': 'RMB', '￥': 'RMB', '¥': 'RMB', '元': 'RMB',
            'USD': 'USD', '$': 'USD',
            'EUR': 'EUR', '€': 'EUR',
            'GBP': 'GBP', '£': 'GBP',
            'MYR': 'MYR', 'RM': 'MYR',
            'SGD': 'SGD',  # ✅ 修复问题5：添加新加坡元
            'HKD': 'HKD',  # 港币
            'JPY': 'JPY',  # 日元
            'AUD': 'AUD',  # 澳元
            'CAD': 'CAD',  # 加元
        }
        
        # 费用类型关键词（向前查找）
        self.fee_type_keywords = [
            '海运', '空运', '快递', '运费', '集运',
            '附加费', '产品附加费', '燃油附加费',
            '清关费', '报关费', '操作费', '仓储费', '包装费',
            '派送费', '提货费', '卸货费', '拆箱费',
            # ✅ 修复问题1、3、4：添加更多费用类型
            'SIRIM费', 'SIRIM', '证件办理费', '证件费',
            '舱单费', '通关费', '通关手续费',
            '提派费', 'handlift费', 'hand lift费', 'handlift',
            '上楼费', '下楼费'
        ]
    
    def _extract_with_rules(self, sheet, agent_col_idx: int = None, **kwargs) -> List[FeeItem]:
        """
        规则提取
        
        ✅ 修改：只提取单价和单位，不提取数量
        """
        if not agent_col_idx:
            return []
        
        fee_items = []
        
        # 扫描该代理商列的所有行（前20行）
        max_scan_rows = min(30, sheet.max_row)
        
        for row_idx in range(1, max_scan_rows + 1):
            cell = sheet.cell(row=row_idx, column=agent_col_idx)
            if not cell.value:
                continue
            
            cell_text = str(cell.value).strip()
            
            # 提取该单元格中的所有单价费用
            items = self._extract_from_text(cell_text)
            
            if items:
                fee_items.extend(items)
                if self.logger:
                    self.logger.debug(f"      行{row_idx}提取{len(items)}个单价费用")
        
        if self.logger:
            self.logger.debug(f"    FeeItem共提取 {len(fee_items)} 个")
        
        return fee_items
    
    # 所有支持的单位
    _UNITS = r'(?:kg|KG|Kg|cbm|CBM|Cbm|吨|人|个|次|票|柜|天|小时|工作日|木箱|台|hawb|HAWB|entry|ENTRY|件)'

    # 所有支持的币种
    _CURRENCIES = r'(?:RMB|CNY|USD|EUR|GBP|MYR|SGD|HKD|JPY|AUD|CAD|￥|¥|元)'

    # 行内任意位置的"数字/单位"搜索模式（用于金额不在行首的情况）
    _PRICE_UNIT_SEARCH = None  # 延迟初始化

    def _get_price_unit_pattern(self):
        if self._PRICE_UNIT_SEARCH is None:
            type(self)._PRICE_UNIT_SEARCH = re.compile(
                r'(' + self._CURRENCIES + r')?\s*'
                r'(\d+(?:\.\d+)?)\s*(?:元)?\s*/\s*'
                r'(' + self._UNITS + r')',
                re.IGNORECASE
            )
        return self._PRICE_UNIT_SEARCH

    def _extract_from_text(self, text: str) -> List[FeeItem]:
        """
        从文本中提取所有单价费用（按行处理，支持跨行费用名）。

        支持格式：
          A. "人工费: USD180/人"        — 冒号分隔（含双冒号）
          B. "操作费 2.9/kg"            — 空格分隔
          C. "空运费：\n  DFW/USD2.9/kg" — 费用名在上一行，金额在下一行
          D. "USD25/kg" / "2.9/kg"      — 无名称，默认"运费"
        """
        exclude_keywords = ['赔付', '赔偿', '理赔', '不退运费', '不退', '退费']
        for kw in exclude_keywords:
            if kw in text:
                return []

        fee_items = []
        seen = set()
        pending_name = None  # 上一行留下的纯费用名（如"空运费："）

        for line in text.split('\n'):
            line = line.strip()
            if not line:
                pending_name = None
                continue

            item, new_pending = self._extract_from_line(line, seen, pending_name)
            if item:
                fee_items.append(item)
                pending_name = None
            else:
                pending_name = new_pending  # 可能是新的纯名称行，或 None

        return fee_items

    def _extract_from_line(self, line: str, seen: set, pending_name: str = None):
        """
        尝试从单行提取费用。

        返回 (FeeItem | None, pending_name | None)：
          - 成功提取：(FeeItem, None)
          - 本行只有费用名无金额：(None, 费用名)
          - 无法提取：(None, None)
        """
        units = self._UNITS
        currencies = self._CURRENCIES

        # ── 模式A：费用名 + 一个或多个冒号 + [币种] + 数字 + /单位
        # 例："人工费: USD180/人"  "安检费：: USD0.2/kg"
        pat_a = re.compile(
            r'^([^\d:：/\n]+?)'
            r'\s*[:：]+\s*'             # 一个或多个冒号（处理双冒号）
            r'(' + currencies + r')?\s*'
            r'(\d+(?:\.\d+)?)\s*(?:元)?\s*/\s*'
            r'(' + units + r')',
            re.IGNORECASE
        )

        # ── 模式B：费用名 + 空格 + [币种] + 数字 + /单位（无冒号）
        # 例："操作费 2.9/kg"
        pat_b = re.compile(
            r'^([^\d:：/\n]+?)\s+'
            r'(' + currencies + r')?\s*'
            r'(\d+(?:\.\d+)?)\s*(?:元)?\s*/\s*'
            r'(' + units + r')',
            re.IGNORECASE
        )

        # 尝试模式A和B（费用名在行首）
        for pat in (pat_a, pat_b):
            m = pat.match(line)
            if m:
                fee_name = self._clean_fee_name_simple(m.group(1)) or '运费'
                currency_str = m.group(2) or 'RMB'
                price = float(m.group(3))
                unit_raw = m.group(4)
                key = (price, unit_raw.lower())
                if key in seen:
                    return None, None
                seen.add(key)
                return FeeItem(
                    费用类型=fee_name,
                    单价=price,
                    币种=self._parse_currency(currency_str),
                    单位=self._fmt_unit(unit_raw),
                ), None

        # ── 模式C：行内任意位置搜索"[币种]数字/单位"
        # 例："DFW-CDG-SIN / AF / +100KG / USD2.9/kg"（金额在中间）
        pu = self._get_price_unit_pattern()
        m = pu.search(line)
        if m:
            currency_str = m.group(1) or 'RMB'
            price = float(m.group(2))
            unit_raw = m.group(3)
            key = (price, unit_raw.lower())
            if key in seen:
                return None, None
            seen.add(key)
            # 费用名优先用上一行传来的 pending_name
            if pending_name:
                fee_name = pending_name
            else:
                fee_name = self._infer_fee_name(line, m.start(2))
            return FeeItem(
                费用类型=fee_name,
                单价=price,
                币种=self._parse_currency(currency_str),
                单位=self._fmt_unit(unit_raw),
            ), None

        # ── 本行只有费用名，没有金额（如"空运费："）
        # 判断：以费用关键词或汉字结尾，末尾带冒号
        if re.search(r'[\u4e00-\u9fa5A-Za-z]+[:：]+\s*$', line):
            name = re.sub(r'[:：\s]+$', '', line).strip()
            name = self._clean_fee_name_simple(name)
            if name:
                return None, name

        return None, None

    def _clean_fee_name_simple(self, name: str) -> str:
        """清理费用名称：去掉多余标点和空白"""
        name = re.sub(r'[+&\-]', '', name)
        name = name.strip('.。,，;；: ')
        name = ' '.join(name.split())
        return name

    def _fmt_unit(self, unit_raw: str) -> str:
        """格式化单位：英文转小写，加斜杠前缀"""
        if unit_raw.upper() in ('KG', 'CBM'):
            return f'/{unit_raw.lower()}'
        return f'/{unit_raw}'

    def _infer_fee_name(self, line: str, num_start: int) -> str:
        """当行首没有明确名称时，在数字前的文字里推断费用类型"""
        prefix = line[:num_start].strip()
        prefix = re.sub(r'[A-Z]{3,4}', '', prefix, flags=re.IGNORECASE).strip()
        if not prefix:
            return '运费'
        for kw in self.fee_type_keywords:
            if kw in prefix:
                return kw if kw.endswith('费') else kw + '费'
        if any(ak in prefix.upper() for ak in ['BY', 'HK', 'CX', 'CA', 'MU', 'CZ']):
            return '空运费'
        return '运费'
    
    def _process_fee_match(self, fee_type_prefix: str, currency_str: str, price: float, 
                          unit_raw: str, text: str, match_start: int, fee_items: List[FeeItem]):
        """处理匹配到的费用"""
        # 识别币种
        currency = self._parse_currency(currency_str)
        
        # 识别费用类型
        fee_type = self._extract_fee_type(fee_type_prefix, text, match_start)
        
        # ✅ 修复问题3：根据单位推断费用类型
        # 如果识别为"运费"但单位是"/票"，很可能是派送费
        if fee_type == "运费" and unit_raw == '票':
            # 扩大范围查找"派送"
            context_large = text[max(0, match_start - 100):match_start]
            if '派送' in context_large:
                fee_type = '派送费'
        
        # ✅ 修复问题2：单位格式化
        # 英文单位（kg、cbm）转小写，中文单位（人、个、小时）保持原样
        if unit_raw.upper() in ['KG', 'CBM']:
            unit_formatted = f"/{unit_raw.lower()}"  # "/kg"、"/cbm"
        else:
            unit_formatted = f"/{unit_raw}"  # "/人"、"/个"、"/小时"
        
        fee_item = FeeItem(
            费用类型=fee_type,
            单价=price,
            币种=currency,
            单位=unit_formatted  # ✅ 使用格式化后的单位
        )
        
        fee_items.append(fee_item)
    
    def _extract_fee_type(self, prefix: str, full_text: str, match_start: int) -> str:
        """
        识别费用类型

        1. 先检查prefix中的明确费用名称（最高优先级）
        2. 向前查找context中的明确费用名称（仅限当前行）
        3. 检查航空公司缩写 → "空运费"（最后才用，优先级最低）
        4. 默认"运费"
        """
        # 找到当前行的起始位置，避免跨行污染（如"提货费"出现在上一行导致后续费用都被标为"提货费"）
        line_start = full_text.rfind('\n', 0, match_start)
        line_start = 0 if line_start == -1 else line_start + 1

        # ✅ 策略1：prefix有费用关键词（包括"操作费"等明确的费用）
        # 优先级最高，即使前面有航空公司缩写，也优先识别明确的费用名称
        if prefix:
            # ✅ 修复问题1：SIRIM费识别
            if 'SIRIM' in prefix.upper():
                return 'SIRIM费'
            
            # ✅ 修复问题3：舱单费识别
            if '舱单' in prefix:
                return '舱单费'
            
            # ✅ 修复问题4：通关费、提派费等识别
            if '通关手续费' in prefix:
                return '通关手续费'
            if '通关费' in prefix or '通关' in prefix:
                return '通关费'
            if '提派费' in prefix or '提派' in prefix:
                return '提派费'
            if 'handlift' in prefix.lower() or 'hand lift' in prefix.lower():
                return 'handlift费'
            if '上楼费' in prefix or '上楼' in prefix:
                return '上楼费'
            if '下楼费' in prefix or '下楼' in prefix:
                return '下楼费'
            
            # 先检查是否有完整的费用名称或关键词
            if '操作费' in prefix or '操作' in prefix:
                return '操作费'
            if '卸货费' in prefix or '卸货' in prefix:
                return '卸货费'
            if '拆包装费' in prefix or '拆包装' in prefix or '拆箱费' in prefix or '拆箱' in prefix:
                return '拆箱费'
            if '派送费' in prefix or '派送' in prefix:
                return '派送费'
            
            # 然后检查关键词
            for keyword in self.fee_type_keywords:
                if keyword in prefix:
                    # ✅ 修复：确保以"费"结尾
                    if not keyword.endswith('费'):
                        return keyword + '费'
                    return keyword
        
        # ✅ 策略2：向前查找（仅在当前行内查找，避免跨行污染）
        # 第一层：15个字符（避免匹配到前面的其他费用）
        start_near = max(line_start, match_start - 15)
        context_near = full_text[start_near:match_start]
        
        # ✅ 修复问题1、3、4：先在近距离查找新费用类型
        if 'SIRIM' in context_near.upper():
            return 'SIRIM费'
        if '舱单' in context_near:
            return '舱单费'
        if '通关手续费' in context_near:
            return '通关手续费'
        if '通关费' in context_near or '通关' in context_near:
            return '通关费'
        if '提派费' in context_near or '提派' in context_near:
            return '提派费'
        if 'handlift' in context_near.lower() or 'hand lift' in context_near.lower():
            return 'handlift费'
        if '上楼费' in context_near or '上楼' in context_near:
            return '上楼费'
        if '下楼费' in context_near or '下楼' in context_near:
            return '下楼费'
        
        # 先在近距离查找
        if '操作费' in context_near or '操作' in context_near:
            return '操作费'
        if '卸货费' in context_near or '卸货' in context_near:
            return '卸货费'
        if '拆包装费' in context_near or '拆包装' in context_near or '拆箱费' in context_near or '拆箱' in context_near:
            return '拆箱费'
        if '派送费' in context_near or '派送' in context_near:
            return '派送费'
        
        for keyword in self.fee_type_keywords:
            if keyword in context_near:
                if not keyword.endswith('费'):
                    return keyword + '费'
                return keyword
        
        # 第二层：扩大到行首（当前行全部文本）
        start_far = line_start
        context_far = full_text[start_far:match_start]
        
        # ✅ 修复问题1、3、4：检查所有费用类型（包括新增的）
        if 'SIRIM' in context_far.upper():
            return 'SIRIM费'
        if '舱单' in context_far:
            return '舱单费'
        if '通关手续费' in context_far:
            return '通关手续费'
        if '通关费' in context_far or '通关' in context_far:
            return '通关费'
        if '提派费' in context_far or '提派' in context_far:
            return '提派费'
        if 'handlift' in context_far.lower() or 'hand lift' in context_far.lower():
            return 'handlift费'
        if '上楼费' in context_far or '上楼' in context_far:
            return '上楼费'
        if '下楼费' in context_far or '下楼' in context_far:
            return '下楼费'
        
        # 检查所有费用类型（不仅仅是"操作"）
        if '操作费' in context_far or '操作' in context_far:
            return '操作费'
        if '卸货费' in context_far or '卸货' in context_far:
            return '卸货费'
        if '拆包装费' in context_far or '拆包装' in context_far or '拆箱费' in context_far or '拆箱' in context_far:
            return '拆箱费'
        if '派送费' in context_far or '派送' in context_far:
            return '派送费'
        if '提货费' in context_far or '提货' in context_far:
            return '提货费'
        if '清关费' in context_far or '清关' in context_far:
            return '清关费'
        if '报关费' in context_far or '报关' in context_far:
            return '报关费'
        
        for keyword in self.fee_type_keywords:
            if keyword in context_far:
                if not keyword.endswith('费'):
                    return keyword + '费'
                return keyword
        
        # ✅ 策略3（修复问题4）：检查航空公司缩写（优先级降低，放到最后）
        # 只有在prefix和context中都没有明确费用名称时，才根据航空公司推断为"空运费"
        airline_keywords = ['BY', 'HK', 'CX', 'SIN', 'CA', 'MU', 'HU', 'CZ', 'FM', 'ZH']
        context_before = full_text[line_start:match_start]
        
        for airline in airline_keywords:
            if airline in context_before.upper():
                return "空运费"
        
        # ✅ 策略4：默认改为"运费"（不再默认"海运费"）
        return "运费"
    
    def _parse_currency(self, currency_str: str) -> str:
        """解析币种"""
        if not currency_str:
            return 'RMB'
        
        currency_str = currency_str.strip().upper()
        return self.currency_map.get(currency_str, 'RMB')
    
    # ========== BaseExtractor 必需方法 ==========
    
    def _evaluate_quality(self, result: List[FeeItem], sheet, **kwargs) -> float:
        if not result or len(result) == 0:
            return 0.0
        
        score = 0.5
        has_price = sum(1 for f in result if f.单价) / len(result)
        score += has_price * 0.5
        
        return score
    
    def _build_enhancement_prompt(self, result, sheet, **kwargs) -> str:
        """构建Fee Item增强的prompt"""
        import json
        
        # 获取sheet文本
        sheet_text = self._serialize_sheet(sheet, max_rows=30)  # 减少行数避免prompt太长
        
        # 获取规则提取的结果
        fee_items_data = []
        if result and isinstance(result, list):
            for item in result:
                if hasattr(item, 'to_dict'):
                    fee_items_data.append(item.to_dict())
        
        prompt = f"""请验证和补充以下单价费用的提取结果。

【原始Excel内容】
{sheet_text}

【规则提取结果】
{json.dumps(fee_items_data, ensure_ascii=False, indent=2)}

【任务】
1. 验证提取结果是否正确
2. 补充缺失的费用项
3. 修正错误的字段

【提取规则】
单价费用格式：xx元/kg、xx元/cbm、xx元/票等
例如：
- "海运费：25.5元/kg"
- "报关费：300元/票"
- "THC：1200/柜"

【提取字段】
1. 费用类型: 如"海运费"、"报关费"、"THC"
2. 单价: 数字，如25.5
3. 单位: 如"kg"、"cbm"、"票"、"柜"
4. 币种: RMB/USD/EUR等

【返回格式】（严格JSON数组，不要其他文字）
[
  {{{{
    "费用类型": "...",
    "单价": ...,
    "单位": "...",
    "币种": "..."
  }}}}
]

注意：
- 如果没有找到费用，返回空数组 []
- 单价必须是数字，不是字符串
- 只提取单价费用，不提取整单费用
"""
        
        return prompt
    
    def _merge_results(self, rule_result: List[FeeItem], llm_result) -> List[FeeItem]:
        """合并规则和LLM结果"""
        # 如果LLM结果为空，返回规则结果
        if not llm_result:
            return rule_result
        
        # 如果LLM结果是列表
        if isinstance(llm_result, list):
            # 将LLM结果转换为FeeItem对象
            llm_fees = []
            for item in llm_result:
                if isinstance(item, dict):
                    fee = FeeItem()
                    fee.费用类型 = item.get('费用类型')
                    fee.单价 = item.get('单价')
                    fee.单位 = item.get('单位')
                    fee.币种 = item.get('币种')
                    
                    # 只添加有效的fee
                    if fee.费用类型 or fee.单价:
                        llm_fees.append(fee)
            
            # 合并：规则结果 + LLM新增的结果
            all_fees = list(rule_result) if rule_result else []
            
            # 去重：避免重复添加
            existing_types = {f.费用类型 for f in all_fees if f.费用类型}
            for llm_fee in llm_fees:
                if llm_fee.费用类型 and llm_fee.费用类型 not in existing_types:
                    all_fees.append(llm_fee)
                    existing_types.add(llm_fee.费用类型)
            
            if self.logger and len(llm_fees) > 0:
                self.logger.info(f"      ✅ LLM新增{len(llm_fees)}个费用项")
            elif self.logger:
                self.logger.info(f"      ⚠️  LLM未新增费用项")
            
            return all_fees
        
        # 其他情况返回规则结果
        return rule_result
    
    def _extract_with_llm(self, sheet, **kwargs) -> List[FeeItem]:
        return []
    
    def _is_valid(self, result: List[FeeItem]) -> bool:
        return result and len(result) > 0
    
    def _get_default(self) -> List[FeeItem]:
        return []


__all__ = ['FeeItemExtractor', 'FeeItem']