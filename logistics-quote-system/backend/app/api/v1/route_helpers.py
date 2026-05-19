# backend/app/api/v1/route_helpers.py
"""
Pure utility functions extracted from routes.py for testability.
These have no FastAPI or SQLAlchemy imports, so they can be imported in isolation.
"""
from __future__ import annotations


def sf(val, default: float = 0.0) -> float:
    """Safe float conversion — returns default on None or invalid input."""
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def dedupe_agents(agents: list) -> dict:
    """Deduplicate agent list by (代理商, 运输方式) composite key.
    When two entries share the same key, the one with fee data wins."""
    agent_map: dict = {}
    for a in agents:
        name = a.get('代理商', '')
        mode = a.get('运输方式', '')
        key = f"{name}|{mode}"
        if name:
            if key not in agent_map:
                agent_map[key] = a
            elif a.get('fee_items') or a.get('fee_total') or a.get('summary'):
                agent_map[key] = a
    return agent_map
