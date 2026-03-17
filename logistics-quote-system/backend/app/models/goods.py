# backend/app/models/goods.py
"""
货物相关模型
"""
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Boolean, func, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base


class GoodsDetail(Base):
    """货物明细表模型"""
    __tablename__ = "goods_details"

    货物ID = Column("货物ID", Integer, primary_key=True, index=True, autoincrement=True)
    路线ID = Column("路线ID", Integer, ForeignKey("routes.路线ID"), nullable=False)
    货物名称 = Column("货物名称", String(200), nullable=True)
    SKU = Column("SKU", String(100), nullable=True)
    HS编码 = Column("HS编码", String(20), nullable=True)
    原产国 = Column("原产国", String(60), nullable=True)
    货物大类 = Column("货物大类", String(50), nullable=True)
    是否新品 = Column("是否新品", Boolean, default=False)
    货物种类 = Column("货物种类", String(100), nullable=True)
    数量 = Column("数量", DECIMAL(18, 3), default=0.000)
    单价 = Column("单价", DECIMAL(18, 4), default=0.0000)
    币种 = Column("币种", String(20), default='RMB')
    重量 = Column("重量(/kg)", DECIMAL(18, 3), default=0.000)
    总重量 = Column("总重量(/kg)", DECIMAL(18, 3), default=0.000)
    总价 = Column("总价", DECIMAL(18, 2), default=0.00)
    备注 = Column("备注", String(255), nullable=True)
    创建时间 = Column("创建时间", DateTime, server_default=func.now())
    
    # 关系
    route = relationship("Route", back_populates="goods_details")


class GoodsTotal(Base):
    """整单货物表模型"""
    __tablename__ = "goods_total"
    
    整单货物ID = Column("整单货物ID", Integer, primary_key=True, index=True, autoincrement=True)
    路线ID = Column("路线ID", Integer, ForeignKey("routes.路线ID"), nullable=False)  # ✅ 添加ForeignKey
    货物名称 = Column("货物名称", String(255), nullable=True)
    实际重量 = Column("实际重量(/kg)", DECIMAL(18, 2), default=0.00)
    货值 = Column("货值", DECIMAL(18, 2), default=0.00)
    货值币种 = Column("货值币种", String(20), default='RMB')
    总体积 = Column("总体积(/cbm)", DECIMAL(18, 3), default=0.000)
    备注 = Column("备注", String(255), nullable=True)
    创建时间 = Column("创建时间", DateTime, server_default=func.now())
    
    # 关系
    route = relationship("Route", back_populates="goods_total")