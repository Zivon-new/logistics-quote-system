# 架构重构方案

本文档记录当前代码库中待处理的架构改进项。
已完成的优化：`calcGroupSubtotals` 统一、O(n²) 数据整形修复、LPI 评分辅助函数去重、
`fee_service.py` 抽取（`get_forex_rates`/`convert_min_fee`/`apply_min_fee`/`clean_goods_*`，
同时去重了 quotes.py 里重复的汇率查询与最低收费换算逻辑，并补齐单元测试）、
`get_route_detail` 输出接入 Pydantic 响应模型校验（务实版：保留手动组装逻辑，
新增 `RouteDetailDataResponse` 等模型在组装完 dict 后做一次校验/序列化，详见候选三）。

---

## 候选一：删除 CRUD 层（或真正深化它） ~~**已完成（方案 A）**~~

**实际采用：方案 A（彻底删除）**

行动前先做了实证验证，而不是直接相信下方诊断：对全部 14 个 CRUD 函数逐一在
`app/` 全树 grep 引用计数，证明只有 `get_routes`/`get_routes_count`（route.py）、
`authenticate_user`（user.py）共 3 个被外部调用过，其余 11 个零引用、纯死代码——
确证"伪深模块"判断成立，方案 A 是唯一合理选择。

具体改动：
- `routes.py`：删除 `crud_route` 导入，将 `get_routes`/`get_routes_count` 内联为
  共享的 `db.query(Route)` 基查询，分别派生 `.count()` 与
  `.order_by().offset().limit().all()`（比原 CRUD 中两个函数各自重复过滤逻辑更 DRY）；
  顺带去掉了原 `get_routes` 里从未被消费的 `joinedload(Route.agents)`
  （端点本就单独查询 `RouteAgent` 自行组装 `agents_by_route`，这个 JOIN 纯属浪费）。
- `auth.py`：删除 `crud_user` 导入，将 `authenticate_user` 的核心逻辑内联为
  `db.query(User).filter(...).first()` + `verify_password()`，行为完全等价。
- 删除整个 `app/crud/` 目录（route.py 139行 + user.py 81行）。
- 清理孤儿 schema：`RouteCreate`/`RouteUpdate`/`UserCreate`/`UserUpdate` 仅被
  即将删除的 CRUD 函数消费，属于"自己改动产生的孤儿"而非预先存在的死代码，
  一并从 `schemas/route.py`/`schemas/user.py`/`schemas/__init__.py` 移除。

已通过：grep 全仓库零残留（`crud_route`/`crud_user`/`from ...crud`/
`RouteCreate`/`RouteUpdate`/`UserCreate`/`UserUpdate`）、应用导入正常、
33/33 单元测试通过，并通过 `TestClient` + `get_current_user` 依赖覆盖走真实
HTTP 路由层验证：列表分页、`起始地`/`目的地` 模糊过滤（含叠加过滤）、
分页参数、`verify_password()` 正确/错误密码判定均与原实现行为一致。

---

## 候选一原计划（存档）

**文件**：`backend/app/crud/route.py`（139行）、`backend/app/crud/user.py`（81行）

**问题**

CRUD 层是伪深模块。每个函数都是 3-5 行的 SQLAlchemy 直接调用，
调用者需要理解的东西（`joinedload`、`.filter()`、`.first()` vs `.all()`）
和实现者需要理解的东西完全相同，零收益。

更致命的是，`routes.py` 里 create/update/delete 的所有核心逻辑
根本没走 CRUD 层，直接写在 API 接口里——说明这个 CRUD 层是不完整的假象。

**删除测试**：删掉这两个文件，复杂度不会增加，只是平移到调用方。

**方案 A（推荐）：彻底删除 CRUD 层**

- 直接在接口/服务层调用 `db.query()` 等 SQLAlchemy 原语
- 减少一层无意义间接，意图更清晰

**方案 B：真正深化它**

让 CRUD 层承担业务规则，而不是裸包 SQLAlchemy：
- 参数校验（dates 有效范围、必填字段）
- 权限过滤（只返回当前用户有权限看的路线）
- 关联数据组装（`get_route_with_full_detail`）

这需要让 CRUD 函数接收 `current_user` 并内部处理，
调用方变成 `crud.get_route(db, route_id, user)` 而不是
`db.query(Route).options(...).filter(...).first()`。

**预计工作量**：方案 A 约 0.5 天，方案 B 约 2 天

---

## 候选二：拆分 `routes.py` 的内联辅助函数到服务层 ~~**已完成**~~

**实际采用：与原计划一致，分三步完成**

1. ~~创建 `backend/app/services/fee_service.py`~~ **已完成**
   - 已移入：`apply_min_fee`、`convert_min_fee`、`get_forex_rates`、`clean_goods_detail`、`clean_goods_total`
   - 顺带去重了 quotes.py 中重复的 `_get_forex_rates`/`_convert_min_to_fee_currency`
   - 已补充单元测试 `tests/test_fee_service.py`（15 个用例覆盖跨币种换算、最低收费、字段清洗）

2. ~~创建 `backend/app/services/route_service.py`~~ **已完成**
   - 移入 `create_full_route`（路线→代理方案+费用→货物→触发器补写，4 阶段）与
     `update_route`（更新路线字段→替换代理方案→货物先 INSERT 后 DELETE→触发器补写
     →汇总二次写回，5 阶段）的全部业务逻辑，以及它们依赖的 `_upsert_summary`/
     `_insert_agent_with_fees`
   - 接口层（`routes.py`）现在只剩参数解析 + 调用服务 + 异常转换为 HTTP 响应：
     `create_full_route`/`update_route` 端点函数体从 ~40/~115 行精简到 ~12/~14 行
   - `update_route` 的"路线不存在"404 前置检查刻意保留在接口层（service 层假定
     调用方已确认路线存在），与既有"service 不感知 HTTP、纯异常或返回值"的约定一致
     （已 grep 全部 `app/services/*.py` 确认零 `HTTPException`/`fastapi` 引用、零自定义异常类）

3. ~~创建 `backend/app/services/trigger_guard_service.py`~~ **已完成**
   - 封装 `protect_route_fields`（触发器重算后回写手动录入的重量/体积/货值）
     与 `correct_agent_summaries`（触发器重算汇总后强制改回手动录入的
     税金/汇损/进口税率原文）
   - 让 `routes.py` 与 `route_service.py` 都不需要理解 MySQL 触发器副作用的细节

顺带把仅服务于以上模块的纯工具函数 `sf`/`dedupe_agents`
（`route_helpers.py`）用 `git mv` 从 `app/api/v1/` 迁到 `app/services/`
——迁移前已 grep 确认 `routes.py` 中对它们的引用已全部随抽取移走，留在
`api/v1` 会形成"service 反向依赖 api"的倒置依赖；同步更新了
`tests/conftest.py` 中硬编码的加载路径。

已通过：33/33 单元测试（含 `conftest.py` 路径更新后的动态加载）+ 应用整体
导入检查（`IMPORT_OK`）+ `TestClient` + `get_current_user` 依赖覆盖走真实
HTTP 路由层验证 —— 创建完整路线（路线+代理方案+费用项，验证
`protect_route_fields`/`_upsert_summary` 落库结果与响应形状）、更新已有路线
（验证 5 阶段流程：字段更新、代理方案整体替换、`correct_agent_summaries`
对税金/汇损/进口税率原文的二次写回均生效）、不存在路线返回 404、
创建与更新后数据可正确读取与删除，行为与重构前完全一致。

---

## 候选二原计划（存档）

**文件**：`backend/app/api/v1/routes.py`（700+行）

**问题**

接口层（API routes）承担了服务层该做的事：
- `_get_forex_rates(db)` — 查汇率，同时也在 `quotes.py` 里有类似逻辑
- `_convert_min_fee()` / `_apply_min_fee()` — 最低收费换算
- `_protect_route_fields()` — 手动构建 SQL UPDATE 子句来绕过触发器
- `_upsert_summary()` — 直接写 INSERT...ON DUPLICATE KEY UPDATE
- `_clean_goods_detail()` / `_clean_goods_total()` — 清理字段

这些逻辑暴露在接口层，导致：
1. 无法独立测试（必须通过 HTTP 才能触发）
2. 同类逻辑在多文件分散（汇率转换在 routes.py 和 quotes.py 各有一份）
3. `create_full_route` 和 `update_route` 各自 40-120 行，业务逻辑和路由逻辑混在一起

**方案**

1. ~~创建 `backend/app/services/fee_service.py`~~ **已完成**
   - 已移入：`apply_min_fee`、`convert_min_fee`、`get_forex_rates`、`clean_goods_detail`、`clean_goods_total`
   - 顺带去重了 quotes.py 中重复的 `_get_forex_rates`/`_convert_min_to_fee_currency`
   - 已补充单元测试 `tests/test_fee_service.py`（15 个用例覆盖跨币种换算、最低收费、字段清洗）

2. 创建 `backend/app/services/route_service.py`
   - 移入：`create_full_route` 的业务逻辑（4个阶段）
   - 移入：`update_route` 的业务逻辑（5个阶段）
   - 接口层只剩参数解析 + 调用服务 + 返回响应

3. 创建 `backend/app/services/trigger_guard_service.py`
   - 封装触发器后的字段补写逻辑（`_protect_route_fields`、税金/汇损手动回写）
   - 让接口层不再需要理解 MySQL 触发器的副作用

**预计工作量**：3-5 天，需要全量回归测试

---

## 候选三：用 Pydantic 响应模型替代手动序列化 ~~**已完成（务实版）**~~

**文件**：`backend/app/api/v1/routes.py`（`get_route_detail`）

**问题**

`get_route_detail` 接口手动把 Route ORM 对象转成 dict，
100 行嵌套 for 循环。如果 Schema 变化，只能改接口代码，无法复用。

**实际采用的方案（与下方原计划不同）**

调研后发现原计划的 `RouteDetailResponse.model_validate(route).model_dump()` 假设 ORM→Pydantic
是 1:1 映射，但实际输出包含业务规则转换（`apply_min_fee` 需要外部 `forex_rates`）、
单位后缀键名重命名（`"实际重量(/kg)"` 等不是合法 Python 标识符）、计算字段（`总货值`）、
条件默认值（`summary` 为空时返回 `{}`）——手动 dict 组装本身承载着真实业务逻辑，不能简单替换。

改为"务实版"：保留手动组装 `route_data` 的逻辑不变，新增一组精确匹配实际输出形状的
Pydantic 响应模型（`schemas/route.py` 新增 `RouteDetailDataResponse`/`AgentDetailResponse`/
`FeeItemDetailResponse`/`FeeTotalResponse`/`AgentSummaryResponse`/`GoodsDetailItemResponse`/
`GoodsTotalItemResponse`，使用 `Field(alias=...)` + `model_config = ConfigDict(populate_by_name=True)`
处理单位后缀键名），在组装好 dict 之后做一次输出校验：
`RouteDetailDataResponse(**route_data).model_dump(by_alias=True)`。

为避免与 `schemas/route.py` 中已存在但形状不匹配、且未被任何 `response_model=` 引用的
`RouteResponse`/`AgentResponse`/`FeeItemResponse`/`RouteDetailResponse`（疑似死代码，
仅在 `schemas/__init__.py` 中被导出）发生命名冲突或混淆，新模型使用了不同的命名
（`RouteDetailDataResponse` 而非 `RouteDetailResponse` 等）。

已通过：33/33 单元测试 + 真实数据库数据验证（含最低收费换算、单位后缀键名、
fee_total/summary/goods_details/goods_total 全部分支）。

---

## 候选三原计划（存档，未采用）

**文件**：`backend/app/api/v1/routes.py` 第 351-437 行

**问题**

`get_route_detail` 接口手动把 Route ORM 对象转成 dict，
100 行嵌套 for 循环。如果 Schema 变化，只能改接口代码，无法复用。

```python
# 现在的写法
route_data = {
    "路线ID": route.路线ID,
    "起始地": route.起始地,
    ...
    "agents": [
        {
            "代理路线ID": agent.代理路线ID,
            ...
            "fee_items": [...],
        }
        for agent in route.agents
    ]
}
```

**方案**

定义 Pydantic 响应模型：

```python
# schemas/route.py
class FeeItemResponse(BaseModel):
    费用类型: str
    单价: float
    ...
    model_config = ConfigDict(from_attributes=True)

class AgentDetailResponse(BaseModel):
    代理路线ID: int
    代理商: str
    fee_items: List[FeeItemResponse]
    ...

class RouteDetailResponse(BaseModel):
    路线ID: int
    起始地: str
    agents: List[AgentDetailResponse]
```

接口层变为：
```python
return RouteDetailResponse.model_validate(route).model_dump()
```

**收益**：
- Schema 变化只改 Pydantic 类，接口自动跟进
- 前端 API 文档自动更新
- 序列化逻辑可以独立测试

**预计工作量**：2-3 天

---

## 优先级建议

| 优先级 | 候选 | 理由 |
|--------|------|------|
| 1 | 候选二（拆分 fee_service） | 最大收益，纯函数部分可以低风险先做 |
| 2 | 候选三（Pydantic 响应模型） | 不改业务逻辑，风险低 |
| 3 | 候选一（删除 CRUD 层） | 需要配合候选二同步进行才有意义 |
