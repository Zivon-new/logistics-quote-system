# CLAUDE.md（中文版）

本文件为 Claude Code（claude.ai/code）在此代码仓库中工作时提供指导说明。

## 项目概述

**国际物流报价查询系统** — 一个用于管理和查询运输报价的全栈企业级 Web 应用。后端已 100% 完成，前端仍在积极开发中。

## 常用命令

### 后端（FastAPI）
```bash
cd logistics-quote-system/backend

# 安装依赖
pip install -r requirements.txt

# 初始化数据库（只需运行一次）
python init_db.py

# 启动开发服务器（API 文档地址：http://localhost:8000/docs）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端（Vue 3 + Vite）
```bash
cd logistics-quote-system/frontend

npm install
npm run dev      # 访问地址：http://localhost:5173
npm run build
npm run preview
```

### 数据处理脚本
```bash
# 运行提取流水线的集成测试
python test_new_architecture_with_llm.py

# 将 Excel 文件处理为 JSON
python scripts/excel_reader.py
```

## 系统架构

### 技术栈
- **后端**：Python 3.11+、FastAPI、SQLAlchemy 2.0、PyMySQL → MySQL 8.0（数据库：`price_test_v2`）
- **前端**：Vue 3、Vite、Pinia、Element Plus、Axios
- **数据提取**：openpyxl/pandas + 智谱 ChatGLM-4 大模型兜底

### 后端目录结构（`logistics-quote-system/backend/app/`）
- `main.py` — FastAPI 应用入口 + 全局异常处理器
- `database.py` — SQLAlchemy 引擎与会话管理
- `config.py` — 数据库凭据、JWT 密钥、CORS 来源配置（当前为硬编码，生产环境请使用 .env）
- `api/v1/` — 路由处理器：`auth.py`、`quotes.py`、`routes.py`
- `models/` — ORM 模型：`route.py`（Route、RouteAgent）、`fee.py`、`goods.py`、`user.py`
- `schemas/` — Pydantic 请求/响应模型定义
- `crud/` — 数据库访问层
- `core/security.py` — JWT 鉴权（token 有效期 24 小时）、基于角色的权限控制（管理员/普通用户）

### 数据模型关系
```
Route（路线，1） → RouteAgent（代理商，N） → FeeItem（费用项，N）
                                          → Summary（汇总，1）
Route（路线，1） → GoodsDetail/GoodsTotal（货物明细/汇总，N）
```

### 数据提取流水线（`scripts/`）
两阶段混合流水线：

1. **规则提取**（快速、确定性）：
   - `modules/horizontal_table_parser_v2.py` — 解析 Excel 横向表格
   - `modules/date_extractor.py` — 从文件名中提取日期
   - `data/agent_whitelist.py`、`data/location_whitelist.py` — 校验白名单

2. **大模型兜底**（处理模糊数据）：
   - `modules/llm_enhancer.py` — 规则提取失败时调用智谱 ChatGLM-4
   - 触发条件：路线/代理商数据不匹配白名单，或被标记为"unknown"

3. **数据组装**：
   - `DataAssembler` 负责分配 ID，并建立各提取实体之间的关联关系

数据校验规则：路线的起点和终点必须不同（且均不能为"unknown"），至少有 1 个已知地点。代理商名称：1–20 个字符，不能为"unknown"或"pending"。

### 前端目录结构（`logistics-quote-system/frontend/src/`）
- `views/` — 页面组件：`Login.vue`、`Dashboard.vue`、`QuoteSearch.vue`、`RouteManage.vue`、`NewRoute/`
- `components/` — 可复用 UI 组件
- `api/` — Axios 请求封装：`auth.js`、`quote.js`、`route.js`
- `stores/` — Pinia 状态管理
- `router/` — Vue Router 路由配置

### API 接口列表
- `POST /api/v1/auth/login` — 登录，返回 JWT token
- `GET/POST /api/v1/quotes` — 多条件报价查询
- `GET/POST/PUT/DELETE /api/v1/routes` — 路线增删改查（写操作需管理员权限）

## 关键文档
- `docs/CODE_GUIDE.md` — 详细代码说明
- `docs/DEPLOYMENT.md` — 部署流程说明
- `database/README.md` — 数据库结构与字段说明
- `logistics-quote-system/完整启动指南.md` — 完整启动指南
