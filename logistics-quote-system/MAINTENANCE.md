# 系统运维说明

> 适用系统：国际物流报价系统
> 服务器：阿里云 ECS，IP `101.200.146.28`，Ubuntu 24.04
> 部署目录：`/opt/logistics`

---

## 一、系统组成

```
用户浏览器
    ↓ HTTPS（Nginx 反代）
Nginx（80端口对外）
    ↓ 内部转发
FastAPI 后端（127.0.0.1:8000，由 systemd 守护）
    ↓
MySQL 数据库（price_test_v2）
```

---

## 二、日常自动任务

系统配置了两个定时任务（crontab），无需人工干预自动运行。

### 数据库备份（每天凌晨3点）

- **做什么**：把完整数据库导出为 `.sql` 文件
- **存在哪**：
  - 本机：`/opt/logistics/logistics-quote-system/backend/backups/`（保留最近14份，约两周）
  - 异地：阿里云 OSS，bucket `cjnldhj`，路径 `backups/`（保留90天，由生命周期规则自动清理）
- **日志**：`/opt/logistics/logistics-quote-system/backend/logs/backup.log`
- **手动触发**：
  ```bash
  cd /opt/logistics/logistics-quote-system/backend
  venv/bin/python backup_database.py
  ```

### 监控告警（每5分钟）

- **检查什么**：
  1. HTTP 健康检查（`/health` 接口是否正常响应）
  2. systemd 服务状态（`logistics` 服务是否 active）
  3. 磁盘空间（剩余低于 20% 时告警）
  4. 错误日志（`error.log` 有新增 ERROR/CRITICAL 条目时告警）
- **发现问题时**：自动发邮件到 `sunzhiweiblcu@163.com`
- **日志**：`/opt/logistics/logistics-quote-system/backend/logs/monitor.log`
- **手动触发**：
  ```bash
  cd /opt/logistics/logistics-quote-system/backend
  venv/bin/python monitor.py
  ```

### 查看当前定时任务

```bash
crontab -l
```

---

## 三、服务管理

后端服务由 systemd 守护，崩溃后会自动在3秒内重启。

| 操作 | 命令 |
|------|------|
| 查看服务状态 | `systemctl status logistics` |
| 重启服务 | `systemctl restart logistics` |
| 查看服务日志 | `journalctl -u logistics -n 50` |

---

## 四、代码更新流程

每次改完代码、推送到 GitHub 后，SSH 登录服务器执行：

```bash
cd /opt/logistics && git pull origin main && systemctl restart logistics
```

- 只改前端：`git pull` 后不需要重启（Nginx 直接服务静态文件）
- 只改后端：需要 `systemctl restart logistics`
- 改了 `.env` 配置：需要 `systemctl restart logistics`

> **注意**：`.env` 文件不会随 git pull 同步，服务器上的 `.env` 需要手动修改。

---

## 五、数据库恢复（出现数据丢失时）

### 第一步：找到备份文件

```bash
# 查看本地备份
ls -t /opt/logistics/logistics-quote-system/backend/backups/

# 或者去阿里云 OSS 控制台 → bucket cjnldhj → backups/ 文件夹下载
```

### 第二步：恢复数据库

```bash
cd /opt/logistics/logistics-quote-system/backend

# 把备份文件导入生产库（会覆盖当前数据，谨慎操作）
mysql -u root -p'JHL181116' price_test_v2 < backups/price_test_v2_日期时间.sql
```

### 第三步：重启服务

```bash
systemctl restart logistics
```

> **恢复演练记录**：2026-06-09 验证过，19张表、89条路线数据完整恢复。

---

## 六、收到告警邮件怎么处理

### 邮件标题：【物流系统告警】

**[健康检查失败]** — 后端服务没有响应
```bash
systemctl status logistics     # 查看服务状态
systemctl restart logistics    # 尝试重启
journalctl -u logistics -n 50  # 查看错误日志
```

**[服务异常]** — systemd 服务不是 active 状态
```bash
systemctl restart logistics
journalctl -u logistics -n 50
```

**[磁盘告警]** — 磁盘剩余低于 20%
```bash
df -h                          # 查看磁盘使用情况
du -sh /opt/logistics/logistics-quote-system/backend/backups/  # 备份占用
# 手动删除一些旧备份，或者扩容磁盘
```

**[错误日志]** — 应用程序出现 ERROR
```bash
tail -100 /opt/logistics/logistics-quote-system/backend/logs/error.log
# 查看具体错误内容，判断是否影响正常使用
# 大多数 ERROR 是单次请求失败，不影响整体服务
```

---

## 七、服务器关键路径速查

| 内容 | 路径 |
|------|------|
| 项目根目录 | `/opt/logistics/logistics-quote-system/` |
| 后端代码 | `/opt/logistics/logistics-quote-system/backend/` |
| 环境变量配置 | `/opt/logistics/logistics-quote-system/backend/.env` |
| 数据库备份 | `/opt/logistics/logistics-quote-system/backend/backups/` |
| 应用错误日志 | `/opt/logistics/logistics-quote-system/backend/logs/error.log` |
| 监控运行日志 | `/opt/logistics/logistics-quote-system/backend/logs/monitor.log` |
| 备份运行日志 | `/opt/logistics/logistics-quote-system/backend/logs/backup.log` |
| systemd 服务文件 | `/etc/systemd/system/logistics.service` |
| Nginx 配置 | `/etc/nginx/` |
| 启动脚本 | `/opt/logistics/start.sh` |

---

## 八、账号与密钥

> 以下信息不要外传，不要提交到 git。

| 项目 | 位置 |
|------|------|
| 数据库密码 | 服务器 `.env` → `DB_PASSWORD` |
| JWT 签名密钥 | 服务器 `.env` → `SECRET_KEY` |
| 163 邮箱 SMTP 授权码 | 服务器 `.env` → `SMTP_AUTH_CODE` |
| 阿里云 OSS AccessKey | 服务器 `.env` → `OSS_ACCESS_KEY_ID` / `OSS_ACCESS_KEY_SECRET` |
| 智谱 AI API Key | 服务器 `.env` → `ZHIPU_API_KEY` |
