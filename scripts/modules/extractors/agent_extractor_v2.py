# scripts/modules/extractors/agent_extractor_v2.py
"""
代理提取器 v2.3（优化版）

【v2.3 更新内容】
1. 优化时效备注提取 - 剔除"不含"相关内容
2. 增强"不含"字段提取 - 支持多种格式
3. 增强赔付信息提取 - 识别更多关键词
4. 优化字段提取逻辑 - 避免重复和冗余
"""

import sys
import os
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# 导入BaseExtractor
from .base_extractor import BaseExtractor

AIRLINE_CODES = {
    # 主要航空公司
    'CX': '国泰航空', 'CA': '中国国航', 'CZ': '南方航空',
    'MU': '东方航空', 'HU': '海南航空', 'SC': '山东航空',
    'ZH': '深圳航空', 'KN': '中国联航', 'MF': '厦门航空',
    'SQ': '新加坡航空', 'TG': '泰国航空', 'BA': '英国航空',
    'LH': '汉莎航空', 'AF': '法国航空', 'KL': 'KLM荷航',
    'EK': '阿联酋航空', 'QR': '卡塔尔航空', 'TK': '土耳其航空',
    'NH': '全日空', 'JL': '日本航空', 'KE': '大韩航空',
    'OZ': '韩亚航空', 'UA': '美联航', 'AA': '美国航空',
    'DL': '达美航空', 'AC': '加拿大航空', 'NZ': '新西兰航空',
    # 货运航空
    'HK': '香港华民', 'CV': 'Cargolux', 'PO': 'Polar Air',
    'CK': '中国货运', 'QF': '澳洲航空'
}

# 贸易类型白名单
TRADE_TYPES = [
    '一般贸易', '正清', '双清', '专线', 
    '贸易代理', '贸代', 'DDP', 'DDU',
    '包税', '不包税', '清关代理',
    '快递', 'EMS', '国际快递'
]

@dataclass
class Agent:
    """代理商数据类"""
    代理商: Optional[str] = None
    代理备注: Optional[str] = None
    时效: Optional[str] = None
    时效备注: Optional[str] = None
    不含: Optional[str] = None
    是否赔付: Optional[str] = None
    赔付内容: Optional[str] = None
    运输方式: Optional[str] = None
    贸易类型: Optional[str] = None
    _column: Optional[int] = None


class AgentExtractorV2(BaseExtractor):
    """代理提取器 v2.3"""
    
    def __init__(self, logger=None, llm_client=None, enable_llm=False):
        super().__init__(logger, llm_client, enable_llm)
        
        # 代理行的识别模式
        self.agent_row_patterns = [
            '代理',
            '报价方',
            '货代',
            '物流商',
            '供应商',
            '承运商',
            '贸易代理方案',
            '运输方案',
            '物流方案',
        ]
    
    def _extract_with_rules(self, sheet, **kwargs) -> List[Agent]:
        """使用规则提取代理商"""
        agents = []
        
        # 查找所有可能的代理行
        agent_rows = self._find_agent_rows_extended(sheet)
        
        if not agent_rows:
            if self.logger:
                self.logger.debug("      未找到代理行")
            return []
        
        if self.logger:
            self.logger.debug(f"      找到{len(agent_rows)}个可能的代理行: {agent_rows}")
        
        # 遍历每个代理行的每一列
        for agent_row_idx in agent_rows:
            for col_idx in range(2, sheet.max_column + 1):
                agent = self._parse_agent_column(sheet, agent_row_idx, col_idx)
                
                if agent and agent.代理商:
                    # 检查去重
                    is_duplicate = any(
                        a.代理商 == agent.代理商 and 
                        a._column == agent._column
                        for a in agents
                    )
                    
                    if not is_duplicate:
                        agents.append(agent)
                    else:
                        # 更新备注
                        for existing in agents:
                            if existing.代理商 == agent.代理商 and existing._column == agent._column:
                                if agent.代理备注 and not existing.代理备注:
                                    existing.代理备注 = agent.代理备注
                                break
        
        if self.logger:
            self.logger.debug(f"      提取到{len(agents)}个代理商")
        
        return agents
    
    def _find_agent_row(self, sheet) -> Optional[int]:
        """查找"代理"行"""
        for row_idx, row in enumerate(sheet.iter_rows(max_row=30), 1):
            first_cell = row[0].value
            if not first_cell:
                continue
            
            first_cell_text = str(first_cell).strip()
            
            for pattern in self.agent_row_patterns:
                if pattern in first_cell_text:
                    return row_idx
        
        return None
    
    def _find_agent_rows_extended(self, sheet) -> List[int]:
        """扩展的代理行查找"""
        agent_rows = []
        
        standard_row = self._find_agent_row(sheet)
        if standard_row:
            agent_rows.append(standard_row)
        
        from ...data.agent_whitelist import AGENT_WHITELIST
        
        for row_idx in range(1, min(40, sheet.max_row + 1)):
            for col_idx in range(1, min(10, sheet.max_column + 1)):
                cell = sheet.cell(row=row_idx, column=col_idx)
                if not cell.value:
                    continue
                
                cell_text = str(cell.value).strip()
                
                if '方案' in cell_text or '代理' in cell_text:
                    for agent in AGENT_WHITELIST:
                        if agent in cell_text:
                            if row_idx not in agent_rows:
                                agent_rows.append(row_idx)
                            break
        
        return agent_rows
    
    def _parse_agent_column(self, sheet, agent_row_idx: int, col_idx: int) -> Optional[Agent]:
        """
        解析一列的代理信息（优化版）
        
        【v2.3 改进】
        1. 时效备注清理 - 剔除"不含"内容
        2. 不含字段增强 - 支持多种格式
        3. 赔付信息增强 - 识别更多关键词
        """
        agent = Agent(_column=col_idx)
        
        # ========== 提取代理商名 ==========
        agent_cell = sheet.cell(row=agent_row_idx, column=col_idx)
        if not agent_cell.value:
            return None
        
        agent_text = str(agent_cell.value).strip()

        from ...data.agent_whitelist import extract_agent_name_and_remark, is_valid_agent_name, AGENT_WHITELIST

        # 方法1: 标准分离
        agent_name, remark = extract_agent_name_and_remark(agent_text)

        # 方法2: 在文本中查找白名单代理商
        if not agent_name or not is_valid_agent_name(agent_name):
            found = False
            for candidate in sorted(AGENT_WHITELIST, key=len, reverse=True):
                if candidate in agent_text:
                    agent_name = candidate
                    remark = agent_text.replace(candidate, '').strip()
                    remark = remark.lstrip('-—－:：').strip()
                    found = True
                    break
            
            if not found:
                agent_name = None
                remark = None

        # 方法3: 检查是否是纯方案描述
        if not agent_name or not is_valid_agent_name(agent_name):
            if any(kw in agent_text for kw in ['方案', '过港', '双清', '包税']):
                if self.logger:
                    self.logger.debug(f"        列{col_idx}: '{agent_text}' 是方案描述，非代理商")
                return None
            else:
                if self.logger:
                    self.logger.debug(f"        列{col_idx}: 无效的代理商名'{agent_text}'")
                return None

        # 验证代理商名
        if not is_valid_agent_name(agent_name):
            if self.logger:
                self.logger.debug(f"        列{col_idx}: 无效的代理商名'{agent_name}'")
            return None

        agent.代理商 = agent_name
        if remark:
            agent.代理备注 = remark

        # ========== 提取其他信息（优化版）==========
        # 用于收集所有相关内容
        timeliness_texts = []  # 时效相关文本
        not_include_texts = []  # 不含相关文本
        compensate_texts = []  # 赔付相关文本
        
        for offset in range(1, min(20, sheet.max_row - agent_row_idx + 1)):  # 扫描20行
            row_idx = agent_row_idx + offset
            cell = sheet.cell(row=row_idx, column=col_idx)
            
            if not cell.value:
                continue
            
            cell_text = str(cell.value).strip()
            
            # ========== v2.7 改进：按行分割处理 ==========
            # 如果cell中包含多行内容（用\n分隔），逐行处理
            lines = cell_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # ========== 1. 识别"不含"内容（优先级最高）==========
                if self._is_not_include_content(line):
                    not_include_texts.append(line)
                    continue  # 识别为"不含"后跳过，不再处理
                
                # ========== 2. 识别赔付信息 ==========
                if self._is_compensate_content(line):
                    compensate_texts.append(line)
                    continue
                
                # ========== 3. 识别时效 ==========
                if self._is_timeliness_content(line):
                    timeliness_texts.append(line)
                    continue
            
            # ========== 4. 识别运输方式（优化版）==========
            if not agent.运输方式:
                # ✅ 优先识别航空公司代码
                airline_code = self._extract_airline_code(cell_text)
                if airline_code:
                    agent.运输方式 = '空运'
                    if self.logger:
                        self.logger.debug(f"      识别航空公司代码: {airline_code} → 空运")
                else:
                    # 原有的关键词匹配
                    for mode in ['海运', '空运', '快递', '铁路', '陆运', '空派', '海派']:
                        if mode in cell_text:
                            agent.运输方式 = mode
                            break
            
            # ========== 5. 识别贸易类型（优化版）==========
            if not agent.贸易类型:
                # ✅ 优先从sheet标题提取
                sheet_trade_type = self._extract_trade_type_from_title(sheet)
                if sheet_trade_type:
                    agent.贸易类型 = sheet_trade_type
                    if self.logger:
                        self.logger.debug(f"      从标题提取贸易类型: {sheet_trade_type}")
                else:
                    # ✅ 使用白名单匹配
                    for trade_type in TRADE_TYPES:
                        if trade_type in cell_text:
                            agent.贸易类型 = trade_type
                            break
        
        # ========== 处理时效 ==========
        if timeliness_texts:
            agent.时效, agent.时效备注 = self._process_timeliness(timeliness_texts)
        
        # ========== 处理"不含" ==========
        if not_include_texts:
            agent.不含 = self._process_not_include(not_include_texts)
        
        # ========== 处理赔付 ==========
        if compensate_texts:
            agent.是否赔付, agent.赔付内容 = self._process_compensate(compensate_texts)

        return agent
    
    def _is_not_include_content(self, text: str) -> bool:
        """
        判断是否是"不含"相关内容（优化版）
        
        【识别规则】
        1. 包含"不含"、"不包含"等明确关键词
        2. 费用项列举（保险费、运费、查验费...）
        3. 排除：价格信息、时效描述
        """
        # 排除价格信息（如"380RMB/CBM"、"USD100"）
        if re.search(r'\d+\s*(RMB|USD|CNY|EUR|GBP|SGD)', text, re.IGNORECASE):
            return False
        
        # 排除时效描述
        if any(kw in text for kw in ['时效', '时间', '天数', '工期', '近期', '船期']):
            return False
        
        # 明确的"不含"关键词
        keywords = ['不含', '不包含', '不包括', '另计', '另付', '需另', '额外', '不负责']
        for kw in keywords:
            if kw in text:
                return True
        
        # 识别费用列举（必须有2个以上费用项）
        fee_pattern = r'(保险费|运费|关税|查验费|待时费|转运费|包装费|仓储费|杂费|卸货费|拆箱费|提货费|派送费|燃油费)'
        fee_matches = re.findall(fee_pattern, text)
        
        if len(fee_matches) >= 2:
            # 但要排除包含明确时效描述的
            if not re.search(r'\d+[-~]\d+[天日]|约\d+[天日]', text):
                return True
        
        return False
    
    def _is_compensate_content(self, text: str) -> bool:
        """判断是否是赔付相关内容"""
        keywords = ['赔付', '赔偿', '货损', '货差', '理赔', '保险赔']
        return any(kw in text for kw in keywords)
    
    def _is_timeliness_content(self, text: str) -> bool:
        """
        判断是否是时效相关内容（v2.8 优化版）
        
        【识别规则】
        1. 包含时效关键词（天、日、时间、时效、船期等）
        2. 排除价格信息
        3. 排除重量/尺寸限制（v2.8新增）
        
        【排除优先级】
        先排除非时效内容，再检查时效关键词
        """
        # 排除1: 价格信息
        if re.search(r'\d+\s*(RMB|USD|CNY|EUR|GBP|SGD|/CBM|/KG)', text, re.IGNORECASE):
            return False
        
        # 排除2: 重量限制（v2.8新增）
        # 识别模式：包含重量单位（KG、kg、吨等）且包含限制词（不超、最大、限制等）
        weight_patterns = [
            r'(不超|最大|限制|控制|单件|实重|毛重|净重|体积重).*?\d+\s*(KG|kg|千克|吨|T|LB|磅)',
            r'\d+\s*(KG|kg|千克|吨|T|LB|磅).*(不超|最大|限制|控制|以下)',
        ]
        for pattern in weight_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        # 排除3: 尺寸限制（v2.8新增）
        # 识别模式：包含尺寸单位（CM、M等）且有多个数字
        if re.search(r'\d+X\d+X\d+\s*(CM|cm|M|m)', text, re.IGNORECASE):
            return False
        
        # 排除4: 纯数字+单位（如"40KG"、"500CNY"），但没有时效描述
        # 这种通常是规格限制，不是时效
        if re.search(r'^\d+\s*(KG|kg|千克|吨|CNY|RMB)', text, re.IGNORECASE):
            return False
        
        # 识别时效关键词
        keywords = ['天', '日', '时间', '时效', '船期', '工期', '工作日', '自然日', '左右', '到达', '查验', '顺延', '近期', '晚到']
        has_timeliness_keyword = any(kw in text for kw in keywords)
        
        # 如果包含时效关键词，进一步验证是否真的是时效描述
        if has_timeliness_keyword:
            # 检查是否包含明确的时间数量（如"3天"、"5-7日"）或时效描述（如"近期"、"船期"）
            time_indicators = [
                r'\d+[-~]\d+\s*[天日]',      # 5-7天
                r'\d+\s*[天日工作日自然日]',  # 3天、5工作日
                r'(近期|最近|约|预计|大概)',   # 近期、约3天
                r'(船期|航班|时效|工期)',     # 船期乱、时效不稳定
                r'(晚到|延误|顺延|推迟)',     # 晚到港、顺延
            ]
            
            for indicator in time_indicators:
                if re.search(indicator, text):
                    return True
            
            # 包含时效关键词但没有明确的时间指标，可能是误判
            return False
        
        return False
    
    def _process_timeliness(self, texts: List[str]) -> tuple:
        """
        处理时效信息（v2.6 优化版）
        
        【v2.6 改进】
        1. 支持"12-15个工作日"格式
        2. 处理"近期船期乱"等无明确天数的情况
        
        Returns:
            (时效, 时效备注) 元组
        """
        # 合并所有时效相关文本
        combined = '\n'.join(texts)
        
        # 提取所有天数（v2.6改进：支持"个工作日"、"个自然日"等）
        day_patterns = [
            r'全程\s*(\d+[-~至到]\d+)\s*个?[天日工作日自然日]',
            r'预计\s*(\d+[-~至到]\d+)\s*个?[天日工作日自然日]',
            r'约?\s*(\d+[-~至到]\d+)\s*个?[天日工作日自然日]',
            r'(\d+[-~至到]\d+)\s*个?[天日工作日自然日]',
            r'约?\s*(\d+)\s*个?[天日工作日自然日]',
        ]
        
        max_days = 0
        
        for pattern in day_patterns:
            matches = re.finditer(pattern, combined)
            for match in matches:
                time_str = match.group(1)
                
                if '-' in time_str or '~' in time_str or '至' in time_str or '到' in time_str:
                    numbers = re.findall(r'\d+', time_str)
                    if numbers:
                        current_max = max(int(n) for n in numbers)
                        if current_max > max_days:
                            max_days = current_max
                else:
                    current = int(time_str)
                    if current > max_days:
                        max_days = current
        
        # 设置时效
        timeliness = f"{max_days}天" if max_days > 0 else None
        
        # 清理时效备注（v2.4 增强版 - 彻底移除费用内容）
        cleaned_remarks = []
        
        for text in texts:
            # 先移除明确的费用列举部分
            text = self._remove_fee_listings(text)
            
            # 然后分句处理
            sentences = re.split(r'[。；\n]', text)
            
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                
                # 保留条件：
                # 1. 包含时效关键词（天、日、时间、时效、船期等）
                # 2. 不是纯费用描述
                has_time_keyword = any(kw in sent for kw in ['天', '日', '时间', '时效', '船期', '工期', '左右', '到达', '查验', '顺延', '工作日'])
                is_fee_only = self._is_fee_only_sentence(sent)
                
                if has_time_keyword and not is_fee_only:
                    cleaned_remarks.append(sent)
        
        timeliness_remark = '；'.join(cleaned_remarks) if cleaned_remarks else None
        
        # 限制备注长度
        if timeliness_remark and len(timeliness_remark) > 200:
            timeliness_remark = timeliness_remark[:200] + '...'
        
        return (timeliness, timeliness_remark)
    
    def _remove_fee_listings(self, text: str) -> str:
        """
        移除文本中的费用列举部分
        
        例如：
        "保险费，查验费，待时费；约2-3天" → "约2-3天"
        """
        # 识别费用列举模式
        fee_pattern = r'(保险费|运费|关税|查验费|待时费|转运费|包装费|仓储费|杂费|卸货费|拆箱费|提货费|派送费|燃油费)'
        
        # 如果包含费用列举，尝试分离
        if re.search(fee_pattern, text):
            # 按标点分句
            parts = re.split(r'[；;,，、]', text)
            clean_parts = []
            
            for part in parts:
                part = part.strip()
                # 统计该部分的费用项数量
                fee_count = len(re.findall(fee_pattern, part))
                
                # 如果费用项 >= 2，认为是费用列举，跳过
                # 如果费用项 < 2，保留
                if fee_count < 2:
                    clean_parts.append(part)
            
            return '；'.join(clean_parts)
        
        return text
    
    def _is_fee_only_sentence(self, sentence: str) -> bool:
        """
        判断一个句子是否是纯费用描述
        
        例如：
        "保险费，查验费，待时费" → True
        "约2-3天，海关查验顺延" → False
        """
        # 统计费用关键词数量
        fee_pattern = r'(保险费|运费|关税|查验费|待时费|转运费|包装费|仓储费|杂费|卸货费|拆箱费|提货费|派送费|燃油费)'
        fee_count = len(re.findall(fee_pattern, sentence))
        
        # 如果包含2个以上费用项，且没有明确的时效数字，认为是纯费用
        if fee_count >= 2:
            has_time_number = re.search(r'\d+[-~]\d+[天日]|约\d+[天日]', sentence)
            
            if not has_time_number:
                return True
        
        return False
    
    def _process_not_include(self, texts: List[str]) -> str:
        """
        处理"不含"信息（v2.5 优化版 - 保留原文）
        
        【v2.5 改进】
        不再只提取关键词，而是保留原始文本（排除价格和时效）
        这样可以保留"卡车等待费"、"停车费"等非标准费用项
        
        Returns:
            不含内容字符串
        """
        cleaned_items = []
        
        for text in texts:
            # 去除"不含："前缀
            cleaned = re.sub(r'^(不含|不包含|不包括)[:：]?\s*', '', text)
            cleaned = cleaned.strip()
            
            if not cleaned:
                continue
            
            # 分句处理
            sentences = re.split(r'[。\n]', cleaned)
            
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                
                # 排除条件：
                # 1. 包含价格信息（如"380RMB/CBM"）
                has_price = re.search(r'\d+\s*(RMB|USD|CNY|EUR|GBP|SGD|/CBM|/KG)', sent, re.IGNORECASE)
                # 2. 包含明确的时效描述（如"近期船期乱"、"时效不稳定"）
                has_timeliness = any(kw in sent for kw in ['时效', '时间', '天数', '工期', '近期', '船期', '不稳定', '不做保证'])
                
                # 如果不包含价格和时效，保留原文
                if not has_price and not has_timeliness:
                    # v2.5改进：直接保留原文，不再提取关键词
                    cleaned_items.append(sent)
        
        # 合并结果
        result = '，'.join(cleaned_items)
        
        # 限制长度
        if len(result) > 500:  # 增加长度限制到500
            result = result[:500] + '...'
        
        return result if result else None
    
    def _extract_fee_items(self, text: str) -> str:
        """
        从文本中提取费用项
        
        例如：
        "不含卸货拆箱等" → "卸货拆箱等"
        "保险费，查验费，待时费" → "保险费，查验费，待时费"
        """
        # 费用关键词列表
        fee_keywords = [
            '保险费', '运费', '关税', '查验费', '待时费', '转运费', '包装费',
            '仓储费', '杂费', '卸货费', '拆箱费', '提货费', '派送费', '燃油费',
            '报关费', '清关费', '行验费', '堆存费', '仓租费', '搬运费'
        ]
        
        # 提取所有费用项
        found_items = []
        for keyword in fee_keywords:
            if keyword in text:
                found_items.append(keyword)
        
        # 如果找到费用项，返回
        if found_items:
            return '，'.join(found_items)
        
        # 如果没有找到，但文本很短且包含"等"字，可能是其他费用
        if len(text) < 20 and '等' in text:
            return text
        
        return ''
    
    def _process_compensate(self, texts: List[str]) -> tuple:
        """
        处理赔付信息（v2.5 优化版 - 保留完整原文）
        
        【v2.5 改进】
        不再只匹配简单模式，而是保留完整的赔付说明
        这样可以保留复杂的赔付规则（如"电池专线赔偿标准：在运输RMB40/kg..."）
        
        Returns:
            (是否赔付, 赔付内容) 元组
        """
        combined = '\n'.join(texts)
        
        # 判断是否赔付
        is_compensate = '否'
        if any(kw in combined for kw in ['不赔', '不予赔', '无赔', '不负责']):
            is_compensate = '否'
        elif any(kw in combined for kw in ['赔付', '赔偿', '理赔', '货损']):
            is_compensate = '是'
        
        # 提取赔付内容（v2.5改进：保留完整原文）
        compensate_content = None
        
        if is_compensate == '是':
            # 去除"赔付标准："、"赔偿标准："等前缀
            cleaned = re.sub(r'^(赔付标准|赔偿标准|理赔标准|货损标准)[:：]?\s*', '', combined)
            cleaned = cleaned.strip()
            
            if cleaned:
                compensate_content = cleaned
                
                # 限制长度（保留更多内容）
                if len(compensate_content) > 300:
                    compensate_content = compensate_content[:300] + '...'
        
        return (is_compensate, compensate_content)
    
    def _is_valid(self, result: List[Agent]) -> bool:
        """验证agents是否有效"""
        if not result:
            if self.logger:
                self.logger.debug("      验证失败: agents列表为空")
            return False
        
        valid_count = sum(1 for agent in result if self._is_valid_agent(agent))
        
        if valid_count == 0:
            if self.logger:
                self.logger.debug("      验证失败: 没有有效的agent")
            return False
        
        return True
    
    def _is_valid_agent(self, agent: Agent) -> bool:
        """验证单个agent是否有效"""
        if not agent or not agent.代理商:
            return False
        
        from ...data.agent_whitelist import is_valid_agent_name
        return is_valid_agent_name(agent.代理商)
    
    def _extract_with_llm(self, sheet, **kwargs) -> List[Agent]:
        """使用LLM提取代理商（兜底）"""
        if not self.llm_client:
            return []
        
        try:
            content_lines = []
            for row_idx, row in enumerate(sheet.iter_rows(max_row=50), 1):
                row_data = [str(cell.value) if cell.value else '' for cell in row[:10]]
                if any(row_data):
                    content_lines.append(f"行{row_idx}: {' | '.join(row_data)}")
            
            content_text = '\n'.join(content_lines[:30])
            
            prompt = f"""
请从以下Excel表格内容中提取所有代理商信息。

表格内容：
{content_text}

要求：
1. 识别所有代理商名称
2. 提取每个代理商的备注信息（如有）
3. 返回JSON数组格式

返回格式：
[
    {{"代理商": "融迅", "代理备注": "双清含税"}},
    {{"代理商": "骐盛", "代理备注": null}}
]

如果没有找到代理商，返回空数组 []
"""
            
            response = self.llm_client.chat(prompt)
            
            import json
            agents_data = json.loads(response)
            
            agents = []
            for data in agents_data:
                agent = Agent(
                    代理商=data.get('代理商'),
                    代理备注=data.get('代理备注')
                )
                if agent.代理商:
                    agents.append(agent)
            
            return agents
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"LLM提取失败: {e}")
            return []
    
    def _to_dict(self, result: List[Agent]) -> List[Dict[str, Any]]:
        """将Agent对象列表转换为字典列表"""
        return [asdict(agent) for agent in result]
    
    # ========== v2.0 新增：质量驱动架构方法 ==========
    
    def _evaluate_quality(self, result: List[Agent], sheet, **kwargs) -> float:
        """
        评估Agent提取质量（v2.0 新增）
        
        【评估维度】
        1. 完整性 (Completeness) - 40%
        2. 合理性 (Reasonableness) - 30%
        3. 一致性 (Consistency) - 30%
        
        Returns:
            质量分数 (0-1)
        """
        if not result or len(result) == 0:
            return 0.0  # 没有提取到任何agent
        
        total_score = 0.0
        
        for agent in result:
            # 1. 完整性检查 (40%)
            completeness = self._check_completeness(agent)
            
            # 2. 合理性检查 (30%)
            reasonableness = self._check_reasonableness(agent)
            
            # 3. 一致性检查 (30%)
            consistency = self._check_consistency(agent)
            
            # 加权平均
            agent_score = (
                completeness * 0.4 +
                reasonableness * 0.3 +
                consistency * 0.3
            )
            
            total_score += agent_score
        
        # 平均质量分数
        avg_score = total_score / len(result)
        
        return avg_score
    
    def _check_completeness(self, agent: Agent) -> float:
        """检查完整性"""
        score = 0.0
        checks = 0
        
        # 检查1: 代理商必须有值
        checks += 1
        if agent.代理商:
            score += 1.0
        
        # 检查2: 时效和时效备注的一致性
        checks += 1
        if agent.时效备注:
            if self._contains_days(agent.时效备注) and not agent.时效:
                score += 0.2  # 不一致，严重扣分
            else:
                score += 1.0
        elif agent.时效:
            score += 1.0
        else:
            score += 1.0
        
        # 检查3: 赔付字段的一致性
        checks += 1
        if agent.是否赔付 == '是' and not agent.赔付内容:
            score += 0.4  # 说有赔付但没内容，扣分
        else:
            score += 1.0
        
        return score / checks if checks > 0 else 0.0
    
    def _contains_days(self, text: str) -> bool:
        """检查文本是否包含明确的天数信息"""
        if not text:
            return False
        return bool(re.search(r'\d+[-~]\d+\s*个?[天日工作日]|\d+\s*个?[天日工作日]', text))
    
    def _check_reasonableness(self, agent: Agent) -> float:
        """检查合理性"""
        score = 0.0
        checks = 0
        
        # 检查1: "不含"字段长度
        if agent.不含:
            checks += 1
            length = len(agent.不含)
            if length < 5:
                score += 0.2
            elif length > 600:
                score += 0.6
            else:
                score += 1.0
        
        # 检查2: 时效值合理性
        if agent.时效:
            checks += 1
            try:
                days = int(re.search(r'\d+', agent.时效).group())
                if 1 <= days <= 180:
                    score += 1.0
                elif days > 365:
                    score += 0.1
                else:
                    score += 0.5
            except:
                score += 0.3
        
        # 检查3: 赔付内容长度
        if agent.赔付内容:
            checks += 1
            length = len(agent.赔付内容)
            if length < 3:
                score += 0.2
            elif length > 400:
                score += 0.6
            else:
                score += 1.0
        
        if checks == 0:
            return 0.8
        
        return score / checks
    
    def _check_consistency(self, agent: Agent) -> float:
        """检查一致性"""
        score = 0.0
        checks = 0
        
        # 检查: 运输方式和贸易类型的合理搭配
        checks += 1
        if agent.运输方式 and agent.贸易类型:
            score += 1.0
        elif not agent.运输方式 and not agent.贸易类型:
            score += 1.0
        else:
            score += 0.7
        
        if checks == 0:
            return 0.8
        
        return score / checks
    
    def _build_enhancement_prompt(self, result: List[Agent], sheet, **kwargs) -> str:
        """构建LLM增强提示词（v2.0 新增）"""
        # 提取sheet原文
        content_lines = []
        for row_idx, row in enumerate(sheet.iter_rows(max_row=50), 1):
            row_data = [str(cell.value) if cell.value else '' for cell in row[:15]]
            if any(row_data):
                content_lines.append(f"行{row_idx}: {' | '.join(row_data)}")
        
        sheet_content = '\n'.join(content_lines[:40])
        
        # 格式化规则提取结果
        rule_results = []
        for agent in result:
            rule_results.append({
                '代理商': agent.代理商,
                '代理备注': agent.代理备注,
                '时效': agent.时效,
                '时效备注': agent.时效备注,
                '不含': agent.不含,
                '是否赔付': agent.是否赔付,
                '赔付内容': agent.赔付内容,
                '运输方式': agent.运输方式,
                '贸易类型': agent.贸易类型,
            })
        
        import json
        
        prompt = f"""
你是一个专业的物流数据提取助手。我已经使用规则方法从Excel中提取了代理商信息，但提取结果可能不完整或不准确。

请帮我验证和补充这些信息。

【原始Excel内容】：
{sheet_content}

【规则提取的结果】：
{json.dumps(rule_results, ensure_ascii=False, indent=2)}

【你的任务】：
1. 逐个验证每个agent的每个字段
2. 补充缺失的信息
3. 修正错误的信息

【特别注意的问题】：
1. **时效不一致**：如果"时效备注"中包含明确的天数（如"12-15个工作日"），但"时效"字段为null，请提取时效（取最大值，如"15天"）
2. **时效为null的情况**：如果"时效备注"中没有明确天数（如"近期船期乱"、"时效不稳定"），"时效"应该保持null
3. **"不含"不完整**：如果原文中列举了多个费用项，但提取结果只有部分，请补充完整
4. **赔付内容截断**：如果原文中的赔付说明很长，但提取结果被截断，请补充完整
5. **时效备注混入重量限制**：时效备注中不应包含重量限制（如"单件实重不超40KG"），这应该被移除
6. **运输方式识别**：
   - 如果看到航空公司代码（如"BY HK CX"、"BY CA"），识别为"空运"
   - 航空公司代码：HK、CX、CA、MU、CZ、SQ、TG等（都是两个大写字母）
   - 如果看到"海运费"、"ocean"、"sea"，识别为"海运"

7. **贸易类型识别**：
   - 从标题或内容中提取，例如"一般贸易成本" → "一般贸易"
   - 白名单：一般贸易、正清、双清、专线、贸易代理、贸代、DDP、DDU、包税、不包税
   - 必须使用白名单中的词汇，不要自己创造

【返回格式】：
请返回完整的JSON数组，格式与输入相同。只返回JSON，不要有任何其他文字说明。

示例：
[
  {{
    "代理商": "融迅",
    "代理备注": null,
    "时效": "15天",
    "时效备注": "12-15个工作日左右",
    "不含": "保险费，查验费，待时费",
    "是否赔付": "是",
    "赔付内容": "货损按80%赔付",
    "运输方式": "海运",
    "贸易类型": "双清"
  }}
]
"""
        
        return prompt
    
    def _merge_results(self, rule_result: List[Agent], llm_result) -> List[Agent]:
        """合并规则和LLM的结果（v2.0 新增）"""
        if not llm_result:
            return rule_result
        
        try:
            if not isinstance(llm_result, list):
                if self.logger:
                    self.logger.warning("      LLM结果格式错误，使用规则结果")
                return rule_result
            
            # 转换为Agent对象
            merged = []
            for idx, llm_agent_dict in enumerate(llm_result):
                agent = Agent(
                    代理商=llm_agent_dict.get('代理商'),
                    代理备注=llm_agent_dict.get('代理备注'),
                    时效=llm_agent_dict.get('时效'),
                    时效备注=llm_agent_dict.get('时效备注'),
                    不含=llm_agent_dict.get('不含'),
                    是否赔付=llm_agent_dict.get('是否赔付'),
                    赔付内容=llm_agent_dict.get('赔付内容'),
                    运输方式=llm_agent_dict.get('运输方式'),
                    贸易类型=llm_agent_dict.get('贸易类型'),
                    _column=rule_result[idx]._column if idx < len(rule_result) else None,
                )
                merged.append(agent)
            
            if self.logger:
                self.logger.debug(f"      合并结果：{len(merged)}个agents")
            
            return merged
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"      合并结果失败: {e}")
            return rule_result
        
    def _extract_airline_code(self, text: str) -> Optional[str]:
        """
        提取航空公司代码（新增）
        
        【识别模式】
        BY HK CX → 识别HK和CX
        BY CA 235 → 识别CA
        
        Returns:
            航空公司名称，如果识别到；否则None
        """
        if not text:
            return None
        
        # 模式：BY XX YY（XX YY是航空公司代码）
        pattern = r'BY\s+([A-Z]{2})(?:\s+([A-Z]{2}))?'
        match = re.search(pattern, text.upper())
        
        if match:
            codes = [match.group(1)]
            if match.group(2):
                codes.append(match.group(2))
            
            # 检查是否在白名单中
            for code in codes:
                if code in AIRLINE_CODES:
                    return AIRLINE_CODES[code]
        
        return None

    def _extract_trade_type_from_title(self, sheet) -> Optional[str]:
        """
        从sheet标题提取贸易类型（新增）
        
        【示例】
        "深圳-新加坡一般贸易成本" → "一般贸易"
        "国内-西班牙双清专线" → "双清"
        """
        # 检查前3行
        for row_idx in range(1, min(4, sheet.max_row + 1)):
            for col_idx in range(1, min(10, sheet.max_column + 1)):
                try:
                    cell = sheet.cell(row=row_idx, column=col_idx)
                    if cell.value:
                        text = str(cell.value).strip()
                        
                        # ✅ 白名单匹配
                        for trade_type in TRADE_TYPES:
                            if trade_type in text:
                                return trade_type
                except:
                    continue
        
        return None
    
    def _get_default(self) -> List[Agent]:
        """获取默认值"""
        return []