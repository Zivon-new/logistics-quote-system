"""
执行 migration_v3 的 PART 6.2、6.3、PART 7
（PART 6.1 已通过 Python 手动执行完毕，agents 表已有 17 条记录）
"""
import sys
sys.path.insert(0, 'D:/project_root/venv/Lib/site-packages')
import pymysql

conn = pymysql.connect(
    host='localhost', user='root', password='JHL181116',
    database='price_test_v2', charset='utf8mb4'
)
cur = conn.cursor()

# ── PART 6.2: 将 route_agents.代理商ID 关联到 agents 主表 ──────────────
try:
    sql = """
    UPDATE `route_agents` ra
    INNER JOIN `agents` a ON a.`代理商名称` = TRIM(ra.`代理商`)
    SET ra.`代理商ID` = a.`代理商ID`
    WHERE ra.`代理商` IS NOT NULL
    """
    cur.execute(sql)
    conn.commit()
    print(f"PART 6.2 成功，影响行数: {cur.rowcount}")
except Exception as e:
    print(f"PART 6.2 失败: {e}")

# ── PART 6.3: 从 route_agents.时效 提取数字天数 ────────────────────────
try:
    sql = """
    UPDATE `route_agents`
    SET `时效天数` = CASE
        WHEN `时效` REGEXP '[0-9]+-[0-9]+(天|工作日|days?)' THEN
            ROUND(
                (CAST(SUBSTRING_INDEX(`时效`, '-', 1) AS UNSIGNED) +
                 CAST(REGEXP_SUBSTR(SUBSTRING_INDEX(`时效`, '-', -1), '[0-9]+') AS UNSIGNED)) / 2
            )
        WHEN `时效` REGEXP '[0-9]+周' THEN
            CAST(REGEXP_SUBSTR(`时效`, '[0-9]+') AS UNSIGNED) * 7
        WHEN `时效` REGEXP '[0-9]+(天|days?)' THEN
            CAST(REGEXP_SUBSTR(`时效`, '[0-9]+') AS UNSIGNED)
        ELSE NULL
    END
    WHERE `时效` IS NOT NULL AND `时效天数` IS NULL
    """
    cur.execute(sql)
    conn.commit()
    print(f"PART 6.3 成功，影响行数: {cur.rowcount}")
except Exception as e:
    print(f"PART 6.3 失败: {e}")

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

# ── 验证结果 ──────────────────────────────────────────────────────────
print("\n=== 验证结果 ===")

cur.execute("SELECT COUNT(*) FROM agents")
print(f"agents 表记录数: {cur.fetchone()[0]}")

cur.execute("""
    SELECT COUNT(*),
           SUM(CASE WHEN `代理商ID` IS NOT NULL THEN 1 ELSE 0 END),
           ROUND(SUM(CASE WHEN `代理商ID` IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100, 1)
    FROM route_agents
""")
total, linked, rate = cur.fetchone()
print(f"route_agents 总数: {total}，已关联代理商ID: {linked}，关联率: {rate}%")

cur.execute("""
    SELECT COUNT(*),
           SUM(CASE WHEN `时效天数` IS NOT NULL THEN 1 ELSE 0 END),
           ROUND(SUM(CASE WHEN `时效天数` IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100, 1)
    FROM route_agents
    WHERE `时效` IS NOT NULL AND `时效` != ''
""")
total, extracted, rate = cur.fetchone()
print(f"有时效文本记录: {total}，已提取天数: {extracted}，提取率: {rate}%")

cur.execute("SELECT `代理商ID`, `代理商名称`, `主营运输方式` FROM agents LIMIT 10")
print("\n前10个代理商:")
for r in cur.fetchall():
    print(f"  {r}")

conn.close()
print("\n迁移完成！")
