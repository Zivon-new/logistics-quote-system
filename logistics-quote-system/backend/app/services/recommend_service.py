# backend/app/services/recommend_service.py
"""
智能推荐引擎 - 服务层
综合打分维度：时效(30%) + 价格(30%) + 目的国LPI(20%) + 代理商信用(20%)
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List, Dict
from .scoring_service import get_lpi_map, match_country, normalize_inverse, lpi_to_score

# 保留别名，避免修改下方大量调用点
_get_lpi_map     = get_lpi_map
_match_country   = match_country
_normalize_inverse = normalize_inverse
_lpi_to_score    = lpi_to_score


def get_recommendations(
    db: Session,
    origin: str,
    destination: str,
    goods_keyword: Optional[str] = None,
    transport_mode: Optional[str] = None,
    sort_by: str = "score",   # score | time | price
    top_n: int = 10
) -> Dict:
    """
    智能推荐主函数

    Args:
        origin: 起始地（模糊匹配）
        destination: 目的地（模糊匹配）
        goods_keyword: 货物关键词（可选，模糊匹配 routes.货物名称）
        transport_mode: 运输方式（可选，精确匹配）
        sort_by: 排序方式 score/time/price
        top_n: 最多返回条数
    """
    # ── 1. 构建查询 ───────────────────────────────────────────────────
    sql = """
        SELECT
            ra.代理路线ID,
            ra.代理商,
            ra.运输方式,
            ra.时效,
            ra.时效天数,
            ra.是否赔付,
            ra.赔付内容,
            ra.不含,
            r.路线ID,
            r.起始地,
            r.目的地,
            r.货物名称,
            r.`计费重量(/kg)`   AS 计费重量,
            r.交易开始日期,
            s.总计              AS 总价,
            a.信用评分,
            a.代理商ID,
            a.代理商名称
        FROM route_agents ra
        JOIN routes r ON ra.路线ID = r.路线ID
        LEFT JOIN (
            SELECT 代理路线ID, 总计
            FROM summary
            WHERE 汇总ID IN (
                SELECT MAX(汇总ID) FROM summary GROUP BY 代理路线ID
            )
        ) s ON ra.代理路线ID = s.代理路线ID
        LEFT JOIN agents a ON ra.代理商ID = a.代理商ID
        WHERE r.起始地 LIKE :origin
          AND r.目的地 LIKE :destination
    """
    params: Dict = {
        "origin": f"%{origin}%",
        "destination": f"%{destination}%"
    }

    if goods_keyword:
        sql += " AND r.货物名称 LIKE :goods"
        params["goods"] = f"%{goods_keyword}%"

    if transport_mode:
        sql += " AND ra.运输方式 = :transport_mode"
        params["transport_mode"] = transport_mode

    rows = db.execute(text(sql), params).fetchall()

    if not rows:
        return {
            "results": [], "total": 0,
            "目的国LPI": None, "目的国风险等级": "未知", "目的国名称": None
        }

    records = [dict(r._mapping) for r in rows]

    # ── 2. 确定目的国 LPI ─────────────────────────────────────────────
    lpi_map = _get_lpi_map(db)
    country_code = _match_country(destination)
    lpi_info = lpi_map.get(country_code) if country_code else None
    dest_lpi = lpi_info["lpi"] if lpi_info else None
    dest_risk = lpi_info["风险等级"] if lpi_info else "未知"
    dest_name = lpi_info["国家中文名"] if lpi_info else None

    # ── 3. 归一化打分 ─────────────────────────────────────────────────
    # 先计算单价/kg，价格评分以单价/kg为准（消除货重差异）
    for r in records:
        peso = float(r["计费重量"]) if r["计费重量"] else None
        total_price = float(r["总价"]) if r["总价"] is not None else None
        if peso and peso > 0 and total_price is not None:
            r["单价_per_kg"] = round(total_price / peso, 2)
        else:
            r["单价_per_kg"] = None
        r["总价"] = round(total_price, 2) if total_price is not None else None
        r["计费重量"] = peso
        r["信用评分"] = float(r["信用评分"]) if r["信用评分"] else None
        r["是否赔付"] = int(r["是否赔付"]) if r["是否赔付"] is not None else 0
        r["交易开始日期"] = str(r["交易开始日期"]) if r["交易开始日期"] else None

    times = [r["时效天数"] for r in records if r["时效天数"] is not None]
    # 价格归一化：优先用单价/kg，无重量数据时降级用总价
    per_kg_prices = [r["单价_per_kg"] for r in records if r["单价_per_kg"] is not None]
    raw_prices = [r["总价"] for r in records if r["总价"] is not None]

    min_time, max_time = (min(times), max(times)) if times else (None, None)
    if per_kg_prices:
        min_price, max_price = min(per_kg_prices), max(per_kg_prices)
        use_per_kg = True
    else:
        min_price, max_price = (min(raw_prices), max(raw_prices)) if raw_prices else (None, None)
        use_per_kg = False

    lpi_score = _lpi_to_score(dest_lpi)

    for r in records:
        time_s = _normalize_inverse(r["时效天数"], min_time, max_time)
        price_val = r["单价_per_kg"] if use_per_kg else r["总价"]
        price_s = _normalize_inverse(price_val, min_price, max_price)
        credit_s = r["信用评分"] if r["信用评分"] else 60.0

        total = round(time_s * 0.3 + price_s * 0.3 + lpi_score * 0.2 + credit_s * 0.2, 1)

        r["各项得分"] = {
            "时效得分": time_s,
            "价格得分": price_s,
            "LPI得分": lpi_score,
            "信用得分": credit_s,
        }
        r["综合评分"] = total

    # ── 4. 排序 ──────────────────────────────────────────────────────
    if sort_by == "time":
        # 时效天数升序（NULL排最后）
        records.sort(key=lambda x: (x["时效天数"] is None, x["时效天数"] or 9999))
    elif sort_by == "price":
        # 单价/kg升序（无重量数据则用总价，NULL排最后）
        records.sort(key=lambda x: (
            x["单价_per_kg"] is None and x["总价"] is None,
            x["单价_per_kg"] if x["单价_per_kg"] is not None else (x["总价"] or 9999999)
        ))
    else:
        # 默认：综合评分降序
        records.sort(key=lambda x: x["综合评分"], reverse=True)

    for i, r in enumerate(records):
        r["rank"] = i + 1

    return {
        "results": records[:top_n],
        "total": len(records),
        "目的国LPI": dest_lpi,
        "目的国风险等级": dest_risk,
        "目的国名称": dest_name,
    }


def get_available_origins(db: Session) -> List[str]:
    """获取所有可用的起始地"""
    rows = db.execute(text(
        "SELECT DISTINCT 起始地 FROM routes WHERE 起始地 IS NOT NULL ORDER BY 起始地"
    )).fetchall()
    return [r[0] for r in rows]


def get_available_destinations(db: Session) -> List[str]:
    """获取所有可用的目的地"""
    rows = db.execute(text(
        "SELECT DISTINCT 目的地 FROM routes WHERE 目的地 IS NOT NULL ORDER BY 目的地"
    )).fetchall()
    return [r[0] for r in rows]


def get_available_goods(db: Session) -> List[str]:
    """获取所有货物名称关键词（用于前端自动补全）"""
    rows = db.execute(text(
        "SELECT DISTINCT 货物名称 FROM routes WHERE 货物名称 IS NOT NULL AND 货物名称 != '' ORDER BY 货物名称"
    )).fetchall()
    return [r[0] for r in rows]
