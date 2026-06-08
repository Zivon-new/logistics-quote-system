# backend/app/schemas/route.py
"""
路线相关Schema
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Union
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


# ========== get_route_detail 实际输出结构（手动序列化校验用）==========
# 与上面的 RouteResponse/AgentResponse/FeeItemResponse/RouteDetailResponse 不同：
# 这组模型描述 GET /routes/{route_id} 真实返回的 dict 形状
# （含单位后缀键名、最低收费换算后的金额、整单费用、汇总等字段），
# 用于在 routes.py 手动组装 route_data 之后做一次输出校验。

class FeeItemDetailResponse(BaseModel):
    """费用明细（已套用最低收费规则）"""
    费用ID: int
    费用类型: Optional[str] = None
    单价: float = 0
    单位: Optional[str] = None
    数量: float = 0
    最低收费: Optional[float] = None
    最低收费币种: Optional[str] = None
    币种: str = 'RMB'
    原币金额: float = 0
    人民币金额: float = 0
    备注: Optional[str] = None
    参与核算: int = 1


class FeeTotalResponse(BaseModel):
    """整单费用"""
    整单费用ID: int
    费用名称: Optional[str] = None
    币种: Optional[str] = None
    原币金额: float = 0
    人民币金额: float = 0
    备注: Optional[str] = None
    参与核算: int = 1


class AgentSummaryResponse(BaseModel):
    """代理方案费用汇总"""
    汇总ID: int
    小计: float = 0
    税率: float = 0
    税金: float = 0
    汇损率: float = 0
    汇损: float = 0
    总计: float = 0
    备注: Optional[str] = None
    进口税率原文: Optional[str] = None


class AgentDetailResponse(BaseModel):
    """代理方案详情（含费用明细/整单费用/汇总）"""
    代理路线ID: int
    代理商: Optional[str] = None
    运输方式: Optional[str] = None
    贸易类型: Optional[str] = None
    时效: Optional[str] = None
    时效备注: Optional[str] = None
    不含: Optional[str] = None
    是否赔付: Optional[str] = None
    赔付内容: Optional[str] = None
    代理备注: Optional[str] = None
    fee_items: List[FeeItemDetailResponse] = []
    fee_total: List[FeeTotalResponse] = []
    summary: Union[AgentSummaryResponse, dict] = {}


class GoodsDetailItemResponse(BaseModel):
    """货物明细"""
    model_config = ConfigDict(populate_by_name=True)

    货物ID: int
    货物名称: Optional[str] = None
    是否新品: Optional[str] = None
    货物种类: Optional[str] = None
    数量: float = 0
    单价: float = 0
    币种: Optional[str] = None
    重量_kg: float = Field(0, alias="重量(/kg)")
    总重量_kg: float = Field(0, alias="总重量(/kg)")
    总价: float = 0
    总货值: float = 0
    备注: Optional[str] = None


class GoodsTotalItemResponse(BaseModel):
    """整单货物"""
    model_config = ConfigDict(populate_by_name=True)

    整单货物ID: int
    货物名称: Optional[str] = None
    实际重量_kg: float = Field(0, alias="实际重量(/kg)")
    数量: float = 0
    总体积_cbm: float = Field(0, alias="总体积(/cbm)")
    货值: float = 0
    货值币种: str = 'RMB'
    备注: Optional[str] = None


class RouteDetailDataResponse(BaseModel):
    """GET /routes/{route_id} 的 data 字段完整结构"""
    model_config = ConfigDict(populate_by_name=True)

    路线ID: int
    起始地: Optional[str] = None
    途径地: Optional[str] = None
    目的地: Optional[str] = None
    交易开始日期: Optional[str] = None
    交易结束日期: Optional[str] = None
    交易年份: Optional[int] = None
    交易月份: Optional[int] = None
    实际重量_kg: float = Field(0, alias="实际重量(/kg)")
    计费重量_kg: float = Field(0, alias="计费重量(/kg)")
    总体积_cbm: float = Field(0, alias="总体积(/cbm)")
    货值: float = 0
    货值币种: str = 'RMB'
    货物名称: Optional[str] = None
    创建时间: Optional[str] = None
    agents: List[AgentDetailResponse] = []
    goods_details: List[GoodsDetailItemResponse] = []
    goods_total: List[GoodsTotalItemResponse] = []
