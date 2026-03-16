# backend/app/api/v1/warnings.py
"""
航线风险预警 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from ...database import get_db
from ...core.deps import get_current_user
from ...models.user import User

router = APIRouter(prefix="/warnings", tags=["航线预警"])

LEVEL_LABEL = {1: "低风险", 2: "中等风险", 3: "高风险"}


def _row_to_dict(r) -> dict:
    return {
        "预警ID":    r[0],
        "国家代码":  r[1],
        "国家中文名": r[2],
        "风险类型":  r[3],
        "风险等级":  r[4],
        "风险等级文字": LEVEL_LABEL.get(r[4], "未知"),
        "预警标题":  r[5],
        "预警详情":  r[6],
        "生效日期":  str(r[7]),
    }


@router.get("/list", summary="获取全部有效预警")
async def list_warnings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rows = db.execute(text("""
        SELECT 预警ID, 国家代码, 国家中文名, 风险类型, 风险等级,
               预警标题, 预警详情, 生效日期
        FROM route_warnings
        WHERE 是否有效 = 1
        ORDER BY 风险等级 DESC, 生效日期 DESC
    """)).fetchall()
    return [_row_to_dict(r) for r in rows]


# ── 供其他模块直接调用的工具函数 ──────────────────────────────────

def get_warnings_for_destinations(db: Session, destinations: List[str]) -> dict:
    """
    给定目的地列表，返回 {目的地: [预警列表]} 映射。
    匹配规则：route_warnings.目的地关键词 是 目的地字符串的子串，或反之。
    """
    if not destinations:
        return {}

    rows = db.execute(text("""
        SELECT 预警ID, 国家代码, 国家中文名, 风险类型, 风险等级,
               预警标题, 预警详情, 生效日期, 目的地关键词
        FROM route_warnings
        WHERE 是否有效 = 1
        ORDER BY 风险等级 DESC
    """)).fetchall()

    # 预处理：{keyword: [warning_dict, ...]}
    warnings_by_kw: dict = {}
    for r in rows:
        kw = r[8]  # 目的地关键词
        w = _row_to_dict(r)
        warnings_by_kw.setdefault(kw, []).append(w)

    result: dict = {}
    for dest in destinations:
        matched = []
        dest_lower = dest.lower() if dest else ""
        for kw, ws in warnings_by_kw.items():
            kw_lower = kw.lower()
            if kw_lower in dest_lower or dest_lower in kw_lower:
                matched.extend(ws)
        if matched:
            # 去重（同一目的地可能匹配多个关键词但指向同一预警）
            seen = set()
            unique = []
            for w in matched:
                if w["预警ID"] not in seen:
                    seen.add(w["预警ID"])
                    unique.append(w)
            result[dest] = sorted(unique, key=lambda x: -x["风险等级"])

    return result
