# scripts/modules/extractors/sheet_format_detector.py
"""
Sheet格式检测器

判断一个Sheet是否符合标准横向表格格式。
用于决定是走规则提取路径还是LLM全量提取路径。

【标准格式特征】
1. Sheet名或第1行包含路线信息（如"深圳-新加坡"）
2. 有明确的代理商行（含"代理"/"货代"/"物流商"等关键词）
3. 有多列数据（代理商信息横向排列）
4. 有结构化字段关键词（时效、赔付、不含等）

【判断逻辑】
- 4项检查，每项1分，满分4分
- 置信度 = 得分 / 4
- 置信度 >= THRESHOLD → 'standard'（走规则提取）
- 置信度 < THRESHOLD  → 'unstructured'（走LLM全量提取）
"""

from typing import Tuple


class SheetFormatDetector:
    """Sheet格式检测器"""

    AGENT_ROW_KEYWORDS = [
        '代理', '报价方', '货代', '物流商', '供应商',
        '承运商', '贸易代理方案', '运输方案', '物流方案',
    ]

    ROUTE_SEPARATORS = ['→', '->', '--', '—', '－', '-', '~', '至']

    # 结构化字段关键词（出现≥2个才算命中）
    STRUCTURED_FIELD_KEYWORDS = [
        '时效', '赔付', '不含', '运输方式', '贸易类型',
        '海运费', '操作费', '报关费', '汇率', '税率',
    ]

    def detect(self, sheet) -> Tuple[str, float]:
        """
        检测Sheet格式类型

        Returns:
            (format_type, confidence)
            format_type: 'standard' | 'unstructured'
            confidence: 0.0-1.0
        """
        score = 0.0

        if self._has_route_info(sheet):
            score += 1.0

        if self._has_agent_row(sheet):
            score += 1.0

        if self._has_multi_column_structure(sheet):
            score += 1.0

        if self._has_structured_fields(sheet):
            score += 1.0

        confidence = score / 4.0
        fmt = 'standard' if confidence >= 0.5 else 'unstructured'
        return fmt, confidence

    # ── 检查项 ──────────────────────────────────────────

    def _has_route_info(self, sheet) -> bool:
        """Sheet名或前3行有路线格式"""
        if self._contains_route_pattern(getattr(sheet, 'title', '')):
            return True
        for row_idx in range(1, min(4, sheet.max_row + 1)):
            for col_idx in range(1, min(5, sheet.max_column + 1)):
                val = sheet.cell(row=row_idx, column=col_idx).value
                if val and self._contains_route_pattern(str(val)):
                    return True
        return False

    def _contains_route_pattern(self, text: str) -> bool:
        if not text:
            return False
        for sep in self.ROUTE_SEPARATORS:
            if sep in text:
                parts = text.split(sep, 1)
                if (len(parts) == 2
                        and len(parts[0].strip()) >= 2
                        and len(parts[1].strip()) >= 2):
                    return True
        return False

    def _has_agent_row(self, sheet) -> bool:
        """前20行第1列有代理商关键词"""
        for row_idx in range(1, min(21, sheet.max_row + 1)):
            val = sheet.cell(row=row_idx, column=1).value
            if val:
                text = str(val).strip()
                if any(kw in text for kw in self.AGENT_ROW_KEYWORDS):
                    return True
        return False

    def _has_multi_column_structure(self, sheet) -> bool:
        """前10行中，有一行同时有3列以上非空数据"""
        for row_idx in range(1, min(11, sheet.max_row + 1)):
            count = sum(
                1 for col_idx in range(1, min(sheet.max_column + 1, 12))
                if sheet.cell(row=row_idx, column=col_idx).value
            )
            if count >= 3:
                return True
        return False

    def _has_structured_fields(self, sheet) -> bool:
        """前30行第1列出现≥2个结构化字段关键词"""
        found = 0
        for row_idx in range(1, min(31, sheet.max_row + 1)):
            val = sheet.cell(row=row_idx, column=1).value
            if val:
                text = str(val).strip()
                if any(kw in text for kw in self.STRUCTURED_FIELD_KEYWORDS):
                    found += 1
        return found >= 2


__all__ = ['SheetFormatDetector']
