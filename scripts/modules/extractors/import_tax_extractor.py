# scripts/modules/extractors/import_tax_extractor.py
"""
进口税率提取器

从 summary_extractor 产出的 进口税率原文 中，解析出逐条结构化税项记录，
用于写入 import_tax_items 表。

每条税项格式示例：
  交换机8517620090 印度原产，税率 0+10%
  光缆85442000 原产中国，税率25%+10%
  笔记本电脑8471300000 马来西亚，关税0% 增值税13%
"""

import re
from typing import List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ImportTaxItem:
    """单条进口税项"""
    货物描述:  Optional[str]   = None   # 货物名称（原文）
    HS编码:    Optional[str]   = None   # 8-10位HS编码
    原产国:    Optional[str]   = None   # 原产地/原产国
    关税率:    Optional[float] = None   # 关税率（小数，如0.25）
    增值税率:  Optional[float] = None   # 增值税率（小数，如0.13）
    综合税率:  Optional[float] = None   # 综合税率（如无单独字段则用关税+增值税估算）
    税金金额:  Optional[float] = None   # 该货物对应税金金额（若原文有）
    原文:      Optional[str]   = None   # 该条目原始文本

    def to_dict(self):
        return asdict(self)


# ── 正则常量 ────────────────────────────────────────────────────────────────

# HS编码：8-10位数字，可能带点或空格分隔（使用lookaround避免中文字边界问题）
_RE_HS = re.compile(r'(?<!\d)(\d{4}[\.\s]?\d{2}[\.\s]?\d{2,4})(?!\d)')

# 百分比税率（支持 "0+10%"、"25%+10%"、"0%+10%"、"13%" 等）
_RE_PCT_PAIR = re.compile(r'(\d+\.?\d*)\s*%?\s*\+\s*(\d+\.?\d*)\s*%')  # A+B% or A%+B%
_RE_PCT_SINGLE = re.compile(r'(\d+\.?\d*)\s*%')

# 关键词：关税 / 增值税
_RE_GUANSHUI = re.compile(r'关税\s*[:：]?\s*(\d+\.?\d*)\s*%', re.IGNORECASE)
_RE_ZENZHISHUI = re.compile(r'增值税\s*[:：]?\s*(\d+\.?\d*)\s*%', re.IGNORECASE)

# 原产国关键词映射（顺序敏感，越长越靠前以防短串覆盖）
_COUNTRY_PATTERNS = [
    (re.compile(r'马来西亚|Malaysia', re.I), '马来西亚'),
    (re.compile(r'越南|Vietnam', re.I),     '越南'),
    (re.compile(r'印度尼西亚|Indonesia', re.I), '印度尼西亚'),
    (re.compile(r'印度|India', re.I),       '印度'),
    (re.compile(r'泰国|Thailand', re.I),    '泰国'),
    (re.compile(r'菲律宾|Philippines', re.I), '菲律宾'),
    (re.compile(r'美国|USA|United States', re.I), '美国'),
    (re.compile(r'德国|Germany', re.I),     '德国'),
    (re.compile(r'日本|Japan', re.I),       '日本'),
    (re.compile(r'韩国|South Korea|Korea', re.I), '韩国'),
    (re.compile(r'中国|China|大陆', re.I),  '中国'),
    (re.compile(r'台湾|Taiwan', re.I),      '台湾'),
    (re.compile(r'香港|Hongkong|Hong Kong', re.I), '香港'),
    (re.compile(r'英国|UK|United Kingdom', re.I), '英国'),
    (re.compile(r'法国|France', re.I),      '法国'),
]

# 原产地触发词（用于定位原产国信息）
_RE_ORIGIN_TRIGGER = re.compile(
    r'原产地?[:：]?\s*(\S+)|(\S+)\s*原产'
)


def _pct_to_float(s: str) -> float:
    """'13' → 0.13"""
    return float(s) / 100.0


def _extract_hs(text: str) -> Optional[str]:
    m = _RE_HS.search(text)
    if m:
        return re.sub(r'[\.\s]', '', m.group(1))
    return None


def _extract_country(text: str) -> Optional[str]:
    for pat, name in _COUNTRY_PATTERNS:
        if pat.search(text):
            return name
    return None


def _extract_rates(text: str):
    """
    返回 (关税率, 增值税率, 综合税率) 三元组（均为小数或None）。
    支持：
      - "关税25% 增值税10%"
      - "税率 0+10%"  → 关税0, 增值税10
      - "税率25%+10%" → 关税25, 增值税10
      - "综合税率35%"
      - 单个 "%"
    """
    guanshui = None
    zengzhishui = None
    zonghe = None

    # 优先显式关键词
    mg = _RE_GUANSHUI.search(text)
    if mg:
        guanshui = _pct_to_float(mg.group(1))
    mz = _RE_ZENZHISHUI.search(text)
    if mz:
        zengzhishui = _pct_to_float(mz.group(1))

    # A%+B% 模式（关税+增值税）
    if guanshui is None and zengzhishui is None:
        mp = _RE_PCT_PAIR.search(text)
        if mp:
            guanshui = _pct_to_float(mp.group(1))
            zengzhishui = _pct_to_float(mp.group(2))

    # 综合税率关键词
    mzh = re.search(r'综合\s*税率\s*[:：]?\s*(\d+\.?\d*)\s*%', text)
    if mzh:
        zonghe = _pct_to_float(mzh.group(1))

    # 估算综合税率
    if zonghe is None and guanshui is not None and zengzhishui is not None:
        # 通关税率计算：综合=(1+关税率)×增值税率 + 关税率，简化为相加
        zonghe = round(guanshui + zengzhishui + guanshui * zengzhishui, 6)

    return guanshui, zengzhishui, zonghe


def _extract_amount(text: str) -> Optional[float]:
    """从行中提取金额（较大数字，通常 > 100）"""
    nums = re.findall(r'\b(\d{3,}\.?\d*)\b', text)
    for n in reversed(nums):
        val = float(n)
        if val > 100:  # 排除税率数字（通常<100）
            return val
    return None


def _extract_goods_name(text: str) -> Optional[str]:
    """提取货物名称（HS编码之前的文字）"""
    # 移除括号注释
    cleaned = re.sub(r'[（(][^)）]*[)）]', '', text).strip()
    # 取HS编码前的部分
    hs_match = _RE_HS.search(cleaned)
    if hs_match:
        before = cleaned[:hs_match.start()].strip()
        if before:
            return before[:50]  # 最多50字符
    # 无HS编码，取前30字符
    return cleaned[:30].strip() or None


# ── 主解析函数 ───────────────────────────────────────────────────────────────

def parse_import_tax_text(raw_text: str) -> List[ImportTaxItem]:
    """
    将进口税率原文解析为结构化税项列表。

    Args:
        raw_text: summary.进口税率原文 字段内容（多行文本）

    Returns:
        ImportTaxItem 列表，每行或每个明确货物一条记录
    """
    if not raw_text or not raw_text.strip():
        return []

    items: List[ImportTaxItem] = []

    # 按换行拆分，每行尝试解析为一条税项
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]

    for line in lines:
        # 跳过纯标题行（如"进口税率："、"税率说明"等）
        if len(line) < 5:
            continue
        if re.match(r'^[进口税率说明：:]+$', line):
            continue

        item = ImportTaxItem(原文=line)
        item.HS编码 = _extract_hs(line)
        item.原产国 = _extract_country(line)
        item.货物描述 = _extract_goods_name(line)
        item.关税率, item.增值税率, item.综合税率 = _extract_rates(line)
        item.税金金额 = _extract_amount(line) if '元' in line or 'rmb' in line.lower() else None

        # 至少有一个有效字段才保留
        if any([item.HS编码, item.原产国, item.关税率, item.增值税率, item.综合税率]):
            items.append(item)

    return items


__all__ = ['ImportTaxItem', 'parse_import_tax_text']
