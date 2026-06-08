# backend/app/api/v1/routes.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, text
from typing import Optional
from datetime import datetime
from ...core.deps import get_db, get_current_user
from ...models.user import User
from ...models.route import Route, RouteAgent
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routes", tags=["路线管理"])

from ...schemas.route import RouteDetailDataResponse
from ...services.fee_service import (
    get_forex_rates as _get_forex_rates,
    apply_min_fee, clean_goods_detail, clean_goods_total
)
from ...services import route_service


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("", response_model=dict, summary="获取路线列表")
async def get_routes(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    起始地: Optional[str] = Query(None, description="起始地筛选"),
    目的地: Optional[str] = Query(None, description="目的地筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取路线列表（分页）"""
    skip = (page - 1) * page_size

    query = db.query(Route)
    if 起始地:
        query = query.filter(Route.起始地.like(f"%{起始地}%"))
    if 目的地:
        query = query.filter(Route.目的地.like(f"%{目的地}%"))
    total = query.count()
    routes = query.order_by(Route.创建时间.desc()).offset(skip).limit(page_size).all()

    route_ids = [r.路线ID for r in routes]
    all_agents = (
        db.query(RouteAgent).filter(RouteAgent.路线ID.in_(route_ids)).all()
        if route_ids else []
    )
    agents_by_route: dict = {}
    for agent in all_agents:
        agents_by_route.setdefault(agent.路线ID, []).append(agent)

    # 批量查操作人姓名
    user_ids = set()
    for r in routes:
        if r.创建人ID: user_ids.add(r.创建人ID)
        if r.更新人ID: user_ids.add(r.更新人ID)
    user_names: dict = {}
    if user_ids:
        from ...models.user import User as UserModel
        users = db.query(UserModel).filter(UserModel.id.in_(user_ids)).all()
        user_names = {u.id: (u.full_name or u.username) for u in users}

    results = []
    for route in routes:
        results.append({
            "路线ID":        route.路线ID,
            "起始地":        route.起始地,
            "途径地":        route.途径地,
            "目的地":        route.目的地,
            "交易开始日期":  str(route.交易开始日期) if route.交易开始日期 else None,
            "交易结束日期":  str(route.交易结束日期) if route.交易结束日期 else None,
            "实际重量(/kg)": float(route.实际重量) if route.实际重量 else 0,
            "计费重量(/kg)": float(route.计费重量) if route.计费重量 else 0,
            "总体积(/cbm)":  float(route.总体积) if route.总体积 else 0,
            "货值":          float(route.货值) if route.货值 else 0,
            "货值币种":      route.货值币种 or 'RMB',
            "创建时间":      str(route.创建时间) if route.创建时间 else None,
            "创建人名":      user_names.get(route.创建人ID),
            "更新人名":      user_names.get(route.更新人ID),
            "agents": [
                {"代理商": a.代理商, "运输方式": a.运输方式}
                for a in agents_by_route.get(route.路线ID, [])
            ],
        })

    return {
        "success": True,
        "data": {"results": results, "total": total, "page": page, "page_size": page_size}
    }


@router.get("/stats", summary="获取统计数据")
async def get_route_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_routes  = db.query(Route).count()
    total_agents  = db.query(func.count(func.distinct(RouteAgent.代理商))).scalar()
    now           = datetime.now()
    month_routes  = db.query(Route).filter(
        extract('year',  Route.交易开始日期) == now.year,
        extract('month', Route.交易开始日期) == now.month
    ).count()
    return {"success": True, "data": {
        "total_routes": total_routes,
        "total_agents": total_agents,
        "month_routes": month_routes,
    }}


@router.get("/forex_rates", summary="获取汇率")
async def get_forex_rates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从数据库获取汇率，未录入的币种使用默认值"""
    rates = {
        'RMB': 1.0, 'USD': 7.2, 'EUR': 7.8, 'GBP': 9.2,
        'AUD': 4.7, 'CAD': 5.3, 'SGD': 5.3, 'HKD': 0.93,
        'JPY': 0.05, 'MYR': 1.6,
    }
    reference_date = None
    try:
        for row in db.execute(text("SELECT `币种`, `汇率`, `参考日期` FROM forex_rate")).fetchall():
            rates[row[0]] = float(row[1])
            if row[2] and not reference_date:
                reference_date = str(row[2])
    except Exception:
        pass
    return {"success": True, "data": rates, "reference_date": reference_date}


@router.post("/refresh_forex", summary="手动刷新汇率")
async def refresh_forex_rates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可刷新汇率")
    from ...services.forex_scraper import update_forex_rates
    try:
        rates = update_forex_rates(db)
        return {"success": True, "data": rates, "message": f"汇率已更新，共同步 {len(rates)} 种货币"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"汇率同步失败：{str(e)}")


@router.get("/{route_id}", summary="获取路线详情")
async def get_route_detail(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取路线完整详情（包含代理方案、费用明细、整单费用、货物）"""
    from ...models.fee import FeeItem, FeeTotal, Summary
    from ...models.goods import GoodsDetail, GoodsTotal

    forex_rates = _get_forex_rates(db)
    route = db.query(Route).filter(Route.路线ID == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="路线不存在")

    route_data = {
        "路线ID":        route.路线ID,
        "起始地":        route.起始地,
        "途径地":        route.途径地,
        "目的地":        route.目的地,
        "交易开始日期":  str(route.交易开始日期) if route.交易开始日期 else None,
        "交易结束日期":  str(route.交易结束日期) if route.交易结束日期 else None,
        "交易年份":      route.交易年份,
        "交易月份":      route.交易月份,
        "实际重量(/kg)": float(route.实际重量) if route.实际重量 else 0,
        "计费重量(/kg)": float(route.计费重量) if route.计费重量 else 0,
        "总体积(/cbm)":  float(route.总体积) if route.总体积 else 0,
        "货值":          float(route.货值) if route.货值 else 0,
        "货值币种":      route.货值币种 or 'RMB',
        "货物名称":      route.货物名称,
        "创建时间":      str(route.创建时间) if route.创建时间 else None,
        "agents":        [],
        "goods_details": [],
        "goods_total":   [],
    }

    for agent in db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).all():
        fee_items = db.query(FeeItem).filter(FeeItem.代理路线ID == agent.代理路线ID).all()
        fee_total = db.query(FeeTotal).filter(FeeTotal.代理路线ID == agent.代理路线ID).all()
        summary   = db.query(Summary).filter(Summary.代理路线ID == agent.代理路线ID).first()

        route_data["agents"].append({
            "代理路线ID": agent.代理路线ID,
            "代理商":     agent.代理商,
            "运输方式":   agent.运输方式,
            "贸易类型":   agent.贸易类型,
            "时效":       agent.时效,
            "时效备注":   agent.时效备注,
            "不含":       agent.不含,
            "是否赔付":   agent.是否赔付,
            "赔付内容":   agent.赔付内容,
            "代理备注":   agent.代理备注,
            "fee_items": apply_min_fee(fee_items, forex_rates),
            "fee_total": [{
                "整单费用ID": ft.整单费用ID,
                "费用名称":   ft.费用名称,
                "币种":       ft.币种,
                "原币金额":   float(ft.原币金额) if ft.原币金额 else 0,
                "人民币金额": float(ft.人民币金额) if ft.人民币金额 else 0,
                "备注":       ft.备注,
                "参与核算":   ft.参与核算 if ft.参与核算 is not None else 1,
            } for ft in fee_total],
            "summary": {
                "汇总ID":     summary.汇总ID,
                "小计":       float(summary.小计) if summary.小计 else 0,
                "税率":       float(summary.税率) if summary.税率 else 0,
                "税金":       float(summary.税金) if summary.税金 else 0,
                "汇损率":     float(summary.汇损率) if summary.汇损率 else 0,
                "汇损":       float(summary.汇损) if summary.汇损 else 0,
                "总计":       float(summary.总计) if summary.总计 else 0,
                "备注":       summary.备注,
                "进口税率原文": summary.进口税率原文,
            } if summary else {},
        })

    route_data["goods_details"] = [{
        "货物ID":     g.货物ID,
        "货物名称":   g.货物名称,
        "是否新品":   g.是否新品,
        "货物种类":   g.货物种类,
        "数量":       float(g.数量) if g.数量 else 0,
        "单价":       float(g.单价) if g.单价 else 0,
        "币种":       g.币种,
        "重量(/kg)":  float(g.重量) if g.重量 else 0,
        "总重量(/kg)": float(g.总重量) if g.总重量 else 0,
        "总价":       float(g.总价) if g.总价 else 0,
        "总货值":     float(g.总价) if g.总价 else 0,
        "备注":       g.备注,
    } for g in db.query(GoodsDetail).filter(GoodsDetail.路线ID == route_id).all()]

    route_data["goods_total"] = [{
        "整单货物ID":   g.整单货物ID,
        "货物名称":     g.货物名称,
        "实际重量(/kg)": float(g.实际重量) if g.实际重量 else 0,
        "数量":         float(g.数量) if g.数量 else 0,
        "总体积(/cbm)": float(g.总体积) if g.总体积 else 0,
        "货值":         float(g.货值) if g.货值 else 0,
        "货值币种":     g.货值币种 or 'RMB',
        "备注":         g.备注,
    } for g in db.query(GoodsTotal).filter(GoodsTotal.路线ID == route_id).all()]

    return {"success": True, "data": RouteDetailDataResponse(**route_data).model_dump(by_alias=True)}


@router.post("/full", summary="创建完整路线（手动录入/Excel导入）")
async def create_full_route(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        route_id = route_service.create_full_route(db, data, current_user)
        return {"success": True, "message": "创建成功", "route_id": route_id}

    except Exception as e:
        db.rollback()
        logger.error("create_full_route 失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.put("/{route_id}", summary="更新路线")
async def update_route(
    route_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新策略：独立事务分阶段提交；货物先INSERT后DELETE防止触发器把汇总清零。"""
    if not db.execute(text("SELECT COUNT(*) FROM routes WHERE `路线ID` = :id"), {"id": route_id}).scalar():
        raise HTTPException(status_code=404, detail="路线不存在")

    try:
        route_service.update_route(db, route_id, data, current_user)
        return {"success": True, "message": "更新成功", "route_id": route_id}

    except Exception as e:
        db.rollback()
        logger.error("update_route 失败 route_id=%s: %s", route_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/{route_id}", summary="删除路线")
async def delete_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除路线及其所有关联数据"""
    from ...models.fee import FeeItem, FeeTotal, Summary
    from ...models.goods import GoodsDetail, GoodsTotal

    route = db.query(Route).filter(Route.路线ID == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="路线不存在")

    for agent in db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).all():
        db.query(FeeItem).filter(FeeItem.代理路线ID == agent.代理路线ID).delete()
        db.query(FeeTotal).filter(FeeTotal.代理路线ID == agent.代理路线ID).delete()
        db.query(Summary).filter(Summary.代理路线ID == agent.代理路线ID).delete()
    db.query(RouteAgent).filter(RouteAgent.路线ID == route_id).delete()
    db.query(GoodsDetail).filter(GoodsDetail.路线ID == route_id).delete()
    db.query(GoodsTotal).filter(GoodsTotal.路线ID == route_id).delete()
    db.delete(route)
    db.commit()

    return {"success": True, "message": "删除成功"}


@router.post("/import/upload", summary="上传Excel并提取数据")
async def upload_and_extract_excel(
    file: UploadFile = File(...),
    enable_llm: bool = Form(False),
    current_user: User = Depends(get_current_user)
):
    """上传Excel文件并提取路线、代理方案、费用数据"""
    import uuid
    file_path = None
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="仅支持 .xlsx 或 .xls 格式")

        upload_dir = Path("temp/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
        file_path = upload_dir / safe_name
        with open(file_path, "wb") as f:
            f.write(await file.read())

        from ...services.excel_import_service import get_excel_import_service
        excel_service = get_excel_import_service(enable_llm=enable_llm)
        result = excel_service.extract_from_file(str(file_path))

        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('message'))

        return {
            "success": True,
            "message": "提取成功",
            "data": result['data'],
            "validation": excel_service.validate_extracted_data(result['data']),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")
    finally:
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass


@router.post("/import/save", summary="保存Excel导入的数据")
async def save_imported_data(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量保存从Excel导入的路线数据"""
    try:
        from ...models.goods import GoodsDetail, GoodsTotal
        saved_count = 0
        for route_data in data.get('routes', []):
            route_info = route_data.get('route', {})
            new_route = Route(**route_info)
            new_route.创建人ID = current_user.id
            db.add(new_route)
            db.flush()
            route_id = new_route.路线ID

            for agent_data in route_data.get('agents', []):
                db.add(RouteAgent(路线ID=route_id, **agent_data))

            for goods in route_data.get('goods_details', []):
                db.add(GoodsDetail(路线ID=route_id, **clean_goods_detail(goods)))

            for goods in route_data.get('goods_total', []):
                db.add(GoodsTotal(路线ID=route_id, **clean_goods_total(goods)))

            saved_count += 1

        db.commit()
        return {"success": True, "message": f"成功保存 {saved_count} 条路线", "count": saved_count}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"保存失败: {str(e)}")
