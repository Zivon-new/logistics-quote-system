# scripts/modules/extractors/summary_extractor.py
"""
Summary提取器 v2.0

【v2.0 更新】
✅ 新增字段：运费小计、税金金额、总计金额、进口税率原文、汇损金额
✅ 完整保存进口税率原文（多行文本块）
✅ 从Excel直接读取小计/税金/总计金额（不再依赖计算）
✅ 兼容旧版单一税率字段
"""

import re
from typing import Optional, List
from dataclasses import dataclass, asdict

from .base_extractor import BaseExtractor


@dataclass
class Summary:
    """Summary数据类 v2.0"""
    # ── 金额字段（从Excel直接读取）──
    运费小计:     Optional[float] = None   # 运费小计（不含税）
    小计:         Optional[float] = None   # 兼容旧版
    税金金额:     Optional[float] = None   # 实际税金金额
    税金:         Optional[float] = None   # 兼容旧版（同税金金额）
    汇损:         Optional[float] = None   # 汇损金额
    总计金额:     Optional[float] = None   # 含税总计金额
    总计:         Optional[float] = None   # 兼容旧版（同总计金额）

    # ── 税率字段 ──
    税率:         Optional[float] = None   # 综合税率（兼容旧版，取第一个识别到的税率）
    汇损率:       Optional[float] = None   # 汇损率
    进口税率原文: Optional[str]  = None   # 完整进口税率文本块（多行）

    # ── 备注 ──
    备注:         Optional[str]  = None

    def to_dict(self):
        return asdict(self)


# ── 关键词定义 ──────────────────────────────────────────────
_XIAOJI_KWS   = ['小计', '运费小计', '费用小计', '合计（不含税）', '不含税小计', 'subtotal']
_ZONGJI_KWS   = ['总计', '合计', '总费用', '含税总计', 'total']
_SHUIJIN_KWS  = ['税金', '进口税', '税费', 'tax', 'import tax', '预估税金', '税金小计']
_HUISUN_KWS   = ['汇损', '汇率损失', '汇差']
_TAX_RATE_KWS = ['税率', '税金', '进口税率', 'tax rate', 'tariff']
_IMPORT_KWS   = ['进口税率', '进口税', '关税', 'import tariff', 'hs', 'hs code',
                 '原产', '原产地', '原产国', '税率', '关税率']


def _to_float(val) -> Optional[float]:
    """安全转换为浮点数"""
    if val is None:
        return None
    try:
        s = str(val).replace(',', '').replace('，', '').replace(' ', '').strip()
        s = re.sub(r'[^\d.\-]', '', s)
        return float(s) if s else None
    except Exception:
        return None


def _row_text(sheet, row_idx: int, max_col: int = 20) -> str:
    """获取整行文本"""
    parts = []
    for col in range(1, min(max_col, sheet.max_column + 1)):
        v = sheet.cell(row=row_idx, column=col).value
        if v is not None:
            parts.append(str(v).strip())
    return ' '.join(parts)


def _row_cells(sheet, row_idx: int, max_col: int = 20) -> list:
    """获取整行单元格值列表（保留 None）"""
    return [sheet.cell(row=row_idx, column=c).value
            for c in range(1, min(max_col, sheet.max_column + 1))]


def _extract_number_from_row(sheet, row_idx: int) -> Optional[float]:
    """
    从一行中提取第一个有效数字（跳过纯文本列）。
    优先取靠右的数字列（金额通常在右侧）。
    """
    candidates = []
    for col in range(1, min(20, sheet.max_column + 1)):
        v = sheet.cell(row=row_idx, column=col).value
        if v is None:
            continue
        f = _to_float(v)
        if f is not None and f > 0:
            candidates.append((col, f))
    # 取最后一个（最右侧）有效数字
    return candidates[-1][1] if candidates else None


def _extract_percentage(text: str) -> Optional[float]:
    """从文本中提取百分比，返回小数（19% → 0.19）"""
    if not text:
        return None
    m = re.search(r'(\d+\.?\d*)\s*%', text)
    if m:
        return float(m.group(1)) / 100.0
    m = re.search(r'\b0\.\d+\b', text)
    if m:
        return float(m.group(0))
    return None


def _kw_in(text: str, keywords: list) -> bool:
    t = text.lower()
    return any(k.lower() in t for k in keywords)


class SummaryExtractor(BaseExtractor):
    """Summary提取器 v2.0"""

    QUALITY_THRESHOLD = 0.3

    def __init__(self, logger=None, llm_client=None, enable_llm=True):
        super().__init__(logger, llm_client, enable_llm)

    # ── 主提取入口 ────────────────────────────────────────────
    def _extract_with_rules(self, sheet, agent_start_row=None,
                            agent_end_row=None, **kwargs) -> Summary:
        summary = Summary()
        r_start = agent_start_row or 1
        r_end   = agent_end_row   or sheet.max_row

        # 第一遍：定位关键行号
        xiaoji_row  = None
        shuijin_row = None
        zongji_row  = None
        import_rows: List[int] = []   # 进口税率相关行

        for ri in range(r_start, min(r_end + 1, sheet.max_row + 1)):
            txt = _row_text(sheet, ri)
            if not txt:
                continue

            if not xiaoji_row and _kw_in(txt, _XIAOJI_KWS):
                xiaoji_row = ri
            if not shuijin_row and _kw_in(txt, _SHUIJIN_KWS):
                shuijin_row = ri
            if not zongji_row and xiaoji_row and _kw_in(txt, _ZONGJI_KWS):
                zongji_row = ri
            if _kw_in(txt, _IMPORT_KWS):
                import_rows.append(ri)

        # 第二遍：提取金额
        if xiaoji_row:
            v = _extract_number_from_row(sheet, xiaoji_row)
            if v:
                summary.运费小计 = v
                summary.小计     = v   # 兼容旧版

        if shuijin_row:
            v = _extract_number_from_row(sheet, shuijin_row)
            if v:
                summary.税金金额 = v
                summary.税金     = v   # 兼容旧版

        if zongji_row:
            v = _extract_number_from_row(sheet, zongji_row)
            if v:
                summary.总计金额 = v
                summary.总计     = v   # 兼容旧版

        # 第三遍：在小计→总计区间提取税率、汇损率、汇损
        search_end = zongji_row or min((xiaoji_row or r_start) + 8, r_end)
        for ri in range(xiaoji_row or r_start, search_end + 1):
            txt = _row_text(sheet, ri)
            if not txt:
                continue

            # 税率（兼容旧版）
            if not summary.税率 and _kw_in(txt, _TAX_RATE_KWS):
                pct = _extract_percentage(txt)
                if pct:
                    summary.税率 = pct

            # 汇损率
            if not summary.汇损率 and _kw_in(txt, _HUISUN_KWS):
                pct = _extract_percentage(txt)
                if pct:
                    summary.汇损率 = pct
                v = _extract_number_from_row(sheet, ri)
                if v and v != summary.汇损率:
                    summary.汇损 = v

        # 第四遍：提取进口税率原文（完整文本块）
        if import_rows:
            lines = []
            # 以第一个进口税率行为起点，向下收集连续有内容的行（最多15行）
            start = import_rows[0]
            for ri in range(start, min(start + 15, r_end + 1)):
                txt = _row_text(sheet, ri).strip()
                if txt:
                    lines.append(txt)
                elif lines:  # 遇到空行且已有内容则停止
                    break
            if lines:
                summary.进口税率原文 = '\n'.join(lines)
                # 从原文再次尝试提取整体税率（如果前面没提到）
                if not summary.税率:
                    for line in lines:
                        pct = _extract_percentage(line)
                        if pct and 0 < pct <= 1.5:
                            summary.税率 = pct
                            break

        # 第五遍：提取备注（总计行之后）
        if zongji_row:
            remark_lines = []
            for ri in range(zongji_row + 1, min(r_end + 1, sheet.max_row + 1)):
                txt = _row_text(sheet, ri).strip()
                if not txt or len(txt) < 3:
                    continue
                if _kw_in(txt, _XIAOJI_KWS + _ZONGJI_KWS + _SHUIJIN_KWS):
                    continue
                remark_lines.append(txt)
            if remark_lines:
                summary.备注 = '\n'.join(remark_lines[:10])  # 最多10行备注

        if self.logger:
            self.logger.debug(
                f"  Summary: 小计={summary.运费小计}, 税金={summary.税金金额}, "
                f"总计={summary.总计金额}, 税率={summary.税率}, "
                f"进口税率原文={'有' if summary.进口税率原文 else '无'}"
            )

        return summary

    # ── BaseExtractor 必需方法 ────────────────────────────────
    def _evaluate_quality(self, result: Summary, sheet, **kwargs) -> float:
        if not result:
            return 0.0
        score = 0.0
        if result.运费小计 is not None:  score += 0.25
        if result.税金金额 is not None:  score += 0.20
        if result.总计金额 is not None:  score += 0.20
        if result.进口税率原文:           score += 0.20
        if result.税率 is not None:       score += 0.10
        if result.汇损率 is not None:     score += 0.05
        return score

    def _is_valid(self, result: Summary) -> bool:
        return result and (
            result.运费小计 is not None or
            result.税金金额 is not None or
            result.总计金额 is not None or
            result.进口税率原文 is not None
        )

    def _get_default(self) -> Summary:
        return Summary()

    def _build_enhancement_prompt(self, result: Summary, sheet, **kwargs) -> str:
        agent_start_row = kwargs.get('agent_start_row', 1)
        agent_end_row   = kwargs.get('agent_end_row', sheet.max_row)
        lines = []
        for ri in range(agent_start_row, min(agent_end_row + 1, sheet.max_row + 1)):
            txt = _row_text(sheet, ri)
            if txt:
                lines.append(f"行{ri}: {txt}")
        content = '\n'.join(lines)
        if len(content) > 2000:
            content = content[:2000] + '\n...(截断)'

        return f"""请从以下Excel内容中提取汇总信息。

【文本内容】
{content}

【提取目标】
1. 运费小计（不含税）：查找"小计""运费小计"等行的金额数字
2. 税金金额：查找"税金""进口税"等行的金额数字
3. 总计金额：查找"总计""合计"等行的金额数字
4. 税率：查找百分比（如19%，返回0.19）
5. 汇损率：查找"汇损"百分比
6. 进口税率原文：完整复制"进口税率"/"进口税"相关的文本内容（可多行）

【返回JSON格式】
{{
  "运费小计": 14436.00,
  "税金金额": 1343.78,
  "总计金额": 23976.86,
  "税率": 0.10,
  "汇损率": null,
  "进口税率原文": "交换机8517620090 印度原产，税率 0+10%\\n光缆 原产中国，税率25%+10%"
}}

注意：金额为数字，税率为0-1小数，无数据返回null。"""

    def _merge_results(self, rule_result: Summary, llm_result) -> Summary:
        if not llm_result:
            return rule_result
        # LLM结果补充规则结果的空缺
        for field in ['运费小计', '税金金额', '总计金额', '税率',
                      '汇损率', '进口税率原文', '备注']:
            if getattr(rule_result, field) is None:
                val = (llm_result.get(field) if isinstance(llm_result, dict)
                       else getattr(llm_result, field, None))
                if val is not None:
                    setattr(rule_result, field, val)
        return rule_result

    def _extract_with_llm(self, sheet, **kwargs) -> Summary:
        return Summary()


__all__ = ['SummaryExtractor', 'Summary']
