# scripts/modules/extractors/goods_details_extractor.py
"""
货物明细提取器 v2.0

【v2.0 更新】
✅ 新增字段：SKU / HS编码 / 原产国 / 货物大类
✅ 动态表头识别（不再硬编码列位置）
✅ 从货物名称自动提取 SKU 型号
✅ 识别表格中的 HS编码列和原产国列
✅ 货物大类自动归类
"""

import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

from .base_extractor import BaseExtractor


# ── 货物大类映射 ──────────────────────────────────────────────
_CATEGORY_MAP = {
    '网络设备': ['交换机', '路由器', '防火墙', '网络', '无线', 'switch', 'router', 'firewall', 'ap'],
    '服务器':   ['服务器', '存储', 'server', 'storage', 'nas', 'raid', 'blade'],
    '耗材':     ['耗材', '模块', '线缆', '光纤', '光模块', '接口卡', 'sfp', 'qsfp', 'dac',
                 'cable', 'transceiver', '板卡', '硬盘', 'ssd', 'hdd'],
    '电子产品': ['电池', '充电', '显示', '屏', '摄像', '传感', 'ups', 'pdu', '电源'],
    '机械设备': ['机械', '电机', '泵', '阀', '仪器', '仪表', '设备'],
}

# ── SKU 正则：大写字母+数字+连字符，3字符以上 ─────────────────
_SKU_PATTERN = re.compile(
    r'\b([A-Z][A-Z0-9\-\.\/=]{2,}(?:[A-Z0-9]|\-))\b'
)

# ── HS 编码正则：8-10位数字（可含点号分隔） ───────────────────
_HS_PATTERN = re.compile(
    r'\b(\d{4}[\.\s]?\d{2}[\.\s]?\d{2,4})\b'
)

# ── 原产国关键词映射 ──────────────────────────────────────────
_COUNTRY_PATTERNS = [
    (re.compile(r'中国|china|CN原产', re.I), '中国'),
    (re.compile(r'马来西亚|malaysia|MY原产', re.I), '马来西亚'),
    (re.compile(r'印度(?!尼)|india(?!nesia)', re.I), '印度'),
    (re.compile(r'印度尼西亚|indonesia', re.I), '印度尼西亚'),
    (re.compile(r'美国|usa|united states', re.I), '美国'),
    (re.compile(r'日本|japan', re.I), '日本'),
    (re.compile(r'韩国|korea', re.I), '韩国'),
    (re.compile(r'泰国|thailand', re.I), '泰国'),
    (re.compile(r'越南|vietnam', re.I), '越南'),
    (re.compile(r'台湾|taiwan', re.I), '台湾'),
    (re.compile(r'德国|germany', re.I), '德国'),
    (re.compile(r'英国|uk|united kingdom', re.I), '英国'),
    (re.compile(r'新加坡|singapore', re.I), '新加坡'),
    (re.compile(r'菲律宾|philippines', re.I), '菲律宾'),
    (re.compile(r'墨西哥|mexico', re.I), '墨西哥'),
]


@dataclass
class GoodsDetail:
    """货物明细数据类 v2.0"""
    货物名称:  Optional[str]   = None
    SKU:       Optional[str]   = None    # 🆕 产品型号
    HS编码:    Optional[str]   = None    # 🆕 海关商品编码
    原产国:    Optional[str]   = None    # 🆕 原产地国家
    货物大类:  Optional[str]   = None    # 🆕 自动归类
    是否新品:  int             = 0
    货物种类:  Optional[str]   = None
    数量:      Optional[float] = None
    单价:      Optional[float] = None
    币种:      str             = 'RMB'
    重量:      Optional[float] = None
    总重量:    Optional[float] = None
    总价:      Optional[float] = None
    备注:      Optional[str]   = None

    def to_dict(self):
        return asdict(self)


def _infer_category(name: str, kind: str = '') -> Optional[str]:
    """从货物名称/种类推断货物大类"""
    text = (name or '') + ' ' + (kind or '')
    text_lower = text.lower()
    for category, keywords in _CATEGORY_MAP.items():
        if any(kw.lower() in text_lower for kw in keywords):
            return category
    return '其他'


def _extract_sku_from_name(name: str) -> Optional[str]:
    """从货物名称中提取 SKU 型号"""
    if not name:
        return None
    matches = _SKU_PATTERN.findall(name)
    # 过滤掉太短或全是字母（可能是单位）的
    for m in matches:
        if len(m) >= 4 and re.search(r'\d', m):
            return m
    return None


def _extract_hs_from_text(text: str) -> Optional[str]:
    """从文本中提取HS编码"""
    if not text:
        return None
    m = _HS_PATTERN.search(text)
    if m:
        hs = re.sub(r'[\.\s]', '', m.group(1))
        if 8 <= len(hs) <= 10:
            return hs
    return None


def _extract_country_from_text(text: str) -> Optional[str]:
    """从文本中识别原产国"""
    if not text:
        return None
    for pattern, country in _COUNTRY_PATTERNS:
        if pattern.search(text):
            return country
    return None


class GoodsDetailsExtractor(BaseExtractor):
    """货物明细提取器 v2.0"""

    QUALITY_THRESHOLD = 0.5

    def __init__(self, logger=None, llm_client=None, enable_llm=True):
        super().__init__(logger, llm_client, enable_llm)

        # 动态表头关键词映射
        self.header_keywords = {
            '是否新品':  ['新', '旧', '新旧', '状态', 'new/used'],
            '货物种类':  ['品类', '类别', '种类', '分类', 'category'],
            '货物名称':  ['品名', '货物名称', '产品名称', '名称', '货物', '产品', 'description', 'item'],
            '数量':      ['数量', '件数', '个数', 'qty', 'quantity'],
            '单价':      ['单价', '价格', 'unit price', 'price'],
            '总价':      ['总价', '货值', '金额', '总金额', 'amount', 'total price', 'value'],
            '重量':      ['实际重量', '单重', '重量', 'weight', 'unit weight'],
            '总重量':    ['计费重量', '总重', '总重量', 'total weight'],
            'SKU':       ['sku', '型号', '产品型号', '货号', 'model', 'part no', 'part number'],
            'HS编码':    ['hs', 'hs code', 'hs编码', '海关编码', '商品编码', '税则号'],
            '原产国':    ['原产国', '原产地', '产地', 'country of origin', 'origin'],
        }

        self.currency_map = {
            '￥': 'RMB', '¥': 'RMB', '元': 'RMB', 'RMB': 'RMB', 'CNY': 'RMB',
            '$': 'USD', 'USD': 'USD',
            '€': 'EUR', 'EUR': 'EUR',
            '£': 'GBP', 'GBP': 'GBP',
            'SGD': 'SGD', 'MYR': 'MYR', 'HKD': 'HKD', 'JPY': 'JPY',
        }
        # 国家代码→货币（如 Country 列值为 "US" 表示 USD 计价）
        self.country_code_currency = {
            'US': 'USD', 'EU': 'EUR', 'GB': 'GBP', 'UK': 'GBP',
            'JP': 'JPY', 'SG': 'SGD', 'MY': 'MYR', 'HK': 'HKD',
            'CN': 'RMB', 'AU': 'AUD',
        }

    # ── 主提取入口 ────────────────────────────────────────────
    def _extract_with_rules(self, sheet, **kwargs) -> List[GoodsDetail]:
        # 策略1：无表头固定格式（第3列是"新"/"旧"）
        start_row = self._detect_headerless_table(sheet)
        if start_row:
            if self.logger:
                self.logger.info(f"  ✅ 无表头固定格式，起始行{start_row}")
            goods = self._extract_headerless_data(sheet, start_row)
            if goods:
                if self.logger:
                    self.logger.info(f"  📦 提取到 {len(goods)} 个货物明细")
                return goods

        # 策略2：动态表头
        header_row, header_map = self._find_header_row(sheet)
        if header_row and header_map:
            if self.logger:
                self.logger.info(f"  ✅ 动态表头，行{header_row}，字段: {list(header_map.keys())}")
            goods = self._extract_by_header(sheet, header_row, header_map)
            if goods:
                if self.logger:
                    self.logger.info(f"  📦 提取到 {len(goods)} 个货物明细")
                return goods

        if self.logger:
            self.logger.debug("  ⚠️  未找到货物明细表格")
        return []

    # ── 策略1：无表头固定格式 ─────────────────────────────────
    def _detect_headerless_table(self, sheet) -> Optional[int]:
        for ri in range(1, min(21, sheet.max_row + 1)):
            v = self._cell_str(sheet, ri, 3)
            if v and v.strip() in ('新', '旧'):
                if self._count_nonempty_cols(sheet, ri) >= 8:
                    return ri
        return None

    def _extract_headerless_data(self, sheet, start_row: int) -> List[GoodsDetail]:
        """
        固定列位：C=新旧 D=种类 E=名称 F=数量 G=单价 H=总价 I=单重 J=总重
        """
        goods_list = []
        consecutive_miss = 0

        for ri in range(start_row, sheet.max_row + 1):
            v3 = self._cell_str(sheet, ri, 3)
            if not v3 or v3.strip() not in ('新', '旧'):
                consecutive_miss += 1
                if consecutive_miss >= 3:
                    break
                continue
            consecutive_miss = 0

            g = GoodsDetail()
            g.是否新品  = 1 if v3.strip() == '新' else 0
            g.货物种类  = self._cell_str(sheet, ri, 4)
            g.货物名称  = self._cell_str(sheet, ri, 5)
            if not g.货物名称:
                continue

            g.数量   = self._num(sheet, ri, 6)
            g.单价, g.币种 = self._price_currency(sheet, ri, 7)
            g.总价, _ = self._price_currency(sheet, ri, 8)
            g.重量   = self._num(sheet, ri, 9)
            g.总重量 = self._num(sheet, ri, 10)

            if g.数量 and g.重量 and not g.总重量:
                g.总重量 = round(g.数量 * g.重量, 3)

            # 新增字段自动提取
            g.SKU       = self._extract_sku(g.货物名称)
            g.货物大类  = _infer_category(g.货物名称, g.货物种类 or '')

            if self._is_valid(g):
                goods_list.append(g)

        return goods_list

    # ── 策略2：动态表头 ──────────────────────────────────────
    def _find_header_row(self, sheet):
        """扫描前30行，找到含"品名/数量"的表头行"""
        for ri in range(1, min(31, sheet.max_row + 1)):
            cells = [(c, self._cell_str(sheet, ri, c))
                     for c in range(1, min(25, sheet.max_column + 1))
                     if self._cell_str(sheet, ri, c)]
            hmap = self._match_headers(cells)
            if '货物名称' in hmap and '数量' in hmap:
                return ri, hmap
        return None, {}

    def _match_headers(self, cells: list) -> Dict[str, int]:
        hmap = {}
        for col, val in cells:
            val_lower = val.lower().strip()
            for field, kws in self.header_keywords.items():
                if field in hmap:
                    continue
                if any(kw.lower() in val_lower for kw in kws):
                    hmap[field] = col
                    break
        return hmap

    def _infer_table_currency(self, sheet, header_row: int, hmap: Dict[str, int]) -> str:
        """
        从数据行推断整张表的货值币种。
        策略：若存在未被识别的列其值全为国家代码（如"US"），则对应货币为该列货币。
        同时检查总价列第一行是否带货币符号。
        """
        # 优先：总价列第一行有货币符号
        if '总价' in hmap:
            v = self._cell_str(sheet, header_row + 1, hmap['总价'])
            if v:
                for sym, cur in self.currency_map.items():
                    if sym in v:
                        return cur

        # 其次：找一个未被 hmap 使用、且所有数据行的值都是国家代码的列
        used_cols = set(hmap.values())
        sample_rows = range(header_row + 1, min(header_row + 6, sheet.max_row + 1))
        for col in range(1, min(25, sheet.max_column + 1)):
            if col in used_cols:
                continue
            vals = [self._cell_str(sheet, r, col) for r in sample_rows if self._cell_str(sheet, r, col)]
            if vals and all(v.strip().upper() in self.country_code_currency for v in vals):
                # 该列全是国家代码，取第一行推断货币
                return self.country_code_currency.get(vals[0].strip().upper(), 'RMB')

        return 'RMB'

    def _extract_by_header(self, sheet, header_row: int,
                           hmap: Dict[str, int]) -> List[GoodsDetail]:
        table_currency = self._infer_table_currency(sheet, header_row, hmap)
        if table_currency != 'RMB' and self.logger:
            self.logger.info(f"  💱 检测到货值币种：{table_currency}")
        goods_list = []
        for ri in range(header_row + 1, min(header_row + 101, sheet.max_row + 1)):
            if self._is_empty_row(sheet, ri):
                break
            g = self._extract_one_row(sheet, ri, hmap, table_currency)
            if g and self._is_valid(g):
                goods_list.append(g)
        return goods_list

    def _extract_one_row(self, sheet, ri: int,
                         hmap: Dict[str, int],
                         table_currency: str = 'RMB') -> Optional[GoodsDetail]:
        g = GoodsDetail()

        if '是否新品' in hmap:
            v = self._cell_str(sheet, ri, hmap['是否新品'])
            g.是否新品 = 1 if v and '新' in v else 0

        if '货物种类' in hmap:
            g.货物种类 = self._cell_str(sheet, ri, hmap['货物种类'])

        if '货物名称' in hmap:
            g.货物名称 = self._cell_str(sheet, ri, hmap['货物名称'])

        if not g.货物名称:
            if g.货物种类:
                g.货物名称 = g.货物种类
            else:
                return None

        if '数量' in hmap:
            g.数量 = self._num(sheet, ri, hmap['数量'])

        if '单价' in hmap:
            price_val, price_cur = self._price_currency(sheet, ri, hmap['单价'])
            g.单价 = price_val
            g.币种 = price_cur if price_cur != 'RMB' else table_currency

        if '总价' in hmap:
            total_val, total_cur = self._price_currency(sheet, ri, hmap['总价'])
            g.总价 = total_val
            # 若单元格无货币符号则用表级货币
            if total_cur == 'RMB' and table_currency != 'RMB':
                g.币种 = table_currency

        if '重量' in hmap:
            g.重量 = self._num(sheet, ri, hmap['重量'])

        if '总重量' in hmap:
            g.总重量 = self._num(sheet, ri, hmap['总重量'])

        if g.数量 and g.重量 and not g.总重量:
            g.总重量 = round(g.数量 * g.重量, 3)

        # 新字段：从专用列提取
        if 'SKU' in hmap:
            g.SKU = self._cell_str(sheet, ri, hmap['SKU'])
        if 'HS编码' in hmap:
            g.HS编码 = self._cell_str(sheet, ri, hmap['HS编码'])
        if '原产国' in hmap:
            g.原产国 = self._cell_str(sheet, ri, hmap['原产国'])

        # 新字段：从名称自动推断（无专用列时）
        if not g.SKU:
            g.SKU = self._extract_sku(g.货物名称)
        if not g.原产国:
            g.原产国 = _extract_country_from_text(g.货物名称)
        if not g.HS编码:
            g.HS编码 = _extract_hs_from_text(g.货物名称)

        g.货物大类 = _infer_category(g.货物名称, g.货物种类 or '')

        return g

    # ── 辅助方法 ─────────────────────────────────────────────
    def _extract_sku(self, name: str) -> Optional[str]:
        return _extract_sku_from_name(name)

    def _cell_str(self, sheet, ri: int, ci: int) -> Optional[str]:
        try:
            v = sheet.cell(row=ri, column=ci).value
            return str(v).strip() if v is not None else None
        except Exception:
            return None

    def _num(self, sheet, ri: int, ci: int) -> Optional[float]:
        v = self._cell_str(sheet, ri, ci)
        if not v:
            return None
        cleaned = re.sub(r'[￥$€£,，\s¥]', '', v)
        try:
            return float(cleaned)
        except Exception:
            return None

    def _price_currency(self, sheet, ri: int, ci: int):
        v = self._cell_str(sheet, ri, ci)
        if not v:
            return None, 'RMB'
        currency = 'RMB'
        for sym, cur in self.currency_map.items():
            if sym in v:
                currency = cur
                break
        return self._num(sheet, ri, ci), currency

    def _count_nonempty_cols(self, sheet, ri: int) -> int:
        return sum(1 for c in range(1, min(20, sheet.max_column + 1))
                   if sheet.cell(row=ri, column=c).value is not None)

    def _is_empty_row(self, sheet, ri: int) -> bool:
        return all(sheet.cell(row=ri, column=c).value is None
                   for c in range(1, min(20, sheet.max_column + 1)))

    def _is_valid(self, g: GoodsDetail) -> bool:
        if not g.货物名称:
            return False
        if len(g.货物名称) > 120:
            return False
        # 过滤费用/合计类关键词
        _BAD = ['合计', '小计', '总计', '不含', '运费', '操作费', '报关',
                '仓储', '卡车', '保险', '代理', '费用', '明细', '时效']
        if any(kw in g.货物名称 for kw in _BAD):
            return False
        return True

    # ── BaseExtractor 必需方法 ────────────────────────────────
    def _evaluate_quality(self, result: List[GoodsDetail], sheet, **kwargs) -> float:
        if not result:
            return 0.0
        n = len(result)
        score  = 0.3
        score += 0.2 * (sum(1 for g in result if g.货物名称) / n)
        score += 0.2 * (sum(1 for g in result if g.数量) / n)
        score += 0.15 * (sum(1 for g in result if g.单价 or g.总价) / n)
        score += 0.10 * (sum(1 for g in result if g.SKU) / n)
        score += 0.05 * (sum(1 for g in result if g.原产国) / n)
        return score

    def _build_enhancement_prompt(self, result, sheet, **kwargs) -> str:
        return ""

    def _merge_results(self, rule_result, llm_result):
        return rule_result

    def _extract_with_llm(self, sheet, **kwargs):
        return []

    def _is_valid(self, result) -> bool:  # type: ignore[override]
        if isinstance(result, list):
            return len(result) > 0
        if isinstance(result, GoodsDetail):
            if not result.货物名称:
                return False
            if len(result.货物名称) > 120:
                return False
            _BAD = ['合计', '小计', '总计', '不含', '运费', '操作费', '报关',
                    '仓储', '卡车', '保险', '代理', '费用', '明细', '时效']
            return not any(kw in result.货物名称 for kw in _BAD)
        return False

    def _get_default(self):
        return []


__all__ = ['GoodsDetailsExtractor', 'GoodsDetail']
