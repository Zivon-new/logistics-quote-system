# backend/app/services/route_service.py
"""
创建/更新完整路线的核心业务逻辑 — 从 routes.py 接口层抽出，便于独立测试。

接口层职责边界：参数解析、404 前置检查、事务失败时的回滚与错误响应转换。
本模块只负责多阶段的数据落库流程本身，不感知 HTTP。
"""
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..models.route import Route, RouteAgent
from ..models.user import User
from .route_helpers import sf, dedupe_agents
from .fee_service import clean_goods_detail, clean_goods_total
from .trigger_guard_service import protect_route_fields, correct_agent_summaries


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
        '小计':         sf(summary_data.get('运费小计') or summary_data.get('小计')),
        '手动小计':     1 if summary_data.get('手动小计') else 0,
        '运费小计':     summary_data.get('运费小计'),
        '税率':         sf(summary_data.get('税率')),
        '进口税率原文': summary_data.get('进口税率原文'),
        '税金':         sf(summary_data.get('税金金额') or summary_data.get('税金')),
        '税金金额':     summary_data.get('税金金额'),
        '汇损率':       sf(summary_data.get('汇损率')),
        '汇损':         sf(summary_data.get('汇损')),
        '总计':         sf(summary_data.get('总计金额') or summary_data.get('总计')),
        '总计金额':     summary_data.get('总计金额'),
        '备注':         summary_data.get('备注') or '',
    })


def _insert_agent_with_fees(db: Session, route_id: int, agent_data: dict):
    """Insert one RouteAgent plus its fee_items, fee_total, and summary.
    Mutates agent_data (pops nested keys).
    Returns (agent_id, cleaned_summary_data) so callers can do a second-pass writeback."""
    from ..models.fee import FeeItem, FeeTotal

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


def create_full_route(db: Session, data: dict, current_user: User) -> int:
    """执行创建路线的全部业务阶段（路线 → 代理方案+费用 → 货物 → 触发器补写），
    返回新路线ID。失败时调用方负责 rollback 与错误响应转换。"""
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
        for agent_data in dedupe_agents(data['agents']).values():
            _insert_agent_with_fees(db, route_id, agent_data)

    # Stage 3: Create goods
    from ..models.goods import GoodsDetail, GoodsTotal
    for goods in data.get('goods_details', []):
        db.add(GoodsDetail(路线ID=route_id, **clean_goods_detail(goods)))

    for goods in data.get('goods_total', []):
        db.add(GoodsTotal(路线ID=route_id, **clean_goods_total(goods)))

    db.commit()

    # Stage 4: Restore manual fields that triggers may have overwritten
    protect_route_fields(db, route_id, data.get('route', {}))

    return route_id


def update_route(db: Session, route_id: int, data: dict, current_user: User):
    """执行更新路线的全部业务阶段。调用方需先确认路线存在（404 前置检查）。
    更新策略：独立事务分阶段提交；货物先INSERT后DELETE防止触发器把汇总清零。"""
    from ..models.fee import FeeItem, FeeTotal, Summary
    from ..models.goods import GoodsDetail, GoodsTotal

    # Stage 1: Update route fields
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

        for agent_data in dedupe_agents(data['agents']).values():
            agent_id, summary_data = _insert_agent_with_fees(db, route_id, agent_data)
            agent_summaries.append((agent_id, dict(summary_data)))

    # Stage 3: Goods — INSERT new first, then DELETE old
    # (prevents triggers from zeroing the route's aggregate values mid-transaction)
    if 'goods_details' in data:
        new_goods = []
        for goods in data['goods_details']:
            g = GoodsDetail(路线ID=route_id, **clean_goods_detail(goods))
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
            g = GoodsTotal(路线ID=route_id, **clean_goods_total(goods))
            new_goods.append(g)
            db.add(g)
        db.flush()
        db.query(GoodsTotal).filter(
            GoodsTotal.路线ID == route_id,
            ~GoodsTotal.整单货物ID.in_([g.整单货物ID for g in new_goods])
        ).delete(synchronize_session=False)

    db.commit()

    # Stage 4: Restore manual fields after triggers
    protect_route_fields(db, route_id, route_info)

    # Stage 5: Final summary writeback — after all triggers have run, force-correct
    # 税金/汇损/进口税率原文 which the recompute trigger may have overwritten
    correct_agent_summaries(db, agent_summaries)
