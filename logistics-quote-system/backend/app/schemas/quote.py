# backend/app/schemas/quote.py
"""
报价查询相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from decimal import Decimal
from .route import RouteResponse, AgentResponse, FeeItemResponse


class QuoteSearchRequest(BaseModel):
    """报价查询请求"""
    起始地: str = Field(..., description="起始地")
    目的地: str = Field(..., description="目的地")
    交易开始日期: Optional[date] = Field(None, description="交易开始日期")
    交易结束日期: Optional[date] = Field(None, description="交易结束日期")
    最小重量: Optional[Decimal] = Field(None, description="最小重量(kg)")
    最大重量: Optional[Decimal] = Field(None, description="最大重量(kg)")
    最小体积: Optional[Decimal] = Field(None, description="最小体积(cbm)")
    最大体积: Optional[Decimal] = Field(None, description="最大体积(cbm)")
    代理商: Optional[str] = Field(None, description="代理商名称")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")


class AgentWithFees(AgentResponse):
    """代理商及费用信息"""
    fee_items: List[FeeItemResponse] = []
    总费用: Optional[Decimal] = 0.00


class QuoteResult(RouteResponse):
    """单个报价结果"""
    agents: List[AgentWithFees] = []


class QuoteSearchResponse(BaseModel):
    """报价查询响应"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    results: List[QuoteResult] = Field(..., description="查询结果")
