# backend/app/api/v1/analytics.py
"""
价格分析看板 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from ...database import get_db
from ...core.deps import get_current_user
from ...models.user import User

router = APIRouter(prefix="/analytics", tags=["价格分析"])

VALID_CURRENCIES = {'USD', 'EUR', 'GBP', 'AUD', 'CAD', 'SGD', 'HKD', 'JPY', 'MYR'}


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
            COUNT(DISTINCT ra.代理路线ID) AS 代理报价数,
            COUNT(DISTINCT ra.代理商)    AS 代理商数,
            ROUND(AVG(s.总计), 2)        AS 平均报价
        FROM routes r
        JOIN route_agents ra ON r.路线ID = ra.路线ID
        LEFT JOIN summary s ON ra.代理路线ID = s.代理路线ID
        WHERE s.总计 > 0
        GROUP BY r.起始地, r.目的地
        ORDER BY 代理报价数 DESC
        LIMIT 15
    """)).fetchall()
    return [
        {
            "起始地": r[0], "目的地": r[1],
            "代理报价数": r[2], "代理商数": r[3],
            "平均报价": float(r[4]) if r[4] else 0,
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


@router.get("/forex-history")
async def get_forex_history(
    days: int = Query(default=90, ge=7, le=365),
    currencies: str = Query(default="USD,EUR,SGD,JPY,MYR"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """汇率历史走势：返回各货币近N天对人民币汇率"""
    currency_list = [c.strip() for c in currencies.split(",") if c.strip() in VALID_CURRENCIES]
    result = {c: [] for c in currency_list}
    if not currency_list:
        return {"success": True, "data": result, "days": days}
    try:
        placeholders = ",".join(f"'{c}'" for c in currency_list)
        rows = db.execute(text(f"""
            SELECT `币种`, `参考日期`, `汇率`
            FROM forex_rate_history
            WHERE `币种` IN ({placeholders})
              AND `参考日期` >= DATE_SUB(CURDATE(), INTERVAL :days DAY)
            ORDER BY `参考日期` ASC
        """), {"days": days}).fetchall()
        for row in rows:
            currency, ref_date, rate = row[0], str(row[1]), float(row[2])
            if currency in result:
                result[currency].append({"date": ref_date, "rate": rate})
    except Exception:
        pass  # 表不存在时返回空数据，前端显示空状态提示
    return {"success": True, "data": result, "days": days}


@router.get("/fuel-history")
async def get_fuel_history(
    days: int = Query(default=90, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """布伦特原油价格历史（用于燃油附加费参考）"""
    data = []
    try:
        # 取数据库中最新的 days 条记录（新浪数据可能截止在过去某年，不能用当前日期过滤）
        rows = db.execute(text("""
            SELECT `交易日期`, `收盘价`
            FROM (
                SELECT `交易日期`, `收盘价`
                FROM fuel_price_history
                ORDER BY `交易日期` DESC
                LIMIT :days
            ) t
            ORDER BY `交易日期` ASC
        """), {"days": days}).fetchall()
        data = [{"date": str(r[0]), "price": float(r[1])} for r in rows]
    except Exception:
        pass
    return {"success": True, "data": data, "days": days}


@router.post("/forex-backfill")
async def trigger_forex_backfill(
    days: int = Query(default=30, ge=7, le=180),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """回填历史汇率数据（Frankfurter API）"""
    from fastapi import HTTPException
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可执行")
    from ...services.forex_scraper import backfill_forex_history
    try:
        count = backfill_forex_history(db, days=days)
        return {"success": True, "message": f"汇率历史回填完成，写入 {count} 条记录"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"回填失败：{str(e)}")


@router.post("/fuel-backfill")
async def trigger_fuel_backfill(
    days: int = Query(default=90, ge=30, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """管理员手动回填燃油历史数据"""
    from fastapi import HTTPException
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可执行")
    from ...services.fuel_scraper import backfill_fuel_prices
    try:
        count = backfill_fuel_prices(db, days=days)
        return {"success": True, "message": f"回填完成，写入 {count} 条数据"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"数据拉取失败：{str(e)}")


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


@router.get("/agent-report", summary="代理商年度报价汇总（含跨年对比与单价异动）")
async def get_agent_report(
    代理商: str = Query(..., description="代理商名称（模糊匹配）"),
    year: int = Query(..., description="分析年份"),
    compare_year: Optional[int] = Query(None, description="对比年份，默认 year-1"),
    month: Optional[int] = Query(None, ge=1, le=12, description="分析月份，不填则全年"),
    compare_month: Optional[int] = Query(None, ge=1, le=12, description="对比月份，不填同 month"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    代理商年度综合报告：
    1. 年度/月度概览（使用次数、小计总额、总计总额、计费重量）与对比期对比
    2. 贸易类型 / 运输方式分布
    3. 单价异动分析（按路线+运输方式+费用类型+单位，跨期比较平均单价）
    """
    cmp_year  = compare_year  if compare_year  else year - 1
    cmp_month = compare_month if compare_month else month
    agent_like = f"%{代理商}%"

    def _month_clause(m):
        return "AND MONTH(r.交易开始日期) = :m" if m else ""

    def _overview(y, m=None):
        mc = _month_clause(m)
        params = {"agent": agent_like, "y": y}
        if m: params["m"] = m
        row = db.execute(text(f"""
            SELECT
                COUNT(ra.代理路线ID)                    AS 使用次数,
                COALESCE(SUM(s.小计),  0)               AS 小计总额,
                COALESCE(SUM(s.总计),  0)               AS 总计总额,
                COALESCE(SUM(r.`计费重量(/kg)`), 0)     AS 计费重量
            FROM route_agents ra
            JOIN routes r ON ra.路线ID = r.路线ID
            LEFT JOIN summary s ON ra.代理路线ID = s.代理路线ID
            WHERE ra.代理商 LIKE :agent AND YEAR(r.交易开始日期) = :y {mc}
        """), params).fetchone()
        return {
            "使用次数":  int(row[0] or 0),
            "小计总额":  float(row[1] or 0),
            "总计总额":  float(row[2] or 0),
            "计费重量":  float(row[3] or 0),
        }

    def _dist(y, m, field):
        mc = _month_clause(m)
        params = {"agent": agent_like, "y": y}
        if m: params["m"] = m
        rows = db.execute(text(f"""
            SELECT ra.`{field}`, COUNT(*) AS 条数
            FROM route_agents ra
            JOIN routes r ON ra.路线ID = r.路线ID
            WHERE ra.代理商 LIKE :agent AND YEAR(r.交易开始日期) = :y {mc}
              AND ra.`{field}` IS NOT NULL AND ra.`{field}` != ''
            GROUP BY ra.`{field}`
            ORDER BY 条数 DESC
        """), params).fetchall()
        return {r[0]: int(r[1]) for r in rows}

    # ── 概览 ──
    cur_ov  = _overview(year, month)
    prv_ov  = _overview(cmp_year, cmp_month)

    def _pct(cur, prv):
        if prv and prv > 0:
            return round((cur - prv) / prv * 100, 1)
        return None

    overview = {
        "today_year":    year,
        "today_month":   month,
        "compare_year":  cmp_year,
        "compare_month": cmp_month,
        "today":         cur_ov,
        "previous":      prv_ov,
        "changes": {k: _pct(cur_ov[k], prv_ov[k]) for k in cur_ov},
    }

    # ── 分布 ──
    def _merge_dist(field):
        cur = _dist(year, month, field)
        prv = _dist(cmp_year, cmp_month, field)
        keys = sorted(set(cur) | set(prv), key=lambda k: -(cur.get(k, 0) + prv.get(k, 0)))
        return [{"类型": k, "今年": cur.get(k, 0), "去年": prv.get(k, 0)} for k in keys]

    trade_dist     = _merge_dist("贸易类型")
    transport_dist = _merge_dist("运输方式")

    # ── 单价异动（跨期，按路线+运输方式+费用类型+单位） ──
    # 今年/去年各自加月份条件（若有）
    m1_clause = "AND MONTH(r.交易开始日期) = :m1" if month     else ""
    m2_clause = "AND MONTH(r.交易开始日期) = :m2" if cmp_month else ""
    price_params = {"agent": agent_like, "y1": year, "y2": cmp_year}
    if month:     price_params["m1"] = month
    if cmp_month: price_params["m2"] = cmp_month

    price_rows = db.execute(text(f"""
        SELECT
            r.起始地, r.目的地, ra.运输方式,
            fi.费用类型, fi.单位,
            YEAR(r.交易开始日期) AS yr,
            ROUND(AVG(fi.单价), 4) AS avg_price
        FROM route_agents ra
        JOIN routes r ON ra.路线ID = r.路线ID
        JOIN fee_items fi ON fi.代理路线ID = ra.代理路线ID
        WHERE ra.代理商 LIKE :agent
          AND (
            (YEAR(r.交易开始日期) = :y1 {m1_clause})
            OR
            (YEAR(r.交易开始日期) = :y2 {m2_clause})
          )
          AND fi.备注 != '__GROUP_HEADER__'
          AND (fi.参与核算 IS NULL OR fi.参与核算 != 0)
          AND fi.单价 > 0
          AND fi.单位 IS NOT NULL AND fi.单位 != ''
        GROUP BY r.起始地, r.目的地, ra.运输方式, fi.费用类型, fi.单位, yr
        ORDER BY r.起始地, r.目的地, fi.费用类型, yr
    """), price_params).fetchall()

    # 按 (路线, 运输方式, 费用类型, 单位) 聚合，拿今年和去年单价
    from collections import defaultdict
    price_map = defaultdict(dict)
    for row in price_rows:
        key = (f"{row[0]} → {row[1]}", row[2] or "—", row[3], row[4])
        price_map[key][int(row[5])] = float(row[6])

    unit_price_changes = []
    for (route, transport, fee_type, unit), yr_map in price_map.items():
        cur_p = yr_map.get(year)
        prv_p = yr_map.get(cmp_year)
        pct   = round((cur_p - prv_p) / prv_p * 100, 1) if cur_p and prv_p and prv_p > 0 else None
        unit_price_changes.append({
            "路线":      route,
            "运输方式":  transport,
            "费用类型":  fee_type,
            "单位":      unit,
            "今年单价":  cur_p,
            "去年单价":  prv_p,
            "涨幅":      pct,
            "异常":      pct is not None and pct > 15,
        })

    unit_price_changes.sort(key=lambda x: (not x["异常"], -(x["涨幅"] or 0)))

    return {
        "代理商":        代理商,
        "overview":      overview,
        "贸易类型分布":  trade_dist,
        "运输方式分布":  transport_dist,
        "单价异动":      unit_price_changes,
        "异常单价数":    sum(1 for x in unit_price_changes if x["异常"]),
    }
