# scripts/modules/extractors/route_extractor_v2.py
"""
路线提取器 v2.2（修复版）

【v2.2 修复内容】✅ 2026-02-05
1. ✅ 增强符号清理（彻底移除>、<、*等所有符号）
2. ✅ 支持途径地提取（如"香港-日本" → 途径地=香港, 目的地=日本）
3. ✅ 修复">马来西亚"等格式的符号残留问题
4. ✅ 修复"深圳→香港-日本"等多段式路线提取

【v2.1 修复内容】
1. ✅ 改进质量评估逻辑（让LLM增强真正起作用）
2. ✅ 改进地名清理（移除数字、符号、业务关键词残留）
3. ✅ 改进重量提取（优先识别"总重量"、"合计"等）
4. ✅ 降低LLM触发阈值（0.7 → 让更多情况走LLM）
5. ✅ 加强白名单验证
"""

import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

from .base_extractor import BaseExtractor

try:
    from scripts.data.location_whitelist import is_valid_location, clean_location_text
except ImportError:
    try:
        from data.location_whitelist import is_valid_location, clean_location_text
    except ImportError:
        def is_valid_location(loc):
            return loc and len(loc) >= 2
        def clean_location_text(loc):
            return loc.strip() if loc else ""


@dataclass
class Route:
    """路线数据类"""
    起始地: Optional[str] = None
    目的地: Optional[str] = None
    途径地: Optional[str] = None
    贸易备注: Optional[str] = None
    weight: Optional[float] = None
    volume: Optional[float] = None
    value: Optional[float] = None
    
    def to_dict(self):
        return asdict(self)


class RouteExtractorV2(BaseExtractor):
    """路线提取器 v2.1（完全修复版）"""
    
    # ✅ 修复：降低阈值，让LLM更容易触发
    QUALITY_THRESHOLD = 1.0  # 0.7以下才走LLM增强
    
    def __init__(self, logger=None, llm_client=None, enable_llm=True):
        super().__init__(logger, llm_client, enable_llm)
        
        self.route_separators = ["→", "->", "--", "—", "－", "-", "~", "至"]
        
        self.route_patterns = [
            re.compile(r'^([^\s\-:：]{2,10})\s*[-–—→~至]\s*([^\s:：专线海运空运快递]{2,10})(?:专线|海运|空运|快递)?'),
            re.compile(r'货交\s*([^\s\-:：]{2,20})\s*[-–—→~至]\s*([^\s:：]{2,20})'),
            re.compile(r'([^\s\-:：]{2,20})\s*[-–—→~至]\s*([^\s:：]{2,20})\s*[：:]'),
            re.compile(r'([^\s\-:：]{2,20})\s*[-–—→~至]\s*([^\s:：]{2,20})'),
        ]
        
        self.value_patterns = [
            re.compile(r'货值\s*[:：]?\s*([￥$€£]?)\s*(\d+(?:[,，]\d{3})*(?:\.\d+)?)'),
            re.compile(r'([￥$€£])\s*(\d+(?:[,，]\d{3})*(?:\.\d+)?)'),
        ]
        
        # ✅ 修复：改进重量模式，增加"总重量"、"合计"等关键词
        self.weight_patterns = [
            re.compile(r'总重量\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:kgs?|KGS?|千克|公斤)?', re.IGNORECASE),
            re.compile(r'合计\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:kgs?|KGS?|千克|公斤)?', re.IGNORECASE),
            re.compile(r'重量\s*[:：]?\s*(?:KG)?\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
            re.compile(r'(\d+(?:\.\d+)?)\s*(?:kgs?|KGS?)', re.IGNORECASE),
            re.compile(r'(\d+(?:\.\d+)?)\s*(?:千克|公斤)'),
        ]
        
        self.volume_patterns = [
            re.compile(r'(\d+(?:\.\d+)?)\s*cbm', re.IGNORECASE),
            re.compile(r'(\d+(?:\.\d+)?)\s*(?:立方|方)'),
        ]
        
        # ✅ 修复：扩充业务关键词列表
        self.business_keywords = [
            '海运', '空运', '快递', '铁路', '陆运', '专线', '正清', '双清', 
            '包税', '到门', '到港', 'DDP', 'DAP', 'DDU', 'FOB', 'CIF',
            '一般贸易', '贸易', '贸代', '成本', '询价', '方案', '代理', '过港',  # ✅ 加"贸易"
            '报价', '明细', '费用', '汇总', '宣传册', '伴手礼', '货物',
            '客户', '提供', '重量', '数量', '预估', '易代理'
        ]
    
    def _extract_with_rules(self, sheet, **kwargs) -> Route:
        """规则提取"""
        route = Route()
        sheet_name = sheet.title if hasattr(sheet, 'title') else str(sheet)
        
        # ✅ 修复：提取路线（三级优先级），支持途径地
        route_from_first_line = self._extract_route_from_first_line(sheet)
        if route_from_first_line:
            route.起始地 = route_from_first_line.get('origin')
            route.目的地 = route_from_first_line.get('destination')
            route.途径地 = route_from_first_line.get('via')  # ✅ 新增
        else:
            route_from_content = self._extract_route_from_content(sheet)
            if route_from_content:
                route.起始地 = route_from_content.get('origin')
                route.目的地 = route_from_content.get('destination')
                route.途径地 = route_from_content.get('via')  # ✅ 新增
            else:
                route_from_name = self._extract_route_from_sheet_name(sheet_name)
                if route_from_name:
                    route.起始地 = route_from_name.get('origin')
                    route.目的地 = route_from_name.get('destination')
                    route.途径地 = route_from_name.get('via')  # ✅ 新增
        
        # ✅ 修复：二次清理（确保彻底）
        if route.起始地:
            route.起始地 = self._final_clean_location(route.起始地)
        if route.目的地:
            route.目的地 = self._final_clean_location(route.目的地)
        if route.途径地:  # ✅ 新增
            route.途径地 = self._final_clean_location(route.途径地)
        
        # 提取其他字段
        route.value = self._extract_value(sheet)
        route.weight = self._extract_weight(sheet)
        route.volume = self._extract_volume(sheet)
        
        return route
    
    def _extract_route_from_first_line(self, sheet) -> Optional[Dict[str, str]]:
        """
        从第一行提取完整路线
        
        ✅ 新增：支持途径地识别
        - 格式1: "深圳 → 新加坡" → origin=深圳, destination=新加坡, via=None
        - 格式2: "深圳 → 香港-日本" → origin=深圳, via=香港, destination=日本
        - 格式3: "香港-日本" → via=香港, destination=日本, origin=None（后续会用sheet名补充）
        """
        first_cell = sheet.cell(row=1, column=1)
        if not first_cell.value:
            return None
        
        first_line = str(first_cell.value).strip()
        pattern = self.route_patterns[0]
        match = pattern.search(first_line)
        
        if match:
            origin_raw = match.group(1).strip()
            destination_raw = match.group(2).strip()
            
            # ✅ 新增：检查destination是否包含途径地（如"香港-日本"）
            via = None
            if '-' in destination_raw and '专线' not in destination_raw:
                # 可能是"途径地-目的地"格式
                parts = destination_raw.split('-')
                if len(parts) == 2:
                    via_candidate = self._deep_clean_location(parts[0].strip())
                    dest_candidate = self._deep_clean_location(parts[1].strip())
                    
                    # 验证两个部分都是有效地名
                    if (is_valid_location(via_candidate) and 
                        is_valid_location(dest_candidate) and 
                        via_candidate != dest_candidate):
                        via = via_candidate
                        destination_raw = parts[1].strip()
            
            origin = self._deep_clean_location(origin_raw)
            destination = self._deep_clean_location(destination_raw)
            
            # ✅ 修复：如果没有origin但有via，说明是"香港-日本"这种格式
            # origin会在后续从sheet_name中提取
            if via and not origin:
                return {'origin': None, 'destination': destination, 'via': via}
            
            if self._is_valid_route(origin, destination):
                return {'origin': origin, 'destination': destination, 'via': via}
        
        return None
    
    def _extract_route_from_content(self, sheet) -> Optional[Dict[str, str]]:
        """
        从内容提取路线
        
        ✅ 新增：支持途径地识别
        """
        lines = []
        for row_idx in range(2, min(11, sheet.max_row + 1)):
            for col_idx in range(1, min(10, sheet.max_column + 1)):
                cell = sheet.cell(row=row_idx, column=col_idx)
                if cell.value:
                    lines.append(str(cell.value).strip())
        
        for pattern in self.route_patterns:
            for line in lines:
                match = pattern.search(line)
                if match:
                    origin_raw = match.group(1).strip()
                    destination_raw = match.group(2).strip()
                    
                    # ✅ 新增：检查destination是否包含途径地
                    via = None
                    if '-' in destination_raw and '专线' not in destination_raw:
                        parts = destination_raw.split('-')
                        if len(parts) == 2:
                            via_candidate = self._deep_clean_location(parts[0].strip())
                            dest_candidate = self._deep_clean_location(parts[1].strip())
                            
                            if (is_valid_location(via_candidate) and 
                                is_valid_location(dest_candidate) and 
                                via_candidate != dest_candidate):
                                via = via_candidate
                                destination_raw = parts[1].strip()
                    
                    origin = self._deep_clean_location(origin_raw)
                    destination = self._deep_clean_location(destination_raw)
                    
                    if self._is_valid_route(origin, destination):
                        return {'origin': origin, 'destination': destination, 'via': via}
        
        return None
    
    def _extract_route_from_sheet_name(self, sheet_name: str) -> Optional[Dict[str, str]]:
        """
        从sheet名提取路线
        
        ✅ 新增：支持途径地识别
        """
        for pattern in self.route_patterns:
            match = pattern.search(sheet_name)
            if match:
                origin_raw = match.group(1).strip()
                destination_raw = match.group(2).strip()
                
                # ✅ 新增：检查destination是否包含途径地
                via = None
                if '-' in destination_raw and '专线' not in destination_raw:
                    parts = destination_raw.split('-')
                    if len(parts) == 2:
                        via_candidate = self._deep_clean_location(parts[0].strip())
                        dest_candidate = self._deep_clean_location(parts[1].strip())
                        
                        if (is_valid_location(via_candidate) and 
                            is_valid_location(dest_candidate) and 
                            via_candidate != dest_candidate):
                            via = via_candidate
                            destination_raw = parts[1].strip()
                
                origin = self._deep_clean_location(origin_raw)
                destination = self._deep_clean_location(destination_raw)
                
                if self._is_valid_route(origin, destination):
                    return {'origin': origin, 'destination': destination, 'via': via}
        
        return None
    
    def _deep_clean_location(self, location: str) -> str:
        """深度清理地点（第一遍）"""
        if not location:
            return ""
        
        cleaned = clean_location_text(location)
        
        # 移除业务关键词
        for _ in range(3):
            prev = cleaned
            for keyword in self.business_keywords:
                if keyword in cleaned:
                    parts = cleaned.split(keyword)
                    if parts[0].strip():
                        cleaned = parts[0].strip()
                        break
                    elif len(parts) > 1 and parts[1].strip():
                        cleaned = parts[1].strip()
                        break
            if cleaned == prev:
                break
        
        cleaned = cleaned.strip('：:,，。.、 \t\n[]【】()')
        
        # 提取常见地名
        if not cleaned or len(cleaned) < 2:
            common_locations = [
                '深圳', '上海', '北京', '广州', '香港', '澳门', '新加坡', 
                '印度', '泰国', '越南', '马来西亚', '马来', '菲律宾', '印尼',
                '沙特', '迪拜', '英国', '法国', '德国', '西班牙', '意大利',
                '美国', '巴西', '澳洲', '澳大利亚', '新西兰', '日本', '韩国',
                '国内', '中国', '达拉斯', '法兰克福', '荷兰', '柔佛'
            ]
            for loc in common_locations:
                if loc in location:
                    cleaned = loc
                    break
        
        return cleaned
    
    def _final_clean_location(self, location: str) -> str:
        """
        ✅ 增强版：最终清理（二次清理）
        
        移除所有数字、符号、业务关键词残留
        """
        if not location:
            return ""
        
        cleaned = location
        
        # 1. 移除数字和点号（如"1.深圳" → "深圳"）
        cleaned = re.sub(r'^\d+[\.\、]\s*', '', cleaned)
        cleaned = re.sub(r'\d+', '', cleaned)
        
        # 2. ✅ 增强：移除所有符号残留（包括>、<、*等）
        # 2.1 移除开头的符号
        cleaned = re.sub(r'^[>\<\*\+\=\|/\\!@#$%^&\(\)\[\]\{\}]+', '', cleaned)
        # 2.2 移除结尾的符号
        cleaned = re.sub(r'[>\<\*\+\=\|/\\!@#$%^&\(\)\[\]\{\}]+$', '', cleaned)
        # 2.3 移除箭头等常见符号
        cleaned = re.sub(r'[-–—→~]+$', '', cleaned)
        cleaned = re.sub(r'^[-–—→~]+', '', cleaned)
        
        # 3. 再次移除业务关键词
        for keyword in self.business_keywords:
            if keyword in cleaned:
                cleaned = cleaned.replace(keyword, '')
        
        # 4. 清理空白和特殊字符
        cleaned = cleaned.strip('：:,，。.、 \t\n[]【】()- ><*+=/\\')
        
        return cleaned
    
    def _is_valid_route(self, origin: str, destination: str) -> bool:
        """验证路线是否有效"""
        if not origin or not destination:
            return False
        
        # 单字地名验证
        if len(origin) == 1 or len(destination) == 1:
            valid_single_char = {'中', '美', '日', '韩', '英', '法', '德'}
            if origin not in valid_single_char or destination not in valid_single_char:
                return False
        
        # 白名单验证
        if not is_valid_location(origin) or not is_valid_location(destination):
            return False
        
        # 不能相等
        if origin == destination:
            return False
        
        return True
    
    def _extract_value(self, sheet) -> Optional[float]:
        """提取货值"""
        for row_idx in range(1, min(21, sheet.max_row + 1)):
            for col_idx in range(1, min(10, sheet.max_column + 1)):
                cell = sheet.cell(row=row_idx, column=col_idx)
                if not cell.value:
                    continue
                
                cell_text = str(cell.value).strip()
                for pattern in self.value_patterns:
                    match = pattern.search(cell_text)
                    if match:
                        try:
                            if len(match.groups()) >= 2:
                                amount_str = match.group(2)
                            else:
                                amount_str = match.group(1)
                            amount_str = amount_str.replace(',', '').replace('，', '')
                            return float(amount_str)
                        except (ValueError, AttributeError):
                            continue
        return None
    
    def _extract_weight(self, sheet) -> Optional[float]:
        """
        ✅ 修复：改进重量提取逻辑
        
        【优先级】
        1. 明确标注"总重量"、"合计"的值
        2. 标注"重量：XX"的值
        3. 所有重量值中的最大值
        """
        # 第1优先级：查找"总重量"、"合计"
        for row_idx in range(1, min(31, sheet.max_row + 1)):
            for col_idx in range(1, min(10, sheet.max_column + 1)):
                cell = sheet.cell(row=row_idx, column=col_idx)
                if not cell.value:
                    continue
                
                cell_text = str(cell.value).strip()

                # ✅ 新增：识别"重量: KG"标签（分离格式）
                if self._is_weight_label(cell_text):
                    weight = self._extract_weight_from_adjacent(sheet, row_idx, col_idx)
                    if weight:
                        if self.logger:
                            self.logger.debug(f"      ✅ 找到重量（分离格式）: {weight}kg")
                        return weight
                
                # 尝试"总重量"、"合计"模式
                for pattern in self.weight_patterns[:2]:  # 前两个是总重量和合计
                    match = pattern.search(cell_text)
                    if match:
                        try:
                            weight = float(match.group(1))
                            if 0.1 <= weight <= 50000:
                                if self.logger:
                                    self.logger.debug(f"      ✅ 找到总重量: {weight}kg")
                                return weight
                        except (ValueError, AttributeError):
                            continue
        
        # 第2优先级：查找"重量：XX"
        for row_idx in range(1, min(31, sheet.max_row + 1)):
            for col_idx in range(1, min(10, sheet.max_column + 1)):
                cell = sheet.cell(row=row_idx, column=col_idx)
                if not cell.value:
                    continue
                
                cell_text = str(cell.value).strip()
                
                # 尝试"重量："模式
                pattern = self.weight_patterns[2]  # "重量："
                match = pattern.search(cell_text)
                if match:
                    try:
                        weight = float(match.group(1))
                        if 0.1 <= weight <= 50000:
                            if self.logger:
                                self.logger.debug(f"      ✅ 找到重量标注: {weight}kg")
                            return weight
                    except (ValueError, AttributeError):
                        continue
        
        # 第3优先级：收集所有重量，取最大值
        weights = []
        for row_idx in range(1, min(31, sheet.max_row + 1)):
            for col_idx in range(1, min(10, sheet.max_column + 1)):
                cell = sheet.cell(row=row_idx, column=col_idx)
                if not cell.value:
                    continue
                
                cell_text = str(cell.value).strip()
                
                # 尝试所有重量模式
                for pattern in self.weight_patterns[3:]:
                    matches = pattern.finditer(cell_text)
                    for match in matches:
                        try:
                            weight = float(match.group(1))
                            if 0.1 <= weight <= 50000:
                                weights.append(weight)
                        except (ValueError, AttributeError):
                            continue
        
        if weights:
            unique_weights = list(set(weights))
            max_weight = max(unique_weights)
            if self.logger:
                self.logger.debug(f"      ⚠️  使用最大重量: {max_weight}kg (共{len(unique_weights)}个重量值)")
            return max_weight
        
        return None
    
    def _extract_volume(self, sheet) -> Optional[float]:
        """提取体积"""
        for row_idx in range(1, min(31, sheet.max_row + 1)):
            for col_idx in range(1, min(10, sheet.max_column + 1)):
                cell = sheet.cell(row=row_idx, column=col_idx)
                if not cell.value:
                    continue
                
                cell_text = str(cell.value).strip()
                for pattern in self.volume_patterns:
                    match = pattern.search(cell_text)
                    if match:
                        try:
                            volume = float(match.group(1))
                            if 0.01 <= volume <= 1000:
                                return volume
                        except (ValueError, AttributeError):
                            continue
        return None
    
    def _evaluate_quality(self, result: Route, sheet, **kwargs) -> float:
        """
        ✅ 修复：改进质量评估逻辑
        
        【评估维度】
        1. 基础验证（40%）：有起始地、目的地
        2. 地名质量（30%）：长度合理、无数字/符号残留
        3. 业务关键词残留（30%）：无"贸易"、"专线"等残留
        """
        if not result or not result.起始地 or not result.目的地:
            return 0.0
        
        if result.起始地 in ['未知', '待定', '暂无'] or result.目的地 in ['未知', '待定', '暂无']:
            return 0.0
        
        if result.起始地 == result.目的地:
            return 0.0
        
        score = 0.4  # 基础分40%
        
        # ✅ 新增：地名质量检查（30%）
        quality_score = 0.0
        
        # 检查长度（2-8字为佳）
        if 2 <= len(result.起始地) <= 8 and 2 <= len(result.目的地) <= 8:
            quality_score += 0.15
        elif len(result.起始地) > 10 or len(result.目的地) > 10:
            quality_score -= 0.1  # 太长扣分
        
        # 检查是否有数字残留
        if re.search(r'\d', result.起始地) or re.search(r'\d', result.目的地):
            quality_score -= 0.1  # 有数字扣分
        else:
            quality_score += 0.1
        
        # 检查是否有符号残留
        if re.search(r'[-–—.]+', result.起始地) or re.search(r'[-–—.]+', result.目的地):
            quality_score -= 0.05  # 有符号扣分
        else:
            quality_score += 0.05
        
        score += max(0, min(quality_score, 0.3))
        
        # ✅ 新增：业务关键词检查（30%）
        keyword_score = 0.3
        for keyword in ['贸易', '专线', '代理', '海运', '空运', '快递']:
            if keyword in result.起始地 or keyword in result.目的地:
                keyword_score -= 0.1
        
        score += max(0, keyword_score)
        
        if self.logger:
            self.logger.debug(f"      📊 质量评分: {score:.2f} (阈值={self.QUALITY_THRESHOLD})")
        
        return score
    
    def _build_enhancement_prompt(self, result: Route, sheet, **kwargs) -> str:
        """构建LLM增强提示词"""
        content_lines = []
        for row_idx in range(1, min(21, sheet.max_row + 1)):
            row_data = []
            for col_idx in range(1, min(10, sheet.max_column + 1)):
                cell = sheet.cell(row=row_idx, column=col_idx)
                if cell.value:
                    row_data.append(str(cell.value)[:50])
            if row_data:
                content_lines.append(f"行{row_idx}: {' | '.join(row_data)}")
        
        content = '\n'.join(content_lines)
        
        prompt = f"""请从以下Excel内容中提取运输路线信息。

【Excel内容】：
{content}

【当前提取结果】：
起始地: {result.起始地 or "未提取"}
目的地: {result.目的地 or "未提取"}
重量: {result.weight or "未提取"} kg
货值: {result.value or "未提取"}
体积: {result.volume or "未提取"} cbm

【提取要求】：
1. 起始地和目的地：只提取纯地名，不要包含数字、符号、"贸易"、"专线"等词
2. **重量**：
   - 标准格式：100kg、100KG
   - ✅ 分离格式：左边"重量: KG"，右边"100"
   - ✅ 如果看到类似"重量: KG | 100"，提取100
   - 查找"总重量"、"合计"等关键词
3. 货值：提取货物价值的金额
4. 体积：提取体积（cbm）

【返回格式】：
{{
    "起始地": "纯地名",
    "目的地": "纯地名",
    "重量": 数字,
    "货值": 数字,
    "体积": 数字
}}

注意：如果某个字段确实无法提取，返回null。
"""
        return prompt
    
    def _merge_results(self, rule_result: Route, llm_result) -> Route:
        """合并规则和LLM结果"""
        if not llm_result or not isinstance(llm_result, dict):
            return rule_result
        
        # ✅ LLM结果优先（因为LLM被触发说明规则提取质量不高）
        if llm_result.get('起始地'):
            rule_result.起始地 = llm_result['起始地']
        if llm_result.get('目的地'):
            rule_result.目的地 = llm_result['目的地']
        if llm_result.get('重量'):
            rule_result.weight = llm_result['重量']
        if llm_result.get('货值'):
            rule_result.value = llm_result['货值']
        if llm_result.get('体积'):
            rule_result.volume = llm_result['体积']
        
        return rule_result
    
    def _extract_with_llm(self, sheet, **kwargs) -> Route:
        return None
    
    def _is_valid(self, result: Route) -> bool:
        if not result or not result.起始地 or not result.目的地:
            return False
        if result.起始地 in ['未知', '待定', '暂无'] or result.目的地 in ['未知', '待定', '暂无']:
            return False
        if result.起始地 == result.目的地:
            return False
        return True
    
    def _is_weight_label(self, text: str) -> bool:
        """
        判断是否是重量标签（新增）
        
        【识别】
        - "重量: KG"
        - "重量：KG"
        - "重量:KG"
        - "重量 KG"
        - "重量(KG)"
        - "WEIGHT: KG"
        """
        if not text:
            return False
        
        text_upper = text.upper().strip()
        
        patterns = [
            r'重量[：:\s]*KG',
            r'重量[：:\s]*千克',
            r'WEIGHT[：:\s]*KG',
            r'重量[\(（]KG[\)）]',
        ]
        
        for pattern in patterns:
            if re.search(pattern, text_upper):
                return True
        
        return False

    def _extract_weight_from_adjacent(self, sheet, row_idx: int, col_idx: int) -> Optional[float]:
        """
        从相邻单元格提取重量数值（新增）
        
        【检查顺序】
        1. 右边单元格（col_idx + 1）
        2. 下边单元格（row_idx + 1）
        3. 同行后面2个单元格（col_idx + 2, col_idx + 3）
        """
        # 1. 检查右边
        try:
            right_cell = sheet.cell(row=row_idx, column=col_idx + 1)
            if right_cell.value:
                weight = self._extract_number(str(right_cell.value))
                if weight and 0.1 <= weight <= 50000:
                    return weight
        except:
            pass
        
        # 2. 检查下边
        try:
            below_cell = sheet.cell(row=row_idx + 1, column=col_idx)
            if below_cell.value:
                weight = self._extract_number(str(below_cell.value))
                if weight and 0.1 <= weight <= 50000:
                    return weight
        except:
            pass
        
        # 3. 检查同行后面2个单元格
        for offset in [2, 3]:
            try:
                cell = sheet.cell(row=row_idx, column=col_idx + offset)
                if cell.value:
                    weight = self._extract_number(str(cell.value))
                    if weight and 0.1 <= weight <= 50000:
                        return weight
            except:
                continue
        
        return None

    def _extract_number(self, text: str) -> Optional[float]:
        """
        从文本中提取数字（新增）
        
        【支持格式】
        - "100"
        - "100.5"
        - "  100  "
        """
        if not text:
            return None
        
        text = text.strip()
        
        # 尝试直接转换
        try:
            return float(text)
        except:
            pass
        
        # 提取数字部分
        match = re.search(r'(\d+\.?\d*)', text)
        if match:
            try:
                return float(match.group(1))
            except:
                pass
        
        return None
    
    def _get_default(self) -> Route:
        return Route()


    def _serialize_sheet(self, sheet, max_rows: int = 50) -> str:
        """将sheet序列化为文本（给LLM使用）"""
        lines = [f"Sheet名称: {sheet.title}", ""]
        
        for row_idx, row in enumerate(sheet.iter_rows(max_row=max_rows), 1):
            cells = [str(cell.value or '') for cell in row]
            if any(cell.strip() for cell in cells):
                line = f"行{row_idx}: " + " | ".join(cells)
                lines.append(line)
        
        return "\n".join(lines)


__all__ = ['RouteExtractorV2', 'Route']