# backend/app/models/fee.py
"""
费用相关模型
"""
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base


class FeeItem(Base):
    """费用明细表模型"""
    __tablename__ = "fee_items"
    
    费用ID = Column("费用ID", Integer, primary_key=True, index=True, autoincrement=True)
    代理路线ID = Column("代理路线ID", Integer, ForeignKey("route_agents.代理路线ID"), nullable=False)  # ✅ 添加ForeignKey
    费用类型 = Column("费用类型", String(200), nullable=True)
    单价 = Column("单价", DECIMAL(18, 2), default=0.00)
    单位 = Column("单位", String(50), nullable=True)
    数量 = Column("数量", DECIMAL(18, 3), default=0)
    币种 = Column("币种", String(20), default='RMB')
    原币金额 = Column("原币金额", DECIMAL(18, 2), default=0.00)
    人民币金额 = Column("人民币金额", DECIMAL(18, 2), default=0.00)
    备注 = Column("备注", String(255), nullable=True)
    创建时间 = Column("创建时间", DateTime, server_default=func.now())
    
    # 关系
    agent = relationship("RouteAgent", back_populates="fee_items")


class FeeTotal(Base):
    """整单费用表模型"""
    __tablename__ = "fee_total"
    
    整单费用ID = Column("整单费用ID", Integer, primary_key=True, index=True, autoincrement=True)
    代理路线ID = Column("代理路线ID", Integer, ForeignKey("route_agents.代理路线ID"), nullable=False)  # ✅ 添加ForeignKey
    费用名称 = Column("费用名称", String(200), nullable=True)
    原币金额 = Column("原币金额", DECIMAL(18, 2), default=0.00)
    币种 = Column("币种", String(20), default='RMB')
    人民币金额 = Column("人民币金额", DECIMAL(18, 2), default=0.00)
    备注 = Column("备注", String(255), nullable=True)
    创建时间 = Column("创建时间", DateTime, server_default=func.now())
    
    # 关系
    agent = relationship("RouteAgent", back_populates="fee_total")


class Summary(Base):
    """汇总表模型"""
    __tablename__ = "summary"

    汇总ID = Column("汇总ID", Integer, primary_key=True, index=True, autoincrement=True)
    代理路线ID = Column("代理路线ID", Integer, ForeignKey("route_agents.代理路线ID"), nullable=False, unique=True)
    小计 = Column("小计", DECIMAL(18, 2), default=0.00)
    运费小计 = Column("运费小计", DECIMAL(18, 2), nullable=True)
    税率 = Column("税率", DECIMAL(10, 4), default=0.0000)
    进口税率原文 = Column("进口税率原文", Text, nullable=True)
    税金 = Column("税金", DECIMAL(18, 2), default=0.00)
    税金金额 = Column("税金金额", DECIMAL(18, 2), nullable=True)
    汇损率 = Column("汇损率", DECIMAL(10, 6), default=0.000000)
    汇损 = Column("汇损", DECIMAL(18, 2), default=0.00)
    总计 = Column("总计", DECIMAL(18, 2), default=0.00)
    总计金额 = Column("总计金额", DECIMAL(18, 2), nullable=True)
    备注 = Column("备注", String(255), nullable=True)
    创建时间 = Column("创建时间", DateTime, server_default=func.now())
    
    # 关系
    agent = relationship("RouteAgent", back_populates="summary")