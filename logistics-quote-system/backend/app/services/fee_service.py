# backend/app/services/fee_service.py
"""
费用计算公用工具 — 被 routes 和 quotes 共享。
保持单一来源，避免汇率/最低收费换算逻辑在两处分叉。
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text


def get_forex_rates(db: Session) -> dict:
    """Return {currency: rmb_rate} from forex_rate table, with RMB=1."""
    rows = db.execute(text("SELECT 币种, 汇率 FROM forex_rate")).fetchall()
    rates = {r[0]: float(r[1]) for r in rows}
    rates.setdefault('RMB', 1.0)
    rates.setdefault('CNY', 1.0)
    return rates


def convert_min_fee(min_fee: float, min_cur: str, fee_cur: str, rates: dict) -> float:
    """Convert min_fee from min_cur to fee_cur using forex rates (RMB as pivot)."""
    if min_cur == fee_cur:
        return min_fee
    rmb_per_min = rates.get(min_cur, 1.0)
    rmb_per_fee = rates.get(fee_cur, 1.0)
    if rmb_per_fee == 0:
        return min_fee
    return min_fee * rmb_per_min / rmb_per_fee


def apply_min_fee(fee_items, rates: Optional[dict] = None) -> list:
    """Return fee_items list with 原币金额/人民币金额 corrected for minimum charge.
    rates: {currency: rmb_rate} dict for cross-currency conversion."""
    if rates is None:
        rates = {'RMB': 1.0, 'CNY': 1.0}
    result = []
    for item in fee_items:
        min_fee_raw = float(item.最低收费) if item.最低收费 else None
        yuan_orig = float(item.原币金额) if item.原币金额 else 0.0
        rmb_raw = float(item.人民币金额) if item.人民币金额 else 0.0
        fee_cur = item.币种 or 'RMB'
        min_cur = item.最低收费币种 or fee_cur
        # Convert min fee to same currency as the fee item
        min_fee = convert_min_fee(min_fee_raw, min_cur, fee_cur, rates) if min_fee_raw else None
        shi_ji_yuan = max(yuan_orig, min_fee) if min_fee else yuan_orig
        if min_fee and shi_ji_yuan > yuan_orig and yuan_orig > 0:
            shi_ji_rmb = round(rmb_raw * shi_ji_yuan / yuan_orig, 2)
        else:
            shi_ji_rmb = rmb_raw
        result.append({
            "费用ID":       item.费用ID,
            "费用类型":     item.费用类型,
            "单价":         float(item.单价) if item.单价 else 0,
            "单位":         item.单位,
            "数量":         float(item.数量) if item.数量 else 0,
            "最低收费":     min_fee_raw,
            "最低收费币种": item.最低收费币种,
            "币种":         fee_cur,
            "原币金额":     shi_ji_yuan,
            "人民币金额":   shi_ji_rmb,
            "备注":         item.备注,
            "参与核算":     item.参与核算 if item.参与核算 is not None else 1,
        })
    return result


def clean_goods_detail(goods: dict) -> dict:
    """Strip frontend-only/DB-generated keys and normalise column names for GoodsDetail."""
    for k in ['货物ID', '路线ID', '创建时间', '路线索引', '_index', '总货值']:
        goods.pop(k, None)
    # get_route_detail returns keys with unit suffixes; map them back to ORM attr names
    for old, new in [('重量(/kg)', '重量'), ('总重量(/kg)', '总重量')]:
        if old in goods:
            goods[new] = goods.pop(old)
    return goods


def clean_goods_total(goods: dict) -> dict:
    """Strip frontend-only/DB-generated keys and normalise column names for GoodsTotal."""
    for k in ['整单货物ID', '路线ID', '创建时间', '路线索引', '_index']:
        goods.pop(k, None)
    for old, new in [('实际重量(/kg)', '实际重量'), ('总体积(/cbm)', '总体积')]:
        if old in goods:
            goods[new] = goods.pop(old)
    return goods
