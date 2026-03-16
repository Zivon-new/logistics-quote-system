# backend/app/api/v1/ports.py
"""
全球港口地图 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...database import get_db
from ...core.deps import get_current_user
from ...models.user import User

router = APIRouter(prefix="/ports", tags=["港口地图"])


@router.get("")
async def get_ports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有港口列表（含坐标），用于地图渲染"""
    rows = db.execute(text("""
        SELECT
            港口ID, UNLOCODE, 港口名称, 港口英文名,
            国家代码, 国家名称, 城市,
            纬度, 经度, 港口类型,
            所属时区, 平均清关天数, LPI风险等级, 备注
        FROM ports
        WHERE 纬度 IS NOT NULL AND 经度 IS NOT NULL
        ORDER BY 国家名称, 港口名称
    """)).fetchall()

    return [
        {
            "id": r[0],
            "unlocode": r[1],
            "name": r[2],
            "name_en": r[3],
            "country_code": r[4],
            "country": r[5],
            "city": r[6],
            "lat": float(r[7]),
            "lng": float(r[8]),
            "type": r[9],
            "timezone": r[10],
            "clearance_days": float(r[11]) if r[11] else None,
            "lpi_risk": r[12],
            "remark": r[13],
        }
        for r in rows
    ]


@router.get("/stats")
async def get_port_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """港口统计概览"""
    total = db.execute(text("SELECT COUNT(*) FROM ports")).scalar()
    by_type = db.execute(text(
        "SELECT 港口类型, COUNT(*) FROM ports GROUP BY 港口类型"
    )).fetchall()
    by_risk = db.execute(text(
        "SELECT LPI风险等级, COUNT(*) FROM ports GROUP BY LPI风险等级"
    )).fetchall()
    countries = db.execute(text(
        "SELECT COUNT(DISTINCT 国家代码) FROM ports"
    )).scalar()

    return {
        "total": total,
        "countries": countries,
        "by_type": {r[0]: r[1] for r in by_type},
        "by_risk": {r[0]: r[1] for r in by_risk},
    }
