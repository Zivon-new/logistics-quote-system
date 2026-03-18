# 国际物流智能报价及推荐系统 — 开发路线图

> 毕业设计项目 | 工作目录：`D:/project_root`
> 数据库：MySQL 8.0，库名 `price_test_v2`
> 最后更新：2026-03-18

---

## 项目背景

这是一个面向外贸企业的**国际物流智能报价及推荐系统**。
基础功能（报价查询、航线管理、Excel导入）已开发完毕。
毕设需要体现"智能"特性，因此规划了6个新模块，均已于本阶段（v3）完成开发。

---

## 已有基础功能（v1/v2，已完成）

| 模块 | 文件位置 |
|------|---------|
| 报价查询页 | `frontend/src/views/QuoteSearch.vue` |
| 航线管理页 | `frontend/src/views/RouteManage.vue` |
| Excel 导入 | `frontend/src/views/NewRoute/ExcelImport.vue` |
| 手动录入 | `frontend/src/views/NewRoute/ManualInput.vue` |
| 仪表盘 | `frontend/src/views/Dashboard.vue` |
| 后端 API | `backend/app/api/v1/` |
| 数据提取 | `backend/scripts/` (LLM 全量提取器 + 规则提取器) |

---

## 数据库升级（v3，已完成 ✅）

**新建4张表：**
- `agents` — 代理商主表（从 route_agents 提取去重）
- `ports` — 全球港口表（133条，含经纬度、清关天数）
- `country_lpi` — 世界银行 LPI 2023（含风险等级自动计算列）
- `agent_check_history` — AI 背调历史记录表

**修改3张表：**
- `route_agents` — 新增 `代理商ID`、`时效天数`
- `routes` — 新增 `起始港口ID`、`目的港口ID`
- `goods_details` — 新增 `货物大类`

---

## 6大新模块（全部已完成 ✅）

### 模块1：智能推荐引擎 ✅

- **功能**：用户输入起点/终点/货物类型，系统综合打分推荐最优代理商
- **打分维度**：时效天数（30%）+ 报价价格（30%）+ 目的国LPI风险（20%）+ 代理商信用（20%）
- **实现文件**：
  - `backend/app/api/v1/recommend.py`
  - `backend/app/services/recommend_service.py`
  - `frontend/src/views/QuoteSearch.vue`（推荐功能集成在报价查询页）
- **说明**：推荐入口集成在报价查询页，不单独设菜单

### 模块2：价格分析看板 ✅

- **功能**：展示各航线/运输方式的价格趋势、分布、对比；ECharts 下钻交互（点击柱状图联动饼图）
- **实现文件**：
  - `backend/app/api/v1/analytics.py`（6个聚合接口）
  - `frontend/src/views/Analytics.vue`

### 模块3：报价对比工具 ✅

- **功能**：勾选多家代理商，横向对比价格/时效/风险
- **实现文件**：`frontend/src/views/QuoteSearch.vue`（对比功能集成在报价查询页）
- **说明**：复用现有报价查询接口，无独立后端接口

### 模块4：全球港口地图 ✅

- **功能**：世界地图显示133个港口，点击查看详情（清关天数、风险等级、预警联动）
- **技术**：Leaflet.js + 高德地图瓦片
- **实现文件**：
  - `backend/app/api/v1/ports.py`
  - `frontend/src/views/PortMap.vue`

### 模块5：航线风险画像 ✅

- **功能**：为每条航线生成目的国风险报告，ECharts 雷达图展示世界银行LPI 6维指标
- **数据来源**：`country_lpi` 表（World Bank LPI 2023 真实数据）
- **实现文件**：
  - `backend/app/api/v1/risk.py`
  - `frontend/src/views/RiskProfile.vue`

### 模块6：AI 企业背调助手 ✅

- **功能**：用户粘贴工商信息文本，GLM-4-Flash 进行结构化解析与风险推理，历史记录可查（7天缓存）
- **技术**：智谱 GLM-4-Flash API，结果缓存到 `agent_check_history`
- **说明**：基于用户提供的文本进行推理分析，不主动爬取外部数据库
- **实现文件**：
  - `backend/app/api/v1/agent_check.py`
  - `backend/app/services/agent_check_service.py`
  - `frontend/src/views/AgentCheck.vue`

---

## 当前进度

```
✅ 数据提取层（LLM全量提取器 + 规则提取器）
✅ 数据库 v3 迁移（4新表 + 种子数据 + 数据迁移）
✅ 模块1：智能推荐引擎（集成于报价查询页）
✅ 模块2：价格分析看板
✅ 模块3：报价对比工具（集成于报价查询页）
✅ 模块4：全球港口地图
✅ 模块5：航线风险画像
✅ 模块6：AI 企业背调助手
```

---

## 已知局限与答辩准备说明

| 问题 | 现状 | 答辩口径 |
|------|------|---------|
| 代理商信用评分字段为空 | fallback 60分，区别度低 | 字段预留，当前以历史报价活跃度和价格稳定性作为代理指标 |
| LPI 城市映射覆盖约40个目的地 | 其余 fallback 60分 | 已覆盖主要贸易航线，长尾目的地作为后续数据扩充方向 |
| 汇率数据为静态快照 | 无定时更新机制 | 参考日期已在前端标注，定时调度为后续优化方向 |
| AI背调不主动联网 | 仅解析用户粘贴文本 | 定位为"结构化辅助工具"而非"主动调查系统"，符合产品设计预期 |

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python + FastAPI + SQLAlchemy |
| 前端 | Vue 3 + Vite + Element Plus |
| 图表 | ECharts 5 |
| 地图 | Leaflet.js + 高德瓦片 |
| 数据库 | MySQL 8.0 |
| AI | 智谱 GLM-4-Flash |
| 数据来源 | World Bank LPI 2023 |

---

## 快速启动

```bash
# 后端
cd D:/project_root/logistics-quote-system/backend
uvicorn app.main:app --reload --port 5174

# 前端
cd D:/project_root/logistics-quote-system/frontend
npm run dev
```
