# backend/app/api/v1/analytics.py
"""
价格分析看板 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...database import get_db
from ...core.deps import get_current_user
from ...models.user import User

router = APIRouter(prefix="/analytics", tags=["价格分析"])


@router.get("/overview")
async def get_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """总览数据：路线数、代理商数、目的地数、平均报价"""
    rows = db.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM routes) AS total_routes,
            (SELECT COUNT(DISTINCT 代理商) FROM route_agents) AS total_agents,
            (SELECT COUNT(DISTINCT 目的地) FROM routes) AS total_destinations,
            (SELECT ROUND(AVG(总计),2) FROM summary WHERE 总计 > 0) AS avg_price,
            (SELECT ROUND(MIN(总计),2) FROM summary WHERE 总计 > 0) AS min_price,
            (SELECT ROUND(MAX(总计),2) FROM summary WHERE 总计 > 0) AS max_price
    """)).fetchone()
    return {
        "total_routes": rows[0],
        "total_agents": rows[1],
        "total_destinations": rows[2],
        "avg_price": float(rows[3]) if rows[3] else 0,
        "min_price": float(rows[4]) if rows[4] else 0,
        "max_price": float(rows[5]) if rows[5] else 0,
    }


@router.get("/by-destination")
async def get_by_destination(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """各目的地报价统计：报价次数、平均总价、最低总价、最高总价"""
    rows = db.execute(text("""
        SELECT
            r.目的地,
            COUNT(DISTINCT ra.代理路线ID) AS 报价次数,
            ROUND(AVG(s.总计), 2)        AS 平均总价,
            ROUND(MIN(s.总计), 2)        AS 最低总价,
            ROUND(MAX(s.总计), 2)        AS 最高总价
        FROM routes r
        JOIN route_agents ra ON r.路线ID = ra.路线ID
        JOIN summary s ON ra.代理路线ID = s.代理路线ID
        WHERE s.总计 > 0 AND r.目的地 IS NOT NULL
        GROUP BY r.目的地
        ORDER BY 报价次数 DESC
    """)).fetchall()
    return [
        {
            "目的地": r[0],
            "报价次数": r[1],
            "平均总价": float(r[2]) if r[2] else 0,
            "最低总价": float(r[3]) if r[3] else 0,
            "最高总价": float(r[4]) if r[4] else 0,
        }
        for r in rows
    ]


@router.get("/by-transport")
async def get_by_transport(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """各运输方式统计：报价次数、平均总价"""
    rows = db.execute(text("""
        SELECT
            COALESCE(ra.运输方式, '未填写') AS 运输方式,
            COUNT(DISTINCT ra.代理路线ID)   AS 报价次数,
            ROUND(AVG(s.总计), 2)           AS 平均总价
        FROM route_agents ra
        JOIN summary s ON ra.代理路线ID = s.代理路线ID
        WHERE s.总计 > 0
        GROUP BY ra.运输方式
        ORDER BY 报价次数 DESC
    """)).fetchall()
    return [
        {
            "运输方式": r[0],
            "报价次数": r[1],
            "平均总价": float(r[2]) if r[2] else 0,
        }
        for r in rows
    ]


@router.get("/by-agent")
async def get_by_agent(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """各代理商报价统计：报价次数、平均总价、路线数"""
    rows = db.execute(text("""
        SELECT
            ra.代理商,
            COUNT(DISTINCT ra.代理路线ID) AS 报价次数,
            COUNT(DISTINCT ra.路线ID)     AS 路线数,
            ROUND(AVG(s.总计), 2)         AS 平均总价,
            ROUND(MIN(s.总计), 2)         AS 最低报价,
            ROUND(MAX(s.总计), 2)         AS 最高报价
        FROM route_agents ra
        JOIN summary s ON ra.代理路线ID = s.代理路线ID
        WHERE s.总计 > 0 AND ra.代理商 IS NOT NULL
        GROUP BY ra.代理商
        ORDER BY 报价次数 DESC
        LIMIT 15
    """)).fetchall()
    return [
        {
            "代理商": r[0],
            "报价次数": r[1],
            "路线数": r[2],
            "平均总价": float(r[3]) if r[3] else 0,
            "最低报价": float(r[4]) if r[4] else 0,
            "最高报价": float(r[5]) if r[5] else 0,
        }
        for r in rows
    ]


@router.get("/trend")
async def get_trend(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """月度报价趋势：按月统计路线数和平均报价"""
    rows = db.execute(text("""
        SELECT
            DATE_FORMAT(r.交易开始日期, '%Y-%m') AS 月份,
            COUNT(DISTINCT r.路线ID)              AS 路线数,
            ROUND(AVG(s.总计), 2)                 AS 平均总价,
            ROUND(SUM(s.总计), 2)                 AS 总报价额
        FROM routes r
        JOIN route_agents ra ON r.路线ID = ra.路线ID
        JOIN summary s ON ra.代理路线ID = s.代理路线ID
        WHERE r.交易开始日期 IS NOT NULL AND s.总计 > 0
        GROUP BY 月份
        ORDER BY 月份
    """)).fetchall()
    return [
        {
            "月份": r[0],
            "路线数": r[1],
            "平均总价": float(r[2]) if r[2] else 0,
            "总报价额": float(r[3]) if r[3] else 0,
        }
        for r in rows
    ]


@router.get("/price-distribution")
async def get_price_distribution(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """报价区间分布（用于直方图）"""
    rows = db.execute(text("""
        SELECT
            CASE
                WHEN 总计 < 5000    THEN '0-5K'
                WHEN 总计 < 10000   THEN '5K-1W'
                WHEN 总计 < 20000   THEN '1W-2W'
                WHEN 总计 < 50000   THEN '2W-5W'
                WHEN 总计 < 100000  THEN '5W-10W'
                ELSE '10W+'
            END AS 区间,
            COUNT(*) AS 数量,
            CASE
                WHEN 总计 < 5000    THEN 1
                WHEN 总计 < 10000   THEN 2
                WHEN 总计 < 20000   THEN 3
                WHEN 总计 < 50000   THEN 4
                WHEN 总计 < 100000  THEN 5
                ELSE 6
            END AS 排序
        FROM summary
        WHERE 总计 > 0
        GROUP BY 区间, 排序
        ORDER BY 排序
    """)).fetchall()
    return [{"区间": r[0], "数量": r[1]} for r in rows]
