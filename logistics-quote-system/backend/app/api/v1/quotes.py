# backend/app/api/v1/quotes.py
"""
报价查询相关API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from ...core.deps import get_db, get_current_user
from ...models.route import Route, RouteAgent
from ...models.goods import GoodsDetail
from ...models.fee import Summary  # ✅ 新增导入 Summary
from ...models.user import User
from sqlalchemy import and_, or_

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
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": quote_results
    }