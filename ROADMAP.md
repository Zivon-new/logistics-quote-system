# 国际物流智能报价及推荐系统 — 开发路线图

> 毕业设计项目 | 工作目录：`D:/project_root`
> 数据库：MySQL 8.0，库名 `price_test_v2`
> 最后更新：2026-03-16

---

## 项目背景

这是一个面向外贸企业的**国际物流智能报价及推荐系统**。
基础功能（报价查询、航线管理、Excel导入）已开发完毕。
毕设需要体现"智能"特性，因此规划了6个新模块，并于本阶段（v3）完成了数据库升级。

---

## 已有基础功能（v1/v2，已完成）

| 模块 | 文件位置 |
|------|---------|
| 报价查询页 | `frontend/src/views/QuoteSearch.vue` |
| 航线管理页 | `frontend/src/views/RouteManage.vue` |
| Excel 导入 | `frontend/src/views/NewRoute/ExcelImport.vue` |
| 手动录入 | `frontend/src/views/NewRoute/ManualInput.vue` |
| 仪表盘 | `frontend/src/views/Dashboard.vue` |
| 后端 API | `backend/app/routers/routes.py` |
| 数据提取 | `scripts/modules/extractors/`（含 LLM 全量提取器） |

---

## 数据库升级（v3，已完成 ✅）

**新建4张表：**
- `agents` — 代理商主表（17条，从 route_agents 提取去重）
- `ports` — 全球港口表（32条，含经纬度、清关天数）
- `country_lpi` — 世界银行 LPI 2023（16国，含风险等级自动计算列）
- `agent_check_history` — AI 背调历史记录表

**修改3张表：**
- `route_agents` — 新增 `代理商ID`（关联率100%）、`时效天数`（提取率100%）
- `routes` — 新增 `起始港口ID`、`目的港口ID`
- `goods_details` — 新增 `货物大类`

---

## 6大新模块开发计划

### Phase 1（优先，直接支撑论文核心论点）

#### 模块1：智能推荐引擎 ⭐ 最重要
- **功能**：用户输入起点/终点/货物类型，系统综合打分推荐最优代理商
- **打分维度**：时效天数（30%）+ 报价价格（30%）+ LPI风险（20%）+ 信用评分（20%）
- **技术**：FastAPI 规则打分接口 + Vue 推荐结果卡片
- **新增文件**：
  - `backend/app/routers/recommend.py`
  - `backend/app/services/recommend_service.py`
  - `frontend/src/views/Recommend.vue`

#### 模块2：价格分析看板
- **功能**：展示各航线/运输方式的价格趋势、分布、对比
- **技术**：ECharts 折线图 + 柱状图，FastAPI 聚合接口
- **新增文件**：
  - `backend/app/routers/analytics.py`
  - `frontend/src/views/Analytics.vue`

#### 模块3：报价对比工具
- **功能**：勾选多家代理商，横向对比价格/时效/风险
- **技术**：前端表格对比，复选框选择，无需新建后端接口（复用现有数据）
- **新增文件**：
  - `frontend/src/views/Compare.vue`

---

### Phase 2（后续完善）

#### 模块4：全球港口地图
- **功能**：世界地图上显示31个港口，点击查看详情（清关天数、风险等级）
- **技术**：Leaflet.js + OpenStreetMap（免费，无需 API Key）
- **数据来源**：`ports` 表（经纬度已录入）
- **新增文件**：`frontend/src/views/PortMap.vue`

#### 模块5：航线风险画像
- **功能**：为每条航线生成目的国风险报告，雷达图展示6维LPI指标
- **技术**：ECharts 雷达图 + 风险等级标签
- **数据来源**：`country_lpi` 表
- **新增文件**：`frontend/src/views/RiskProfile.vue`

#### 模块6：AI 企业背调助手
- **功能**：输入代理商名称，调用 GLM-4 生成背调报告，历史记录可查
- **技术**：调用智谱 GLM-4 API，报告缓存到 `agent_check_history`
- **新增文件**：
  - `backend/app/routers/agent_check.py`
  - `backend/app/services/agent_check_service.py`
  - `frontend/src/views/AgentCheck.vue`

---

## 当前进度

```
✅ 数据提取层（LLM全量提取器）
✅ 数据库 v3 迁移（4新表 + 种子数据 + 数据迁移）
⬜ 模块1：智能推荐引擎      ← 下一步
⬜ 模块2：价格分析看板
⬜ 模块3：报价对比工具
⬜ 模块4：全球港口地图
⬜ 模块5：航线风险画像
⬜ 模块6：AI 企业背调助手
```

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python + FastAPI + SQLAlchemy |
| 前端 | Vue 3 + Vite + Element Plus |
| 图表 | ECharts |
| 地图 | Leaflet.js |
| 数据库 | MySQL 8.0 |
| AI | 智谱 GLM-4（背调模块） |

---

## 快速启动

```bash
# 后端
cd D:/project_root/logistics-quote-system/backend
uvicorn app.main:app --reload

# 前端
cd D:/project_root/logistics-quote-system/frontend
npm run dev
```
