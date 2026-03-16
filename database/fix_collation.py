"""
修复 PART 6.2 字符集排序规则冲突，并重新执行 PART 7
"""
import sys
sys.path.insert(0, 'D:/project_root/venv/Lib/site-packages')
import pymysql

conn = pymysql.connect(
    host='localhost', user='root', password='JHL181116',
    database='price_test_v2', charset='utf8mb4'
)
cur = conn.cursor()

# ── PART 6.2 修复版：用 COLLATE 统一排序规则 ──────────────────────────
try:
    sql = """
    UPDATE `route_agents` ra
    INNER JOIN `agents` a
        ON a.`代理商名称` COLLATE utf8mb4_0900_ai_ci = TRIM(ra.`代理商`)
    SET ra.`代理商ID` = a.`代理商ID`
    WHERE ra.`代理商` IS NOT NULL
    """
    cur.execute(sql)
    conn.commit()
    print(f"PART 6.2 成功，影响行数: {cur.rowcount}")
except Exception as e:
    print(f"PART 6.2 失败: {e}")

# ── PART 7: 更新 agents 主营运输方式 ──────────────────────────────────
try:
    sql = """
    UPDATE `agents` a
    INNER JOIN (
        SELECT
            `代理商ID`,
            `运输方式`,
            COUNT(*) AS cnt,
            ROW_NUMBER() OVER (PARTITION BY `代理商ID` ORDER BY COUNT(*) DESC) AS rn
        FROM `route_agents`
        WHERE `代理商ID` IS NOT NULL
          AND `运输方式` IS NOT NULL
          AND `运输方式` != ''
        GROUP BY `代理商ID`, `运输方式`
    ) top_mode ON top_mode.`代理商ID` = a.`代理商ID` AND top_mode.rn = 1
    SET a.`主营运输方式` = top_mode.`运输方式`
    """
    cur.execute(sql)
    conn.commit()
    print(f"PART 7 成功，影响行数: {cur.rowcount}")
except Exception as e:
    print(f"PART 7 失败: {e}")

# ── 最终验证 ──────────────────────────────────────────────────────────
print("\n=== 最终验证 ===")

cur.execute("""
    SELECT COUNT(*),
           SUM(CASE WHEN `代理商ID` IS NOT NULL THEN 1 ELSE 0 END),
           ROUND(SUM(CASE WHEN `代理商ID` IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100, 1)
    FROM route_agents
""")
total, linked, rate = cur.fetchone()
print(f"route_agents 总数: {total}，已关联代理商ID: {linked}，关联率: {rate}%")

cur.execute("SELECT `代理商ID`, `代理商名称`, `主营运输方式` FROM agents ORDER BY `代理商ID`")
print("\n所有代理商:")
for r in cur.fetchall():
    print(f"  {r}")

conn.close()
print("\n全部完成！")
