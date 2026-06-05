# backend/app/services/scoring_service.py
"""
LPI 评分公用工具 — 被 recommend_service 和 quotes 共享。
保持单一来源，避免两处各自维护导致行为分叉。
"""
from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text

# 目的地关键词 → ISO 国家代码
DEST_TO_COUNTRY_CODE: Dict[str, str] = {
    '美国': 'US', '洛杉矶': 'US', '纽约': 'US', 'LAX': 'US', 'JFK': 'US',
    'IAD': 'US', 'ORD': 'US', 'DFW': 'US', 'ATL': 'US', 'MIA': 'US',
    '英国': 'GB', '伦敦': 'GB',
    '德国': 'DE', '法兰克福': 'DE',
    '法国': 'FR', '巴黎': 'FR',
    '日本': 'JP', '东京': 'JP', '大阪': 'JP',
    '韩国': 'KR', '首尔': 'KR',
    '新加坡': 'SG',
    '澳大利亚': 'AU', '悉尼': 'AU', '墨尔本': 'AU',
    '加拿大': 'CA', '多伦多': 'CA', '温哥华': 'CA',
    '荷兰': 'NL', '阿姆斯特丹': 'NL',
    '比利时': 'BE', '布鲁塞尔': 'BE',
    '西班牙': 'ES', '马德里': 'ES', '巴塞罗那': 'ES',
    '意大利': 'IT', '米兰': 'IT', '罗马': 'IT',
    '瑞典': 'SE', '斯德哥尔摩': 'SE',
    '波兰': 'PL', '华沙': 'PL',
    '捷克': 'CZ', '布拉格': 'CZ',
    '印度': 'IN', '孟买': 'IN', '德里': 'IN',
    '泰国': 'TH', '曼谷': 'TH',
    '越南': 'VN', '胡志明': 'VN', '河内': 'VN',
    '马来西亚': 'MY', '吉隆坡': 'MY',
    '印尼': 'ID', '雅加达': 'ID',
    '菲律宾': 'PH', '马尼拉': 'PH',
    '巴西': 'BR', '圣保罗': 'BR',
    '墨西哥': 'MX', '墨西哥城': 'MX',
    '南非': 'ZA', '约翰内斯堡': 'ZA',
    '土耳其': 'TR', '伊斯坦布尔': 'TR',
    '俄罗斯': 'RU', '莫斯科': 'RU',
    '香港': 'HK',
    '阿联酋': 'AE', '迪拜': 'AE',
    '沙特': 'SA', '吉达': 'SA',
    '澳门': 'MO',
    '中国': 'CN', '深圳': 'CN', '上海': 'CN', '广州': 'CN', '北京': 'CN',
}


def get_lpi_map(db: Session) -> Dict[str, Dict]:
    """加载 country_lpi 表：国家代码 → {LPI综合评分, 风险等级, 国家中文名}"""
    rows = db.execute(text(
        "SELECT 国家代码, LPI综合评分, 风险等级, 国家中文名 FROM country_lpi"
    )).fetchall()
    return {
        r[0]: {
            "lpi": float(r[1]) if r[1] else None,
            "风险等级": r[2],
            "国家中文名": r[3],
        }
        for r in rows
    }


def match_country(destination: str) -> Optional[str]:
    """从目的地文本中匹配国家代码"""
    for keyword, code in DEST_TO_COUNTRY_CODE.items():
        if keyword in destination:
            return code
    return None


def normalize_inverse(val, min_v, max_v, default: float = 60.0) -> float:
    """低值更优：min→100分，max→0分"""
    if val is None or min_v is None:
        return default
    if max_v == min_v:
        return 100.0
    return round((1 - (val - min_v) / (max_v - min_v)) * 100, 1)


def lpi_to_score(lpi: Optional[float]) -> float:
    """LPI(1-5) → 百分制"""
    if lpi is None:
        return 50.0
    return round((lpi - 1) / 4 * 100, 1)
