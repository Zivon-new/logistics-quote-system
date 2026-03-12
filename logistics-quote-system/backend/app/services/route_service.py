# app/services/route_service.py
"""
路线管理服务层
处理路线相关的业务逻辑
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, Dict, List, Any
from datetime import datetime

from ..models import (
    Route, GoodsDetail, GoodsTotal, RouteAgent, 
    FeeItem, FeeTotal, Summary
)


# ============================================================
# 查询功能
# ============================================================

def get_routes_list(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    origin: Optional[str] = None,
    destination: Optional[str] = None
):
    """
    获取路线列表（带分页和筛选）
    """
    query = db.query(Route)
    
    # 筛选条件
    if origin:
        query = query.filter(Route.起始地.like(f"%{origin}%"))
    if destination:
        query = query.filter(Route.目的地.like(f"%{destination}%"))
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    routes = query.offset(offset).limit(page_size).all()
    
    return {
        "total": total,
        "results": [route_to_dict(route) for route in routes]
    }


def get_route_detail(db: Session, route_id: int):
    """
    获取路线详情（用于查看）
    """
    route = db.query(Route).filter(Route.路线ID == route_id).first()
    if not route:
        return None
    
    # 获取关联数据
    goods_details = db.query(GoodsDetail).filter(GoodsDetail.路线ID == route_id).all()
    goods_total = db.query(GoodsTotal).filter(GoodsTotal.路线ID == route_id).all()
    agents = db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).all()
    
    # 组装数据
    agents_data = []
    for agent in agents:
        fee_items = db.query(FeeItem).filter(FeeItem.代理路线ID == agent.代理路线ID).all()
        fee_total = db.query(FeeTotal).filter(FeeTotal.代理路线ID == agent.代理路线ID).all()
        # ✅ 修复：使用 ORDER BY 汇总ID DESC 获取最新的 summary（防止重复时取错）
        summary = db.query(Summary).filter(
            Summary.代理路线ID == agent.代理路线ID
        ).order_by(Summary.汇总ID.desc()).first()
        
        agents_data.append({
            **agent_to_dict(agent),
            "fee_items": [fee_item_to_dict(f) for f in fee_items],
            "fee_total": [fee_total_to_dict(f) for f in fee_total],
            "summary": summary_to_dict(summary) if summary else None
        })
    
    return {
        "route": route_to_dict(route),
        "goods_details": [goods_detail_to_dict(g) for g in goods_details],
        "goods_total": [goods_total_to_dict(g) for g in goods_total],
        "agents": agents_data
    }


def get_route_for_edit(db: Session, route_id: int):
    """
    获取路线完整数据（用于编辑）
    与get_route_detail相同
    """
    return get_route_detail(db, route_id)


# ============================================================
# 创建功能
# ============================================================

def create_route_with_all_data(db: Session, route_data: Dict) -> int:
    """
    创建路线及所有关联数据
    
    Args:
        route_data: {
            "route": {...},
            "goods_details": [...],
            "goods_total": [...],
            "agents": [...]
        }
    
    Returns:
        route_id: 新创建的路线ID
    """
    try:
        # ✅ 调试日志
        agents_input = route_data.get("agents", [])
        print(f"\n========== 接收创建请求 ==========")
        print(f"📊 agents数量: {len(agents_input)}")
        for i, a in enumerate(agents_input):
            print(f"   Agent {i+1}: {a.get('代理商', '未知')}")
            s = a.get("summary", {})
            print(f"      税率: {s.get('税率', 0)}, 税金: {s.get('税金', 0)}")
            print(f"      汇损率: {s.get('汇损率', 0)}, 汇损: {s.get('汇损', 0)}")
        print(f"==================================\n")

        # 1. 创建路线
        route_info = route_data.get("route", {})
        route = Route(
            起始地=route_info.get("起始地"),
            途径地=route_info.get("途径地"),
            目的地=route_info.get("目的地"),
            交易开始日期=route_info.get("交易开始日期"),
            交易结束日期=route_info.get("交易结束日期"),
            货物名称=route_info.get("货物名称", ""),
            实际重量=route_info.get("实际重量", 0),
            计费重量=route_info.get("计费重量", 0),
            总体积=route_info.get("总体积", 0),
            货值=route_info.get("货值", 0)
        )
        db.add(route)
        db.flush()  # 获取route_id
        
        route_id = route.路线ID
        
        # 2. 创建货物明细
        if route_data.get("goods_details"):
            for goods_data in route_data["goods_details"]:
                goods = GoodsDetail(
                    路线ID=route_id,
                    货物名称=goods_data.get("货物名称"),
                    货物种类=goods_data.get("货物种类"),
                    是否新品=goods_data.get("是否新品", 1),
                    数量=goods_data.get("数量", 0),
                    总重量=goods_data.get("总重量", 0),
                    总货值=goods_data.get("总货值", 0),
                    总价=goods_data.get("总价", goods_data.get("总货值", 0)),
                    备注=goods_data.get("备注")
                )
                db.add(goods)
        
        # 3. 创建整单货物
        if route_data.get("goods_total"):
            for goods_data in route_data["goods_total"]:
                goods = GoodsTotal(
                    路线ID=route_id,
                    货物名称=goods_data.get("货物名称"),
                    实际重量=goods_data.get("实际重量", 0),  # ✅ 修复：使用实际重量（原来是计费重量，字段不存在）
                    货值=goods_data.get("货值", 0),
                    总体积=goods_data.get("总体积", 0),
                    备注=goods_data.get("备注")  # ✅ 新增：保存备注
                )
                db.add(goods)
        
        # 4. 创建代理商及费用
        if route_data.get("agents"):
            for agent_data in route_data["agents"]:
                # 创建代理商
                agent = RouteAgent(
                    路线ID=route_id,
                    代理商=agent_data.get("代理商"),
                    运输方式=agent_data.get("运输方式"),
                    贸易类型=agent_data.get("贸易类型"),
                    时效=agent_data.get("时效"),
                    时效备注=agent_data.get("时效备注"),
                    不含=agent_data.get("不含"),
                    是否赔付=agent_data.get("是否赔付", "0"),
                    赔付内容=agent_data.get("赔付内容"),
                    代理备注=agent_data.get("代理备注")
                )
                db.add(agent)
                db.flush()  # 获取agent_id
                
                agent_id = agent.代理路线ID
                
                # 创建费用明细
                if agent_data.get("fee_items"):
                    for fee_data in agent_data["fee_items"]:
                        fee = FeeItem(
                            代理路线ID=agent_id,
                            费用类型=fee_data.get("费用类型"),
                            单价=fee_data.get("单价", 0),
                            单位=fee_data.get("单位", "/kg"),
                            数量=fee_data.get("数量", 0),
                            币种=fee_data.get("币种", "RMB"),
                            原币金额=fee_data.get("原币金额", 0),
                            人民币金额=fee_data.get("人民币金额", 0),
                            备注=fee_data.get("备注")  # ✅ 新增：保存备注
                        )
                        db.add(fee)
                
                # 创建整单费用
                if agent_data.get("fee_total"):
                    for fee_data in agent_data["fee_total"]:
                        fee = FeeTotal(
                            代理路线ID=agent_id,
                            费用名称=fee_data.get("费用名称"),
                            原币金额=fee_data.get("原币金额", 0),
                            币种=fee_data.get("币种", "RMB"),
                            人民币金额=fee_data.get("人民币金额", 0),
                            备注=fee_data.get("备注")  # ✅ 新增：保存备注
                        )
                        db.add(fee)
                
                # 创建汇总
                if agent_data.get("summary"):
                    # ✅ 修复：先删除旧的summary（防止重复），再插入新的
                    db.query(Summary).filter(Summary.代理路线ID == agent_id).delete()
                    db.flush()
                    
                    summary_data = agent_data["summary"]
                    summary = Summary(
                        代理路线ID=agent_id,
                        小计=summary_data.get("小计", 0),
                        税率=summary_data.get("税率", 0),
                        税金=summary_data.get("税金", 0),
                        汇损率=summary_data.get("汇损率", 0),
                        汇损=summary_data.get("汇损", 0),
                        总计=summary_data.get("总计", 0),
                        备注=summary_data.get("备注")
                    )
                    db.add(summary)
                    print(f"✅ 创建Summary: agent_id={agent_id}, 税率={summary_data.get('税率', 0)}, 税金={summary_data.get('税金', 0)}")
        
        # 提交事务
        db.commit()
        print(f"✅ 路线创建成功: route_id={route_id}")
        
        return route_id
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建失败: {e}")
        raise e


# ============================================================
# 更新功能
# ============================================================

def update_route_with_all_data(db: Session, route_id: int, route_data: Dict) -> bool:
    """
    更新路线及所有关联数据
    
    策略：删除旧数据，插入新数据
    """
    try:
        # 1. 检查路线是否存在
        route = db.query(Route).filter(Route.路线ID == route_id).first()
        if not route:
            return False
        
        # 2. 更新路线基本信息
        route_info = route_data.get("route", {})
        for key, value in route_info.items():
            if hasattr(route, key):
                setattr(route, key, value)
        
        # 3. 删除旧的货物信息
        db.query(GoodsDetail).filter(GoodsDetail.路线ID == route_id).delete()
        db.query(GoodsTotal).filter(GoodsTotal.路线ID == route_id).delete()
        
        # 4. 插入新的货物信息
        if route_data.get("goods_details"):
            for goods_data in route_data["goods_details"]:
                goods = GoodsDetail(
                    路线ID=route_id,
                    货物名称=goods_data.get("货物名称"),
                    货物种类=goods_data.get("货物种类"),
                    是否新品=goods_data.get("是否新品", 1),
                    数量=goods_data.get("数量", 0),
                    总重量=goods_data.get("总重量", 0),
                    总货值=goods_data.get("总货值", 0),
                    总价=goods_data.get("总价", goods_data.get("总货值", 0)),
                    备注=goods_data.get("备注")
                )
                db.add(goods)
        
        if route_data.get("goods_total"):
            for goods_data in route_data["goods_total"]:
                goods = GoodsTotal(
                    路线ID=route_id,
                    货物名称=goods_data.get("货物名称"),
                    实际重量=goods_data.get("实际重量", 0),  # ✅ 修复：使用实际重量
                    货值=goods_data.get("货值", 0),
                    总体积=goods_data.get("总体积", 0),
                    备注=goods_data.get("备注")  # ✅ 新增：保存备注
                )
                db.add(goods)
        
        # 5. 删除旧的代理商及费用
        agents = db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).all()
        for agent in agents:
            db.query(FeeItem).filter(FeeItem.代理路线ID == agent.代理路线ID).delete()
            db.query(FeeTotal).filter(FeeTotal.代理路线ID == agent.代理路线ID).delete()
            db.query(Summary).filter(Summary.代理路线ID == agent.代理路线ID).delete()
        db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).delete()
        
        # 6. 插入新的代理商及费用
        if route_data.get("agents"):
            for agent_data in route_data["agents"]:
                agent = RouteAgent(
                    路线ID=route_id,
                    代理商=agent_data.get("代理商"),
                    运输方式=agent_data.get("运输方式"),
                    贸易类型=agent_data.get("贸易类型"),
                    时效=agent_data.get("时效"),
                    时效备注=agent_data.get("时效备注"),
                    不含=agent_data.get("不含"),
                    是否赔付=agent_data.get("是否赔付", "0"),
                    赔付内容=agent_data.get("赔付内容"),
                    代理备注=agent_data.get("代理备注")
                )
                db.add(agent)
                db.flush()
                
                agent_id = agent.代理路线ID
                
                # 费用明细
                if agent_data.get("fee_items"):
                    for fee_data in agent_data["fee_items"]:
                        fee = FeeItem(
                            代理路线ID=agent_id,
                            费用类型=fee_data.get("费用类型"),
                            单价=fee_data.get("单价", 0),
                            单位=fee_data.get("单位", "/kg"),
                            数量=fee_data.get("数量", 0),
                            币种=fee_data.get("币种", "RMB"),
                            原币金额=fee_data.get("原币金额", 0),
                            人民币金额=fee_data.get("人民币金额", 0),
                            备注=fee_data.get("备注")  # ✅ 新增：保存备注
                        )
                        db.add(fee)
                
                # 整单费用
                if agent_data.get("fee_total"):
                    for fee_data in agent_data["fee_total"]:
                        fee = FeeTotal(
                            代理路线ID=agent_id,
                            费用名称=fee_data.get("费用名称"),
                            原币金额=fee_data.get("原币金额", 0),
                            币种=fee_data.get("币种", "RMB"),
                            人民币金额=fee_data.get("人民币金额", 0),
                            备注=fee_data.get("备注")  # ✅ 新增：保存备注
                        )
                        db.add(fee)
                
                # 汇总
                if agent_data.get("summary"):
                    # ✅ 修复：先删除旧的summary（防止重复）
                    db.query(Summary).filter(Summary.代理路线ID == agent_id).delete()
                    db.flush()
                    
                    summary_data = agent_data["summary"]
                    summary = Summary(
                        代理路线ID=agent_id,
                        小计=summary_data.get("小计", 0),
                        税率=summary_data.get("税率", 0),
                        税金=summary_data.get("税金", 0),
                        汇损率=summary_data.get("汇损率", 0),
                        汇损=summary_data.get("汇损", 0),
                        总计=summary_data.get("总计", 0),
                        备注=summary_data.get("备注")
                    )
                    db.add(summary)
        
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        raise e


# ============================================================
# 删除功能
# ============================================================

def delete_route(db: Session, route_id: int) -> bool:
    """
    删除路线（级联删除所有关联数据）
    """
    try:
        route = db.query(Route).filter(Route.路线ID == route_id).first()
        if not route:
            return False
        
        # 删除货物
        db.query(GoodsDetail).filter(GoodsDetail.路线ID == route_id).delete()
        db.query(GoodsTotal).filter(GoodsTotal.路线ID == route_id).delete()
        
        # 删除代理商及费用
        agents = db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).all()
        for agent in agents:
            db.query(FeeItem).filter(FeeItem.代理路线ID == agent.代理路线ID).delete()
            db.query(FeeTotal).filter(FeeTotal.代理路线ID == agent.代理路线ID).delete()
            db.query(Summary).filter(Summary.代理路线ID == agent.代理路线ID).delete()
        db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).delete()
        
        # 删除路线
        db.delete(route)
        db.commit()
        
        return True
        
    except Exception as e:
        db.rollback()
        raise e


# ============================================================
# 代理商管理
# ============================================================

def add_agent_to_route(db: Session, route_id: int, agent_data: Dict) -> int:
    """
    为路线添加代理商
    """
    try:
        agent = RouteAgent(
            路线ID=route_id,
            代理商=agent_data.get("代理商"),
            运输方式=agent_data.get("运输方式"),
            贸易类型=agent_data.get("贸易类型"),
            时效=agent_data.get("时效"),
            时效备注=agent_data.get("时效备注"),
            不含=agent_data.get("不含"),
            是否赔付=agent_data.get("是否赔付", "0"),
            赔付内容=agent_data.get("赔付内容"),
            代理备注=agent_data.get("代理备注")
        )
        db.add(agent)
        db.flush()
        
        agent_id = agent.代理路线ID
        
        # 添加费用等（如果有）
        # ...
        
        db.commit()
        return agent_id
        
    except Exception as e:
        db.rollback()
        raise e


def delete_agent(db: Session, route_id: int, agent_id: int) -> bool:
    """
    删除代理商
    """
    try:
        agent = db.query(RouteAgent).filter(
            and_(
                RouteAgent.代理路线ID == agent_id,
                RouteAgent.路线ID == route_id
            )
        ).first()
        
        if not agent:
            return False
        
        # 删除费用
        db.query(FeeItem).filter(FeeItem.代理路线ID == agent_id).delete()
        db.query(FeeTotal).filter(FeeTotal.代理路线ID == agent_id).delete()
        db.query(Summary).filter(Summary.代理路线ID == agent_id).delete()
        
        # 删除代理商
        db.delete(agent)
        db.commit()
        
        return True
        
    except Exception as e:
        db.rollback()
        raise e


# ============================================================
# 辅助函数 - Model转Dict
# ============================================================

def route_to_dict(route):
    """Route模型转字典"""
    return {
        "路线ID": route.路线ID,
        "起始地": route.起始地,
        "途径地": route.途径地,
        "目的地": route.目的地,
        "交易开始日期": str(route.交易开始日期) if route.交易开始日期 else None,
        "交易结束日期": str(route.交易结束日期) if route.交易结束日期 else None,
        "货物名称": route.货物名称,
        "实际重量(/kg)": float(route.实际重量) if route.实际重量 else 0,
        "计费重量(/kg)": float(route.计费重量) if route.计费重量 else 0,
        "总体积(/cbm)": float(route.总体积) if route.总体积 else 0,
        "货值": float(route.货值) if route.货值 else 0
    }


def goods_detail_to_dict(goods):
    """GoodsDetail模型转字典"""
    return {
        "货物ID": goods.货物ID,
        "路线ID": goods.路线ID,
        "货物名称": goods.货物名称,
        "货物种类": goods.货物种类,
        "是否新品": goods.是否新品,
        "数量": goods.数量,
        "总重量(/kg)": float(goods.总重量) if goods.总重量 else 0,
        "总货值": float(goods.总货值) if goods.总货值 else 0,
        "总价": float(goods.总价) if goods.总价 else 0,
        "备注": goods.备注
    }


def goods_total_to_dict(goods):
    """GoodsTotal模型转字典"""
    return {
        "整单货物ID": goods.整单货物ID,
        "路线ID": goods.路线ID,
        "货物名称": goods.货物名称,
        "实际重量(/kg)": float(goods.实际重量) if goods.实际重量 else 0,  # ✅ 修复：正确字段名和属性
        "货值": float(goods.货值) if goods.货值 else 0,
        "总体积(/cbm)": float(goods.总体积) if goods.总体积 else 0,
        "备注": goods.备注  # ✅ 新增：返回备注
    }


def agent_to_dict(agent):
    """RouteAgent模型转字典"""
    return {
        "代理路线ID": agent.代理路线ID,
        "路线ID": agent.路线ID,
        "代理商": agent.代理商,
        "运输方式": agent.运输方式,
        "贸易类型": agent.贸易类型,
        "时效": agent.时效,
        "时效备注": agent.时效备注,
        "不含": agent.不含,
        "是否赔付": agent.是否赔付,
        "赔付内容": agent.赔付内容,
        "代理备注": agent.代理备注
    }


def fee_item_to_dict(fee):
    """FeeItem模型转字典"""
    return {
        "费用ID": fee.费用ID,
        "代理路线ID": fee.代理路线ID,
        "费用类型": fee.费用类型,
        "单价": float(fee.单价) if fee.单价 else 0,
        "单位": fee.单位,
        "数量": float(fee.数量) if fee.数量 else 0,
        "币种": fee.币种,
        "原币金额": float(fee.原币金额) if fee.原币金额 else 0,
        "人民币金额": float(fee.人民币金额) if fee.人民币金额 else 0,
        "备注": fee.备注  # ✅ 新增：返回备注
    }


def fee_total_to_dict(fee):
    """FeeTotal模型转字典"""
    return {
        "整单费用ID": fee.整单费用ID,
        "代理路线ID": fee.代理路线ID,
        "费用名称": fee.费用名称,
        "原币金额": float(fee.原币金额) if fee.原币金额 else 0,
        "币种": fee.币种,
        "人民币金额": float(fee.人民币金额) if fee.人民币金额 else 0,
        "备注": fee.备注  # ✅ 新增：返回备注
    }


def summary_to_dict(summary):
    """Summary模型转字典"""
    if not summary:
        return None
    return {
        "汇总ID": summary.汇总ID,
        "代理路线ID": summary.代理路线ID,
        "小计": float(summary.小计) if summary.小计 else 0,
        "税率": float(summary.税率) if summary.税率 else 0,
        "税金": float(summary.税金) if summary.税金 else 0,
        "汇损率": float(summary.汇损率) if summary.汇损率 else 0,
        "汇损": float(summary.汇损) if summary.汇损 else 0,
        "总计": float(summary.总计) if summary.总计 else 0,
        "备注": summary.备注
    }