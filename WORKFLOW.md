# 国际物流报价系统 — 开发工作流手册

## 项目概览

**国际物流报价系统**，前后端分离架构：

| 层 | 技术栈 | 启动端口 |
|---|---|---|
| 前端 | Vue 3 + Vite + Element Plus | 5173 |
| 后端 | FastAPI + SQLAlchemy + MySQL | 8000 |
| 数据库 | MySQL (`price_test_v2`) | 3306 |

核心功能模块：

| 模块 | 入口文件 | 说明 |
|---|---|---|
| 路线录入 | `NewRoute/` | 手动录入（4步骤）/ Excel 导入 |
| 路线管理 | `RouteManage.vue` | 查看、编辑、删除已录入路线 |
| 报价查询 | `QuoteSearch.vue` | 多维度搜索历史报价 |
| 智能推荐 | `Recommend.vue` | 基于规则打分的代理商推荐 |
| 价格分析 | `Analytics.vue` | ECharts 趋势图 / 统计看板 |
| 港口地图 | `PortMap.vue` | Leaflet + OpenStreetMap |
| 航线风险 | `RiskProfile.vue` | LPI 风险雷达图 |
| 企业背调 | `AgentCheck.vue` | GLM-4 生成背调报告 |

---

## 一、本地启动

### 1. 启动后端

```powershell
cd logistics-quote-system/backend

# 首次：创建虚拟环境并安装依赖
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# 复制环境变量（首次）
copy .env.example .env   # 按需修改 DB 密码等

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

后端启动后可访问 API 文档：`http://localhost:8000/docs`

### 2. 启动前端

```powershell
cd logistics-quote-system/frontend
npm install          # 首次
npm run dev          # 开发服务器 http://localhost:5173
```

### 3. 数据库初始化（首次）

```powershell
cd logistics-quote-system/backend
python init_db.py
```

如有新的迁移脚本（`database/` 目录），手动执行对应 `.sql` 文件。

---

## 二、目录结构速查

```
project_root/
├── logistics-quote-system/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/v1/          # 所有 API 路由
│   │   │   │   ├── routes.py    # 路线 CRUD
│   │   │   │   ├── attachments.py
│   │   │   │   ├── analytics.py
│   │   │   │   └── ...
│   │   │   ├── models/          # SQLAlchemy 模型
│   │   │   ├── schemas/         # Pydantic 校验
│   │   │   └── core/            # 鉴权、依赖注入
│   │   ├── uploads/             # 附件文件（不入 git）
│   │   └── requirements.txt
│   └── frontend/
│       └── src/
│           ├── api/             # 前端 API 封装（axios）
│           ├── components/      # 公共组件（AttachmentPanel 等）
│           ├── views/
│           │   ├── NewRoute/    # 录入流程（Step1-4）
│           │   └── ...
│           └── stores/          # Pinia 状态管理
├── database/                    # SQL 迁移脚本
├── CLAUDE.md                    # AI 编码规范
└── WORKFLOW.md                  # 本文档
```

---

## 三、开发任务与技能对照

技能分两套，共存互补：
- **gstack**（`/investigate`、`/qa`、`/ship` 等）— 侧重浏览器测试、PR 流程、代码审查
- **mattpocock**（`/diagnose`、`/grill-with-docs`、`/improve-codebase-architecture`）— 侧重调试纪律、需求对齐、架构深度

---

### 修 Bug

**简单 Bug / 逻辑错误** → 用 `/investigate`（gstack）：

```
/investigate  [描述现象，如：货值输入 500.06 时 0 录不进去]
```

`/investigate` 走完「收集症状 → 根因假设 → 验证 → 修复 → 回归测试」完整流程。

**复杂 Bug / 性能问题** → 用 `/diagnose`（mattpocock）：

```
/diagnose  [描述现象]
```

`/diagnose` 的核心理念是**先建可复现的反馈回路**，再假设、验证、修复。流程：
1. 建反馈回路（失败测试 / curl 脚本 / 浏览器脚本）
2. 复现确认
3. 生成 3-5 个可证伪假设
4. 精准打点验证
5. 修复 + 回归测试
6. 清理 + 记录根因到 commit

> **选哪个？** 看 Bug 是否好复现：能快速复现 → `/investigate`；难复现/性能回归/需要最小化场景 → `/diagnose`

---

### 功能开发

**第一步：需求拍板**

```
/grill-with-docs  [描述你想加的功能，如：加一个代理商黑名单功能]
```

mattpocock 的 `/grill-with-docs` 会：
- 逐一拷问你的方案，暴露模糊点
- 参照 `CONTEXT.md` 里的领域词汇，纠正术语不一致
- 把拍板的决定同步写入 `CONTEXT.md` 和 `docs/adr/`

如果需求比较简单，也可以用轻量版：

```
/office-hours  [描述功能]
```

**第二步：架构评审**

```
/plan-eng-review  [让 AI 做架构评审，锁定实现方案]
```

**第三步：代码审查**

```
/review  # 提交前的最后一关
```

---

### 提交 & PR

```
/ship  # 版本号 → CHANGELOG → commit → push → PR，一键完成
```

---

### UI / 前端验证

```
/qa   [描述要测试的功能，如：测试手动录入路线的 4 步流程]
```

`/qa` 跑完主路径和边界情况，自动修复发现的 bug。只看报告不改代码用 `/qa-only`。

---

### 定期维护

**每周**：

```
/retro      # 工程复盘：commit 统计、代码质量趋势
/health     # 代码健康仪表盘：类型检查 + lint + 测试覆盖率
```

**每隔几周**（代码乱了就跑）：

```
/improve-codebase-architecture
```

mattpocock 的架构优化技能，扫描"浅模块"（接口复杂度 ≈ 实现复杂度，没有收益）并提出"深化"方案。做完后产出可以拿去 `/plan-eng-review` 评审。

**安全**（有安全相关改动时）：

```
/cso        # 安全审计：密钥泄漏、OWASP Top 10、依赖漏洞
```

---

## 四、录入流程（Step1 ~ Step4）说明

路线手动录入分 4 步，代码在 `frontend/src/views/NewRoute/`：

```
Step1RouteInfo.vue   →  起始/目的地、日期、重量、货值
Step2GoodsInfo.vue   →  货物明细（或整单货物）
Step3AgentsForm.vue  →  代理商信息、费用明细、汇总（含税率/汇损）
Step4Preview.vue     →  预览确认后提交
```

**提交后**：`savedRouteId` 解锁 Step3 各代理商卡片底部的附件上传区；新建路线出现"完成"按钮，编辑模式下立即可用。

### 汇率刷新

Step3 顶部有"刷新汇率"按钮，触发 `POST /v1/routes/refresh_forex`，从 ExchangeRate-API 拉取最新数据。

同步币种（共 9 种）：`USD / EUR / GBP / AUD / CAD / SGD / HKD / JPY / MYR`

定时任务：每天 09:30 自动同步，写入 `forex_rate`（最新）和 `forex_rate_history`（历史快照）。历史数据可通过 `POST /v1/analytics/forex-backfill` 手动回填（Frankfurter API）。

### 税率说明

税率字段输入**百分比**（如输入 `9` 代表 9%，`9.15` 代表 9.15%），内部存储为小数（0.09），下游计算和显示不受影响。

多货物税率模式：Step3 切换到「多货物税率」后，每行按货物名称 + 货值 + 综合税率% 分别计算，汇总税金自动写入 `summary.进口税率原文`（JSON）。

---

## 五、常见开发场景

### 场景 A：加一个新的费用字段

1. 后端：`app/models/` 加字段 → `app/schemas/` 加 Pydantic 字段 → `app/api/v1/routes.py` 的 INSERT/SELECT 补字段
2. 前端：`Step3AgentsForm.vue` 表格加列 → `Step4Preview.vue` 预览加行 → `RouteManage.vue` 详情加展示

运行 `/review` 确认无遗漏。

### 场景 B：前端页面出现计算错误

1. 先跑 `/investigate [描述现象]`，让它找根因
2. 典型坑：`Step4Preview.vue` 的计算函数不读 `手动` 标志 → 已修复；后续改动如有类似函数，记得加守卫
3. `是否赔付` 的值可能是整数 `1` 或字符串 `'1'`，判断统一用 `isCompensation(v)` 辅助函数，不要用 `=== '1'` 硬比较

### 场景 C：数据库加新字段

```powershell
# 在 database/ 目录写 SQL 迁移
# 文件命名：add_<field>_to_<table>.sql

# 本机执行（后端项目根目录）
python -c "
import sys; sys.path.insert(0, '.')
from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE xxx ADD COLUMN yyy ...'))
    conn.commit()
print('done')
"
```

### 场景 D：调试附件上传问题

- 上传文件存储路径：`backend/uploads/<route_id>/<uuid>.<ext>`
- 数据库表：`route_attachments`（含 `agent_index` 字段区分各代理商）
- 鉴权：所有附件 API 需 Bearer Token，前端通过 `authFetch` 统一处理

### 场景 E：编辑路线时货值币种不生效

`PUT /v1/routes/{id}` 的 `field_mapping` 已包含 `货值币种`，前端提交时 `route` 对象里带上 `货值币种` 字段即可。

### 场景 F：Excel 导入调试

- 导入入口：`POST /v1/routes/import/upload`（需登录）
- 上传的临时文件在处理完成后会自动删除（`finally` 块），不会积累在磁盘
- 文件名用 UUID 前缀避免冲突：`{uuid}_{原始文件名}`
- 解析器日志级别为 `DEBUG`，生产环境默认不输出；如需调试，调低日志级别即可

---

## 六、近期重要修复记录（2026-05-14）

| 位置 | 问题 | 状态 |
|---|---|---|
| `analytics.py` | `forex-history` 接口 `currencies` 参数 SQL 注入 | ✅ 白名单过滤 |
| `routes.py` | `/import/upload` 无登录鉴权 | ✅ 补加 `get_current_user` |
| `forex_scraper.py` | AUD/GBP/CAD 不在同步列表，永用默认值 | ✅ 已加入 `TARGET_CURRENCIES` |
| `routes.py` | `update_route` 无法保存 `货值币种` 变更 | ✅ 补入 `field_mapping` |
| `routes.py` | `get_routes` N+1 查询 | ✅ 改为批量加载 |
| `routes.py` | 上传临时文件不清理 | ✅ `finally` 块删除 |
| `main.py` | `_scheduled_scrape` 缺少异常捕获 | ✅ 补 `except` |
| `RouteManage.vue` | 货值列硬编码 `¥` | ✅ 改为显示货值币种 |
| `Step4Preview.vue` | `是否赔付` 用 `=== '1'` 硬比较 | ✅ 改用 `isCompensation()` |
| `QuoteSearch.vue` | "导出Excel" 按钮无功能 | ✅ 实现 CSV 导出 |
| `excel_import_service.py` | `print()` 调试语句污染 stdout | ✅ 改为 `logger.debug` |

---

## 七、环境变量速查

| 变量 | 说明 | 示例 |
|---|---|---|
| `DB_HOST` | 数据库地址 | `localhost` |
| `DB_NAME` | 数据库名 | `price_test_v2` |
| `SECRET_KEY` | JWT 签名密钥 | 生产环境必须修改 |
| `CORS_ORIGINS` | 允许的前端来源 | `http://localhost:5173` |

`.env` 不入 git；敏感字段参考 `.env.example`。

---

## 八、快速命令参考

### gstack 技能（浏览器测试 / PR 流程 / 审查）

| 任务 | 命令 |
|---|---|
| 修 Bug（逻辑/简单） | `/investigate` |
| 功能需求（轻量拍板） | `/office-hours` |
| 架构评审 | `/plan-eng-review` |
| 代码审查 | `/review` |
| 提交 PR | `/ship` |
| 浏览器测试 + 修 bug | `/qa` |
| 浏览器测试（纯报告） | `/qa-only` |
| 周复盘 | `/retro` |
| 代码质量 | `/health` |
| 安全审计 | `/cso` |
| 保存进度 | `/context-save` |
| 恢复进度 | `/context-restore` |

### mattpocock 技能（调试纪律 / 需求对齐 / 架构深度）

| 任务 | 命令 |
|---|---|
| 修 Bug（复杂/难复现） | `/diagnose` |
| 功能需求（深度拍板 + 文档） | `/grill-with-docs` |
| 架构深化（每隔几周跑一次） | `/improve-codebase-architecture` |

### 选哪个？

| 场景 | 推荐 |
|---|---|
| Bug 能快速复现 | `/investigate` |
| Bug 难复现 / 性能 / 需最小化场景 | `/diagnose` |
| 快速确认需求 | `/office-hours` |
| 新功能涉及领域术语/架构决策 | `/grill-with-docs` |
| 代码跑了几周开始乱 | `/improve-codebase-architecture` |
