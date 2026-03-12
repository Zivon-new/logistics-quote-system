# scripts/modules/extractors/goods_total_extractor.py
"""
整单货物提取器 - 最终修复版 V2

【新增修复】
✅ 过滤"税率"、"10月"等垃圾
✅ 支持"X台XXX"格式（Dell服务器）
✅ 支持括号内的货物名称（雨伞）
✅ 扫描所有行，不遗漏任何货物
"""

import re
from typing import List, Optional
from dataclasses import dataclass, asdict

from .base_extractor import BaseExtractor


@dataclass
class GoodsTotal:
    """整单货物数据类"""
    货物名称: Optional[str] = None
    实际重量: Optional[float] = None
    货值: Optional[float] = None
    总体积: Optional[float] = None
    备注: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


class GoodsTotalExtractor(BaseExtractor):
    """整单货物提取器（最终修复版V2）"""
    
    QUALITY_THRESHOLD = 0.3
    
    def __init__(self, logger=None, llm_client=None, enable_llm=True):
        super().__init__(logger, llm_client, enable_llm)
        
        # 货物关键词
        self.goods_keywords = [
            '电池', '展示柜', '标本', '电子屏', '陶坛', '板卡', '模块',
            '服务器', '交换机', '路由器', '光纤', '网线', '雨伞', '风扇',
            '礼品', '宣传册', '伴手礼', '柜', '屏', 'Dell', 'Nokia'
        ]
        
        # ✅ 扩充的无效关键词列表
        self.invalid_keywords = [
            # 运输相关
            '专线', '运费', '货交', '双清', '包税', '到门', '派送', '提货',
            '卸货', '转运', '操作费', '物流费', '仓储费', '包装费', '木箱费',
            '提货费', '入库', '出库', '装卸', '短驳',
            # 代理相关
            '代理', '合作', '协议', '未合作', '新代理', '仅合作',
            # 费用相关
            '费用', '明细', '小计', '总计', '合计', '报价', '等时费',
            # 备注相关
            '备注', '不含', '时效', '赔付', '注：', '注意', '请', '标签',
            '声明', '标准',
            # 税率相关 ✅ 新增
            '税率', '税', 'HS CODE', '关税', '增值税', 'VAT', 'GST',
            # 日期相关 ✅ 新增
            '10月', '11月', '12月', '1月', '2月', '3月', '4月', '5月',
            '6月', '7月', '8月', '9月', '月2', '月3',
            # 地点相关
            '香港', '深圳', '北京', '上海', '达拉斯', '新加坡', '马来',
            '沙特', '澳门', '澳洲', '英国', '法兰克福', '越南', '西班牙',
            '门头沟', '机房', '指定地址',
            # 其他
            '重量', 'KG', 'kg', '地址', '询价', '方案', '预估', '交货',
            '天左右', '受天气', '影响', '晚开船', '查验', '顺延',
            '丢失', '赔偿', '保险', '购买', '如果', '需要', '左右',
            '陆运', '海运', '空运', '快递', 'USD', '货币', 'RMB', 'CNY',
            '报关', '派送', '等时', '垃圾', '木托', '减震', '回收',
            '次日', '二次', '空木箱', '贸易', '进口', '出口', '海关',
            '灰清', '未购买', '按', '倍', '如果丢失', '全赔', 'CODE'
        ]
        
        # 品类词
        self.category_keywords = [
            '耗材', '设备', '网络设备', '交换机'
        ]
    
    def _extract_with_rules(self, sheet, **kwargs) -> List[GoodsTotal]:
        """规则提取"""
        goods_list = []
        
        # ✅ 策略1：从第1行提取货物名称
        first_row_goods = self._extract_from_first_row(sheet)
        if first_row_goods:
            goods_list.append(first_row_goods)
            if self.logger:
                self.logger.debug(f"    行1提取: {first_row_goods.货物名称}")
        
        # ✅ 策略2：扫描所有行
        max_scan_rows = sheet.max_row
        
        for row_idx in range(2, max_scan_rows + 1):
            goods = self._extract_from_row(sheet, row_idx)
            if goods and goods.货物名称 and goods.货物名称 != "未提取":
                if not self._is_duplicate(goods, goods_list):
                    goods_list.append(goods)
                    if self.logger:
                        self.logger.debug(f"    行{row_idx}提取: {goods.货物名称}")
        
        if self.logger:
            self.logger.info(f"  📦 GoodsTotal提取到 {len(goods_list)} 个货物")
        
        return goods_list
    
    def _extract_from_first_row(self, sheet) -> Optional[GoodsTotal]:
        """从第1行提取货物"""
        row_text = self._get_row_text(sheet, 1)
        if not row_text:
            return None
        
        goods = GoodsTotal()
        
        # 提取货物名称
        goods_name = self._extract_goods_name_from_text(row_text)
        if not goods_name:
            return None
        
        goods.货物名称 = goods_name
        
        # 提取重量
        weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:KGS?|千克|公斤)', row_text, re.IGNORECASE)
        if weight_match:
            goods.实际重量 = float(weight_match.group(1))
        
        # 提取体积
        volume_match = re.search(r'(\d+(?:\.\d+)?)\s*cbm', row_text, re.IGNORECASE)
        if volume_match:
            goods.总体积 = float(volume_match.group(1))
        
        # 提取货值
        goods.货值 = self._extract_value_from_row(sheet, 1)
        if not goods.货值:
            goods.货值 = self._extract_value_from_row(sheet, 2)
        
        return goods
    
    def _extract_goods_name_from_text(self, text: str) -> Optional[str]:
        """
        从文本中提取货物名称
        
        ✅ 新增策略：
        1. "X台XXX"格式（Dell服务器）
        2. 括号内的货物名称（雨伞）
        3. "XX件XX"格式
        4. 货物关键词
        """
        # ✅ 策略1：匹配"X台XXX"格式
        # "4台Dell PowerEdge R7625" → "4台Dell PowerEdge R7625"
        match = re.search(r'(\d+台[^\s，。\n]+(?:\s+[A-Za-z0-9\-]+){0,3})', text)
        if match:
            raw_name = match.group(1).strip()
            cleaned = self._clean_goods_name(raw_name)
            if cleaned != "未提取":
                return cleaned
        
        # ✅ 策略2：括号内的货物名称
        # "（长雨伞和短雨伞）" → "长雨伞和短雨伞"
        match = re.search(r'[（(]([^）)]+雨伞[^）)]*)[）)]', text)
        if match:
            raw_name = match.group(1).strip()
            cleaned = self._clean_goods_name(raw_name)
            if cleaned != "未提取":
                return cleaned
        
        # ✅ 策略3：匹配"XX件XX"格式
        match = re.match(r'(\d+件[^/\s]+)', text)
        if match:
            raw_name = match.group(1).strip()
            cleaned = self._clean_goods_name(raw_name)
            if cleaned != "未提取":
                return cleaned
        
        # ✅ 策略4：查找货物关键词
        for keyword in self.goods_keywords:
            if keyword in text:
                idx = text.find(keyword)
                
                # 向前找到空格或开头
                start = max(0, idx - 15)
                for i in range(idx - 1, start - 1, -1):
                    if i < 0 or text[i] in [' ', '，', '。', '\n', '\t', '、', '：']:
                        start = i + 1
                        break
                
                # 向后找到空格或特殊字符
                end = min(len(text), idx + len(keyword) + 20)
                for i in range(idx + len(keyword), end):
                    if i >= len(text) or text[i] in [' ', '，', '。', '\n', '\t', '、', '/', '客', '预']:
                        end = i
                        break
                
                raw_name = text[start:end].strip()
                cleaned = self._clean_goods_name(raw_name)
                if cleaned != "未提取":
                    return cleaned
        
        return None
    
    def _extract_from_row(self, sheet, row_idx: int) -> Optional[GoodsTotal]:
        """从单行提取货物"""
        row_text = self._get_row_text(sheet, row_idx)
        if not row_text or len(row_text) < 3:
            return None
        
        goods = GoodsTotal()
        
        # ✅ 模式1: "XX件XX/5.46cbm/910kg"
        pattern1 = re.compile(r'(.+?)/\s*(\d+(?:\.\d+)?)\s*cbm\s*/\s*(\d+(?:\.\d+)?)\s*kg', re.IGNORECASE)
        match = pattern1.search(row_text)
        if match:
            raw_name = match.group(1).strip()
            if '/' in raw_name:
                raw_name = raw_name.split('/')[0].strip()
            
            goods.货物名称 = self._clean_goods_name(raw_name)
            goods.总体积 = float(match.group(2))
            goods.实际重量 = float(match.group(3))
            goods.货值 = self._extract_value_from_row(sheet, row_idx)
            
            return goods if goods.货物名称 != "未提取" else None
        
        # ✅ 模式2: 第1列有货物关键词
        first_col_text = self._get_cell_value(sheet, row_idx, 1)
        if first_col_text:
            goods_name = self._extract_goods_name_from_text(first_col_text)
            if goods_name:
                goods.货物名称 = goods_name
                
                # 提取尺寸
                dimension_match = re.search(r'(\d+(?:\.\d+)?)\s*[*×xX]\s*(\d+(?:\.\d+)?)\s*[*×xX]\s*(\d+(?:\.\d+)?)', row_text)
                if dimension_match:
                    l = float(dimension_match.group(1))
                    w = float(dimension_match.group(2))
                    h = float(dimension_match.group(3))
                    goods.总体积 = self._calculate_volume(l, w, h)
                
                # 提取重量
                weight_text = self._get_cell_value(sheet, row_idx, 3)
                if weight_text:
                    try:
                        goods.实际重量 = float(re.sub(r'[^\d.]', '', weight_text))
                    except:
                        pass
                
                return goods
        
        return None
    
    def _clean_goods_name(self, raw_name: str) -> str:
        """
        清理货物名称（严格模式）
        """
        if not raw_name:
            return "未提取"
        
        # ✅ 1. 去除/后面的内容
        if '/' in raw_name:
            raw_name = raw_name.split('/')[0].strip()
        
        # ✅ 2. 去除换行符
        raw_name = raw_name.replace('\n', ' ').replace('\r', ' ').strip()
        
        # ✅ 3. 长度限制
        if len(raw_name) > 50:
            raw_name = raw_name[:50]
        
        if len(raw_name) < 2:
            return "未提取"
        
        # ✅ 4. 严格过滤无效关键词
        for keyword in self.invalid_keywords:
            if keyword in raw_name:
                return "未提取"
        
        # ✅ 5. 去除冒号结尾
        if raw_name.endswith('：') or raw_name.endswith(':'):
            raw_name = raw_name[:-1].strip()
        
        if len(raw_name) < 2:
            return "未提取"
        
        # ✅ 6. 过滤品类词
        if raw_name in self.category_keywords:
            return "未提取"
        
        return raw_name
    
    def _calculate_volume(self, length: float, width: float, height: float) -> float:
        """计算体积"""
        if length < 10:
            volume = length * width * height
        elif length < 1000:
            volume = (length * width * height) / 1000000
        else:
            volume = (length * width * height) / 1000000000
        
        return round(volume, 3) if 0.001 < volume < 100 else None
    
    def _is_duplicate(self, goods: GoodsTotal, goods_list: List[GoodsTotal]) -> bool:
        """检查是否重复"""
        for existing in goods_list:
            if existing.货物名称 == goods.货物名称:
                return True
        return False
    
    def _extract_value_from_row(self, sheet, row_idx: int) -> Optional[float]:
        """提取货值"""
        row_text = self._get_row_text(sheet, row_idx)
        
        match = re.search(r'货值\s*[:：]?\s*([￥$€£]?)\s*(\d+(?:[,，]\d{3})*(?:\.\d+)?)', row_text)
        if match:
            try:
                amount_str = match.group(2).replace(',', '').replace('，', '')
                value = float(amount_str)
                if value >= 100:
                    return value
            except:
                pass
        
        return None
    
    def _get_row_text(self, sheet, row_idx: int) -> str:
        """获取整行文本"""
        texts = []
        for col_idx in range(1, min(10, sheet.max_column + 1)):
            cell = sheet.cell(row=row_idx, column=col_idx)
            if cell.value:
                texts.append(str(cell.value).strip())
        return ' '.join(texts)
    
    def _get_cell_value(self, sheet, row_idx: int, col_idx: int) -> Optional[str]:
        """获取单元格值"""
        try:
            cell = sheet.cell(row=row_idx, column=col_idx)
            if cell.value:
                return str(cell.value).strip()
        except:
            pass
        return None
    
    # ========== BaseExtractor 必需方法 ==========
    
    def _evaluate_quality(self, result: List[GoodsTotal], sheet, **kwargs) -> float:
        """
        质量评估（GoodsTotal总是返回低分，强制使用LLM）
        
        因为goods_total格式混乱，规则提取不可靠，所以总是返回低分
        强制调用LLM增强
        """
        # ✅ 总是返回0.3，低于阈值0.7，强制调用LLM
        return 0.3
    
    def _build_enhancement_prompt(self, result: List[GoodsTotal], sheet, **kwargs) -> str:
        """
        构建LLM提取prompt（GoodsTotal完全依赖LLM）
        """
        # 获取sheet内容（前50行）
        sheet_text = self._serialize_sheet(sheet, max_rows=30)  # 减少行数避免prompt太长
        
        prompt = f"""请从以下Excel内容中提取货物信息。

【文本内容】
{sheet_text}

【提取规则】
1. 只提取真实的货物名称（如"展示柜"、"Dell服务器"、"粮食标本"、"雨伞"）
2. 忽略以下内容：
   - 代理商名称（如"银顺达"、"欧力物流"、"融迅"）
   - 费用项目（如"海运费"、"报关费"、"操作费"、"THC"）
   - 时效说明（如"3-5天"、"8-12个工作日"）
   - 赔付标准、不含说明
   - 专线名称（如"国内-西班牙海运专线"）
   - 税率信息（如"税率：19%"、"HS CODE"）
   - 日期信息（如"10月"、"11月"）
   - 地点名称（如"深圳"、"香港"、"达拉斯"）
3. 提取货物的：
   - 实际重量(kg) - 提取数字，如果没有返回null
   - 总体积(cbm) - 提取数字，如果没有返回null
   - 货值 - 提取数字，如果没有返回null

【返回格式】（严格JSON数组，不要其他文字）
[
  {{{{
    "货物名称": "...",
    "实际重量": ...,
    "总体积": ...,
    "货值": ...
  }}}}
]

注意：
- 如果没有找到任何货物，返回空数组 []
- 货物名称必须具体，不能是"货物"、"物品"、"耗材"这种泛称
- 重量、体积、货值必须是数字或null，不是字符串
- 不要提取代理商名称、费用名称、运输方式等非货物信息
"""
        
        return prompt
    
    def _merge_results(self, rule_result: List[GoodsTotal], llm_result) -> List[GoodsTotal]:
        """合并结果（GoodsTotal优先使用LLM结果）"""
        if not llm_result or not isinstance(llm_result, list):
            return rule_result
        
        # 将LLM返回的dict列表转换为GoodsTotal对象
        goods_list = []
        for item in llm_result:
            if isinstance(item, dict):
                goods = GoodsTotal()
                goods.货物名称 = item.get('货物名称')
                goods.实际重量 = item.get('实际重量')
                goods.总体积 = item.get('总体积')
                goods.货值 = item.get('货值')
                
                # 验证货物名称有效
                if goods.货物名称 and goods.货物名称 != "未提取":
                    goods_list.append(goods)
        
        if self.logger and len(goods_list) > 0:
            self.logger.info(f"      LLM提取到{len(goods_list)}个货物")
        
        return goods_list if goods_list else rule_result
    
    def _extract_with_llm(self, sheet, **kwargs) -> List[GoodsTotal]:
        return []
    
    def _is_valid(self, result: List[GoodsTotal]) -> bool:
        return result and len(result) > 0
    
    def _get_default(self) -> List[GoodsTotal]:
        return []


__all__ = ['GoodsTotalExtractor', 'GoodsTotal']