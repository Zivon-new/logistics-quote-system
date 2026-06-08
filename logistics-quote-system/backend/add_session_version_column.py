# backend/add_session_version_column.py
"""
为 users 表新增 session_version 列（单设备登录限制所需）

运行方式:
python add_session_version_column.py

幂等：列已存在时自动跳过，可重复执行。
"""
import sys
import io
from sqlalchemy import text
from app.database import engine
from app.config import settings

# Windows 控制台默认 GBK 编码，无法打印 ✓/⚠ 等符号，强制以 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def add_session_version_column():
    with engine.connect() as conn:
        exists = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = :db AND table_name = 'users' AND column_name = 'session_version'"
            ),
            {"db": settings.DB_NAME}
        ).scalar()

        if exists:
            print("⚠ session_version 列已存在，跳过")
            return

        conn.execute(text(
            "ALTER TABLE users ADD COLUMN session_version INT NOT NULL DEFAULT 0"
        ))
        conn.commit()
        print("✓ 已为 users 表添加 session_version 列")


if __name__ == "__main__":
    add_session_version_column()
