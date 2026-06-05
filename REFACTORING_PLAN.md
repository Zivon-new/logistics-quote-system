# 架构重构方案

本文档记录当前代码库中待处理的架构改进项。
已完成的优化：`calcGroupSubtotals` 统一、O(n²) 数据整形修复、LPI 评分辅助函数去重。

---

## 候选一：删除 CRUD 层（或真正深化它）

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

## 候选二：拆分 `routes.py` 的内联辅助函数到服务层

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

1. 创建 `backend/app/services/fee_service.py`
   - 移入：`_apply_min_fee`、`_convert_min_fee`、`_clean_goods_*`
   - 这些是纯函数，极易测试

2. 创建 `backend/app/services/route_service.py`
   - 移入：`create_full_route` 的业务逻辑（4个阶段）
   - 移入：`update_route` 的业务逻辑（5个阶段）
   - 接口层只剩参数解析 + 调用服务 + 返回响应

3. 创建 `backend/app/services/trigger_guard_service.py`
   - 封装触发器后的字段补写逻辑（`_protect_route_fields`、税金/汇损手动回写）
   - 让接口层不再需要理解 MySQL 触发器的副作用

**预计工作量**：3-5 天，需要全量回归测试

---

## 候选三：用 Pydantic 响应模型替代手动序列化

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
