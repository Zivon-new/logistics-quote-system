# backend/app/api/v1/quotes.py
"""
报价查询相关API（含智能评分）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List, Dict
from datetime import date
from ...core.deps import get_db, get_current_user
from ...models.route import Route, RouteAgent
from ...models.goods import GoodsDetail
from ...models.fee import Summary
from ...models.user import User
from ...services.recommend_service import (
    _get_lpi_map, _match_country, _normalize_inverse, _lpi_to_score
)
from sqlalchemy import and_, or_


def _add_scores(db: Session, results: List[Dict]) -> Dict[str, dict]:
    """
    为 quote_results 中的每个 agent 补充智能评分。
    按目的地分组归一化，返回 {代理路线ID: {综合评分, 各项得分, 时效天数}} 映射。
    同时返回每个目的地的 LPI 信息。
    """
    if not results:
        return {}, {}

    # 收集所有 代理路线ID
    all_agent_ids = []
    for route in results:
        for agent in route.get("agents", []):
            all_agent_ids.append(agent["代理路线ID"])

    if not all_agent_ids:
        return {}, {}

    # 一次性查出 时效天数 和 信用评分
    id_list = ",".join(str(i) for i in all_agent_ids)
    rows = db.execute(text(f"""
        SELECT ra.代理路线ID, ra.时效天数, a.信用评分
        FROM route_agents ra
        LEFT JOIN agents a ON ra.代理商ID = a.代理商ID
        WHERE ra.代理路线ID IN ({id_list})
    """)).fetchall()
    supp = {r[0]: {"时效天数": r[1], "信用评分": r[2]} for r in rows}

    # 获取 LPI 映射
    lpi_map = _get_lpi_map(db)

    # 按目的地分组，分别归一化计算
    score_map: Dict[int, dict] = {}
    dest_lpi_info: Dict[str, dict] = {}

    # 按目的地聚合 agents
    dest_groups: Dict[str, List] = {}
    for route in results:
        dest = route["目的地"]
        for agent in route.get("agents", []):
            dest_groups.setdefault(dest, []).append(agent)

    for dest, agents in dest_groups.items():
        country_code = _match_country(dest)
        lpi_info = lpi_map.get(country_code) if country_code else None
        dest_lpi = lpi_info["lpi"] if lpi_info else None
        lpi_score = _lpi_to_score(dest_lpi)

        dest_lpi_info[dest] = {
            "LPI": dest_lpi,
            "风险等级": lpi_info["风险等级"] if lpi_info else "未知",
            "国家中文名": lpi_info["国家中文名"] if lpi_info else None,
        }

        # 在当前目的地组内归一化
        times = [supp.get(a["代理路线ID"], {}).get("时效天数") for a in agents]
        times = [t for t in times if t is not None]
        prices = [a["总费用"] for a in agents if a["总费用"] > 0]

        min_t, max_t = (min(times), max(times)) if times else (None, None)
        min_p, max_p = (min(prices), max(prices)) if prices else (None, None)

        for agent in agents:
            aid = agent["代理路线ID"]
            s = supp.get(aid, {})
            time_s = _normalize_inverse(s.get("时效天数"), min_t, max_t)
            price_s = _normalize_inverse(
                agent["总费用"] if agent["总费用"] > 0 else None, min_p, max_p
            )
            credit_s = float(s["信用评分"]) if s.get("信用评分") else 60.0
            total = round(time_s * 0.3 + price_s * 0.3 + lpi_score * 0.2 + credit_s * 0.2, 1)

            score_map[aid] = {
                "综合评分": total,
                "时效天数": s.get("时效天数"),
                "各项得分": {
                    "时效得分": time_s,
                    "价格得分": price_s,
                    "LPI得分": lpi_score,
                    "信用得分": credit_s,
                },
            }

    return score_map, dest_lpi_info

router = APIRouter(prefix="/quotes", tags=["报价查询"])


@router.get("/search", summary="搜索报价")
async def search_quotes(
    起始地: str = Query(..., description="起始地（模糊搜索）"),
    目的地: str = Query(..., description="目的地（模糊搜索）"),
    货物名称: Optional[str] = Query(None, description="货物名称（模糊搜索）"),
    交易开始日期: Optional[date] = Query(None, description="交易开始日期"),
    交易结束日期: Optional[date] = Query(None, description="交易结束日期"),
    代理商: Optional[str] = Query(None, description="代理商名称（模糊搜索）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    报价查询接口 - 支持关键词模糊搜索
    
    所有文本字段都支持模糊匹配：
    - 起始地、目的地：模糊匹配
    - 货物名称：模糊匹配（如输入"服务器"可匹配"服务器、网卡、显示器"）
    - 代理商：模糊匹配
    - 时间范围：精确匹配
    """
    from sqlalchemy.orm import joinedload
    
    skip = (page - 1) * page_size
    
    # 构建查询（fee_items和fee_total使用joinedload，summary单独查以避免多条记录问题）
    query = db.query(Route).options(
        joinedload(Route.agents).joinedload(RouteAgent.fee_items),
        joinedload(Route.agents).joinedload(RouteAgent.fee_total),
        joinedload(Route.goods_details),
        joinedload(Route.goods_total)
    )
    
    # 起始地和目的地（模糊搜索）
    query = query.filter(Route.起始地.like(f"%{起始地}%"))
    query = query.filter(Route.目的地.like(f"%{目的地}%"))
    
    # 日期范围筛选
    if 交易开始日期:
        query = query.filter(Route.交易开始日期 >= 交易开始日期)
    if 交易结束日期:
        query = query.filter(Route.交易结束日期 <= 交易结束日期)
    
    # 货物名称模糊查询（关键词搜索）
    if 货物名称:
        # 在货物明细表中搜索
        goods_subquery = db.query(GoodsDetail.路线ID).filter(
            GoodsDetail.货物名称.like(f"%{货物名称}%")
        ).distinct()
        query = query.filter(Route.路线ID.in_(goods_subquery))
    
    # 代理商筛选（模糊搜索）
    if 代理商:
        query = query.join(RouteAgent).filter(RouteAgent.代理商.like(f"%{代理商}%"))
    
    # 获取总数
    total = query.count()
    
    # ✅ 修改：按交易开始日期倒序（最新的交易在前）
    results = query.order_by(Route.交易开始日期.desc()).offset(skip).limit(page_size).all()
    
    # 手动序列化所有数据
    quote_results = []
    for route in results:
        route_dict = {
            "路线ID": route.路线ID,
            "起始地": route.起始地,
            "途径地": route.途径地,
            "目的地": route.目的地,
            "交易开始日期": route.交易开始日期.isoformat() if route.交易开始日期 else None,
            "交易结束日期": route.交易结束日期.isoformat() if route.交易结束日期 else None,
            "实际重量": float(route.实际重量) if route.实际重量 else 0.00,
            "计费重量": float(route.计费重量) if route.计费重量 else None,
            "总体积": float(route.总体积) if route.总体积 else None,
            "货值": float(route.货值) if route.货值 else 0.00,
            "创建时间": route.创建时间.isoformat() if route.创建时间 else None,
            "agents": [],
            "goods_details": [],
            "goods_total": []
        }
        
        # 处理每个代理商的费用
        for agent in route.agents:
            agent_dict = {
                "代理路线ID": agent.代理路线ID,
                "路线ID": agent.路线ID,
                "代理商": agent.代理商,
                "运输方式": agent.运输方式,
                "贸易类型": agent.贸易类型,
                "代理备注": agent.代理备注,
                "时效": agent.时效,
                "时效备注": agent.时效备注,
                "不含": agent.不含,
                "是否赔付": agent.是否赔付,
                "赔付内容": agent.赔付内容,
                "创建时间": agent.创建时间.isoformat() if agent.创建时间 else None,
                "fee_items": [],
                "fee_total": [],
                "summary": None,
                "总费用": 0.00
            }
            
            # 添加费用明细
            total_fee = 0.00
            for fee in agent.fee_items:
                fee_dict = {
                    "费用ID": fee.费用ID,
                    "代理路线ID": fee.代理路线ID,
                    "费用类型": fee.费用类型,
                    "单价": float(fee.单价) if fee.单价 else 0.00,
                    "单位": fee.单位,
                    "数量": float(fee.数量) if fee.数量 else 0,
                    "币种": fee.币种,
                    "原币金额": float(fee.原币金额) if fee.原币金额 else 0.00,
                    "人民币金额": float(fee.人民币金额) if fee.人民币金额 else 0.00,
                    "备注": fee.备注,
                    "创建时间": fee.创建时间.isoformat() if fee.创建时间 else None
                }
                agent_dict["fee_items"].append(fee_dict)
                total_fee += float(fee.人民币金额) if fee.人民币金额 else 0.00
            
            # 添加整单费用
            for fee_total_item in agent.fee_total:
                fee_total_dict = {
                    "整单费用ID": fee_total_item.整单费用ID,
                    "代理路线ID": fee_total_item.代理路线ID,
                    "费用名称": fee_total_item.费用名称,
                    "原币金额": float(fee_total_item.原币金额) if fee_total_item.原币金额 else 0.00,
                    "币种": fee_total_item.币种,
                    "人民币金额": float(fee_total_item.人民币金额) if fee_total_item.人民币金额 else 0.00,
                    "备注": fee_total_item.备注,
                    "创建时间": fee_total_item.创建时间.isoformat() if fee_total_item.创建时间 else None
                }
                agent_dict["fee_total"].append(fee_total_dict)
                total_fee += float(fee_total_item.人民币金额) if fee_total_item.人民币金额 else 0.00
            
            # ✅ 修复：直接查询最新的 summary（ORDER BY 汇总ID DESC）
            # 不使用 agent.summary（relationship），避免多条记录时取到错误的第一条
            best_summary = db.query(Summary).filter(
                Summary.代理路线ID == agent.代理路线ID
            ).order_by(Summary.汇总ID.desc()).first()
            
            if best_summary:
                agent_dict["summary"] = {
                    "汇总ID": best_summary.汇总ID,
                    "小计": float(best_summary.小计) if best_summary.小计 else 0.00,
                    "税率": float(best_summary.税率) if best_summary.税率 else 0.0000,
                    "税金": float(best_summary.税金) if best_summary.税金 else 0.00,
                    "汇损率": float(best_summary.汇损率) if best_summary.汇损率 else 0.000000,
                    "汇损": float(best_summary.汇损) if best_summary.汇损 else 0.00,
                    "总计": float(best_summary.总计) if best_summary.总计 else 0.00,
                    "备注": best_summary.备注
                }
            
            agent_dict["总费用"] = total_fee
            route_dict["agents"].append(agent_dict)
        
        # 添加货物明细
        for goods in route.goods_details:
            goods_dict = {
                "货物ID": goods.货物ID,
                "货物名称": goods.货物名称,
                "是否新品": goods.是否新品,
                "货物种类": goods.货物种类,
                "数量": float(goods.数量) if goods.数量 else 0.000,
                "单价": float(goods.单价) if goods.单价 else 0.0000,
                "币种": goods.币种,
                "重量(/kg)": float(goods.重量) if goods.重量 else 0.000,
                "总重量(/kg)": float(goods.总重量) if goods.总重量 else 0.000,
                "总货值": float(goods.总价) if goods.总价 else 0.00,
                "备注": goods.备注
            }
            route_dict["goods_details"].append(goods_dict)
        
        # 添加整单货物
        for goods_total in route.goods_total:
            goods_total_dict = {
                "整单货物ID": goods_total.整单货物ID,
                "货物名称": goods_total.货物名称,
                "实际重量(/kg)": float(goods_total.实际重量) if goods_total.实际重量 else 0.00,  # ✅ 修复：正确字段名
                "货值": float(goods_total.货值) if goods_total.货值 else 0.00,
                "总体积(/cbm)": float(goods_total.总体积) if goods_total.总体积 else 0.000,
                "备注": goods_total.备注  # ✅ 新增：返回备注
            }
            route_dict["goods_total"].append(goods_total_dict)
        
        quote_results.append(route_dict)

    # 补充智能评分
    score_map, dest_lpi_info = _add_scores(db, quote_results)
    for route in quote_results:
        for agent in route["agents"]:
            aid = agent["代理路线ID"]
            if aid in score_map:
                agent.update(score_map[aid])

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": quote_results,
        "dest_lpi_info": dest_lpi_info,
    }