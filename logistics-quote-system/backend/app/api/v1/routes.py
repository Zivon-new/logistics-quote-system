# backend/app/api/v1/routes.py
"""
路线管理相关API - 完整修复版
修复内容：
1. ✅ update_route: 优化货物更新顺序，先INSERT后DELETE避免触发器问题
2. ✅ 新增 POST /full 路由，支持Excel导入和手动录入
3. ✅ 修复字段名映射问题
"""
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

    routes = crud_route.get_routes(
        db=db,
        skip=skip,
        limit=page_size,
        起始地=起始地,
        目的地=目的地
    )

    total = crud_route.get_routes_count(
        db=db,
        起始地=起始地,
        目的地=目的地
    )

    # 批量加载所有路线的代理商，避免 N+1 查询
    route_ids = [r.路线ID for r in routes]
    all_agents = db.query(RouteAgent).filter(RouteAgent.路线ID.in_(route_ids)).all() if route_ids else []
    agents_by_route: dict = {}
    for agent in all_agents:
        agents_by_route.setdefault(agent.路线ID, []).append(agent)

    # 手动转换为字典 - ✅ 使用正确的属性名
    results = []
    for route in routes:
        route_dict = {
            "路线ID": route.路线ID,
            "起始地": route.起始地,
            "途径地": route.途径地,
            "目的地": route.目的地,
            "交易开始日期": str(route.交易开始日期) if route.交易开始日期 else None,
            "交易结束日期": str(route.交易结束日期) if route.交易结束日期 else None,
            "实际重量(/kg)": float(route.实际重量) if route.实际重量 else 0,
            "计费重量(/kg)": float(route.计费重量) if route.计费重量 else 0,
            "总体积(/cbm)": float(route.总体积) if route.总体积 else 0,
            "货值": float(route.货值) if route.货值 else 0,
            "货值币种": route.货值币种 or 'RMB',
            "创建时间": str(route.创建时间) if route.创建时间 else None,
            "agents": []
        }
        for agent in agents_by_route.get(route.路线ID, []):
            route_dict["agents"].append({
                "代理商": agent.代理商,
                "运输方式": agent.运输方式
            })
        results.append(route_dict)

    return {
        "success": True,
        "data": {
            "results": results,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/stats", summary="获取统计数据")
async def get_route_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取路线统计数据"""
    total_routes = db.query(Route).count()

    total_agents = db.query(func.count(func.distinct(RouteAgent.代理商))).scalar()

    current_year = datetime.now().year
    current_month = datetime.now().month

    month_routes = db.query(Route).filter(
        extract('year', Route.交易开始日期) == current_year,
        extract('month', Route.交易开始日期) == current_month
    ).count()

    return {
        "success": True,
        "data": {
            "total_routes": total_routes,
            "total_agents": total_agents,
            "month_routes": month_routes
        }
    }


@router.get("/forex_rates", summary="获取汇率")
async def get_forex_rates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从数据库获取汇率，未录入的币种使用默认值"""
    default_rates = {
        'RMB': 1.0,
        'USD': 7.2,
        'EUR': 7.8,
        'GBP': 9.2,
        'AUD': 4.7,
        'CAD': 5.3,
        'SGD': 5.3,
        'HKD': 0.93,
        'JPY': 0.05,
        'MYR': 1.6,
    }

    reference_date = None
    try:
        result = db.execute(text("SELECT `币种`, `汇率`, `参考日期` FROM forex_rate")).fetchall()
        for row in result:
            default_rates[row[0]] = float(row[1])
            if row[2] and not reference_date:
                reference_date = str(row[2])
    except Exception:
        pass

    return {
        "success": True,
        "data": default_rates,
        "reference_date": reference_date
    }


@router.post("/refresh_forex", summary="手动刷新汇率")
async def refresh_forex_rates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """管理员手动触发汇率同步（从 ExchangeRate-API 拉取最新数据）"""
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
    """获取路线完整详情（包含代理商、费用、货物）"""
    from ...models.fee import FeeItem, FeeTotal, Summary
    from ...models.goods import GoodsDetail, GoodsTotal

    route = db.query(Route).filter(Route.路线ID == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="路线不存在")

    route_data = {
        "路线ID": route.路线ID,
        "起始地": route.起始地,
        "途径地": route.途径地,
        "目的地": route.目的地,
        "交易开始日期": str(route.交易开始日期) if route.交易开始日期 else None,
        "交易结束日期": str(route.交易结束日期) if route.交易结束日期 else None,
        "交易年份": route.交易年份,
        "交易月份": route.交易月份,
        "实际重量(/kg)": float(route.实际重量) if route.实际重量 else 0,
        "计费重量(/kg)": float(route.计费重量) if route.计费重量 else 0,
        "总体积(/cbm)": float(route.总体积) if route.总体积 else 0,
        "货值": float(route.货值) if route.货值 else 0,
        "货值币种": route.货值币种 or 'RMB',
        "货物名称": route.货物名称,
        "创建时间": str(route.创建时间) if route.创建时间 else None,
        "agents": [],
        "goods_details": [],
        "goods_total": []
    }

    # 获取代理商及其费用
    agents = db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).all()
    for agent in agents:
        fee_items = db.query(FeeItem).filter(FeeItem.代理路线ID == agent.代理路线ID).all()
        fee_total = db.query(FeeTotal).filter(FeeTotal.代理路线ID == agent.代理路线ID).all()
        summary = db.query(Summary).filter(Summary.代理路线ID == agent.代理路线ID).first()

        agent_dict = {
            "代理路线ID": agent.代理路线ID,
            "代理商": agent.代理商,
            "运输方式": agent.运输方式,
            "贸易类型": agent.贸易类型,
            "时效": agent.时效,
            "时效备注": agent.时效备注,
            "不含": agent.不含,
            "是否赔付": agent.是否赔付,
            "赔付内容": agent.赔付内容,
            "代理备注": agent.代理备注,
            "fee_items": [
                {
                    "费用ID": item.费用ID,
                    "费用类型": item.费用类型,
                    "单价": float(item.单价) if item.单价 else 0,
                    "单位": item.单位,
                    "数量": float(item.数量) if item.数量 else 0,
                    "币种": item.币种,
                    "原币金额": float(item.原币金额) if item.原币金额 else 0,
                    "人民币金额": float(item.人民币金额) if item.人民币金额 else 0,
                    "备注": item.备注
                }
                for item in fee_items
            ],
            "fee_total": [
                {
                    "整单费用ID": ft.整单费用ID,
                    "费用名称": ft.费用名称,
                    "币种": ft.币种,
                    "原币金额": float(ft.原币金额) if ft.原币金额 else 0,
                    "人民币金额": float(ft.人民币金额) if ft.人民币金额 else 0,
                    "备注": ft.备注
                }
                for ft in fee_total
            ],
            "summary": {
                "汇总ID": summary.汇总ID,
                "小计": float(summary.小计) if summary.小计 else 0,
                "税率": float(summary.税率) if summary.税率 else 0,
                "税金": float(summary.税金) if summary.税金 else 0,
                "汇损率": float(summary.汇损率) if summary.汇损率 else 0,
                "汇损": float(summary.汇损) if summary.汇损 else 0,
                "总计": float(summary.总计) if summary.总计 else 0,
                "备注": summary.备注,
                "进口税率原文": summary.进口税率原文
            } if summary else {}
        }
        route_data["agents"].append(agent_dict)

    # 获取货物明细
    goods_details = db.query(GoodsDetail).filter(GoodsDetail.路线ID == route_id).all()
    route_data["goods_details"] = [
        {
            "货物ID": g.货物ID,
            "货物名称": g.货物名称,
            "是否新品": g.是否新品,
            "货物种类": g.货物种类,
            "数量": float(g.数量) if g.数量 else 0,
            "单价": float(g.单价) if g.单价 else 0,
            "币种": g.币种,
            "重量(/kg)": float(g.重量) if g.重量 else 0,
            "总重量(/kg)": float(g.总重量) if g.总重量 else 0,
            "总价": float(g.总价) if g.总价 else 0,
            "总货值": float(g.总价) if g.总价 else 0,
            "备注": g.备注
        }
        for g in goods_details
    ]

    # 获取整单货物
    goods_total = db.query(GoodsTotal).filter(GoodsTotal.路线ID == route_id).all()
    route_data["goods_total"] = [
        {
            "整单货物ID": g.整单货物ID,
            "货物名称": g.货物名称,
            "实际重量(/kg)": float(g.实际重量) if g.实际重量 else 0,
            "总体积(/cbm)": float(g.总体积) if g.总体积 else 0,
            "货值": float(g.货值) if g.货值 else 0,
            "货值币种": g.货值币种 or 'RMB',
            "备注": g.备注
        }
        for g in goods_total
    ]

    return {
        "success": True,
        "data": route_data
    }


@router.post("/full", summary="创建完整路线（手动录入/Excel导入）")
async def create_full_route(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🆕 新增路由 - 统一的路线创建接口
    支持：手动录入、Excel导入
    数据格式：
    {
        "route": {...},
        "agents": [...],
        "goods_details": [...],
        "goods_total": [...]
    }
    """
    try:
        logger.debug(f"\n{'='*80}")
        logger.debug("🆕 create_full_route 开始执行")
        logger.debug(f"时间: {datetime.now()}")
        logger.debug(f"接收到的数据keys: {list(data.keys())}")

        # 第一步：创建路线
        route_data = data.get('route', {})
        logger.debug("\n【第一步】创建路线基本信息...")
        logger.debug(f"  route_data: {route_data}")

        # 清理不需要的字段
        for bad_key in ['路线ID', '创建时间']:
            route_data.pop(bad_key, None)

        new_route = Route(**route_data)
        db.add(new_route)
        db.flush()
        route_id = new_route.路线ID
        logger.debug(f"  ✅ 路线已创建，ID={route_id}")

        # 第二步：创建代理商
        from ...models.fee import FeeItem, FeeTotal

        if 'agents' in data:
            logger.debug("\n【第二步】创建代理商...")
            agents = data['agents']

            # 去重代理商
            agent_map = {}
            for a in agents:
                name = a.get('代理商', '')
                if name:
                    if name not in agent_map:
                        agent_map[name] = a
                    else:
                        # 如果新的有费用数据，替换旧的
                        has_fee = a.get('fee_items') or a.get('fee_total') or a.get('summary')
                        if has_fee:
                            agent_map[name] = a

            for agent_data in agent_map.values():
                fee_items_data = agent_data.pop('fee_items', [])
                fee_total_data = agent_data.pop('fee_total', [])
                summary_data = agent_data.pop('summary', {})

                # 清理旧ID字段
                for bad_key in ['代理路线ID', '路线ID', '创建时间']:
                    agent_data.pop(bad_key, None)

                agent = RouteAgent(路线ID=route_id, **agent_data)
                db.add(agent)
                db.flush()
                agent_id = agent.代理路线ID

                # 插入费用明细
                for fee_item in fee_items_data:
                    for bad_key in ['费用ID', '代理路线ID', '创建时间']:
                        fee_item.pop(bad_key, None)
                    db.add(FeeItem(代理路线ID=agent_id, **fee_item))

                # 插入整单费用
                for fee_total in fee_total_data:
                    for bad_key in ['整单费用ID', '代理路线ID', '创建时间']:
                        fee_total.pop(bad_key, None)
                    db.add(FeeTotal(代理路线ID=agent_id, **fee_total))

                # 插入汇总
                for bad_key in ['汇总ID', '代理路线ID', '创建时间']:
                    summary_data.pop(bad_key, None)

                if summary_data and any(v for v in summary_data.values() if v not in [0, 0.0, '', None, {}]):
                    def _sf(val, default=0.0):
                        try:
                            return float(val) if val is not None else default
                        except (TypeError, ValueError):
                            return default
                    # 先 flush 让触发器跑完（autoflush=False 不会自动 flush）
                    # 这样 upsert 是最后写入，覆盖触发器的计算结果
                    db.flush()
                    upsert_sql = text("""
                        INSERT INTO summary (
                            `代理路线ID`, `小计`, `手动小计`, `运费小计`, `税率`, `进口税率原文`,
                            `税金`, `税金金额`, `汇损率`, `汇损`, `总计`, `总计金额`, `备注`
                        )
                        VALUES (
                            :agent_id, :小计, :手动小计, :运费小计, :税率, :进口税率原文,
                            :税金, :税金金额, :汇损率, :汇损, :总计, :总计金额, :备注
                        )
                        ON DUPLICATE KEY UPDATE
                            `小计`        = VALUES(`小计`),
                            `手动小计`    = VALUES(`手动小计`),
                            `运费小计`    = VALUES(`运费小计`),
                            `税率`        = VALUES(`税率`),
                            `进口税率原文`= VALUES(`进口税率原文`),
                            `税金`        = VALUES(`税金`),
                            `税金金额`    = VALUES(`税金金额`),
                            `汇损率`      = VALUES(`汇损率`),
                            `汇损`        = VALUES(`汇损`),
                            `总计`        = VALUES(`总计`),
                            `总计金额`    = VALUES(`总计金额`),
                            `备注`        = VALUES(`备注`)
                    """)
                    db.execute(upsert_sql, {
                        'agent_id':    agent_id,
                        '小计':        _sf(summary_data.get('运费小计') or summary_data.get('小计')),
                        '手动小计':    1 if summary_data.get('手动小计') else 0,
                        '运费小计':    summary_data.get('运费小计'),
                        '税率':        _sf(summary_data.get('税率')),
                        '进口税率原文': summary_data.get('进口税率原文'),
                        '税金':        _sf(summary_data.get('税金金额') or summary_data.get('税金')),
                        '税金金额':    summary_data.get('税金金额'),
                        '汇损率':      _sf(summary_data.get('汇损率')),
                        '汇损':        _sf(summary_data.get('汇损')),
                        '总计':        _sf(summary_data.get('总计金额') or summary_data.get('总计')),
                        '总计金额':    summary_data.get('总计金额'),
                        '备注':        summary_data.get('备注') or '',
                    })

            logger.debug(f"  ✅ 已创建 {len(agent_map)} 个代理商")

        # 第三步：创建货物明细
        from ...models.goods import GoodsDetail, GoodsTotal

        if 'goods_details' in data:
            logger.debug("\n【第三步】创建货物明细...")
            for goods in data['goods_details']:
                for bad_key in ['货物ID', '路线ID', '创建时间']:
                    goods.pop(bad_key, None)
                db.add(GoodsDetail(路线ID=route_id, **goods))
            logger.debug(f"  ✅ 已创建 {len(data['goods_details'])} 个货物明细")

        if 'goods_total' in data:
            logger.debug("\n【第四步】创建整单货物...")
            for goods in data['goods_total']:
                for bad_key in ['整单货物ID', '路线ID', '创建时间']:
                    goods.pop(bad_key, None)
                db.add(GoodsTotal(路线ID=route_id, **goods))
            logger.debug(f"  ✅ 已创建 {len(data['goods_total'])} 个整单货物")

        db.commit()
        logger.debug(f"\n✅ 路线创建成功！route_id={route_id}")

        # 保护性写回（防止触发器覆盖手动值）
        route_data = data.get('route', {})
        protect_fields = {
            "实际重量": "实际重量(/kg)",
            "计费重量": "计费重量(/kg)",
            "总体积": "总体积(/cbm)",
            "货值": "货值"
        }
        protect_params = {"route_id": route_id}
        protect_clauses = []
        for key, db_col in protect_fields.items():
            if key in route_data and route_data[key] is not None:
                val = float(route_data[key]) if route_data[key] else 0
                param = f"protect_{key}"
                protect_params[param] = val
                protect_clauses.append(f"`{db_col}` = :{param}")

        if protect_clauses:
            protect_sql = text("""
                UPDATE routes
                SET {', '.join(protect_clauses)}
                WHERE `路线ID` = :route_id
            """)
            db.execute(protect_sql, protect_params)
            db.commit()
            logger.debug("  保护性写回完成")

        logger.debug(f"{'='*80}\n")

        return {
            "success": True,
            "message": "创建成功",
            "route_id": route_id
        }

    except Exception as e:
        db.rollback()
        logger.error(f"create_full_route 失败: {str(e)}", exc_info=True)
        logger.debug(f"{'='*80}\n")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.put("/{route_id}", summary="更新路线")
async def update_route(
    route_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🔧 终极修复版 - 优化货物更新顺序避免触发器冲突
    策略:
    1. 先commit路线更新
    2. 先INSERT新货物，再DELETE旧货物（避免触发器在空表时把routes改成0）
    """
    try:
        logger.debug(f"\n{'='*80}")
        logger.debug("🔧 update_route 开始执行")
        logger.debug(f"时间: {datetime.now()}")
        logger.debug(f"路线ID: {route_id}")

        # ============================================================
        # 第一阶段：更新路线基本信息（独立事务）
        # ============================================================
        logger.debug("\n【第一阶段】更新路线基本信息...")

        check_sql = text("SELECT COUNT(*) FROM routes WHERE `路线ID` = :route_id")
        result = db.execute(check_sql, {"route_id": route_id})
        count = result.scalar()

        if count == 0:
            raise HTTPException(status_code=404, detail="路线不存在")

        # 查询更新前的数据
        before_sql = text("""
            SELECT `路线ID`, `实际重量(/kg)`, `计费重量(/kg)`, `总体积(/cbm)`, `货值`
            FROM routes WHERE `路线ID` = :route_id
        """)
        before_data = db.execute(before_sql, {"route_id": route_id}).fetchone()
        logger.debug(f"  更新前: 实际重量={before_data[1]}, 计费重量={before_data[2]}, 总体积={before_data[3]}, 货值={before_data[4]}")

        # 构建UPDATE语句
        # 注意：交易年份和交易月份是GENERATED列，不能UPDATE
        field_mapping = {
            "起始地": "起始地",
            "途径地": "途径地",
            "目的地": "目的地",
            "交易开始日期": "交易开始日期",
            "交易结束日期": "交易结束日期",
            # "交易年份": "交易年份",  # GENERATED列，不能UPDATE
            # "交易月份": "交易月份",  # GENERATED列，不能UPDATE
            "实际重量": "实际重量(/kg)",
            "计费重量": "计费重量(/kg)",
            "总体积": "总体积(/cbm)",
            "货值": "货值",
            "货值币种": "货值币种",
            "货物名称": "货物名称"
        }

        route_data = data.get('route', {})
        update_params = {"route_id": route_id}
        set_clauses = []

        for key, db_column in field_mapping.items():
            if key in route_data:
                value = route_data[key]
                param_name = f"param_{key}"
                update_params[param_name] = value
                set_clauses.append(f"`{db_column}` = :{param_name}")

        if set_clauses:
            update_sql = text("""
                UPDATE routes
                SET {', '.join(set_clauses)}
                WHERE `路线ID` = :route_id
            """)
            db.execute(update_sql, update_params)
            db.commit()  # ✅ 立即commit
            logger.debug("  ✅ 路线基本信息已更新并COMMIT")

            verify_data = db.execute(before_sql, {"route_id": route_id}).fetchone()
            logger.debug(
                "  更新后: 实际重量=%s, 计费重量=%s, 总体积=%s, 货值=%s",
                verify_data[1], verify_data[2], verify_data[3], verify_data[4]
            )

        # ============================================================
        # 第二阶段：更新代理商
        # ============================================================
        from ...models.fee import FeeItem, FeeTotal, Summary

        def _sf(val, default=0.0):
            try:
                return float(val) if val is not None else default
            except (TypeError, ValueError):
                return default

        # 收集 agent_id → summary_data，用于最终写回
        _agent_summaries = []

        if 'agents' in data:
            logger.debug("\n【第二阶段】更新代理商...")

            old_agents = db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).all()
            for old_agent in old_agents:
                db.query(FeeItem).filter(FeeItem.代理路线ID == old_agent.代理路线ID).delete()
                db.query(FeeTotal).filter(FeeTotal.代理路线ID == old_agent.代理路线ID).delete()
                db.query(Summary).filter(Summary.代理路线ID == old_agent.代理路线ID).delete()
            db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).delete()
            db.flush()

            # 去重代理商
            agent_map = {}
            for a in data['agents']:
                name = a.get('代理商', '')
                if name:
                    if name not in agent_map:
                        agent_map[name] = a
                    else:
                        has_fee = a.get('fee_items') or a.get('fee_total') or a.get('summary')
                        if has_fee:
                            agent_map[name] = a

            # 插入新代理商
            for agent_data in agent_map.values():
                fee_items_data = agent_data.pop('fee_items', [])
                fee_total_data = agent_data.pop('fee_total', [])
                summary_data = agent_data.pop('summary', {})

                for bad_key in ['代理路线ID', '路线ID', '创建时间']:
                    agent_data.pop(bad_key, None)

                agent = RouteAgent(路线ID=route_id, **agent_data)
                db.add(agent)
                db.flush()
                agent_id = agent.代理路线ID

                for fee_item in fee_items_data:
                    for bad_key in ['费用ID', '代理路线ID', '创建时间']:
                        fee_item.pop(bad_key, None)
                    db.add(FeeItem(代理路线ID=agent_id, **fee_item))

                for fee_total in fee_total_data:
                    for bad_key in ['整单费用ID', '代理路线ID', '创建时间']:
                        fee_total.pop(bad_key, None)
                    db.add(FeeTotal(代理路线ID=agent_id, **fee_total))

                for bad_key in ['汇总ID', '代理路线ID', '创建时间']:
                    summary_data.pop(bad_key, None)

                if summary_data and any(v for v in summary_data.values() if v not in [0, 0.0, '', None, {}]):
                    db.flush()
                    upsert_sql = text("""
                        INSERT INTO summary (
                            `代理路线ID`, `小计`, `手动小计`, `运费小计`, `税率`, `进口税率原文`,
                            `税金`, `税金金额`, `汇损率`, `汇损`, `总计`, `总计金额`, `备注`
                        )
                        VALUES (
                            :agent_id, :小计, :手动小计, :运费小计, :税率, :进口税率原文,
                            :税金, :税金金额, :汇损率, :汇损, :总计, :总计金额, :备注
                        )
                        ON DUPLICATE KEY UPDATE
                            `小计`        = VALUES(`小计`),
                            `手动小计`    = VALUES(`手动小计`),
                            `运费小计`    = VALUES(`运费小计`),
                            `税率`        = VALUES(`税率`),
                            `进口税率原文`= VALUES(`进口税率原文`),
                            `税金`        = VALUES(`税金`),
                            `税金金额`    = VALUES(`税金金额`),
                            `汇损率`      = VALUES(`汇损率`),
                            `汇损`        = VALUES(`汇损`),
                            `总计`        = VALUES(`总计`),
                            `总计金额`    = VALUES(`总计金额`),
                            `备注`        = VALUES(`备注`)
                    """)
                    db.execute(upsert_sql, {
                        'agent_id':    agent_id,
                        '小计':        _sf(summary_data.get('运费小计') or summary_data.get('小计')),
                        '手动小计':    1 if summary_data.get('手动小计') else 0,
                        '运费小计':    summary_data.get('运费小计'),
                        '税率':        _sf(summary_data.get('税率')),
                        '进口税率原文': summary_data.get('进口税率原文'),
                        '税金':        _sf(summary_data.get('税金金额') or summary_data.get('税金')),
                        '税金金额':    summary_data.get('税金金额'),
                        '汇损率':      _sf(summary_data.get('汇损率')),
                        '汇损':        _sf(summary_data.get('汇损')),
                        '总计':        _sf(summary_data.get('总计金额') or summary_data.get('总计')),
                        '总计金额':    summary_data.get('总计金额'),
                        '备注':        summary_data.get('备注') or '',
                    })

                # 记录用于最终写回
                _agent_summaries.append((agent_id, dict(summary_data)))

            logger.debug(f"  ✅ 已更新 {len(agent_map)} 个代理商")

        # ============================================================
        # 第三阶段：更新货物（关键优化：先INSERT后DELETE）
        # ============================================================
        from ...models.goods import GoodsDetail, GoodsTotal

        if 'goods_details' in data:
            logger.debug("\n【第三阶段】更新货物明细（先INSERT后DELETE）...")

            # ✅ 关键修复：先INSERT新数据
            new_goods_list = []
            for goods in data['goods_details']:
                for bad_key in ['货物ID', '路线ID', '创建时间']:
                    goods.pop(bad_key, None)
                new_goods = GoodsDetail(路线ID=route_id, **goods)
                new_goods_list.append(new_goods)
                db.add(new_goods)

            db.flush()  # flush让INSERT生效
            logger.debug(f"  ✅ 已INSERT {len(new_goods_list)} 个新货物明细")

            # ✅ 再DELETE旧数据（此时goods表不为空，触发器不会把routes改成0）
            db.query(GoodsDetail).filter(
                GoodsDetail.路线ID == route_id,
                ~GoodsDetail.货物ID.in_([g.货物ID for g in new_goods_list])
            ).delete(synchronize_session=False)
            logger.debug("  ✅ 已DELETE旧货物明细")

        if 'goods_total' in data:
            logger.debug("\n【第四阶段】更新整单货物（先INSERT后DELETE）...")

            # ✅ 关键修复：先INSERT新数据
            new_goods_list = []
            for goods in data['goods_total']:
                for bad_key in ['整单货物ID', '路线ID', '创建时间']:
                    goods.pop(bad_key, None)
                new_goods = GoodsTotal(路线ID=route_id, **goods)
                new_goods_list.append(new_goods)
                db.add(new_goods)

            db.flush()
            logger.debug(f"  ✅ 已INSERT {len(new_goods_list)} 个新整单货物")

            # ✅ 再DELETE旧数据
            db.query(GoodsTotal).filter(
                GoodsTotal.路线ID == route_id,
                ~GoodsTotal.整单货物ID.in_([g.整单货物ID for g in new_goods_list])
            ).delete(synchronize_session=False)
            logger.debug("  ✅ 已DELETE旧整单货物")

        db.commit()
        logger.debug("\n✅ 主事务已COMMIT")

        # ============================================================
        # 第五阶段：保护性写回（独立事务，在所有触发器执行完毕后）
        # 触发器recompute_route可能已经把手动值清零了，这里强制恢复
        # ============================================================
        route_data = data.get('route', {})
        protect_fields = {
            "实际重量": "实际重量(/kg)",
            "计费重量": "计费重量(/kg)",
            "总体积": "总体积(/cbm)",
            "货值": "货值"
        }
        protect_params = {"route_id": route_id}
        protect_clauses = []
        for key, db_col in protect_fields.items():
            if key in route_data and route_data[key] is not None:
                val = float(route_data[key]) if route_data[key] else 0
                param = f"protect_{key}"
                protect_params[param] = val
                protect_clauses.append(f"`{db_col}` = :{param}")

        if protect_clauses:
            protect_sql = text("""
                UPDATE routes
                SET {', '.join(protect_clauses)}
                WHERE `路线ID` = :route_id
            """)
            db.execute(protect_sql, protect_params)
            db.commit()
            logger.debug(f"【第五阶段】保护性写回完成: {protect_params}")

        # ============================================================
        # 第六阶段：summary 最终写回（在所有触发器都跑完之后强制写入正确值）
        # goods_total/goods_details/routes 的触发器都会调用 recompute_summary_for_route
        # 统一在最后一次覆盖，确保税金/汇损/进口税率原文不被触发器篡改
        # ============================================================
        if _agent_summaries:
            for agent_id, s in _agent_summaries:
                if not s:
                    continue
                correct_tax = _sf(s.get('税金金额') or s.get('税金'))
                correct_loss = _sf(s.get('汇损'))
                import_tax_text = s.get('进口税率原文') or ''
                if correct_tax or correct_loss or import_tax_text:
                    db.execute(text("""
                        UPDATE summary
                        SET `税金`         = :税金,
                            `汇损`         = :汇损,
                            `总计`         = `小计` + :税金 + :汇损,
                            `进口税率原文`  = :进口税率原文
                        WHERE `代理路线ID` = :agent_id
                    """), {
                        'agent_id':    agent_id,
                        '税金':        correct_tax,
                        '汇损':        correct_loss,
                        '进口税率原文': import_tax_text,
                    })
            db.commit()
            logger.debug(f"【第六阶段】summary 最终写回完成，共 {len(_agent_summaries)} 条")

        logger.debug("\n✅ 所有更新已完成并COMMIT")
        logger.debug(f"{'='*80}\n")

        return {
            "success": True,
            "message": "更新成功",
            "route_id": route_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"update_route 失败 route_id={route_id}: {str(e)}", exc_info=True)
        logger.debug(f"{'='*80}\n")
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

    # 删除代理商及其关联数据
    agents = db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).all()
    for agent in agents:
        db.query(FeeItem).filter(FeeItem.代理路线ID == agent.代理路线ID).delete()
        db.query(FeeTotal).filter(FeeTotal.代理路线ID == agent.代理路线ID).delete()
        db.query(Summary).filter(Summary.代理路线ID == agent.代理路线ID).delete()
    db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).delete()

    # 删除货物
    db.query(GoodsDetail).filter(GoodsDetail.路线ID == route_id).delete()
    db.query(GoodsTotal).filter(GoodsTotal.路线ID == route_id).delete()

    # 删除路线
    db.delete(route)
    db.commit()

    return {
        "success": True,
        "message": "删除成功"
    }


@router.post("/import/upload", summary="上传Excel并提取数据")
async def upload_and_extract_excel(
    file: UploadFile = File(...),
    enable_llm: bool = Form(False),
    current_user: User = Depends(get_current_user)
):
    """上传Excel文件并提取数据"""
    import uuid
    file_path = None
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="仅支持 .xlsx 或 .xls 格式")

        upload_dir = Path("temp/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 使用 UUID 避免文件名冲突和路径穿越
        safe_name = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
        file_path = upload_dir / safe_name
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        from ...services.excel_import_service import get_excel_import_service

        excel_service = get_excel_import_service(enable_llm=enable_llm)
        result = excel_service.extract_from_file(str(file_path))

        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('message'))

        validation = excel_service.validate_extracted_data(result['data'])

        return {
            "success": True,
            "message": "提取成功",
            "data": result['data'],
            "validation": validation
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")
    finally:
        # 临时文件用完即删，避免磁盘积累
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
    """保存从Excel导入的路线数据（批量保存）"""
    try:
        routes_data = data.get('routes', [])
        saved_count = 0

        for route_data in routes_data:
            route_info = route_data.get('route', {})
            new_route = Route(**route_info)
            db.add(new_route)
            db.flush()

            route_id = new_route.路线ID

            # 创建代理商
            agents = route_data.get('agents', [])
            for agent_data in agents:
                agent = RouteAgent(路线ID=route_id, **agent_data)
                db.add(agent)

            # 创建货物
            from ...models.goods import GoodsDetail, GoodsTotal

            goods_details = route_data.get('goods_details', [])
            for goods in goods_details:
                goods_detail = GoodsDetail(路线ID=route_id, **goods)
                db.add(goods_detail)

            goods_total = route_data.get('goods_total', [])
            for goods in goods_total:
                goods_t = GoodsTotal(路线ID=route_id, **goods)
                db.add(goods_t)

            saved_count += 1

        db.commit()

        return {
            "success": True,
            "message": f"成功保存 {saved_count} 条路线",
            "count": saved_count
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"保存失败: {str(e)}")
