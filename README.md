# 国际物流智能报价及推荐系统

基于 FastAPI + Vue 3 + MySQL 的国际物流报价管理与智能推荐系统，毕业设计项目。

## 系统概述

本系统面向国际物流从业者，解决报价数据分散、代理商评估困难、目的地风险不透明三大痛点。核心创新点在于：

1. **Excel 自动解析**：针对物流行业非标准横向表格，设计了正则+LLM混合提取引擎，实现结构化数据的批量导入
2. **四维智能推荐**：将时效、价格、目的国物流绩效指数（LPI）、代理商信用评分融合为综合评分模型
3. **实时风险感知**：自动爬取权威贸易风险月报，解析后关联到具体航线，在查询结果中实时展示预警

---

## 功能模块

| 模块 | 核心功能 |
|------|----------|
| 报价查询 | 多条件模糊检索（起始地/目的地/货物/代理商/日期范围），每条报价内嵌综合评分与LPI信息，查询结果旁显示对应航线预警 |
| 智能推荐 | 四维加权评分（时效30% / 价格30% / LPI指数20% / 信用评分20%），支持按评分/时效/价格排序，展示各项得分明细 |
| 路线管理 | 新建/编辑/删除路线，Excel批量导入（正则+LLM混合解析），附件上传/在线预览/下载（支持图片/PDF/Word/Excel） |
| 价格分析看板 | ECharts多维图表：运输方式占比、价格趋势（按周/月/季/年）、热门路线排行、代理商活跃度、报价区间分布、代理商选择分布 |
| 全球港口地图 | Leaflet.js 交互地图，500+港口坐标，点击标记查看港口详情与风险预警，支持一键跳转报价查询 |
| 航线风险画像 | ECharts雷达图，基于世界银行LPI 2023六维评分（通关/基础设施/国际运输/物流能力/货物追踪/时效性）展示目的国物流环境 |
| AI企业背调 | 用户粘贴天眼查/企查查原始文本，GLM-4-Flash生成结构化背调报告（成立背景/主营业务/风险提示/综合评价），7天缓存 |
| 贸易风险预警 | 自动爬取贸法通月报PDF，正则分章解析后按条目拆分，关联国家代码，每日08:00定时同步，30天自动归档 |

---

## 技术栈

### 后端

| 组件 | 版本/说明 |
|------|----------|
| Python | 3.11 |
| FastAPI | 0.104，异步框架，自动生成OpenAPI文档 |
| SQLAlchemy | 2.0，ORM，支持中文字段名映射 |
| MySQL | 8.0，库名 `price_test_v2` |
| APScheduler | 3.x，BackgroundScheduler，cron表达式定时任务 |
| pdfplumber | PDF文本提取，最多读取前10页 |
| httpx | 异步HTTP客户端，用于爬虫和PDF下载 |
| zhipuai SDK | GLM-4-Flash，企业背调与LLM兜底增强 |
| slowapi | 基于IP的接口限速中间件 |
| openpyxl | Excel文件解析（表格结构识别） |

### 前端

| 组件 | 版本/说明 |
|------|----------|
| Vue 3 | 组合式API（setup语法糖） |
| Vite | 构建工具 |
| Element Plus | UI组件库（表格/表单/对话框/上传） |
| ECharts 5 | 数据可视化（饼图/折线图/柱状图/雷达图） |
| Leaflet.js | 全球港口交互地图 |
| SheetJS (xlsx) | 前端Excel文件解析辅助 |
| mammoth.js | Word文档在线预览（.docx → HTML） |
| Axios | HTTP请求，封装JWT鉴权拦截器 |

---

## 系统架构

### 整体架构

```
用户浏览器
    │
    ▼
Vue 3 前端（localhost:5173）
    │  Axios + JWT Bearer Token
    ▼
FastAPI 后端（localhost:8000）
    ├── /api/v1/quotes      报价查询
    ├── /api/v1/recommend   智能推荐
    ├── /api/v1/routes      路线管理 + Excel导入
    ├── /api/v1/analytics   价格分析看板
    ├── /api/v1/ports       港口地图数据
    ├── /api/v1/risk        航线风险画像
    ├── /api/v1/warnings    贸易风险预警
    ├── /api/v1/agent-check AI企业背调
    └── /api/v1/attachments 附件管理
         │
         ├── SQLAlchemy ORM ─────── MySQL 8.0
         ├── APScheduler ─────────── 定时爬虫（08:00）
         ├── pdfplumber + httpx ──── 贸法通PDF解析
         └── zhipuai SDK ─────────── GLM-4-Flash
```

### 数据库表结构

```
routes              路线主表（起始地/目的地/途径地/重量/货值）
route_agents        代理路线表（代理商/运输方式/时效天数）
fee_items           费用明细（单价/数量/最低收费/币种）
fee_total           整单费用（含税/汇损）
summary             汇总表（小计/税率/税金/汇损率/总计）
goods_details       货物明细（货物名称/数量/单价/重量）
goods_total         整单货物（实际重量/货值/总体积）
agents              代理商信息（信用评分）
country_lpi         世界银行LPI数据（160+国家六维评分）
ports               全球港口（500+港口坐标/清关天数）
route_warnings      活跃预警（30天内）
route_warnings_archive  历史预警（超30天自动归档）
route_attachments   附件记录（路线关联文件）
agent_check_history AI背调缓存（7天有效）
```

---

## 核心模块详解

### 1. Excel 横向表格解析（正则 + LLM 混合提取）

物流行业报价单通常以横向布局存储（表头在左列，数据在右侧展开），与普通纵向表格结构截然不同，难以用通用方法解析。本系统设计了分层提取架构：

#### 架构设计

```
HorizontalTableParserV2
    │
    ├── SheetFormatDetector        格式置信度检测（0~1分）
    │       └── 若置信度 < 0.5 → LLMFullExtractor（全量LLM提取）
    │
    ├── 独立提取器（各自继承 BaseExtractor）
    │       ├── RouteExtractorV2   路线提取（起始地/目的地/货重）
    │       ├── AgentExtractorV2   代理商提取（运输方式/时效/赔付）
    │       ├── GoodsExtractor     货物提取（名称/数量/重量）
    │       ├── FeeExtractor       费用提取（单价/数量/币种）
    │       └── SummaryExtractor   汇总提取（税率/汇损率/总计）
    │
    └── DataAssembler              数据组装（分配ID，建立关联）
```

#### BaseExtractor 核心流程（质量驱动的双阶段提取）

每个独立提取器都继承自 `BaseExtractor`，执行统一的两阶段流程：

```
阶段1：规则提取（正则匹配）
    └── _extract_with_rules()：使用正则表达式识别字段

阶段2：质量评估
    └── _evaluate_quality()：返回 0~1 的质量分
        └── 若质量分 < QUALITY_THRESHOLD（默认0.7）
                └── 阶段3：LLM增强
                        └── _enhance_with_llm()：将原始单元格文本发给GLM-4-Flash
                        └── 再次评估质量，记录统计信息
```

**与传统方式的区别**：不是"正则失败才走LLM"，而是"正则先跑，质量不达标才触发LLM"，避免了对LLM的过度依赖，大幅降低API调用成本。

#### RouteExtractorV2 正则提取示例

路线字段（起始地→目的地）支持多种分隔符和格式：

```python
route_patterns = [
    # 格式："深圳→荷兰" / "上海-德国汉堡" / "广州至新加坡"
    re.compile(r'^([^\s\-:：]{2,10})\s*[-–—→~至]\s*([^\s:：专线海运空运]{2,10})'),
    # 格式："货交 深圳-鹿特丹："
    re.compile(r'货交\s*([^\s\-:：]{2,20})\s*[-–—→~至]\s*([^\s:：]{2,20})'),
]

# 支持途径地提取："深圳→香港-日本" → 起始地=深圳, 途径地=香港, 目的地=日本
```

重量字段优先匹配"总重量"、"合计"等聚合词，再回退到"重量"：

```python
weight_patterns = [
    re.compile(r'总重量\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:kgs?|KGS?)?'),
    re.compile(r'合计\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:kgs?|KGS?)?'),
    re.compile(r'重量\s*[:：]?\s*(?:KG)?\s*(\d+(?:\.\d+)?)'),
]
```

#### LLMFullExtractor（全量兜底）

当 `SheetFormatDetector` 判断格式置信度低于阈值（0.5）时，跳过所有正则提取器，直接将整张 sheet 的单元格序列化为文本，发送给 GLM-4-Flash 进行全量理解和结构化输出。这保证了即使面对高度非标准的报价单，系统也能给出解析结果。

#### 断点续传机制

对于包含多个 sheet 的大型Excel文件（如月度汇总表），解析器在每处理完一个 sheet 后立即将中间结果写入 checkpoint JSON 文件。程序中断后可从最后一个检查点继续，不丢失已处理数据。

---

### 2. 智能推荐引擎（四维加权评分）

#### 评分模型

```
综合评分 = 时效得分 × 0.3
         + 价格得分 × 0.3
         + LPI得分  × 0.2
         + 信用得分 × 0.2
```

#### 各维度计算方法

**时效得分**（越短越高，组内归一化）：

```
时效得分 = (1 - (时效天数 - min) / (max - min)) × 100
```

**价格得分**（越低越高，优先用单价/kg消除货重差异）：

```python
# 优先计算单价/kg（消除不同货重报价的可比性问题）
单价_per_kg = 总价 / 计费重量

# 若无重量数据，降级用总价归一化
价格得分 = (1 - (当前价 - min价) / (max价 - min价)) × 100
```

**LPI得分**（世界银行物流绩效指数，同一查询目的地共享同一LPI分）：

```python
# LPI原始值范围 1~5，转换为百分制
LPI得分 = (lpi - 1) / 4 × 100

# 目的地文本先映射到国家代码（关键词匹配），再从 country_lpi 表查询
# 如："鹿特丹" → "NL" → 荷兰LPI数据
```

**信用得分**：直接使用 `agents` 表的 `信用评分` 字段（0~100），无记录时默认60分。

#### 归一化策略

报价查询页的评分与推荐页略有不同：查询页按目的地分组归一化（同目的地的代理商之间相互比较），推荐页在全量候选集内归一化。两者评分公式相同，由 `recommend_service.py` 中的辅助函数复用。

---

### 3. 贸法通预警爬虫（正则分章 + 条目拆分）

#### 数据来源

[贸法通](https://www.ctils.com/categories/7/articles) 每月发布《贸易风险月报》PDF，包含三章：
- 第一章：对华经贸摩擦（贸易政策类预警）
- 第二章：境外安全（**跳过不处理**）
- 第三章：全球经贸动态（贸易动态类预警）

#### 爬取流程

```
1. GET https://www.ctils.com/categories/7/articles?pageNum=1
   └── 正则提取页面内嵌 JS 变量 newsPage JSON（文章列表）

2. 按标题检查去重（主表+归档表，避免重复爬取）

3. 下载 PDF（httpx，60s超时），pdfplumber 提取文本（最多前10页）

4. 章节切分（_split_sections）
   └── 对每个章节标题 pattern.finditer()，取最后一次匹配位置
       （PDF中目录页和正文页各出现一次，取正文那次）

5. 条目拆分（_parse_items）
   └── 按 \n\s*(\d+)[、.．]\s* 分割为独立条目
   └── 过滤目录行（第一行末尾有省略号+页码特征）

6. 字段提取（每条目）
   ├── _extract_country：COUNTRY_MAP 关键词匹配 → ISO-3166 国家代码
   ├── _detect_risk_level：关键词分级（3=高/2=中/1=低）
   └── _detect_risk_type：章节+关键词判断预警类型

7. 写入 route_warnings 表（按预警标题去重）

8. _auto_archive：将生效日期超30天的记录移入归档表
```

#### 风险分级关键词

```python
HIGH_KWORDS = ["封锁", "禁运", "禁止进口", "贸易禁令", "战争", "武装冲突",
               "港口封闭", "严重拥堵", "紧急措施", "出口管制升级"]   # 等级3

MED_KWORDS  = ["反倾销税", "反补贴税", "反规避", "制裁", "关税加征",
               "贸易摩擦", "清关延误", "罢工", "港口拥堵", "临时关税"]  # 等级2
```

#### 国家代码映射

维护了 80+ 中文国家/地区名到 ISO-3166-1 alpha-2 代码的映射字典（`COUNTRY_MAP`），支持地名（也门）、城市（迪拜→AE）、区域（红海→YE）等多种表达方式。

---

### 4. AI企业背调（GLM-4-Flash + 结构化解析）

用户从天眼查/企查查复制企业原始文本，系统调用 GLM-4-Flash 生成 JSON 格式的结构化背调报告。

#### Prompt 设计

System Prompt 要求模型严格按照固定 JSON schema 输出，包含9个字段：

```json
{
  "公司名称": "...",
  "成立背景": "成立时间、注册地、法定代表人、股东背景、营业期限",
  "主营业务": "核心业务范围分析",
  "经营规模": "注册资本、实缴资本、员工规模、参保人数",
  "服务网络": "服务覆盖地区、合作伙伴、认证资质（WCA/ISO等）",
  "合规资质": "AEO/NVOCC/税务评级/高新认证",
  "风险提示": "经营异常、司法涉诉、行政处罚、注册资本与实缴差距",
  "综合评价": "100字以内综合判断",
  "风险评级": "低风险/中等风险/高风险/无法评估",
  "摘要": "不超过150字总结"
}
```

模型参数：`temperature=0.2`（确保输出稳定性），`max_tokens=2000`。

#### 缓存机制

同一公司名称7天内复用历史结果（写入 `agent_check_history` 表），避免重复调用API。用户粘贴新的原始文本时，视为数据更新，强制重新分析。响应结果包含 `from_cache` 标志，前端据此显示缓存提示。

#### 容错解析

GLM 有时会在 JSON 外包裹 markdown 代码块（` ```json ... ``` `），`_parse_report()` 对此做了容错处理：优先提取代码块内容，找不到则直接 `json.loads()`，全部失败时返回 `{"原始输出": content}` 以保留原始信息。

---

### 5. 报价查询与预警联动

报价查询接口在返回结果时，自动关联两类附加信息：

1. **LPI信息**（`dest_lpi_info`）：按目的地聚合，返回目的国的LPI综合评分、风险等级和国家名称
2. **预警信息**（`dest_warnings`）：查询结果中所有目的地对应的活跃预警（来自 `route_warnings` 表）

这使得用户在查看报价的同时，无需切换页面即可感知目的地的贸易风险。

---

### 6. 附件管理

每条路线可关联多个附件，存储路径为 `uploads/{route_id}/{uuid}.ext`，数据库记录原始文件名与存储文件名的映射。

支持的文件类型：

| 类型 | 扩展名 | 前端预览方式 |
|------|--------|-------------|
| 图片 | jpg/png/gif/webp | `<img>` 标签直接预览 |
| PDF | pdf | `<iframe>` 内嵌预览 |
| Word | doc/docx | mammoth.js 转 HTML 预览 |
| Excel | xls/xlsx | SheetJS 解析后表格展示 |

文件大小限制：20MB。下载接口使用 `Content-Disposition: attachment` 强制下载，文件名经 URL 编码处理（支持中文文件名）。

---

## 项目结构

```
logistics-quote-system/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI入口，APScheduler定时任务，CORS/限速中间件
│   │   ├── config.py                  # 环境变量配置（DB/JWT/API Key）
│   │   ├── database.py                # SQLAlchemy引擎与Session工厂
│   │   ├── api/v1/
│   │   │   ├── __init__.py            # 路由聚合（api_router）
│   │   │   ├── quotes.py              # 报价查询（含智能评分注入）
│   │   │   ├── recommend.py           # 智能推荐
│   │   │   ├── routes.py              # 路线CRUD + Excel导入
│   │   │   ├── analytics.py           # 价格分析看板（6个数据端点）
│   │   │   ├── ports.py               # 港口地图数据
│   │   │   ├── risk.py                # 航线风险画像（LPI雷达数据）
│   │   │   ├── warnings.py            # 贸易风险预警查询
│   │   │   ├── agent_check.py         # AI企业背调（GLM-4-Flash）
│   │   │   ├── attachments.py         # 附件上传/预览/下载
│   │   │   └── auth.py                # JWT登录/注册
│   │   ├── models/                    # SQLAlchemy ORM模型
│   │   │   ├── route.py               # Route/RouteAgent
│   │   │   ├── fee.py                 # FeeItem/FeeTotal/Summary
│   │   │   ├── goods.py               # GoodsDetail/GoodsTotal
│   │   │   └── user.py                # User
│   │   ├── services/
│   │   │   ├── recommend_service.py   # 四维评分引擎（含LPI映射）
│   │   │   ├── ctils_scraper.py       # 贸法通爬虫（PDF解析+章节拆分）
│   │   │   ├── excel_import_service.py # Excel导入服务（调用解析器）
│   │   │   └── route_service.py       # 路线业务逻辑
│   │   └── core/
│   │       ├── deps.py                # 依赖注入（get_db/get_current_user）
│   │       └── security.py            # JWT生成与验证
│   └── requirements.txt
│
├── scripts/
│   └── modules/
│       ├── horizontal_table_parser_v2.py   # 解析器主入口（含断点续传）
│       ├── llm_enhancer.py                 # GLM-4-Flash LLM增强器
│       ├── assembler/
│       │   └── data_assembler.py           # 数据组装（分配ID/建立关联）
│       ├── extractors/
│       │   ├── base_extractor.py           # 提取器基类（质量驱动双阶段）
│       │   ├── sheet_format_detector.py    # 格式置信度检测
│       │   ├── route_extractor_v2.py       # 路线提取（正则+白名单验证）
│       │   ├── agent_extractor_v2.py       # 代理商提取
│       │   ├── fee_extractor.py            # 费用提取（含最低收费逻辑）
│       │   ├── goods_extractor.py          # 货物提取
│       │   ├── summary_extractor.py        # 汇总提取（税率/汇损率）
│       │   └── llm_full_extractor.py       # 全量LLM提取（低置信度兜底）
│       └── validators/
│           ├── route_validator.py          # 路线数据验证
│           └── agent_validator.py          # 代理商数据验证
│
└── frontend/
    └── src/
        ├── main.js                # Vue应用入口
        ├── router/index.js        # 路由配置（含JWT守卫）
        ├── views/
        │   ├── Login.vue          # 登录页
        │   ├── Dashboard.vue      # 首页概览
        │   ├── QuoteSearch.vue    # 报价查询（含评分展示/预警联动）
        │   ├── Recommend.vue      # 智能推荐
        │   ├── RouteManage.vue    # 路线管理
        │   ├── NewRoute/          # 新建路线（多步骤表单）
        │   ├── Analytics.vue      # 价格分析看板
        │   ├── PortMap.vue        # 全球港口地图
        │   ├── RiskProfile.vue    # 航线风险画像
        │   └── AgentCheck.vue     # AI企业背调
        └── components/
            └── AttachmentPanel.vue # 附件面板（上传/预览/下载）
```

---

## API 接口概览

服务启动后访问 `http://localhost:8000/docs` 查看完整 Swagger 文档。

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/quotes/search` | GET | 报价查询（分页，含评分和预警） |
| `/api/v1/recommend` | GET | 智能推荐（四维评分排序） |
| `/api/v1/routes` | GET/POST | 路线列表/新建路线 |
| `/api/v1/routes/import-excel` | POST | Excel批量导入 |
| `/api/v1/analytics/overview` | GET | 总览统计数据 |
| `/api/v1/analytics/trend` | GET | 报价趋势（周/月/季/年） |
| `/api/v1/analytics/route-usage` | GET | 热门路线排行 |
| `/api/v1/analytics/by-agent` | GET | 代理商活跃度 |
| `/api/v1/analytics/price-distribution` | GET | 报价区间分布 |
| `/api/v1/ports` | GET | 港口列表（含坐标/预警） |
| `/api/v1/risk/lpi-list` | GET | 全量LPI国家数据 |
| `/api/v1/risk/route-risk` | GET | 指定航线风险画像 |
| `/api/v1/warnings` | GET | 活跃预警列表 |
| `/api/v1/warnings/sync` | POST | 手动触发贸法通同步 |
| `/api/v1/agent-check/check` | POST | AI企业背调 |
| `/api/v1/agent-check/history` | GET | 背调历史记录 |
| `/api/v1/attachments/upload/{route_id}` | POST | 上传附件 |
| `/api/v1/attachments/{route_id}` | GET | 获取路线附件列表 |
| `/api/v1/attachments/download/{attachment_id}` | GET | 下载附件 |
| `/api/v1/auth/login` | POST | 登录（返回JWT Token） |

所有接口（除登录外）均需在请求头携带 `Authorization: Bearer <token>`。

---

## 快速启动

**环境要求**：Python 3.11、Node.js 18+、MySQL 8.0

### 后端

```bash
cd logistics-quote-system/backend

# 激活虚拟环境（venv在项目根目录）
../../venv/Scripts/activate      # Windows
source ../../venv/bin/activate   # Linux/Mac

pip install -r requirements.txt

# 配置环境变量（复制并修改）
cp .env.example .env
# 填写：DB_HOST / DB_PASSWORD / JWT_SECRET_KEY / ZHIPU_API_KEY

uvicorn app.main:app --reload
# Swagger文档：http://localhost:8000/docs
```

### 前端

```bash
cd logistics-quote-system/frontend
npm install
npm run dev
# 访问：http://localhost:5173
```

### 数据库

```bash
mysql -u root -p < database/price_test_v2.sql
```

MySQL库名：`price_test_v2`，建表脚本位于 `database/price_test_v2.sql`。

---

## 预警数据说明

| 项目 | 说明 |
|------|------|
| 数据源 | [贸法通](https://www.ctils.com/categories/7/articles) 每月发布的贸易风险月报 PDF |
| 解析内容 | 第一章（对华经贸摩擦/贸易政策）+ 第三章（全球经贸动态），跳过第二章（境外安全） |
| 条目粒度 | 每篇PDF按章节拆分后，再按编号（1、2、3、）细分为独立条目，每条关联具体国家 |
| 生命周期 | 活跃预警存入 `route_warnings`，超过30天自动归档至 `route_warnings_archive` |
| 同步方式 | 每日08:00 APScheduler自动调度，或在港口地图页手动点击"同步预警"触发 |
| 去重策略 | 以 `预警标题` 为唯一键，同一篇月报（标题前40字匹配）不重复写入 |
