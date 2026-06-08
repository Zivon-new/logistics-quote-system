# backend/app/services/trigger_guard_service.py
"""
封装 MySQL 触发器执行后的字段补写逻辑 — 让 routes.py 接口层和
route_service 不需要理解触发器副作用的细节（哪些字段会被覆盖、
为什么需要二次写回）。
"""
from sqlalchemy.orm import Session
from sqlalchemy import text

from .route_helpers import sf


def protect_route_fields(db: Session, route_id: int, route_data: dict):
    """触发器可能会重算并覆盖手动录入的重量/体积/货值字段，这里重新写回原始值。"""
    field_map = {
        "实际重量": "实际重量(/kg)",
        "计费重量": "计费重量(/kg)",
        "总体积":   "总体积(/cbm)",
        "货值":     "货值",
    }
    params: dict = {"route_id": route_id}
    clauses = []
    for key, col in field_map.items():
        if key in route_data and route_data[key] is not None:
            p = f"p_{key}"
            params[p] = float(route_data[key]) if route_data[key] else 0
            clauses.append(f"`{col}` = :{p}")
    if clauses:
        db.execute(
            text(f"UPDATE routes SET {', '.join(clauses)} WHERE `路线ID` = :route_id"),
            params
        )
        db.commit()


def correct_agent_summaries(db: Session, agent_summaries: list):
    """触发器重算汇总后会覆盖 税金/汇损/进口税率原文，这里强制改回手动录入值。
    agent_summaries: [(agent_id, summary_data_dict), ...]"""
    if not agent_summaries:
        return
    for agent_id, s in agent_summaries:
        if not s:
            continue
        correct_tax  = sf(s.get('税金金额') or s.get('税金'))
        correct_loss = sf(s.get('汇损'))
        import_text  = s.get('进口税率原文') or ''
        if correct_tax or correct_loss or import_text:
            db.execute(text("""
                UPDATE summary
                SET `税金`         = :税金,
                    `汇损`         = :汇损,
                    `总计`         = `小计` + :税金 + :汇损,
                    `进口税率原文` = :进口税率原文
                WHERE `代理路线ID` = :agent_id
            """), {
                'agent_id':     agent_id,
                '税金':         correct_tax,
                '汇损':         correct_loss,
                '进口税率原文': import_text,
            })
    db.commit()
