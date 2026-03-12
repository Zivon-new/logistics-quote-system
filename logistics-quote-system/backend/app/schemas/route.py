# backend/app/schemas/route.py
"""
路线相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# ========== 路线相关 ==========

class RouteBase(BaseModel):
    """路线基础Schema"""
    起始地: str = Field(..., description="起始地")
    途径地: Optional[str] = Field(None, description="途径地")
    目的地: str = Field(..., description="目的地")
    交易开始日期: Optional[date] = Field(None, description="交易开始日期")
    交易结束日期: Optional[date] = Field(None, description="交易结束日期")
    实际重量: Optional[Decimal] = Field(0.00, description="实际重量(kg)")
    计费重量: Optional[Decimal] = Field(None, description="计费重量(kg)")
    总体积: Optional[Decimal] = Field(None, description="总体积(cbm)")
    货值: Optional[Decimal] = Field(0.00, description="货值")


class RouteCreate(RouteBase):
    """创建路线Schema"""
    pass


class RouteUpdate(BaseModel):
    """更新路线Schema"""
    起始地: Optional[str] = None
    途径地: Optional[str] = None
    目的地: Optional[str] = None
    交易开始日期: Optional[date] = None
    交易结束日期: Optional[date] = None
    实际重量: Optional[Decimal] = None
    计费重量: Optional[Decimal] = None
    总体积: Optional[Decimal] = None
    货值: Optional[Decimal] = None


class RouteResponse(RouteBase):
    """路线响应Schema"""
    路线ID: int
    创建时间: datetime
    
    class Config:
        from_attributes = True


# ========== 代理商相关 ==========

class AgentBase(BaseModel):
    """代理商基础Schema"""
    路线ID: int
    代理商: Optional[str] = None
    运输方式: Optional[str] = None
    贸易类型: Optional[str] = None
    代理备注: Optional[str] = None
    时效: Optional[str] = None
    时效备注: Optional[str] = None
    不含: Optional[str] = None
    是否赔付: Optional[str] = '0'
    赔付内容: Optional[str] = None


class AgentCreate(AgentBase):
    """创建代理商Schema"""
    pass


class AgentResponse(AgentBase):
    """代理商响应Schema"""
    代理路线ID: int
    创建时间: datetime
    
    class Config:
        from_attributes = True


# ========== 费用相关 ==========

class FeeItemBase(BaseModel):
    """费用明细基础Schema"""
    代理路线ID: int
    费用类型: Optional[str] = None
    单价: Optional[Decimal] = 0.00
    单位: Optional[str] = None
    数量: Optional[Decimal] = 0
    币种: Optional[str] = 'RMB'
    原币金额: Optional[Decimal] = 0.00
    人民币金额: Optional[Decimal] = 0.00
    备注: Optional[str] = None


class FeeItemResponse(FeeItemBase):
    """费用明细响应Schema"""
    费用ID: int
    创建时间: datetime
    
    class Config:
        from_attributes = True


# ========== 完整路线（含代理商和费用）==========

class RouteDetailResponse(RouteResponse):
    """路线详情响应（含代理商信息）"""
    agents: List[AgentResponse] = []
    
    class Config:
        from_attributes = True