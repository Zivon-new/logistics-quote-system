# app/services/forex_scraper.py
"""
汇率自动同步服务
数据源：https://open.er-api.com/v6/latest/CNY（免费，无需 API Key）
返回"1 CNY = X 外币"，取倒数得"1 外币 = ? CNY"
"""
import logging
import requests
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

TARGET_CURRENCIES = ['USD', 'EUR', 'GBP', 'AUD', 'CAD', 'SGD', 'JPY', 'MYR', 'HKD']
FOREX_API_URL = "https://open.er-api.com/v6/latest/CNY"
REQUEST_TIMEOUT = 15


def fetch_forex_rates() -> dict:
    """从 ExchangeRate-API 获取最新汇率，返回 {币种: CNY汇率} 字典"""
    resp = requests.get(FOREX_API_URL, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    if data.get("result") != "success":
        raise ValueError(f"API 返回异常：{data.get('error-type', '未知错误')}")

    raw_rates = data.get("rates", {})
    rates = {}
    for currency in TARGET_CURRENCIES:
        rate_vs_cny = raw_rates.get(currency)
        if rate_vs_cny and rate_vs_cny > 0:
            rates[currency] = round(1.0 / rate_vs_cny, 6)

    if not rates:
        raise ValueError("未能从 API 解析到任何有效汇率")

    return rates


def update_forex_rates(db: Session) -> dict:
    """拉取最新汇率并写入数据库，返回本次更新的汇率字典"""
    rates = fetch_forex_rates()
    today = date.today()

    for currency, rate in rates.items():
        # 更新最新汇率
        db.execute(
            text("""
                INSERT INTO forex_rate (`币种`, `汇率`, `参考日期`)
                VALUES (:c, :r, :d)
                ON DUPLICATE KEY UPDATE `汇率` = :r, `参考日期` = :d
            """),
            {"c": currency, "r": rate, "d": today}
        )
        # 写入历史记录（幂等）
        db.execute(
            text("""
                INSERT IGNORE INTO forex_rate_history (`币种`, `汇率`, `参考日期`)
                VALUES (:c, :r, :d)
            """),
            {"c": currency, "r": rate, "d": today}
        )
    db.commit()

    logger.info("汇率同步完成 (%s)：%s", today, rates)
    return rates


def backfill_forex_history(db: Session, days: int = 30) -> int:
    """从 Frankfurter API 回填历史汇率（每日汇率快照）"""
    end_date = date.today() - timedelta(days=1)   # 昨天为止（今天用 update_forex_rates 写）
    start_date = end_date - timedelta(days=days)
    currencies = ",".join(TARGET_CURRENCIES)

    url = f"https://api.frankfurter.app/{start_date}..{end_date}"
    resp = requests.get(url, params={"from": "CNY", "to": currencies}, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    rates_by_date = data.get("rates", {})
    count = 0
    for date_str, daily_rates in rates_by_date.items():
        ref_date = date.fromisoformat(date_str)
        for currency, rate_vs_cny in daily_rates.items():
            if rate_vs_cny and rate_vs_cny > 0:
                cny_rate = round(1.0 / rate_vs_cny, 6)
                db.execute(
                    text("""
                        INSERT IGNORE INTO forex_rate_history (`币种`, `汇率`, `参考日期`)
                        VALUES (:c, :r, :d)
                    """),
                    {"c": currency, "r": cny_rate, "d": ref_date}
                )
                count += 1
    db.commit()
    logger.info("汇率历史回填完成：写入 %d 条，区间 %s ~ %s", count, start_date, end_date)
    return count
