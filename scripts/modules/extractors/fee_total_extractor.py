# scripts/modules/extractors/fee_total_extractor.py
"""
整单费用提取器 - 按行处理版

【核心修复】
1. ✅ 按行处理，避免跨行匹配导致金额错配
2. ✅ 识别+号格式（"+ 验电RMB 500"、"+申报税200"）
3. ✅ 处理一行多个费用（"报关费RMB 300 +申报税200"）
4. ⏸️ MIN格式暂时不处理
"""

import re
from typing import List, Optional, Set
from dataclasses import dataclass, asdict

from .base_extractor import BaseExtractor


@dataclass
class FeeTotal:
    """整单费用数据类"""
    费用名称: Optional[str] = None
    原币金额: Optional[float] = None
    币种: str = 'RMB'
    备注: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


class FeeTotalExtractor(BaseExtractor):
    """整单费用提取器 - 按行处理版"""
    
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
            'SGD': 'SGD',
            'HKD': 'HKD',
            'JPY': 'JPY',
            'AUD': 'AUD',
            'CAD': 'CAD',
        }
        
        # 费用名称关键词（长关键词优先）
        self.fee_keywords = [
            # 长关键词优先
            '卸货上楼并拆清费用', '卸货上楼费用', '卸货拆清费用',
            '拆包装和回收垃圾费', '拆包装回收垃圾费',
            '拆箱丢垃圾费', '拆箱垃圾费', '交会展费',
            '人工卸货费', '卸货上楼费',
            '国内报关费', '国外清关费', '出口清关费', '目的港清关费',
            '代理税金操作费', '税金操作费',
            '验电费', '申报税费', '报税费',
            # 常规关键词
            '操作费', '派送费', '包装费', '提货费', '仓储费',
            '木箱费', '报关费', '清关费', '关税', '增值税',
            '保险费', '检验费', '拖车费', '换单费', '文件费',
            '查验费', '滞箱费', '超期费', '附加费', '服务费',
            '卸货费', '拆箱费', '装箱费', '超长费', '超重费',
            '尾板费', '待时费', '转运费', '上楼费', '下楼费',
            '送货费', '卡车费', 'UPS快递费', '贸易代理费',
            '出入库费', '手续费', '通关费', 'SIRIM费',
            'handlift费', '舱单费',
            '扔垃圾费', '丢垃圾费', '垃圾费',
            '会展费', '展会费',
            '卸货上楼', '卸货拆清', '交会展',
            '拆箱丢垃圾', '拆包装和回收垃圾',
            '验电', '申报税', '报税',
            '人工', '卸货'
        ]
    
    def _extract_with_rules(self, sheet, agent_col_idx: int = None, **kwargs) -> List[FeeTotal]:
        """规则提取"""
        if not agent_col_idx:
            return []
        
        fee_totals = []
        max_scan_rows = min(20, sheet.max_row)
        
        for row_idx in range(1, max_scan_rows + 1):
            cell = sheet.cell(row=row_idx, column=agent_col_idx)
            if not cell.value:
                continue
            
            cell_text = str(cell.value).strip()
            
            if len(cell_text) < 3:
                continue
            
            if self.logger:
                self.logger.debug(f"      扫描行{row_idx}: {cell_text[:80]}...")
            
            # 提取该单元格中的所有整单费用
            totals = self._extract_from_text(cell_text)
            
            if totals:
                fee_totals.extend(totals)
                if self.logger:
                    self.logger.debug(f"      提取{len(totals)}个整单费用")
        
        if self.logger:
            self.logger.debug(f"    FeeTotal共提取 {len(fee_totals)} 个")
        
        return fee_totals
    
    def _extract_from_text(self, text: str) -> List[FeeTotal]:
        """
        从文本中提取所有整单费用
        
        ✅ 关键修复：按行处理，避免跨行匹配导致金额错配
        """
        # 排除赔付相关内容
        exclude_keywords = [
            '赔偿', '赔付', '理赔', 
            '不退运费', '不退', '退费',
            '丢失按', '未购买保险',
            '仅对丢失', '赔偿开退',
            '按运费', '丢失'
        ]
        
        for keyword in exclude_keywords:
            if keyword in text:
                return []
        
        # 移除条件性描述
        conditional_keywords = ['如需', '如果', '若需要', '如要', '若要']
        for keyword in conditional_keywords:
            text = re.sub(keyword + r'[^\n。；]*', '', text)
        
        # 预处理：移除单价部分
        text = self._preprocess_mixed_text(text)
        
        # ✅ 关键修复：按行处理
        lines = text.split('\n')
        
        fee_totals = []
        extracted_fees: Set[tuple] = set()
        
        for line in lines:
            line = line.strip()
            if len(line) < 3:
                continue
            
            if self.logger:
                self.logger.debug(f"        处理行: {line[:60]}...")
            
            # 从当前行提取费用
            line_totals = self._extract_from_line(line, extracted_fees)
            
            fee_totals.extend(line_totals)
        
        return fee_totals
    
    # 任意单位的行级别快速检测正则（数字后紧跟斜杠+单位词）
    _LINE_UNIT_PATTERN = re.compile(
        r'\d+(?:\.\d+)?(?:[A-Z]{3,4})?\s*/\s*'
        r'(?:kg|KG|Kg|cbm|CBM|Cbm|吨|方|立方|m3|M3|票|个|件|场|次|箱|台|批|组|套|块|条|张|份|趟|pcs|PCS|set|SET|人)',
        re.IGNORECASE
    )

    def _extract_from_line(self, line: str, extracted_fees: Set[tuple]) -> List[FeeTotal]:
        """
        从单行文本中提取费用

        规则：带单位（/票、/个、/kg 等）的行属于费用明细，整行跳过；
        没有单位的才是整单费用。
        """
        # 行级别判断：只要行内出现"数字/单位"就整行跳过
        if self._LINE_UNIT_PATTERN.search(line):
            return []

        line_totals = []
        
        # ✅ Pattern1: "XX费：数字 币种"（币种在数字后面，有空格）
        pattern1 = re.compile(
            r'([^\d\s]+费)\s*[:：]?\s*'
            r'(\d+(?:\.\d+)?)\s+'
            r'([A-Z]{3,4}|RMB|CNY|USD|EUR|GBP|MYR|SGD|HKD|JPY)',
            re.IGNORECASE
        )
        
        for match in pattern1.finditer(line):
            result = self._process_pattern1(match, line, extracted_fees)
            if result:
                line_totals.append(result)
        
        # ✅ Pattern2: "XX费：币种数字" 或 "XX费：数字"（有冒号）
        # 修复：排除大写字母，避免匹配到"操作费RMB"
        pattern2 = re.compile(
            r'([^\d\s:：A-Z]+)\s*[:：]\s*'  # ← 关键修复：排除A-Z
            r'([A-Z]{3,4}|RMB|CNY|USD|EUR|GBP|MYR|SGD|HKD|JPY|￥|¥|\$|€|£)?\s*'
            r'(\d+(?:\.\d+)?)'
            r'(?:\s*元)?',
            re.IGNORECASE
        )
        
        for match in pattern2.finditer(line):
            result = self._process_pattern2(match, line, extracted_fees)
            if result:
                line_totals.append(result)
        
        # ✅ Pattern_abbr: 全大写缩写费用名，如 "THC: USD180" / "LCL: USD50"
        pattern_abbr = re.compile(
            r'\b([A-Z]{2,6})\s*[:：]\s*'           # 全大写缩写（2-6字符）+ 冒号
            r'([A-Z]{3,4}|USD|EUR|SGD|GBP|RMB)\s*'  # 币种
            r'(\d+(?:\.\d+)?)',                     # 数字
            re.IGNORECASE
        )
        for match in pattern_abbr.finditer(line):
            keyword = match.group(1).upper()
            # 跳过纯货币词（USD/EUR等自身被误匹配为费用名）
            if keyword in ('USD', 'EUR', 'SGD', 'GBP', 'RMB', 'CNY', 'HKD', 'JPY'):
                continue
            # 跳过 "min"（最低收费描述）
            if keyword.lower() == 'min':
                continue
            currency_str = match.group(2)
            amount = float(match.group(3))
            if amount <= 0:
                continue
            match_end = match.end()
            next_chars = line[match_end:match_end + 5] if match_end < len(line) else ''
            if self._is_any_unit_slash(next_chars) or '%' in next_chars:
                continue
            fee_key = (keyword, amount, currency_str.upper())
            if fee_key in extracted_fees:
                continue
            extracted_fees.add(fee_key)
            currency = self._parse_currency(currency_str)
            line_totals.append(FeeTotal(费用名称=keyword, 原币金额=amount, 币种=currency))

        # ✅ Pattern5（新增）: "XX费币种数字"（紧贴，无冒号，无空格）
        # 例如："操作费RMB200"、"报关费RMB300"
        pattern5 = re.compile(
            r'([^\d\s:：]+?)\s*'  # 费用关键词（非贪婪）
            r'([A-Z]{3,4}|RMB|CNY|USD|EUR|GBP|MYR|SGD|HKD|JPY)\s*'  # 币种
            r'(\d+(?:\.\d+)?)',  # 数字
            re.IGNORECASE
        )
        
        for match in pattern5.finditer(line):
            result = self._process_pattern5(match, line, extracted_fees)
            if result:
                line_totals.append(result)
        
        # ✅ Pattern6（新增）: "XX费 币种数字"（空格分隔，无冒号）
        # 例如："报关费 SGD100"、"人工&卸货 SGD 180"
        pattern6 = re.compile(
            r'([^\d\s:：]+)\s+'  # 费用关键词 + 至少一个空格
            r'([A-Z]{3,4}|RMB|CNY|USD|EUR|GBP|MYR|SGD|HKD|JPY)\s*'  # 币种
            r'(\d+(?:\.\d+)?)',  # 数字
            re.IGNORECASE
        )
        
        for match in pattern6.finditer(line):
            result = self._process_pattern6(match, line, extracted_fees)
            if result:
                line_totals.append(result)
        
        # ✅ Pattern3: "币种数字XX费"（数字在前）
        pattern3 = re.compile(
            r'([A-Z]{3,4}|RMB|CNY|USD|EUR|GBP|MYR|SGD|HKD|JPY)?\s*'
            r'(\d+(?:\.\d+)?)\s*'
            r'(?:元)?\s*'
            r'([^\d\s/+,，。；：]{2,})',
            re.IGNORECASE
        )
        
        for match in pattern3.finditer(line):
            result = self._process_pattern3(match, line, extracted_fees)
            if result:
                line_totals.append(result)
        
        # ✅ Pattern4: "+XX费币种数字"（+号开头）
        pattern_plus = re.compile(
            r'\+\s*([^\d\s]+?)\s*'
            r'([A-Z]{3,4}|RMB|CNY|USD|EUR|GBP|MYR|SGD|HKD|JPY)?\s*'
            r'(\d+(?:\.\d+)?)',
            re.IGNORECASE
        )
        
        for match in pattern_plus.finditer(line):
            result = self._process_pattern_plus(match, line, extracted_fees)
            if result:
                line_totals.append(result)
        
        return line_totals
    
    def _process_pattern1(self, match, line: str, extracted_fees: Set[tuple]) -> Optional[FeeTotal]:
        """处理Pattern1: XX费：数字 币种"""
        fee_name = match.group(1).strip()
        amount = float(match.group(2))
        currency_str = match.group(3)
        
        # 检查后面是否有斜杠或百分号
        match_end = match.end()
        if match_end < len(line):
            next_chars = line[match_end:match_end+3]
            if self._is_any_unit_slash(next_chars) or '%' in next_chars:
                return None
        
        # ✅ 关键修复：检查是否是时效（数字后面有"-"或"天"）
        # 例如："包装需要2-3天" → "2"后面有"-"，这是时效，不是费用
        if match_end < len(line):
            next_chars = line[match_end:match_end+5]
            if re.match(r'^[\s\-—]*\d+[\s]*天', next_chars):
                if self.logger:
                    self.logger.debug(f"          跳过P1（时效）: {fee_name} {amount}")
                return None
        
        fee_name = self._clean_fee_name(fee_name)
        
        if not self._is_valid_fee_name(fee_name):
            return None
        
        if amount <= 0:
            return None
        
        currency = self._parse_currency(currency_str)
        
        fee_key = (fee_name, amount, currency)
        if fee_key in extracted_fees:
            return None
        extracted_fees.add(fee_key)
        
        if self.logger:
            self.logger.debug(f"          提取(P1): {fee_name} {amount} {currency}")
        
        return FeeTotal(费用名称=fee_name, 原币金额=amount, 币种=currency)
    
    def _process_pattern2(self, match, line: str, extracted_fees: Set[tuple]) -> Optional[FeeTotal]:
        """处理Pattern2: XX费：币种数字"""
        keyword = match.group(1).strip()
        currency_str = match.group(2) or 'RMB'
        amount = float(match.group(3))
        
        # 检查后面是否有斜杠或百分号
        match_end = match.end()
        if match_end < len(line):
            next_chars = line[match_end:match_end+3]
            if self._is_any_unit_slash(next_chars) or '%' in next_chars:
                return None
        
        # ✅ 关键修复：检查是否是时效（数字后面有"-"或"天"）
        if match_end < len(line):
            next_chars = line[match_end:match_end+5]
            if re.match(r'^[\s\-—]*\d+[\s]*天', next_chars):
                if self.logger:
                    self.logger.debug(f"          跳过P2（时效）: {keyword} {amount}")
                return None
        
        # ✅ 关键修复：如果后面有空格+币种，说明应该由Pattern1处理
        # 例如："代理税金操作费：65 SGD"
        # Pattern2匹配到"65"，但后面还有" SGD"
        # 这种情况应该由Pattern1处理（因为Pattern1要求数字和币种之间有空格）
        if match_end < len(line):
            next_chars = line[match_end:match_end+10]
            # 检查是否有空格+币种
            if re.search(r'\s+([A-Z]{3,4}|RMB|CNY|USD|EUR|GBP|MYR|SGD|HKD|JPY)', 
                        next_chars, re.IGNORECASE):
                if self.logger:
                    self.logger.debug(f"          跳过P2（后面有币种）: {keyword} {amount}")
                return None
        
        keyword = self._clean_fee_name(keyword)
        
        if any(kw in keyword for kw in ['工作日', '运输时间', '时效', '天数', '时间']):
            return None

        # 跳过 min（最低收费说明，不是费用名）
        if keyword.strip().lower() in ('min', 'max', 'minimum', 'maximum'):
            return None

        if not self._is_valid_fee_name(keyword):
            return None

        if amount <= 0:
            return None

        fee_name = self._match_fee_name(keyword)

        if not fee_name:
            if keyword.endswith('费') or keyword.endswith('费用'):
                fee_name = keyword
            else:
                fee_name = keyword + '费'

        if not fee_name:
            return None

        currency = self._parse_currency(currency_str)

        fee_key = (fee_name, amount, currency)
        if fee_key in extracted_fees:
            return None
        extracted_fees.add(fee_key)

        if self.logger:
            self.logger.debug(f"          提取(P2): {fee_name} {amount} {currency}")

        return FeeTotal(费用名称=fee_name, 原币金额=amount, 币种=currency)
    
    def _process_pattern5(self, match, line: str, extracted_fees: Set[tuple]) -> Optional[FeeTotal]:
        """处理Pattern5: XX费币种数字（紧贴）"""
        keyword = match.group(1).strip()
        currency_str = match.group(2)
        amount = float(match.group(3))
        
        # 检查后面是否有斜杠或百分号
        match_end = match.end()
        if match_end < len(line):
            next_chars = line[match_end:match_end+3]
            if self._is_any_unit_slash(next_chars) or '%' in next_chars:
                return None
        
        # ✅ 关键修复：检查是否是时效（数字后面有"-"或"天"）
        if match_end < len(line):
            next_chars = line[match_end:match_end+5]
            if re.match(r'^[\s\-—]*\d+[\s]*天', next_chars):
                if self.logger:
                    self.logger.debug(f"          跳过P5（时效）: {keyword} {amount}")
                return None
        
        keyword = self._clean_fee_name(keyword)
        
        if not self._is_valid_fee_name(keyword):
            return None
        
        if amount <= 0:
            return None
        
        fee_name = self._match_fee_name(keyword)
        
        if not fee_name:
            if keyword.endswith('费') or keyword.endswith('费用'):
                fee_name = keyword
            else:
                fee_name = keyword + '费'
        
        if not fee_name:
            return None
        
        currency = self._parse_currency(currency_str)
        
        fee_key = (fee_name, amount, currency)
        if fee_key in extracted_fees:
            return None
        extracted_fees.add(fee_key)
        
        if self.logger:
            self.logger.debug(f"          提取(P5): {fee_name} {amount} {currency}")
        
        return FeeTotal(费用名称=fee_name, 原币金额=amount, 币种=currency)
    
    def _process_pattern6(self, match, line: str, extracted_fees: Set[tuple]) -> Optional[FeeTotal]:
        """处理Pattern6: XX费 币种数字（空格分隔）"""
        keyword = match.group(1).strip()
        currency_str = match.group(2)
        amount = float(match.group(3))
        
        # 检查后面是否有斜杠或百分号
        match_end = match.end()
        if match_end < len(line):
            next_chars = line[match_end:match_end+3]
            if self._is_any_unit_slash(next_chars) or '%' in next_chars:
                return None
        
        # ✅ 关键修复：检查是否是时效（数字后面有"-"或"天"）
        if match_end < len(line):
            next_chars = line[match_end:match_end+5]
            if re.match(r'^[\s\-—]*\d+[\s]*天', next_chars):
                if self.logger:
                    self.logger.debug(f"          跳过P6（时效）: {keyword} {amount}")
                return None
        
        keyword = self._clean_fee_name(keyword)
        
        if not self._is_valid_fee_name(keyword):
            return None
        
        if amount <= 0:
            return None
        
        fee_name = self._match_fee_name(keyword)
        
        if not fee_name:
            if keyword.endswith('费') or keyword.endswith('费用'):
                fee_name = keyword
            else:
                fee_name = keyword + '费'
        
        if not fee_name:
            return None
        
        currency = self._parse_currency(currency_str)
        
        fee_key = (fee_name, amount, currency)
        if fee_key in extracted_fees:
            return None
        extracted_fees.add(fee_key)
        
        if self.logger:
            self.logger.debug(f"          提取(P6): {fee_name} {amount} {currency}")
        
        return FeeTotal(费用名称=fee_name, 原币金额=amount, 币种=currency)
    
    def _process_pattern3(self, match, line: str, extracted_fees: Set[tuple]) -> Optional[FeeTotal]:
        """处理Pattern3: 币种数字XX费"""
        currency_str = match.group(1) or 'RMB'
        amount = float(match.group(2))
        keyword = match.group(3).strip()
        
        match_end = match.end()
        if match_end < len(line):
            next_chars = line[match_end:match_end+3]
            if self._is_any_unit_slash(next_chars) or '%' in next_chars:
                return None
        
        # ✅ 关键修复：检查是否是时效（数字后面有"-"或"天"）
        # 对于Pattern3，需要检查数字部分后面是否有时效标记
        match_start = match.start()
        # 找到数字的结束位置（group(2)之后）
        amount_str = match.group(2)
        amount_end_in_match = match.group(0).index(amount_str) + len(amount_str)
        amount_end = match_start + amount_end_in_match
        
        if amount_end < len(line):
            next_chars = line[amount_end:amount_end+5]
            if re.match(r'^[\s\-—]*\d+[\s]*天', next_chars):
                if self.logger:
                    self.logger.debug(f"          跳过P3（时效）: {keyword} {amount}")
                return None
        
        keyword = self._clean_fee_name(keyword)
        
        if not self._is_valid_fee_name(keyword):
            return None
        
        if amount <= 0:
            return None
        
        fee_name = self._match_fee_name(keyword)
        
        if fee_name:
            currency = self._parse_currency(currency_str)
            
            fee_key = (fee_name, amount, currency)
            if fee_key in extracted_fees:
                return None
            extracted_fees.add(fee_key)
            
            if self.logger:
                self.logger.debug(f"          提取(P3): {fee_name} {amount} {currency}")
            
            return FeeTotal(费用名称=fee_name, 原币金额=amount, 币种=currency)
        
        return None
    
    def _process_pattern_plus(self, match, line: str, extracted_fees: Set[tuple]) -> Optional[FeeTotal]:
        """处理Pattern+: +XX费币种数字"""
        keyword = match.group(1).strip()
        currency_str = match.group(2) or 'RMB'
        amount = float(match.group(3))
        
        # ✅ 关键修复：检查是否是时效（数字后面有"-"或"天"）
        match_end = match.end()
        if match_end < len(line):
            next_chars = line[match_end:match_end+5]
            if re.match(r'^[\s\-—]*\d+[\s]*天', next_chars):
                if self.logger:
                    self.logger.debug(f"          跳过P+（时效）: {keyword} {amount}")
                return None
        
        keyword = self._clean_fee_name(keyword)
        
        if not self._is_valid_fee_name(keyword):
            return None
        
        if amount <= 0:
            return None
        
        fee_name = self._match_fee_name(keyword)
        
        if not fee_name:
            if keyword.endswith('费') or keyword.endswith('费用'):
                fee_name = keyword
            else:
                fee_name = keyword + '费'
        
        if not fee_name:
            return None
        
        currency = self._parse_currency(currency_str)
        
        fee_key = (fee_name, amount, currency)
        if fee_key in extracted_fees:
            return None
        extracted_fees.add(fee_key)
        
        if self.logger:
            self.logger.debug(f"          提取(P+): {fee_name} {amount} {currency}")
        
        return FeeTotal(费用名称=fee_name, 原币金额=amount, 币种=currency)
    
    # 重量/体积单位（预处理时移除）
    _WEIGHT_VOLUME_UNITS = r'(?:kg|KG|Kg|cbm|CBM|Cbm|吨|方|立方|m3|M3)'

    # 所有单位（包括按票/按件等）——带任意单位的费用属于费用明细，不是整单费用
    _ALL_UNITS = r'(?:kg|KG|Kg|cbm|CBM|Cbm|吨|方|立方|m3|M3|票|个|件|场|次|箱|台|批|组|套|块|条|张|份|趟|pcs|PCS|set|SET)'

    def _preprocess_mixed_text(self, text: str) -> str:
        """
        预处理：只移除重量/体积单价（如 2.9/kg、380/cbm），保留其余文本结构。
        """
        if not text:
            return text

        unit_price_pattern = (
            r'\d+(?:\.\d+)?(?:[元]|[A-Z]{3,4})?\s*/' + self._WEIGHT_VOLUME_UNITS
        )

        if not re.search(unit_price_pattern, text, re.IGNORECASE):
            return text

        cleaned_text = re.sub(unit_price_pattern, '', text, flags=re.IGNORECASE)

        if self.logger:
            self.logger.debug(f"      预处理：移除重量/体积单价")

        return cleaned_text

    def _is_weight_volume_slash(self, next_chars: str) -> bool:
        """判断 / 后面跟的是否是重量/体积单位（用于预处理判断）"""
        return bool(re.match(r'^/\s*' + self._WEIGHT_VOLUME_UNITS, next_chars.strip(), re.IGNORECASE))

    def _is_any_unit_slash(self, next_chars: str) -> bool:
        """判断 / 后面是否跟任意单位——带单位的费用属于费用明细，整单费用提取器应跳过"""
        return bool(re.match(r'^/\s*' + self._ALL_UNITS, next_chars.strip(), re.IGNORECASE))
    
    def _clean_fee_name(self, fee_name: str) -> str:
        """清理费用名称"""
        if not fee_name:
            return ""
        
        fee_name = re.sub(r'元?/\w+[,，]?', '', fee_name)
        fee_name = re.sub(r'费+$', '费', fee_name)
        fee_name = re.sub(r'[+&]', '', fee_name)
        fee_name = re.sub(r'[-]', '', fee_name)
        fee_name = fee_name.lstrip('.。,，;；: +')
        fee_name = fee_name.rstrip(',，。；：+ ')
        fee_name = ' '.join(fee_name.split())
        
        return fee_name.strip()
    
    # 无效费用名词黑名单（限定词、量词、方向词等）
    _INVALID_FEE_WORDS = frozenset(['min', 'max', 'minimum', 'maximum', 'per', 'via', 'and', 'or'])

    def _is_valid_fee_name(self, text: str) -> bool:
        """判断是否是有效的费用名称"""
        if not text:
            return False

        if len(text) < 2:
            return False

        # 过滤英文限定词
        if text.strip().lower() in self._INVALID_FEE_WORDS:
            return False

        if re.match(r'^[\d一二三四五六七八九十]+[天个月年次]', text):
            return False
        
        if ('（' in text or '）' in text or '(' in text or ')' in text):
            if len(text) > 12:
                return False
        
        time_keywords = ['工作日', '运输时间', '时效', '天数', '时间']
        for keyword in time_keywords:
            if keyword in text:
                return False
        
        descriptive_keywords = [
            '按公斤计费', '按方计费', '按票计费',
            '按', '计费', '全程', '时效'
        ]
        
        for keyword in descriptive_keywords:
            if keyword in text and len(text) < 10:
                return False
        
        if '，' in text or '、' in text:
            return False
        
        return True
    
    def _match_fee_name(self, keyword: str) -> Optional[str]:
        """匹配费用名称（长关键词优先）"""
        if not keyword:
            return None
        
        keyword = keyword.strip(' +,，。；：\t\n&')
        
        if not keyword:
            return None
        
        # 精确匹配
        for fee_keyword in self.fee_keywords:
            if keyword == fee_keyword:
                return fee_keyword if fee_keyword.endswith('费') else fee_keyword + '费'
        
        # 长关键词包含匹配
        sorted_keywords = sorted(self.fee_keywords, key=len, reverse=True)
        
        for fee_keyword in sorted_keywords:
            if fee_keyword in keyword:
                return fee_keyword if fee_keyword.endswith('费') else fee_keyword + '费'
        
        for fee_keyword in sorted_keywords:
            if keyword in fee_keyword:
                return fee_keyword if fee_keyword.endswith('费') else fee_keyword + '费'
        
        return None
    
    def _parse_currency(self, currency_str: str) -> str:
        """解析币种"""
        if not currency_str:
            return 'RMB'
        
        currency_str = currency_str.strip().upper()
        return self.currency_map.get(currency_str, 'RMB')
    
    # ========== BaseExtractor 必需方法 ==========
    
    def _evaluate_quality(self, result: List[FeeTotal], sheet, **kwargs) -> float:
        if not result or len(result) == 0:
            return 0.0
        
        score = 0.5
        has_amount = sum(1 for f in result if f.原币金额) / len(result)
        score += has_amount * 0.5
        
        return score
    
    def _build_enhancement_prompt(self, result, sheet, **kwargs) -> str:
        """构建Fee Total增强的prompt"""
        import json
        
        # 获取sheet文本
        sheet_text = self._serialize_sheet(sheet, max_rows=30)  # 减少行数避免prompt太长
        
        # 获取规则提取的结果
        fee_totals_data = []
        if result and isinstance(result, list):
            for item in result:
                if hasattr(item, 'to_dict'):
                    fee_totals_data.append(item.to_dict())
        
        prompt = f"""请验证和补充以下整单费用的提取结果。

【原始Excel内容】
{sheet_text}

【规则提取结果】
{json.dumps(fee_totals_data, ensure_ascii=False, indent=2)}

【任务】
1. 验证提取结果是否正确
2. 补充缺失的费用项
3. 修正错误的字段

【提取规则】
整单费用格式：费用名称 + 金额
例如：
- "操作费：500元"
- "文件费：200"
- "报关费：800RMB"
- "THC：1200"

【提取字段】
1. 费用类型: 如"操作费"、"文件费"、"报关费"
2. 金额: 数字，如500
3. 币种: RMB/USD/EUR等

【返回格式】（严格JSON数组，不要其他文字）
[
  {{{{
    "费用类型": "...",
    "金额": ...,
    "币种": "..."
  }}}}
]

注意：
- 如果没有找到费用，返回空数组 []
- 金额必须是数字，不是字符串
- 只提取整单费用，不提取单价费用（xx元/kg这种）
"""
        
        return prompt
    
    def _merge_results(self, rule_result: List[FeeTotal], llm_result) -> List[FeeTotal]:
        """合并规则和LLM结果"""
        # 如果LLM结果为空，返回规则结果
        if not llm_result:
            return rule_result
        
        # 如果LLM结果是列表
        if isinstance(llm_result, list):
            # 将LLM结果转换为FeeTotal对象
            llm_fees = []
            for item in llm_result:
                if isinstance(item, dict):
                    fee = FeeTotal()
                    fee.费用类型 = item.get('费用类型')
                    fee.总金额 = item.get('总金额')
                    fee.币种 = item.get('币种')
                    
                    # 只添加有效的fee
                    if fee.费用类型 or fee.总金额:
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
                self.logger.info(f"      ✅ LLM新增{len(llm_fees)}个整单费用")
            elif self.logger:
                self.logger.info(f"      ⚠️  LLM未新增整单费用")
            
            return all_fees
        
        # 其他情况返回规则结果
        return rule_result
    
    def _extract_with_llm(self, sheet, **kwargs) -> List[FeeTotal]:
        return []
    
    def _is_valid(self, result: List[FeeTotal]) -> bool:
        return result and len(result) > 0
    
    def _get_default(self) -> List[FeeTotal]:
        return []


__all__ = ['FeeTotalExtractor', 'FeeTotal']