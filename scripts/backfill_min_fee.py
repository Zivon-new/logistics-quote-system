"""
一次性迁移：从 fee_items.备注 中解析最低收费，回填到 最低收费 / 最低收费币种 字段。
只处理 最低收费 IS NULL 且 备注 含 min/MIN/最低 关键词的记录。
"""
import re
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../logistics-quote-system/backend')

from app.database import SessionLocal
from app.models.fee import FeeItem

MIN_FEE_RE = re.compile(r'(?:min|MIN|最低)\s*([A-Z]{2,4})\s*(\d+(?:\.\d+)?)', re.IGNORECASE)

db = SessionLocal()
updated = 0
skipped = 0

items = db.query(FeeItem).filter(FeeItem.最低收费 == None).all()
for item in items:
    note = item.备注 or ''
    m = MIN_FEE_RE.search(note)
    if not m:
        skipped += 1
        continue
    currency = m.group(1).upper()
    amount = float(m.group(2))
    item.最低收费 = amount
    item.最低收费币种 = currency
    updated += 1
    print(f"  费用ID={item.费用ID} 备注={note!r} → 最低收费={amount} {currency}")

db.commit()
db.close()
print(f"\n完成：更新 {updated} 条，跳过（无 min 信息）{skipped} 条")
