# 国际物流智能报价及推荐系统

基于 FastAPI + Vue 3 + MySQL 的国际物流报价管理与智能推荐系统，毕业设计项目。

## 功能模块

| 模块 | 说明 |
|------|------|
| 报价查询 | 多条件筛选（起始地/目的地可选，下拉补全），内置报价对比工具 |
| 智能推荐 | 四维评分：时效30% / 价格30% / LPI指数20% / 信用评分20% |
| 路线管理 | 新建/编辑/删除路线，Excel 批量导入，附件上传/预览/下载 |
| 价格分析看板 | ECharts 图表，含运输方式占比、价格趋势、路线使用量等6个维度 |
| 全球港口地图 | Leaflet.js 交互地图，点击港口查看风险预警，一键跳转报价查询 |
| 航线风险画像 | ECharts 雷达图，基于世界银行 LPI 2023 六维度展示目的国风险 |
| AI 企业背调 | 调用 GLM-4-Flash，7天缓存，结构化解析承运商背景与风险 |
| 贸易风险预警 | 自动爬取贸法通月报 PDF，解析贸易政策与贸易动态章节，每日 08:00 定时同步 |

## 技术栈

**后端**
- Python 3.11 + FastAPI 0.104
- SQLAlchemy 2.0 + MySQL 8.0
- APScheduler 3.x（定时任务）
- pdfplumber（PDF 解析）
- zhipuai SDK（GLM-4-Flash）

**前端**
- Vue 3 + Vite + Element Plus
- ECharts 5 / Leaflet.js / SheetJS / mammoth.js
- Axios（JWT 鉴权统一封装）

## 项目结构

```
logistics-quote-system/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口，APScheduler 定时任务
│   │   ├── api/v1/              # 路由层（routes/quotes/analytics/warnings 等）
│   │   ├── services/            # 业务层（推荐引擎/Excel导入/贸法通爬虫）
│   │   ├── models/              # ORM 模型
│   │   └── core/                # 配置/鉴权/验证码
│   └── requirements.txt
└── frontend/
    └── src/
        ├── main.js              # Vue 应用入口
        ├── router/              # 页面路由
        ├── views/               # 页面组件
        └── components/          # 通用组件（附件面板等）
```

## 快速启动

环境要求：Python 3.11、Node.js 18+、MySQL 8.0

**后端**
```bash
cd logistics-quote-system/backend
# 激活虚拟环境（venv 在项目根目录）
../../venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# API 文档：http://localhost:8000/docs
```

**前端**
```bash
cd logistics-quote-system/frontend
npm install
npm run dev
# 页面：http://localhost:5173
```

数据库：MySQL 8.0，库名 `price_test_v2`，建表脚本见 `database/` 目录。

## 预警数据说明

- 数据源：[贸法通](https://www.ctils.com/categories/7/articles) 每月发布的贸易风险月报 PDF
- 解析内容：第一章（贸易政策）+ 第三章（贸易动态），跳过第二章（境外安全）
- 生命周期：活跃预警存入 `route_warnings`，超过30天自动归档至 `route_warnings_archive`
- 同步方式：每日 08:00 自动调度，或在港口地图页手动点击"同步预警"触发
