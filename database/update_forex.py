"""
更新 forex_rate 汇率表
参考日期：2026-03-16
汇率：1单位外币 = N 人民币
"""
import sys
sys.path.insert(0, 'D:/project_root/venv/Lib/site-packages')
import pymysql

conn = pymysql.connect(
    host='localhost', user='root', password='JHL181116',
    database='price_test_v2', charset='utf8mb4'
)
cur = conn.cursor()

rates = [
    # 币种,   汇率(对人民币),  说明
    ('USD',  7.25,   '美元'),
    ('EUR',  7.90,   '欧元'),
    ('GBP',  9.20,   '英镑'),
    ('JPY',  0.0482, '日元'),
    ('HKD',  0.932,  '港币'),
    ('AUD',  4.55,   '澳大利亚元'),
    ('SGD',  5.38,   '新加坡元'),
    ('AED',  1.97,   '阿联酋迪拉姆'),
    ('SAR',  1.93,   '沙特里亚尔'),
    ('MYR',  1.62,   '马来西亚林吉特'),
    ('VND',  0.000285, '越南盾'),
    ('KRW',  0.0052, '韩元'),
    ('PHP',  0.125,  '菲律宾比索'),
    ('THB',  0.211,  '泰铢'),
    ('INR',  0.0843, '印度卢比'),
    ('CAD',  5.05,   '加拿大元'),
    ('CHF',  8.18,   '瑞士法郎'),
]

sql = """
INSERT INTO forex_rate (币种, 汇率, 更新时间)
VALUES (%s, %s, NOW())
ON DUPLICATE KEY UPDATE
    汇率 = VALUES(汇率),
    更新时间 = NOW()
"""

for code, rate, name in rates:
    cur.execute(sql, (code, rate))
    print(f"  {code} ({name}): {rate}")

conn.commit()

# 验证
cur.execute("SELECT 币种, 汇率, 更新时间 FROM forex_rate ORDER BY 币种")
rows = cur.fetchall()
print(f"\n汇率表现有 {len(rows)} 条记录：")
for r in rows:
    print(f"  {r[0]:<6} {float(r[1]):<12} {r[2]}")

conn.close()
print("\n更新完成！")
