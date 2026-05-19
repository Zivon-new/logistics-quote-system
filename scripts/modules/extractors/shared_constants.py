# scripts/modules/extractors/shared_constants.py
"""
提取器公共常量 — 唯一来源，所有提取器从此导入，禁止在各提取器内重复定义。
"""

# 货币符号 / 代码 → 标准币种代码
CURRENCY_MAP: dict = {
    'CNY': 'RMB', 'RMB': 'RMB', '￥': 'RMB', '¥': 'RMB', '元': 'RMB',
    'USD': 'USD', '$': 'USD',
    'EUR': 'EUR', '€': 'EUR',
    'GBP': 'GBP', '£': 'GBP',
    'MYR': 'MYR', 'RM': 'MYR',
    'SGD': 'SGD',
    'HKD': 'HKD',
    'JPY': 'JPY',
    'AUD': 'AUD',
    'CAD': 'CAD',
}

# 费用锚点关键词 — 唯一来源。
# agent_extractor_v2 和 fee_extractor 均从此处导入（fee_extractor 经由 agent_extractor_v2 转发）。
FEE_ANCHORS: list = ['小计', '合计', '总计', '海运费', '费用明细', '运费']
