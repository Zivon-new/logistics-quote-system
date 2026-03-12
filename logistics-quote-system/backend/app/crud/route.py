# backend/app/crud/route.py
"""
路线CRUD操作
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from datetime import date
from decimal import Decimal
from ..models.route import Route, RouteAgent
from ..models.fee import FeeItem
from ..schemas.route import RouteCreate, RouteUpdate


def get_route(db: Session, route_id: int) -> Optional[Route]:
    """获取单个路线"""
    return db.query(Route).options(
        joinedload(Route.agents).joinedload(RouteAgent.fee_items)
    ).filter(Route.路线ID == route_id).first()


def get_routes(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    起始地: Optional[str] = None,
    目的地: Optional[str] = None,
) -> List[Route]:
    """获取路线列表"""
    query = db.query(Route).options(
        joinedload(Route.agents)
    )
    
    if 起始地:
        query = query.filter(Route.起始地.like(f"%{起始地}%"))
    if 目的地:
        query = query.filter(Route.目的地.like(f"%{目的地}%"))
    
    return query.order_by(Route.创建时间.desc()).offset(skip).limit(limit).all()


def get_routes_count(
    db: Session,
    起始地: Optional[str] = None,
    目的地: Optional[str] = None,
) -> int:
    """获取路线总数"""
    query = db.query(Route)
    
    if 起始地:
        query = query.filter(Route.起始地.like(f"%{起始地}%"))
    if 目的地:
        query = query.filter(Route.目的地.like(f"%{目的地}%"))
    
    return query.count()


def search_quotes(
    db: Session,
    起始地: str,
    目的地: str,
    交易开始日期: Optional[date] = None,
    交易结束日期: Optional[date] = None,
    最小重量: Optional[Decimal] = None,
    最大重量: Optional[Decimal] = None,
    最小体积: Optional[Decimal] = None,
    最大体积: Optional[Decimal] = None,
    代理商: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[List[Route], int]:
    """搜索报价"""
    query = db.query(Route).options(
        joinedload(Route.agents).joinedload(RouteAgent.fee_items)
    )
    
    # 起始地和目的地（模糊搜索）
    query = query.filter(Route.起始地.like(f"%{起始地}%"))
    query = query.filter(Route.目的地.like(f"%{目的地}%"))
    
    # 日期范围筛选
    if 交易开始日期:
        query = query.filter(Route.交易开始日期 >= 交易开始日期)
    if 交易结束日期:
        query = query.filter(Route.交易结束日期 <= 交易结束日期)
    
    # 重量范围筛选
    if 最小重量:
        query = query.filter(Route.实际重量 >= 最小重量)
    if 最大重量:
        query = query.filter(Route.实际重量 <= 最大重量)
    
    # 体积范围筛选
    if 最小体积:
        query = query.filter(Route.总体积 >= 最小体积)
    if 最大体积:
        query = query.filter(Route.总体积 <= 最大体积)
    
    # 代理商筛选（需要join）
    if 代理商:
        query = query.join(RouteAgent).filter(RouteAgent.代理商.like(f"%{代理商}%"))
    
    total = query.count()
    results = query.order_by(Route.创建时间.desc()).offset(skip).limit(limit).all()
    
    return results, total


def create_route(db: Session, route: RouteCreate) -> Route:
    """创建路线"""
    db_route = Route(**route.dict())
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route


def update_route(db: Session, route_id: int, route: RouteUpdate) -> Optional[Route]:
    """更新路线"""
    db_route = get_route(db, route_id)
    if not db_route:
        return None
    
    update_data = route.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_route, field, value)
    
    db.commit()
    db.refresh(db_route)
    return db_route


def delete_route(db: Session, route_id: int) -> bool:
    """删除路线"""
    db_route = get_route(db, route_id)
    if not db_route:
        return False
    
    db.delete(db_route)
    db.commit()
    return True
