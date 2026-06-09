# backend/monitor.py
"""
监控告警脚本

检测范围：
  1. HTTP 健康检查（GET /health 接口）
  2. systemd 服务状态（Linux 有效，Windows 自动跳过）
  3. 错误日志扫描（logs/error.log 中新增的 ERROR/CRITICAL 条目）

发现任何问题时发邮件到 ALERT_EMAIL。

crontab 建议（每5分钟执行一次）：
    */5 * * * * cd /opt/logistics/logistics-quote-system/backend && /path/to/venv/bin/python monitor.py >> logs/monitor.log 2>&1

配置项（在 .env 中设置）：
    SMTP_AUTH_CODE=你的163邮箱授权码
    SERVICE_URL=http://localhost:8000   （可选，默认值即可）
    SYSTEMD_SERVICE=logistics           （可选，默认值即可）
    ALERT_EMAIL=sunzhiweiblcu@163.com   （可选，默认值即可）
"""
import io
import json
import smtplib
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from app.config import settings

SMTP_HOST = "smtp.163.com"
SMTP_PORT = 465

LOG_FILE = Path(__file__).parent / "logs" / "error.log"
STATE_FILE = Path(__file__).parent / "logs" / ".monitor_state.json"

MAX_ERROR_LINES_IN_ALERT = 20


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"log_offset": 0}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state), encoding="utf-8")


def check_http_health() -> tuple[bool, str]:
    url = settings.SERVICE_URL.rstrip("/") + "/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            body = json.loads(resp.read().decode())
            if body.get("status") == "healthy":
                return True, "OK"
            return False, f"接口返回异常: {body}"
    except urllib.error.URLError as e:
        return False, f"无法连接到服务 ({url}): {e.reason}"
    except Exception as e:
        return False, f"HTTP 请求失败: {e}"


def check_systemd_service() -> tuple[bool, str]:
    if sys.platform == "win32":
        return True, "Windows 跳过 systemd 检查"
    try:
        result = subprocess.run(
            ["systemctl", "is-active", settings.SYSTEMD_SERVICE],
            capture_output=True,
            text=True,
            timeout=5,
        )
        status = result.stdout.strip()
        if status == "active":
            return True, "active"
        return False, f"服务状态异常: {status!r}（预期 active）"
    except FileNotFoundError:
        return False, "systemctl 命令不存在，无法检查服务状态"
    except subprocess.TimeoutExpired:
        return False, "systemctl 检查超时"
    except Exception as e:
        return False, f"systemctl 检查失败: {e}"


def scan_new_errors(state: dict) -> tuple[list[str], int]:
    if not LOG_FILE.exists():
        return [], state.get("log_offset", 0)

    current_size = LOG_FILE.stat().st_size
    last_offset = state.get("log_offset", 0)

    # 文件被 rotate 缩小时从头读
    if current_size < last_offset:
        last_offset = 0

    new_errors: list[str] = []
    with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
        f.seek(last_offset)
        for line in f:
            if " - ERROR - " in line or " - CRITICAL - " in line:
                new_errors.append(line.rstrip())

    return new_errors, current_size


def send_alert(subject: str, body: str):
    if not settings.SMTP_AUTH_CODE:
        print("SMTP_AUTH_CODE 未配置，跳过邮件发送")
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = settings.ALERT_EMAIL
    msg.set_content(body, charset="utf-8")
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.login(settings.SMTP_USER, settings.SMTP_AUTH_CODE)
        smtp.send_message(msg)


def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    state = load_state()
    issues: list[str] = []

    http_ok, http_msg = check_http_health()
    if not http_ok:
        issues.append(f"[健康检查失败] {http_msg}")

    svc_ok, svc_msg = check_systemd_service()
    if not svc_ok:
        issues.append(f"[服务异常] {svc_msg}")

    new_errors, new_offset = scan_new_errors(state)
    if new_errors:
        issues.append(f"[错误日志] 发现 {len(new_errors)} 条新错误（最多展示 {MAX_ERROR_LINES_IN_ALERT} 条）:")
        issues.extend(f"  {e}" for e in new_errors[:MAX_ERROR_LINES_IN_ALERT])
        if len(new_errors) > MAX_ERROR_LINES_IN_ALERT:
            issues.append(f"  ... 还有 {len(new_errors) - MAX_ERROR_LINES_IN_ALERT} 条，请查看 logs/error.log")

    state["log_offset"] = new_offset
    save_state(state)

    if issues:
        subject = f"【物流系统告警】{now}"
        body = "\n".join([
            f"检测时间: {now}",
            f"服务地址: {settings.SERVICE_URL}",
            "",
            "── 告警详情 ──",
            "",
        ] + issues)
        try:
            send_alert(subject, body)
            print(f"[{now}] 告警邮件已发送，共 {len(issues)} 条问题")
        except Exception as e:
            print(f"[{now}] 邮件发送失败: {e}")
        sys.exit(1)
    else:
        http_label = f"HTTP {http_msg}"
        svc_label = svc_msg if sys.platform != "win32" else "systemd跳过"
        err_label = f"日志无新增错误" if not new_errors else f"日志{len(new_errors)}条错误"
        print(f"[{now}] 正常 — {http_label} | 服务:{svc_label} | {err_label}")


if __name__ == "__main__":
    main()
