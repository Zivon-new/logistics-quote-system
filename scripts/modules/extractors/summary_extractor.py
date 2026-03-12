# scripts/modules/extractors/summary_extractor.py
"""
Summary提取器

【核心功能】
✅ 提取税率（百分比）
✅ 提取汇损率（百分比）
✅ 提取备注（排除已被其他表提取的内容）
"""

import re
from typing import Optional
from dataclasses import dataclass, asdict

from .base_extractor import BaseExtractor


@dataclass
class Summary:
    """Summary数据类"""
    税率: Optional[float] = None      # 例如：0.19 表示19%
    汇损率: Optional[float] = None    # 例如：0.04 表示4%
    备注: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


class SummaryExtractor(BaseExtractor):
    """Summary提取器"""
    
    QUALITY_THRESHOLD = 0.5
    
    def __init__(self, logger=None, llm_client=None, enable_llm=True):
        super().__init__(logger, llm_client, enable_llm)
        
        # 需要排除的关键词（已被其他表提取）
        self.exclude_keywords = [
            # Agent表已提取
            '时效', '不含', '赔付', '陆运', '海运', '空运',
            # Routes表已提取
            '路线', '起始', '目的地', '代理',
            # Fees表已提取
            '费用明细', '小计', '总计', '操作费', '报关费', '运费',
            # Goods表已提取
            '货物', '品名', '数量', '重量', '体积'
        ]
    
    def _extract_with_rules(self, sheet, agent_start_row=None, agent_end_row=None, **kwargs) -> Summary:
        """
        规则提取
        
        Args:
            sheet: Excel sheet对象
            agent_start_row: 代理商区域起始行
            agent_end_row: 代理商区域结束行
        """
        summary = Summary()
        
        # 如果没有指定区域，扫描整个sheet
        if not agent_start_row:
            agent_start_row = 1
        if not agent_end_row:
            agent_end_row = sheet.max_row
        
        # 1. 找到"小计"和"总计"的位置
        xiaoji_row = None
        zongji_row = None
        
        for row_idx in range(agent_start_row, min(agent_end_row + 1, sheet.max_row + 1)):
            row_text = self._get_row_text(sheet, row_idx)
            
            if '小计' in row_text and not xiaoji_row:
                xiaoji_row = row_idx
                if self.logger:
                    self.logger.debug(f"    找到小计：行{row_idx}")
            
            if '总计' in row_text and xiaoji_row:
                zongji_row = row_idx
                if self.logger:
                    self.logger.debug(f"    找到总计：行{row_idx}")
                break
        
        if not xiaoji_row:
            if self.logger:
                self.logger.debug("    未找到小计行")
            return summary
        
        # 2. 在小计到总计之间，提取税率和汇损率
        search_end = zongji_row if zongji_row else min(xiaoji_row + 5, agent_end_row)
        
        for row_idx in range(xiaoji_row, search_end + 1):
            row_text = self._get_row_text(sheet, row_idx)
            
            # 提取税率
            if not summary.税率:
                tax_rate = self._extract_percentage(row_text, ['税率', '税金'])
                if tax_rate:
                    summary.税率 = tax_rate
                    if self.logger:
                        self.logger.debug(f"    提取税率：{tax_rate*100}%")
            
            # 提取汇损率
            if not summary.汇损率:
                exchange_rate = self._extract_percentage(row_text, ['汇损'])
                if exchange_rate:
                    summary.汇损率 = exchange_rate
                    if self.logger:
                        self.logger.debug(f"    提取汇损率：{exchange_rate*100}%")
        
        # 3. 提取备注（从总计之后开始）
        if zongji_row:
            remark_lines = []
            remark_start = zongji_row + 1
            
            for row_idx in range(remark_start, min(agent_end_row + 1, sheet.max_row + 1)):
                row_text = self._get_row_text(sheet, row_idx)
                
                # 跳过空行
                if not row_text or len(row_text.strip()) < 2:
                    continue
                
                # 跳过已被其他表提取的内容
                if self._should_exclude(row_text):
                    continue
                
                # 收集备注
                remark_lines.append(row_text.strip())
            
            if remark_lines:
                summary.备注 = '\n'.join(remark_lines)
                if self.logger:
                    self.logger.debug(f"    提取备注：{len(remark_lines)}行")
        
        return summary
    
    def _extract_percentage(self, text: str, keywords: list) -> Optional[float]:
        """
        从文本中提取百分比
        
        例如：
        - "税率：19%" → 0.19
        - "汇损：4%" → 0.04
        """
        if not text:
            return None
        
        # 检查是否包含关键词
        has_keyword = any(kw in text for kw in keywords)
        if not has_keyword:
            return None
        
        # 提取百分比：支持多种格式
        # 格式1：19%
        # 格式2：0.19
        # 格式3：19
        
        # 尝试匹配 XX% 格式
        match = re.search(r'(\d+\.?\d*)\s*%', text)
        if match:
            value = float(match.group(1))
            return value / 100.0
        
        # 尝试匹配 0.XX 格式
        match = re.search(r'0\.\d+', text)
        if match:
            return float(match.group(0))
        
        return None
    
    def _get_row_text(self, sheet, row_idx: int) -> str:
        """获取整行的文本（合并所有列）"""
        texts = []
        for col_idx in range(1, min(20, sheet.max_column + 1)):
            try:
                cell = sheet.cell(row=row_idx, column=col_idx)
                if cell.value:
                    texts.append(str(cell.value).strip())
            except:
                pass
        return ' '.join(texts)
    
    def _should_exclude(self, text: str) -> bool:
        """
        判断是否应该排除这行文本
        
        排除规则：
        1. 包含已被其他表提取的关键词
        2. 以特定关键词开头（时效、不含、赔付等）
        """
        if not text:
            return True
        
        text_lower = text.lower().strip()
        
        # 排除以特定关键词开头的行
        exclude_prefixes = [
            '时效', '不含', '赔付', '费用明细', '小计', '总计',
            '代理', '路线', '货物', '品名'
        ]
        
        for prefix in exclude_prefixes:
            if text.startswith(prefix) or text.startswith(prefix + '：') or text.startswith(prefix + ':'):
                return True
        
        # 排除包含多个排除关键词的行
        keyword_count = sum(1 for kw in self.exclude_keywords if kw in text)
        if keyword_count >= 2:
            return True
        
        return False
    
    # ========== BaseExtractor 必需方法 ==========
    
    def _evaluate_quality(self, result: Summary, sheet, **kwargs) -> float:
        """评估提取质量"""
        if not result:
            return 0.0
        
        score = 0.0
        
        # 税率存在：+0.4
        if result.税率 is not None:
            score += 0.4
        
        # 汇损率存在：+0.4
        if result.汇损率 is not None:
            score += 0.4
        
        # 备注存在：+0.2
        if result.备注:
            score += 0.2
        
        return score
    
    def _build_enhancement_prompt(self, result: Summary, sheet, **kwargs) -> str:
        """
        构建LLM增强prompt
        
        ✅ 修复：添加真实的prompt，用于提取税率、汇损率、备注
        """
        # 获取agent区域的行范围
        agent_start_row = kwargs.get('agent_start_row', 1)
        agent_end_row = kwargs.get('agent_end_row', sheet.max_row)
        
        # 序列化sheet内容（只序列化相关区域）
        sheet_text = self._serialize_agent_region(sheet, agent_start_row, agent_end_row)
        
        prompt = f"""请从以下Excel内容中提取Summary信息（税率、汇损率、备注）。

【文本内容】
{sheet_text}

【提取规则】
1. 税率：查找"税率"、"税金"等关键词，提取百分比（如19%）
   - 支持格式："税率：19%"、"税率0.19"、"税 19%"
   - 如果没有找到，返回null
   
2. 汇损率：查找"汇损"关键词，提取百分比（如4%）
   - 支持格式："汇损：4%"、"汇损0.04"
   - 如果没有找到，返回null

3. 备注：提取除了以下内容之外的其他说明文字：
   - 不要提取：代理商名称、费用明细、运输方式、时效说明
   - 不要提取：已在其他字段中的信息（如"税率"、"汇损"等）
   - 只提取真正的备注内容（如特殊要求、注意事项等）
   - 如果没有找到，返回null

【返回格式】（严格JSON格式，不要其他文字）
{{{{
  "税率": 0.19,
  "汇损率": 0.04,
  "备注": "..."
}}}}

注意：
- 税率和汇损率必须是0-1之间的小数（如19%返回0.19）
- 如果某个字段没有找到，返回null
- 备注要过滤掉费用、代理、时效等已被其他表提取的信息
"""
        
        return prompt
    
    def _serialize_agent_region(self, sheet, start_row: int, end_row: int) -> str:
        """
        序列化agent区域的内容
        
        Args:
            sheet: Excel sheet
            start_row: 起始行
            end_row: 结束行
        
        Returns:
            序列化后的文本
        """
        lines = []
        
        for row_idx in range(start_row, min(end_row + 1, sheet.max_row + 1)):
            try:
                cells = []
                for col_idx in range(1, min(10, sheet.max_column + 1)):
                    cell = sheet.cell(row=row_idx, column=col_idx)
                    if cell.value:
                        cells.append(str(cell.value).strip())
                
                if cells:  # 如果这行有内容
                    line = f"行{row_idx}: " + " | ".join(cells)
                    lines.append(line)
            except:
                continue
        
        result = "\n".join(lines)
        
        # 限制长度
        if len(result) > 1500:
            result = result[:1500] + "\n... (内容过长，已截断)"
        
        return result
    
    def _merge_results(self, rule_result: Summary, llm_result) -> Summary:
        """合并规则和LLM结果"""
        return rule_result
    
    def _extract_with_llm(self, sheet, **kwargs) -> Summary:
        """LLM提取（暂不实现）"""
        return Summary()
    
    def _is_valid(self, result: Summary) -> bool:
        """验证结果"""
        # 至少有税率或汇损率之一
        return result and (result.税率 is not None or result.汇损率 is not None)
    
    def _get_default(self) -> Summary:
        """获取默认值"""
        return Summary()


__all__ = ['SummaryExtractor', 'Summary']