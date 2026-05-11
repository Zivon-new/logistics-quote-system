# app/services/fuel_scraper.py
"""
原油价格同步服务
数据源：AKShare（内部调用新浪财经期货接口，支持完整历史+最新数据）
合约：SC0（上期所原油连续合约，人民币/桶）
列：date, open, high, low, close, volume, hold, settle
"""
import logging
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


def _fetch_sc_kline(days: int) -> list[dict]:
    """用 AKShare 拉取 SC0 日K线，返回最近 days 条 [{date, close}]"""
    import akshare as ak

    df = ak.futures_zh_daily_sina(symbol="SC0")
    if df is None or df.empty:
        raise ValueError("AKShare 未返回 SC0 数据")

    # 确保 date 列是 date 类型
    df["date"] = df["date"].apply(
        lambda x: x.date() if hasattr(x, "date") else date.fromisoformat(str(x))
    )
    df = df.sort_values("date")

    records = [
        {"date": row["date"], "close": float(row["close"])}
        for _, row in df.iterrows()
        if row["close"] > 0
    ]

    logger.info("SC0 数据区间：%s ~ %s，取最近 %d 条",
                records[0]["date"], records[-1]["date"], days)
    return records[-days:]


def update_fuel_prices(db: Session, days: int = 7) -> int:
    """同步最近 days 天的 SC0 收盘价，返回写入条数"""
    records = _fetch_sc_kline(days)
    if not records:
        logger.warning("燃油价格同步：本次未获取到任何交易数据")
        return 0

    count = 0
    for rec in records:
        db.execute(
            text("""
                INSERT INTO fuel_price_history (`收盘价`, `交易日期`)
                VALUES (:price, :dt)
                ON DUPLICATE KEY UPDATE `收盘价` = :price
            """),
            {"price": rec["close"], "dt": rec["date"]}
        )
        count += 1
    db.commit()
    logger.info("燃油价格同步完成：写入 %d 条", count)
    return count


def backfill_fuel_prices(db: Session, days: int = 30) -> int:
    logger.info("回填 %d 天 SC0 原油历史价格...", days)
    return update_fuel_prices(db, days=days)
