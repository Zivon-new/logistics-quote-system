# app/routers/routes.py
"""
路线管理路由
新增：手动录入、Excel导入、编辑功能
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import sys
import json
from pathlib import Path

from ..database import get_db
from ..services import route_service
from ..schemas import route as route_schema
from ..api.v1.auth import get_current_user

router = APIRouter(prefix="/routes", tags=["routes"])


# ============================================================
# 基础查询接口
# ============================================================

@router.get("")
async def get_routes(
    page: int = 1,
    page_size: int = 10,
    起始地: Optional[str] = None,
    目的地: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取路线列表（带分页和筛选）
    """
    result = route_service.get_routes_list(
        db=db,
        page=page,
        page_size=page_size,
        origin=起始地,
        destination=目的地
    )
    return result


@router.get("/{route_id}")
async def get_route_detail(
    route_id: int,
    db: Session = Depends(get_db)
):
    """
    获取路线详情（用于查看）
    """
    route_data = route_service.get_route_detail(db, route_id)
    if not route_data:
        raise HTTPException(status_code=404, detail="路线不存在")
    return route_data


@router.get("/{route_id}/edit")
async def get_route_for_edit(
    route_id: int,
    db: Session = Depends(get_db)
):
    """
    获取路线完整数据（用于编辑）
    包含：route, goods_details, goods_total, agents (含fee_items, fee_total, summary)
    """
    route_data = route_service.get_route_for_edit(db, route_id)
    if not route_data:
        raise HTTPException(status_code=404, detail="路线不存在")
    return route_data


# ============================================================
# 手动录入接口
# ============================================================

@router.post("/create")
async def create_route(
    route_data: route_schema.RouteCreateRequest,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user)  # 后续添加权限
):
    """
    创建新路线（手动录入）
    
    请求数据结构：
    {
        "route": {...},           # 路线基本信息
        "goods_details": [...],   # 货物明细（可选）
        "goods_total": [...],     # 整单货物（可选）
        "agents": [               # 代理商列表
            {
                "...": "代理商基本信息",
                "fee_items": [...],   # 费用明细
                "fee_total": [...],   # 整单费用
                "summary": {...}      # 汇总
            }
        ]
    }
    """
    try:
        route_id = route_service.create_route_with_all_data(db, route_data.dict())
        return {
            "success": True,
            "route_id": route_id,
            "message": "路线创建成功"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{route_id}")
async def update_route(
    route_id: int,
    route_data: route_schema.RouteUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    更新路线（编辑功能）
    """
    try:
        success = route_service.update_route_with_all_data(db, route_id, route_data.dict())
        if not success:
            raise HTTPException(status_code=404, detail="路线不存在")
        return {
            "success": True,
            "message": "路线更新成功"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{route_id}")
async def delete_route(
    route_id: int,
    db: Session = Depends(get_db)
):
    """
    删除路线
    """
    success = route_service.delete_route(db, route_id)
    if not success:
        raise HTTPException(status_code=404, detail="路线不存在")
    return {
        "success": True,
        "message": "路线删除成功"
    }


# ============================================================
# Excel导入接口
# ============================================================

# 创建临时文件夹（用于存储上传的Excel）
UPLOAD_DIR = Path("temp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/import/upload")
async def upload_and_extract_excel(
    file: UploadFile = File(...),
    enable_llm: bool = Form(True)
):
    """
    上传Excel文件并提取数据
    
    Returns:
        {
            "routes": [...],
            "route_agents": [...],
            "goods_details": [...],
            "goods_total": [...],
            "fee_items": [...],
            "fee_total": [...],
            "summary": [...]
        }
    """
    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx 或 .xls 格式的文件")
    
    # 保存上传的文件
    file_path = UPLOAD_DIR / file.filename
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 调用Python提取代码
    try:
        # 动态导入你的提取代码
        scripts_path = Path(__file__).parent.parent.parent.parent / "scripts"
        sys.path.insert(0, str(scripts_path))
        
        from scripts.modules.horizontal_table_parser_v2 import HorizontalTableParserV2
        from scripts.modules.llm_enhancer import LLMEnhancer
        from scripts.config import Config
        
        # 初始化LLM客户端（如果启用）
        llm_client = None
        if enable_llm and hasattr(Config, 'ENABLE_LLM_ENHANCE') and Config.ENABLE_LLM_ENHANCE:
            try:
                if hasattr(Config, 'ZHIPU_API_KEY') and Config.ZHIPU_API_KEY:
                    llm_client = LLMEnhancer(api_key=Config.ZHIPU_API_KEY)
            except Exception as e:
                print(f"LLM初始化失败: {e}")
                enable_llm = False
        
        # 创建解析器
        parser = HorizontalTableParserV2(
            enable_llm=enable_llm,
            llm_client=llm_client,
            output_dir=str(UPLOAD_DIR / "output")
        )
        
        # 解析Excel
        result = parser.parse_excel(str(file_path))
        
        # 清理临时文件
        # os.remove(file_path)  # 可选：是否立即删除
        
        return result
        
    except Exception as e:
        # 清理临时文件
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"数据提取失败: {str(e)}")


@router.post("/import/save")
async def save_imported_data(
    import_data: route_schema.ImportDataRequest,
    db: Session = Depends(get_db)
):
    """
    保存Excel导入的数据
    
    数据结构与手动录入相同，但可能包含多条路线
    """
    try:
        # 如果有多条路线，循环创建
        route_ids = []
        
        # 这里简化处理，假设只有一条路线
        # 如果需要支持批量导入，可以修改这里的逻辑
        route_data = {
            "route": import_data.routes[0] if import_data.routes else {},
            "goods_details": import_data.goods_details or [],
            "goods_total": import_data.goods_total or [],
            "agents": []
        }
        
        # 组装agents数据（将route_agents、fee_items、fee_total、summary组合）
        if import_data.route_agents:
            for agent in import_data.route_agents:
                agent_data = {
                    **agent,
                    "fee_items": [],
                    "fee_total": [],
                    "summary": {}
                }
                
                # 查找对应的fee_items
                if import_data.fee_items:
                    agent_data["fee_items"] = [
                        f for f in import_data.fee_items 
                        if f.get("代理路线ID") == agent.get("代理路线ID")
                    ]
                
                # 查找对应的fee_total
                if import_data.fee_total:
                    agent_data["fee_total"] = [
                        f for f in import_data.fee_total 
                        if f.get("代理路线ID") == agent.get("代理路线ID")
                    ]
                
                # 查找对应的summary
                if import_data.summary:
                    summary_list = [
                        s for s in import_data.summary 
                        if s.get("代理路线ID") == agent.get("代理路线ID")
                    ]
                    if summary_list:
                        agent_data["summary"] = summary_list[0]
                
                route_data["agents"].append(agent_data)
        
        # 创建路线
        route_id = route_service.create_route_with_all_data(db, route_data)
        route_ids.append(route_id)
        
        return {
            "success": True,
            "route_ids": route_ids,
            "message": f"成功导入 {len(route_ids)} 条路线"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"保存失败: {str(e)}")


# ============================================================
# 代理商管理接口
# ============================================================

@router.post("/{route_id}/agents")
async def add_agent_to_route(
    route_id: int,
    agent_data: route_schema.AgentCreateRequest,
    db: Session = Depends(get_db)
):
    """
    为路线添加代理商
    """
    try:
        agent_id = route_service.add_agent_to_route(db, route_id, agent_data.dict())
        return {
            "success": True,
            "agent_id": agent_id,
            "message": "代理商添加成功"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{route_id}/agents/{agent_id}")
async def delete_agent(
    route_id: int,
    agent_id: int,
    db: Session = Depends(get_db)
):
    """
    删除代理商
    """
    success = route_service.delete_agent(db, route_id, agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="代理商不存在")
    return {
        "success": True,
        "message": "代理商删除成功"
    }

from sqlalchemy import func
from datetime import datetime

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """获取统计数据"""
    from ..models import Route, RouteAgent
    
    total_routes = db.query(func.count(Route.路线ID)).scalar()
    total_agents = db.query(func.count(func.distinct(RouteAgent.代理商))).scalar()
    
    today = datetime.now()
    first_day_of_month = today.replace(day=1)
    this_month_routes = db.query(func.count(Route.路线ID)).filter(
        Route.交易开始日期 >= first_day_of_month
    ).scalar()
    
    return {
        "totalRoutes": total_routes or 0,
        "totalAgents": total_agents or 0,
        "thisMonthRoutes": this_month_routes or 0
    }