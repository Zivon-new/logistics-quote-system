# backend/app/api/v1/recommend.py
"""
智能推荐引擎 API
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from ...database import get_db
from ...services import recommend_service

router = APIRouter(prefix="/recommend", tags=["智能推荐"])


@router.get("")
async def get_recommendations(
    origin: str = Query(..., description="起始地，如：深圳"),
    destination: str = Query(..., description="目的地，如：荷兰"),
    goods_keyword: Optional[str] = Query(None, description="货物关键词，如：服务器"),
    transport_mode: Optional[str] = Query(None, description="运输方式：海运/空运/铁路"),
    sort_by: str = Query("score", description="排序方式：score/time/price"),
    top_n: int = Query(10, ge=1, le=20, description="最多返回条数"),
    db: Session = Depends(get_db)
):
    """
    智能推荐接口

    综合打分：时效(30%) + 价格(30%) + 目的国LPI(20%) + 代理商信用(20%)
    货物关键词：对 routes.货物名称 做模糊匹配，筛选同类货物的历史报价
    """
    return recommend_service.get_recommendations(
        db=db,
        origin=origin,
        destination=destination,
        goods_keyword=goods_keyword,
        transport_mode=transport_mode,
        sort_by=sort_by,
        top_n=top_n
    )


@router.get("/options")
async def get_search_options(db: Session = Depends(get_db)):
    """获取搜索选项（起始地/目的地/货物列表，用于前端下拉）"""
    return {
        "origins": recommend_service.get_available_origins(db),
        "destinations": recommend_service.get_available_destinations(db),
        "goods": recommend_service.get_available_goods(db),
        "transport_modes": ["海运", "空运", "铁路", "陆运", "多式联运"]
    }
