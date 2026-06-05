# backend/app/api/v1/routes.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, text
from typing import Optional
from datetime import datetime
from ...core.deps import get_db, get_current_user
from ...crud import route as crud_route
from ...models.user import User
from ...models.route import Route, RouteAgent
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routes", tags=["路线管理"])

from .route_helpers import sf as _sf, dedupe_agents as _dedupe_agents  # noqa: E402


def _get_forex_rates(db: Session) -> dict:
    """Return {currency: rmb_rate} from forex_rate table, with RMB=1."""
    from sqlalchemy import text
    rows = db.execute(text("SELECT 币种, 汇率 FROM forex_rate")).fetchall()
    rates = {r[0]: float(r[1]) for r in rows}
    rates.setdefault('RMB', 1.0)
    rates.setdefault('CNY', 1.0)
    return rates


def _convert_min_fee(min_fee: float, min_cur: str, fee_cur: str, rates: dict) -> float:
    """Convert min_fee from min_cur to fee_cur using forex rates."""
    if min_cur == fee_cur:
        return min_fee
    rmb_per_min = rates.get(min_cur, 1.0)
    rmb_per_fee = rates.get(fee_cur, 1.0)
    if rmb_per_fee == 0:
        return min_fee
    return min_fee * rmb_per_min / rmb_per_fee


def _apply_min_fee(fee_items, rates: dict = None) -> list:
    """Return fee_items list with 原币金额/人民币金额 corrected for minimum charge.
    rates: {currency: rmb_rate} dict for cross-currency conversion."""
    if rates is None:
        rates = {'RMB': 1.0, 'CNY': 1.0}
    result = []
    for item in fee_items:
        min_fee_raw = float(item.最低收费) if item.最低收费 else None
        yuan_orig = float(item.原币金额) if item.原币金额 else 0.0
        rmb_raw = float(item.人民币金额) if item.人民币金额 else 0.0
        fee_cur = item.币种 or 'RMB'
        min_cur = item.最低收费币种 or fee_cur
        # Convert min fee to same currency as the fee item
        min_fee = _convert_min_fee(min_fee_raw, min_cur, fee_cur, rates) if min_fee_raw else None
        shi_ji_yuan = max(yuan_orig, min_fee) if min_fee else yuan_orig
        if min_fee and shi_ji_yuan > yuan_orig and yuan_orig > 0:
            shi_ji_rmb = round(rmb_raw * shi_ji_yuan / yuan_orig, 2)
        else:
            shi_ji_rmb = rmb_raw
        result.append({
            "费用ID":       item.费用ID,
            "费用类型":     item.费用类型,
            "单价":         float(item.单价) if item.单价 else 0,
            "单位":         item.单位,
            "数量":         float(item.数量) if item.数量 else 0,
            "最低收费":     min_fee_raw,
            "最低收费币种": item.最低收费币种,
            "币种":         fee_cur,
            "原币金额":     shi_ji_yuan,
            "人民币金额":   shi_ji_rmb,
            "备注":         item.备注,
            "参与核算":     item.参与核算 if item.参与核算 is not None else 1,
        })
    return result


def _upsert_summary(db: Session, agent_id: int, summary_data: dict):
    """Write one summary row via INSERT … ON DUPLICATE KEY UPDATE.
    Must be called after db.flush() so the parent agent row already exists.
    This overrides any values the DB triggers computed."""
    if not summary_data or not any(
        v for v in summary_data.values() if v not in [0, 0.0, '', None, {}]
    ):
        return
    db.flush()
    db.execute(text("""
        INSERT INTO summary (
            `代理路线ID`, `小计`, `手动小计`, `运费小计`, `税率`, `进口税率原文`,
            `税金`, `税金金额`, `汇损率`, `汇损`, `总计`, `总计金额`, `备注`
        ) VALUES (
            :agent_id, :小计, :手动小计, :运费小计, :税率, :进口税率原文,
            :税金, :税金金额, :汇损率, :汇损, :总计, :总计金额, :备注
        )
        ON DUPLICATE KEY UPDATE
            `小计`         = VALUES(`小计`),
            `手动小计`     = VALUES(`手动小计`),
            `运费小计`     = VALUES(`运费小计`),
            `税率`         = VALUES(`税率`),
            `进口税率原文` = VALUES(`进口税率原文`),
            `税金`         = VALUES(`税金`),
            `税金金额`     = VALUES(`税金金额`),
            `汇损率`       = VALUES(`汇损率`),
            `汇损`         = VALUES(`汇损`),
            `总计`         = VALUES(`总计`),
            `总计金额`     = VALUES(`总计金额`),
            `备注`         = VALUES(`备注`)
    """), {
        'agent_id':     agent_id,
        '小计':         _sf(summary_data.get('运费小计') or summary_data.get('小计')),
        '手动小计':     1 if summary_data.get('手动小计') else 0,
        '运费小计':     summary_data.get('运费小计'),
        '税率':         _sf(summary_data.get('税率')),
        '进口税率原文': summary_data.get('进口税率原文'),
        '税金':         _sf(summary_data.get('税金金额') or summary_data.get('税金')),
        '税金金额':     summary_data.get('税金金额'),
        '汇损率':       _sf(summary_data.get('汇损率')),
        '汇损':         _sf(summary_data.get('汇损')),
        '总计':         _sf(summary_data.get('总计金额') or summary_data.get('总计')),
        '总计金额':     summary_data.get('总计金额'),
        '备注':         summary_data.get('备注') or '',
    })


def _insert_agent_with_fees(db: Session, route_id: int, agent_data: dict):
    """Insert one RouteAgent plus its fee_items, fee_total, and summary.
    Mutates agent_data (pops nested keys).
    Returns (agent_id, cleaned_summary_data) so callers can do a second-pass writeback."""
    from ...models.fee import FeeItem, FeeTotal

    fee_items_data = agent_data.pop('fee_items', [])
    fee_total_data = agent_data.pop('fee_total', [])
    summary_data   = agent_data.pop('summary', {}) or {}

    for bad_key in ['代理路线ID', '路线ID', '创建时间']:
        agent_data.pop(bad_key, None)

    agent = RouteAgent(路线ID=route_id, **agent_data)
    db.add(agent)
    db.flush()
    agent_id = agent.代理路线ID

    for item in fee_items_data:
        for bad_key in ['费用ID', '费用明细ID', '代理路线ID', '创建时间',
                        '_id', '_formula_单价', '_formula_数量']:
            item.pop(bad_key, None)
        if item.get('数量') is None:
            item['数量'] = 0
        if '参与核算' in item:
            item['参与核算'] = 0 if item['参与核算'] in (False, 0) else 1
        db.add(FeeItem(代理路线ID=agent_id, **item))

    for ft in fee_total_data:
        for bad_key in ['整单费用ID', '整单ID', '代理路线ID', '创建时间',
                        '_id', '_formula_原币金额']:
            ft.pop(bad_key, None)
        if '参与核算' in ft:
            ft['参与核算'] = 0 if ft['参与核算'] in (False, 0) else 1
        db.add(FeeTotal(代理路线ID=agent_id, **ft))

    for bad_key in ['汇总ID', '代理路线ID', '创建时间',
                    '税金币种', '小计手动', '税金手动', '汇损手动',
                    '税率Display', '税率模式', '税率明细']:
        summary_data.pop(bad_key, None)

    _upsert_summary(db, agent_id, summary_data)

    return agent_id, summary_data


def _clean_goods_detail(goods: dict) -> dict:
    """Strip frontend-only/DB-generated keys and normalise column names for GoodsDetail."""
    for k in ['货物ID', '路线ID', '创建时间', '路线索引', '_index', '总货值']:
        goods.pop(k, None)
    # get_route_detail returns keys with unit suffixes; map them back to ORM attr names
    for old, new in [('重量(/kg)', '重量'), ('总重量(/kg)', '总重量')]:
        if old in goods:
            goods[new] = goods.pop(old)
    return goods


def _clean_goods_total(goods: dict) -> dict:
    """Strip frontend-only/DB-generated keys and normalise column names for GoodsTotal."""
    for k in ['整单货物ID', '路线ID', '创建时间', '路线索引', '_index']:
        goods.pop(k, None)
    for old, new in [('实际重量(/kg)', '实际重量'), ('总体积(/cbm)', '总体积')]:
        if old in goods:
            goods[new] = goods.pop(old)
    return goods


def _protect_route_fields(db: Session, route_id: int, route_data: dict):
    """Re-apply manually-entered weight/volume/value fields after DB triggers may have overwritten them."""
    field_map = {
        "实际重量": "实际重量(/kg)",
        "计费重量": "计费重量(/kg)",
        "总体积":   "总体积(/cbm)",
        "货值":     "货值",
    }
    params: dict = {"route_id": route_id}
    clauses = []
    for key, col in field_map.items():
        if key in route_data and route_data[key] is not None:
            p = f"p_{key}"
            params[p] = float(route_data[key]) if route_data[key] else 0
            clauses.append(f"`{col}` = :{p}")
    if clauses:
        db.execute(
            text(f"UPDATE routes SET {', '.join(clauses)} WHERE `路线ID` = :route_id"),
            params
        )
        db.commit()


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("", response_model=dict, summary="获取路线列表")
async def get_routes(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    起始地: Optional[str] = Query(None, description="起始地筛选"),
    目的地: Optional[str] = Query(None, description="目的地筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取路线列表（分页）"""
    skip = (page - 1) * page_size
    routes = crud_route.get_routes(db=db, skip=skip, limit=page_size, 起始地=起始地, 目的地=目的地)
    total  = crud_route.get_routes_count(db=db, 起始地=起始地, 目的地=目的地)

    route_ids = [r.路线ID for r in routes]
    all_agents = (
        db.query(RouteAgent).filter(RouteAgent.路线ID.in_(route_ids)).all()
        if route_ids else []
    )
    agents_by_route: dict = {}
    for agent in all_agents:
        agents_by_route.setdefault(agent.路线ID, []).append(agent)

    # 批量查操作人姓名
    user_ids = set()
    for r in routes:
        if r.创建人ID: user_ids.add(r.创建人ID)
        if r.更新人ID: user_ids.add(r.更新人ID)
    user_names: dict = {}
    if user_ids:
        from ...models.user import User as UserModel
        users = db.query(UserModel).filter(UserModel.id.in_(user_ids)).all()
        user_names = {u.id: (u.full_name or u.username) for u in users}

    results = []
    for route in routes:
        results.append({
            "路线ID":        route.路线ID,
            "起始地":        route.起始地,
            "途径地":        route.途径地,
            "目的地":        route.目的地,
            "交易开始日期":  str(route.交易开始日期) if route.交易开始日期 else None,
            "交易结束日期":  str(route.交易结束日期) if route.交易结束日期 else None,
            "实际重量(/kg)": float(route.实际重量) if route.实际重量 else 0,
            "计费重量(/kg)": float(route.计费重量) if route.计费重量 else 0,
            "总体积(/cbm)":  float(route.总体积) if route.总体积 else 0,
            "货值":          float(route.货值) if route.货值 else 0,
            "货值币种":      route.货值币种 or 'RMB',
            "创建时间":      str(route.创建时间) if route.创建时间 else None,
            "创建人名":      user_names.get(route.创建人ID),
            "更新人名":      user_names.get(route.更新人ID),
            "agents": [
                {"代理商": a.代理商, "运输方式": a.运输方式}
                for a in agents_by_route.get(route.路线ID, [])
            ],
        })

    return {
        "success": True,
        "data": {"results": results, "total": total, "page": page, "page_size": page_size}
    }


@router.get("/stats", summary="获取统计数据")
async def get_route_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_routes  = db.query(Route).count()
    total_agents  = db.query(func.count(func.distinct(RouteAgent.代理商))).scalar()
    now           = datetime.now()
    month_routes  = db.query(Route).filter(
        extract('year',  Route.交易开始日期) == now.year,
        extract('month', Route.交易开始日期) == now.month
    ).count()
    return {"success": True, "data": {
        "total_routes": total_routes,
        "total_agents": total_agents,
        "month_routes": month_routes,
    }}


@router.get("/forex_rates", summary="获取汇率")
async def get_forex_rates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从数据库获取汇率，未录入的币种使用默认值"""
    rates = {
        'RMB': 1.0, 'USD': 7.2, 'EUR': 7.8, 'GBP': 9.2,
        'AUD': 4.7, 'CAD': 5.3, 'SGD': 5.3, 'HKD': 0.93,
        'JPY': 0.05, 'MYR': 1.6,
    }
    reference_date = None
    try:
        for row in db.execute(text("SELECT `币种`, `汇率`, `参考日期` FROM forex_rate")).fetchall():
            rates[row[0]] = float(row[1])
            if row[2] and not reference_date:
                reference_date = str(row[2])
    except Exception:
        pass
    return {"success": True, "data": rates, "reference_date": reference_date}


@router.post("/refresh_forex", summary="手动刷新汇率")
async def refresh_forex_rates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可刷新汇率")
    from ...services.forex_scraper import update_forex_rates
    try:
        rates = update_forex_rates(db)
        return {"success": True, "data": rates, "message": f"汇率已更新，共同步 {len(rates)} 种货币"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"汇率同步失败：{str(e)}")


@router.get("/{route_id}", summary="获取路线详情")
async def get_route_detail(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取路线完整详情（包含代理方案、费用明细、整单费用、货物）"""
    from ...models.fee import FeeItem, FeeTotal, Summary
    from ...models.goods import GoodsDetail, GoodsTotal

    forex_rates = _get_forex_rates(db)
    route = db.query(Route).filter(Route.路线ID == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="路线不存在")

    route_data = {
        "路线ID":        route.路线ID,
        "起始地":        route.起始地,
        "途径地":        route.途径地,
        "目的地":        route.目的地,
        "交易开始日期":  str(route.交易开始日期) if route.交易开始日期 else None,
        "交易结束日期":  str(route.交易结束日期) if route.交易结束日期 else None,
        "交易年份":      route.交易年份,
        "交易月份":      route.交易月份,
        "实际重量(/kg)": float(route.实际重量) if route.实际重量 else 0,
        "计费重量(/kg)": float(route.计费重量) if route.计费重量 else 0,
        "总体积(/cbm)":  float(route.总体积) if route.总体积 else 0,
        "货值":          float(route.货值) if route.货值 else 0,
        "货值币种":      route.货值币种 or 'RMB',
        "货物名称":      route.货物名称,
        "创建时间":      str(route.创建时间) if route.创建时间 else None,
        "agents":        [],
        "goods_details": [],
        "goods_total":   [],
    }

    for agent in db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).all():
        fee_items = db.query(FeeItem).filter(FeeItem.代理路线ID == agent.代理路线ID).all()
        fee_total = db.query(FeeTotal).filter(FeeTotal.代理路线ID == agent.代理路线ID).all()
        summary   = db.query(Summary).filter(Summary.代理路线ID == agent.代理路线ID).first()

        route_data["agents"].append({
            "代理路线ID": agent.代理路线ID,
            "代理商":     agent.代理商,
            "运输方式":   agent.运输方式,
            "贸易类型":   agent.贸易类型,
            "时效":       agent.时效,
            "时效备注":   agent.时效备注,
            "不含":       agent.不含,
            "是否赔付":   agent.是否赔付,
            "赔付内容":   agent.赔付内容,
            "代理备注":   agent.代理备注,
            "fee_items": _apply_min_fee(fee_items, forex_rates),
            "fee_total": [{
                "整单费用ID": ft.整单费用ID,
                "费用名称":   ft.费用名称,
                "币种":       ft.币种,
                "原币金额":   float(ft.原币金额) if ft.原币金额 else 0,
                "人民币金额": float(ft.人民币金额) if ft.人民币金额 else 0,
                "备注":       ft.备注,
                "参与核算":   ft.参与核算 if ft.参与核算 is not None else 1,
            } for ft in fee_total],
            "summary": {
                "汇总ID":     summary.汇总ID,
                "小计":       float(summary.小计) if summary.小计 else 0,
                "税率":       float(summary.税率) if summary.税率 else 0,
                "税金":       float(summary.税金) if summary.税金 else 0,
                "汇损率":     float(summary.汇损率) if summary.汇损率 else 0,
                "汇损":       float(summary.汇损) if summary.汇损 else 0,
                "总计":       float(summary.总计) if summary.总计 else 0,
                "备注":       summary.备注,
                "进口税率原文": summary.进口税率原文,
            } if summary else {},
        })

    route_data["goods_details"] = [{
        "货物ID":     g.货物ID,
        "货物名称":   g.货物名称,
        "是否新品":   g.是否新品,
        "货物种类":   g.货物种类,
        "数量":       float(g.数量) if g.数量 else 0,
        "单价":       float(g.单价) if g.单价 else 0,
        "币种":       g.币种,
        "重量(/kg)":  float(g.重量) if g.重量 else 0,
        "总重量(/kg)": float(g.总重量) if g.总重量 else 0,
        "总价":       float(g.总价) if g.总价 else 0,
        "总货值":     float(g.总价) if g.总价 else 0,
        "备注":       g.备注,
    } for g in db.query(GoodsDetail).filter(GoodsDetail.路线ID == route_id).all()]

    route_data["goods_total"] = [{
        "整单货物ID":   g.整单货物ID,
        "货物名称":     g.货物名称,
        "实际重量(/kg)": float(g.实际重量) if g.实际重量 else 0,
        "数量":         float(g.数量) if g.数量 else 0,
        "总体积(/cbm)": float(g.总体积) if g.总体积 else 0,
        "货值":         float(g.货值) if g.货值 else 0,
        "货值币种":     g.货值币种 or 'RMB',
        "备注":         g.备注,
    } for g in db.query(GoodsTotal).filter(GoodsTotal.路线ID == route_id).all()]

    return {"success": True, "data": route_data}


@router.post("/full", summary="创建完整路线（手动录入/Excel导入）")
async def create_full_route(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Stage 1: Create route
        route_info = data.get('route', {})
        for bad_key in ['路线ID', '创建时间']:
            route_info.pop(bad_key, None)
        for date_field in ['交易开始日期', '交易结束日期']:
            if route_info.get(date_field) == '':
                route_info[date_field] = None

        new_route = Route(**route_info)
        new_route.创建人ID = current_user.id
        db.add(new_route)
        db.flush()
        route_id = new_route.路线ID

        # Stage 2: Create agents with fees
        if 'agents' in data:
            for agent_data in _dedupe_agents(data['agents']).values():
                _insert_agent_with_fees(db, route_id, agent_data)

        # Stage 3: Create goods
        from ...models.goods import GoodsDetail, GoodsTotal
        for goods in data.get('goods_details', []):
            db.add(GoodsDetail(路线ID=route_id, **_clean_goods_detail(goods)))

        for goods in data.get('goods_total', []):
            db.add(GoodsTotal(路线ID=route_id, **_clean_goods_total(goods)))

        db.commit()

        # Stage 4: Restore manual fields that triggers may have overwritten
        _protect_route_fields(db, route_id, data.get('route', {}))

        return {"success": True, "message": "创建成功", "route_id": route_id}

    except Exception as e:
        db.rollback()
        logger.error("create_full_route 失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.put("/{route_id}", summary="更新路线")
async def update_route(
    route_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新策略：独立事务分阶段提交；货物先INSERT后DELETE防止触发器把汇总清零。"""
    try:
        from ...models.fee import FeeItem, FeeTotal, Summary
        from ...models.goods import GoodsDetail, GoodsTotal

        # Stage 1: Update route fields
        if not db.execute(text("SELECT COUNT(*) FROM routes WHERE `路线ID` = :id"), {"id": route_id}).scalar():
            raise HTTPException(status_code=404, detail="路线不存在")

        field_mapping = {
            "起始地": "起始地", "途径地": "途径地", "目的地": "目的地",
            "交易开始日期": "交易开始日期", "交易结束日期": "交易结束日期",
            "实际重量": "实际重量(/kg)", "计费重量": "计费重量(/kg)",
            "总体积": "总体积(/cbm)", "货值": "货值",
            "货值币种": "货值币种", "货物名称": "货物名称",
        }
        route_info = data.get('route', {})
        params: dict = {"route_id": route_id}
        clauses = []
        for key, col in field_mapping.items():
            if key in route_info:
                p = f"param_{key}"
                params[p] = route_info[key]
                clauses.append(f"`{col}` = :{p}")
        if clauses:
            db.execute(text(f"UPDATE routes SET {', '.join(clauses)} WHERE `路线ID` = :route_id"), params)
        db.execute(text("UPDATE routes SET `更新人ID` = :uid WHERE `路线ID` = :route_id"),
                   {"uid": current_user.id, "route_id": route_id})
        db.commit()

        # Stage 2: Replace all agents (delete old, insert new)
        agent_summaries = []
        if 'agents' in data:
            old_agents = db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).all()
            for old in old_agents:
                db.query(FeeItem).filter(FeeItem.代理路线ID == old.代理路线ID).delete()
                db.query(FeeTotal).filter(FeeTotal.代理路线ID == old.代理路线ID).delete()
                db.query(Summary).filter(Summary.代理路线ID == old.代理路线ID).delete()
            db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).delete()
            db.flush()

            for agent_data in _dedupe_agents(data['agents']).values():
                agent_id, summary_data = _insert_agent_with_fees(db, route_id, agent_data)
                agent_summaries.append((agent_id, dict(summary_data)))

        # Stage 3: Goods — INSERT new first, then DELETE old
        # (prevents triggers from zeroing the route's aggregate values mid-transaction)
        if 'goods_details' in data:
            new_goods = []
            for goods in data['goods_details']:
                g = GoodsDetail(路线ID=route_id, **_clean_goods_detail(goods))
                new_goods.append(g)
                db.add(g)
            db.flush()
            db.query(GoodsDetail).filter(
                GoodsDetail.路线ID == route_id,
                ~GoodsDetail.货物ID.in_([g.货物ID for g in new_goods])
            ).delete(synchronize_session=False)

        if 'goods_total' in data:
            new_goods = []
            for goods in data['goods_total']:
                g = GoodsTotal(路线ID=route_id, **_clean_goods_total(goods))
                new_goods.append(g)
                db.add(g)
            db.flush()
            db.query(GoodsTotal).filter(
                GoodsTotal.路线ID == route_id,
                ~GoodsTotal.整单货物ID.in_([g.整单货物ID for g in new_goods])
            ).delete(synchronize_session=False)

        db.commit()

        # Stage 4: Restore manual fields after triggers
        _protect_route_fields(db, route_id, route_info)

        # Stage 5: Final summary writeback — after all triggers have run, force-correct
        # 税金/汇损/进口税率原文 which the recompute trigger may have overwritten
        if agent_summaries:
            for agent_id, s in agent_summaries:
                if not s:
                    continue
                correct_tax  = _sf(s.get('税金金额') or s.get('税金'))
                correct_loss = _sf(s.get('汇损'))
                import_text  = s.get('进口税率原文') or ''
                if correct_tax or correct_loss or import_text:
                    db.execute(text("""
                        UPDATE summary
                        SET `税金`         = :税金,
                            `汇损`         = :汇损,
                            `总计`         = `小计` + :税金 + :汇损,
                            `进口税率原文` = :进口税率原文
                        WHERE `代理路线ID` = :agent_id
                    """), {
                        'agent_id':     agent_id,
                        '税金':         correct_tax,
                        '汇损':         correct_loss,
                        '进口税率原文': import_text,
                    })
            db.commit()

        return {"success": True, "message": "更新成功", "route_id": route_id}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("update_route 失败 route_id=%s: %s", route_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/{route_id}", summary="删除路线")
async def delete_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除路线及其所有关联数据"""
    from ...models.fee import FeeItem, FeeTotal, Summary
    from ...models.goods import GoodsDetail, GoodsTotal

    route = db.query(Route).filter(Route.路线ID == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="路线不存在")

    for agent in db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).all():
        db.query(FeeItem).filter(FeeItem.代理路线ID == agent.代理路线ID).delete()
        db.query(FeeTotal).filter(FeeTotal.代理路线ID == agent.代理路线ID).delete()
        db.query(Summary).filter(Summary.代理路线ID == agent.代理路线ID).delete()
    db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).delete()
    db.query(GoodsDetail).filter(GoodsDetail.路线ID == route_id).delete()
    db.query(GoodsTotal).filter(GoodsTotal.路线ID == route_id).delete()
    db.delete(route)
    db.commit()

    return {"success": True, "message": "删除成功"}


@router.post("/import/upload", summary="上传Excel并提取数据")
async def upload_and_extract_excel(
    file: UploadFile = File(...),
    enable_llm: bool = Form(False),
    current_user: User = Depends(get_current_user)
):
    """上传Excel文件并提取路线、代理方案、费用数据"""
    import uuid
    file_path = None
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="仅支持 .xlsx 或 .xls 格式")

        upload_dir = Path("temp/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
        file_path = upload_dir / safe_name
        with open(file_path, "wb") as f:
            f.write(await file.read())

        from ...services.excel_import_service import get_excel_import_service
        excel_service = get_excel_import_service(enable_llm=enable_llm)
        result = excel_service.extract_from_file(str(file_path))

        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('message'))

        return {
            "success": True,
            "message": "提取成功",
            "data": result['data'],
            "validation": excel_service.validate_extracted_data(result['data']),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")
    finally:
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass


@router.post("/import/save", summary="保存Excel导入的数据")
async def save_imported_data(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量保存从Excel导入的路线数据"""
    try:
        from ...models.goods import GoodsDetail, GoodsTotal
        saved_count = 0
        for route_data in data.get('routes', []):
            route_info = route_data.get('route', {})
            new_route = Route(**route_info)
            new_route.创建人ID = current_user.id
            db.add(new_route)
            db.flush()
            route_id = new_route.路线ID

            for agent_data in route_data.get('agents', []):
                db.add(RouteAgent(路线ID=route_id, **agent_data))

            for goods in route_data.get('goods_details', []):
                db.add(GoodsDetail(路线ID=route_id, **_clean_goods_detail(goods)))

            for goods in route_data.get('goods_total', []):
                db.add(GoodsTotal(路线ID=route_id, **_clean_goods_total(goods)))

            saved_count += 1

        db.commit()
        return {"success": True, "message": f"成功保存 {saved_count} 条路线", "count": saved_count}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"保存失败: {str(e)}")
