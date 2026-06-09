# backend/backup_database.py
"""
数据库自动备份脚本

用法:
    python backup_database.py

建议通过 crontab 定时执行，例如每天凌晨3点：
    0 3 * * * cd /opt/logistics/logistics-quote-system/backend && /path/to/venv/bin/python backup_database.py >> logs/backup.log 2>&1

备份策略：
- mysqldump 导出完整数据库（结构 + 数据），--single-transaction 保证一致性快照且不锁表
- 输出到 backups/ 目录，文件名含时间戳
- 仅保留最近 RETENTION_COUNT 份，自动清理更早的备份

恢复方式（出现数据丢失/损坏时）：
    mysql -u <user> -p price_test_v2 < backups/price_test_v2_20260101_030000.sql
"""
import os
import subprocess
import sys
import io
import tempfile
from datetime import datetime
from pathlib import Path

from app.config import settings

# Windows 控制台默认 GBK 编码，无法打印 ✓/✗ 等符号，强制以 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BACKUP_DIR = Path(__file__).parent / "backups"
RETENTION_COUNT = 14  # 保留最近14份（按每日一次计算，覆盖两周）


def backup_database():
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"{settings.DB_NAME}_{timestamp}.sql"

    # 通过临时凭据文件传密码，避免密码出现在进程列表（ps aux 可见）中
    fd, cnf_path = tempfile.mkstemp(suffix=".cnf")
    try:
        with os.fdopen(fd, "w") as cnf:
            cnf.write(
                "[client]\n"
                f"host={settings.DB_HOST}\n"
                f"port={settings.DB_PORT}\n"
                f"user={settings.DB_USER}\n"
                f"password={settings.DB_PASSWORD}\n"
            )
        os.chmod(cnf_path, 0o600)

        dump_cmd = [
            "mysqldump",
            f"--defaults-extra-file={cnf_path}",
            "--single-transaction",
            "--routines",
            "--triggers",
            settings.DB_NAME,
        ]
        with open(backup_file, "wb") as f:
            result = subprocess.run(dump_cmd, stdout=f, stderr=subprocess.PIPE)
    finally:
        os.unlink(cnf_path)

    if result.returncode != 0:
        backup_file.unlink(missing_ok=True)
        print(f"✗ 备份失败: {result.stderr.decode('utf-8', errors='replace')}")
        sys.exit(1)

    size_mb = backup_file.stat().st_size / 1024 / 1024
    print(f"✓ 备份完成: {backup_file.name} ({size_mb:.2f} MB)")
    cleanup_old_backups()
    upload_to_oss(backup_file)


def upload_to_oss(backup_file: Path):
    if not settings.OSS_ACCESS_KEY_ID or not settings.OSS_ACCESS_KEY_SECRET:
        print("  OSS 未配置，跳过异地备份")
        return
    try:
        import oss2
        auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET)
        oss_key = f"backups/{backup_file.name}"
        bucket.put_object_from_file(oss_key, str(backup_file))
        print(f"  ✓ 已上传至 OSS: {oss_key}")
    except Exception as e:
        print(f"  ✗ OSS 上传失败（本地备份仍有效）: {e}")


def cleanup_old_backups():
    backups = sorted(BACKUP_DIR.glob(f"{settings.DB_NAME}_*.sql"), key=lambda p: p.name)
    for old in backups[:-RETENTION_COUNT]:
        old.unlink()
        print(f"  已清理旧备份: {old.name}")


if __name__ == "__main__":
    backup_database()
