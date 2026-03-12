# backend/app/models/route.py
"""
路线相关模型 - 修复版：添加缺失的字段
"""
from sqlalchemy import Column, Integer, String, Date, DECIMAL, DateTime, func, ForeignKey, Text, SmallInteger, Computed
from sqlalchemy.orm import relationship
from ..database import Base


class Route(Base):
    """路线表模型"""
    __tablename__ = "routes"
    
    # 使用中文字段名（与数据库保持一致）
    路线ID = Column("路线ID", Integer, primary_key=True, index=True, autoincrement=True)
    起始地 = Column("起始地", String(100), nullable=False)
    途径地 = Column("途径地", String(100), nullable=True)
    目的地 = Column("目的地", String(100), nullable=False)
    交易开始日期 = Column("交易开始日期", Date, nullable=True)
    交易结束日期 = Column("交易结束日期", Date, nullable=True)
    
    # ✅ 修复：GENERATED列用Computed，SQLAlchemy不会在INSERT/UPDATE中包含它们
    交易年份 = Column("交易年份", SmallInteger, Computed("year(`交易开始日期`)"))
    交易月份 = Column("交易月份", SmallInteger, Computed("month(`交易开始日期`)"))
    
    实际重量 = Column("实际重量(/kg)", DECIMAL(18, 2), default=0.00)
    计费重量 = Column("计费重量(/kg)", DECIMAL(18, 2), nullable=True)
    总体积 = Column("总体积(/cbm)", DECIMAL(18, 3), nullable=True)
    货值 = Column("货值", DECIMAL(18, 2), default=0.00)
    
    # ✅ 新增：货物名称
    货物名称 = Column("货物名称", Text, nullable=True)
    
    创建时间 = Column("创建时间", DateTime, server_default=func.now())
    
    # 关系
    agents = relationship("RouteAgent", back_populates="route", cascade="all, delete-orphan")
    goods_details = relationship("GoodsDetail", back_populates="route", cascade="all, delete-orphan")
    goods_total = relationship("GoodsTotal", back_populates="route", cascade="all, delete-orphan")


class RouteAgent(Base):
    """代理路线表模型"""
    __tablename__ = "route_agents"
    
    代理路线ID = Column("代理路线ID", Integer, primary_key=True, index=True, autoincrement=True)
    路线ID = Column("路线ID", Integer, ForeignKey("routes.路线ID"), nullable=False)
    代理商 = Column("代理商", String(200), nullable=True)
    运输方式 = Column("运输方式", String(100), nullable=True)
    贸易类型 = Column("贸易类型", String(100), nullable=True)
    代理备注 = Column("代理备注", String(255), nullable=True)
    时效 = Column("时效", String(50), nullable=True)
    时效备注 = Column("时效备注", String(255), nullable=True)
    不含 = Column("不含", String(511), nullable=True)
    是否赔付 = Column("是否赔付", String(255), default='0')
    赔付内容 = Column("赔付内容", String(255), nullable=True)
    创建时间 = Column("创建时间", DateTime, server_default=func.now())
    
    # 关系
    route = relationship("Route", back_populates="agents")
    fee_items = relationship("FeeItem", back_populates="agent", cascade="all, delete-orphan")
    fee_total = relationship("FeeTotal", back_populates="agent", cascade="all, delete-orphan")
    summary = relationship("Summary", back_populates="agent", cascade="all, delete-orphan", uselist=False)