# backend/app/api/v1/risk.py
"""
航线风险画像 API — 基于 World Bank LPI 数据
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from ...database import get_db
from ...core.deps import get_current_user
from ...models.user import User

router = APIRouter(prefix="/risk", tags=["航线风险画像"])


@router.get("/lpi-list")
async def get_lpi_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有国家LPI数据列表（含六维评分和风险等级）"""
    rows = db.execute(text("""
        SELECT
            国家代码, 国家名称, 国家中文名, 数据年份,
            LPI综合评分, 通关效率, 基础设施, 国际运输,
            物流能力, 货物追踪, 时效性, 全球排名, 风险等级
        FROM country_lpi
        ORDER BY LPI综合评分 DESC
    """)).fetchall()

    return [
        {
            "country_code": r[0],
            "country": r[1],
            "country_cn": r[2] or r[1],
            "year": r[3],
            "lpi": float(r[4]) if r[4] else None,
            "customs": float(r[5]) if r[5] else None,
            "infrastructure": float(r[6]) if r[6] else None,
            "international_shipments": float(r[7]) if r[7] else None,
            "logistics_competence": float(r[8]) if r[8] else None,
            "tracking": float(r[9]) if r[9] else None,
            "timeliness": float(r[10]) if r[10] else None,
            "rank": r[11],
            "risk_level": r[12],
        }
        for r in rows
    ]


@router.get("/route-risk")
async def get_route_risk(
    origin: str = Query(..., description="起始地"),
    destination: str = Query(..., description="目的地"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    根据起始地和目的地，返回该航线的风险画像：
    - 目的国 LPI 六维雷达数据
    - 该路线历史报价统计（均价、最低/最高、代理商数）
    - 目的国港口信息
    """
    # 1. 尝试从 country_lpi 匹配目的地的 LPI 数据
    #    目的地可能是城市名或国家名，用 LIKE 模糊匹配国家中文名/城市
    lpi_row = db.execute(text("""
        SELECT
            国家代码, 国家名称, 国家中文名, 数据年份,
            LPI综合评分, 通关效率, 基础设施, 国际运输,
            物流能力, 货物追踪, 时效性, 全球排名, 风险等级
        FROM country_lpi
        WHERE 国家中文名 LIKE :kw OR 国家名称 LIKE :kw
        ORDER BY 数据年份 DESC
        LIMIT 1
    """), {"kw": f"%{destination}%"}).fetchone()

    # 如果目的地匹配不到，尝试从 ports 表找到目的地对应的国家代码，再查 LPI
    if not lpi_row:
        port_row = db.execute(text("""
            SELECT 国家代码, 国家名称
            FROM ports
            WHERE 港口名称 LIKE :kw OR 城市 LIKE :kw OR 国家名称 LIKE :kw
            LIMIT 1
        """), {"kw": f"%{destination}%"}).fetchone()

        if port_row:
            lpi_row = db.execute(text("""
                SELECT
                    国家代码, 国家名称, 国家中文名, 数据年份,
                    LPI综合评分, 通关效率, 基础设施, 国际运输,
                    物流能力, 货物追踪, 时效性, 全球排名, 风险等级
                FROM country_lpi
                WHERE 国家代码 = :code
                ORDER BY 数据年份 DESC
                LIMIT 1
            """), {"code": port_row[0]}).fetchone()

    lpi_data = None
    if lpi_row:
        lpi_data = {
            "country_code": lpi_row[0],
            "country": lpi_row[1],
            "country_cn": lpi_row[2] or lpi_row[1],
            "year": lpi_row[3],
            "lpi": float(lpi_row[4]) if lpi_row[4] else None,
            "customs": float(lpi_row[5]) if lpi_row[5] else None,
            "infrastructure": float(lpi_row[6]) if lpi_row[6] else None,
            "international_shipments": float(lpi_row[7]) if lpi_row[7] else None,
            "logistics_competence": float(lpi_row[8]) if lpi_row[8] else None,
            "tracking": float(lpi_row[9]) if lpi_row[9] else None,
            "timeliness": float(lpi_row[10]) if lpi_row[10] else None,
            "rank": lpi_row[11],
            "risk_level": lpi_row[12],
        }

    # 2. 历史报价统计
    quote_stats = db.execute(text("""
        SELECT
            COUNT(DISTINCT r.路线ID)                        AS route_count,
            COUNT(DISTINCT ra.代理商)                       AS agent_count,
            ROUND(AVG(s.总计), 2)                           AS avg_price,
            ROUND(MIN(s.总计), 2)                           AS min_price,
            ROUND(MAX(s.总计), 2)                           AS max_price,
            ROUND(AVG(ra.时效天数), 1)                      AS avg_days,
            MIN(ra.时效天数)                                 AS min_days
        FROM routes r
        JOIN route_agents ra ON ra.路线ID = r.路线ID
        LEFT JOIN summary s  ON s.代理路线ID = ra.代理路线ID
        WHERE r.起始地 LIKE :origin AND r.目的地 LIKE :dest
          AND (s.总计 IS NULL OR s.总计 > 0)
    """), {"origin": f"%{origin}%", "dest": f"%{destination}%"}).fetchone()

    stats = {
        "route_count": quote_stats[0] or 0,
        "agent_count": quote_stats[1] or 0,
        "avg_price": float(quote_stats[2]) if quote_stats[2] else None,
        "min_price": float(quote_stats[3]) if quote_stats[3] else None,
        "max_price": float(quote_stats[4]) if quote_stats[4] else None,
        "avg_days": float(quote_stats[5]) if quote_stats[5] else None,
        "min_days": quote_stats[6],
    }

    # 3. 目的地相关港口
    dest_ports = db.execute(text("""
        SELECT 港口名称, 港口类型, 平均清关天数, LPI风险等级, UNLOCODE
        FROM ports
        WHERE 国家名称 LIKE :kw OR 城市 LIKE :kw
        LIMIT 5
    """), {"kw": f"%{destination}%"}).fetchall()

    ports = [
        {
            "name": r[0], "type": r[1],
            "clearance_days": float(r[2]) if r[2] else None,
            "risk": r[3], "unlocode": r[4]
        }
        for r in dest_ports
    ]

    return {
        "origin": origin,
        "destination": destination,
        "lpi": lpi_data,
        "quote_stats": stats,
        "ports": ports,
    }
