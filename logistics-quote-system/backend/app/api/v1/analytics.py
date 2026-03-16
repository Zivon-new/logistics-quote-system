# backend/app/api/v1/analytics.py
"""
价格分析看板 API
"""
from fastapi import APIRouter, Depends, Query
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


@router.get("/route-usage")
async def get_route_usage(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """热门路线排行：按代理报价数排序，展示各路线的使用频次和代理选择情况"""
    rows = db.execute(text("""
        SELECT
            r.起始地,
            r.目的地,
            COALESCE(ra.运输方式, '未知') AS 运输方式,
            COUNT(DISTINCT ra.代理路线ID) AS 代理报价数,
            COUNT(DISTINCT ra.代理商)    AS 代理商数,
            ROUND(AVG(s.总计), 2)        AS 平均报价
        FROM routes r
        JOIN route_agents ra ON r.路线ID = ra.路线ID
        LEFT JOIN summary s ON ra.代理路线ID = s.代理路线ID
        WHERE s.总计 > 0
        GROUP BY r.起始地, r.目的地, ra.运输方式
        ORDER BY 代理报价数 DESC
        LIMIT 15
    """)).fetchall()
    return [
        {
            "起始地": r[0], "目的地": r[1], "运输方式": r[2],
            "代理报价数": r[3], "代理商数": r[4],
            "平均报价": float(r[5]) if r[5] else 0,
        }
        for r in rows
    ]


@router.get("/route-agent-dist")
async def get_route_agent_dist(
    origin: str = Query(default=""),
    dest: str = Query(default=""),
    transport: str = Query(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """指定路线的代理商选择分布（不传参数时返回全部路线汇总）"""
    conditions = ["ra.代理商 IS NOT NULL"]
    params = {}
    if origin:
        conditions.append("r.起始地 = :origin")
        params["origin"] = origin
    if dest:
        conditions.append("r.目的地 = :dest")
        params["dest"] = dest
    if transport and transport != "未知":
        conditions.append("ra.运输方式 = :transport")
        params["transport"] = transport

    where = "WHERE " + " AND ".join(conditions)

    rows = db.execute(text(f"""
        SELECT
            ra.代理商,
            COUNT(ra.代理路线ID)  AS 报价次数,
            ROUND(AVG(s.总计), 2) AS 平均报价
        FROM routes r
        JOIN route_agents ra ON r.路线ID = ra.路线ID
        LEFT JOIN summary s ON ra.代理路线ID = s.代理路线ID
        {where}
        GROUP BY ra.代理商
        ORDER BY 报价次数 DESC
        LIMIT 20
    """), params).fetchall()
    return [
        {"代理商": r[0], "报价次数": r[1], "平均报价": float(r[2]) if r[2] else 0}
        for r in rows
    ]


@router.get("/trend")
async def get_trend(
    granularity: str = Query(default="month"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """报价趋势：支持按周/月/季度/年聚合"""
    if granularity == "week":
        date_expr = "DATE_FORMAT(r.交易开始日期, '%Y-%u周')"
    elif granularity == "quarter":
        date_expr = "CONCAT(YEAR(r.交易开始日期), '-Q', QUARTER(r.交易开始日期))"
    elif granularity == "year":
        date_expr = "DATE_FORMAT(r.交易开始日期, '%Y年')"
    else:
        date_expr = "DATE_FORMAT(r.交易开始日期, '%Y-%m')"

    rows = db.execute(text(f"""
        SELECT
            {date_expr}              AS 时间,
            COUNT(DISTINCT r.路线ID) AS 路线数,
            ROUND(AVG(s.总计), 2)   AS 平均报价,
            ROUND(SUM(s.总计), 2)   AS 总报价额
        FROM routes r
        JOIN route_agents ra ON r.路线ID = ra.路线ID
        JOIN summary s ON ra.代理路线ID = s.代理路线ID
        WHERE r.交易开始日期 IS NOT NULL AND s.总计 > 0
        GROUP BY 时间
        ORDER BY MIN(r.交易开始日期)
    """)).fetchall()
    return [
        {
            "时间": r[0], "路线数": r[1],
            "平均报价": float(r[2]) if r[2] else 0,
            "总报价额": float(r[3]) if r[3] else 0,
        }
        for r in rows
    ]


@router.get("/by-agent")
async def get_by_agent(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """各代理商活跃度：报价次数、路线覆盖数、平均报价"""
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
