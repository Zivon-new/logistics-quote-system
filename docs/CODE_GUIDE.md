# 新架构代码导览

## 📋 目录

1. [架构概述](#架构概述)
2. [核心文件详解](#核心文件详解)
3. [数据流说明](#数据流说明)
4. [使用指南](#使用指南)
5. [与现有代码的关系](#与现有代码的关系)
6. [常见问题](#常见问题)

---

## 🏗️ 架构概述

### 核心原则

1. **独立提取**：routes、agents、fees等完全独立提取
2. **规则为主**：90%情况使用规则提取，快速准确
3. **LLM兜底**：规则失败时使用LLM，给完整上下文
4. **明确验证**：每个提取器都有明确的验证标准
5. **简单关联**：同一sheet的agents自动关联到该sheet的route

### 架构图

```
┌─────────────────────────────────────────┐
│           Excel Sheet                    │
└────────────┬────────────────────────────┘
             │
    ┌────────┼────────┐
    │        │        │
    ▼        ▼        ▼
┌──────┐ ┌──────┐ ┌──────┐
│Route │ │Agent │ │ Fee  │  ← 独立提取器
│Extr  │ │Extr  │ │Extr  │     (各自独立)
└───┬──┘ └───┬──┘ └───┬──┘
    │        │        │
    │ 规则提取（90%）  │
    │        │        │
    │ ✓验证  │ ✓验证  │ ✓验证
    │        │        │
    │ ✗失败? │ ✗失败? │ ✗失败?
    │   ↓    │   ↓    │   ↓
    │ LLM兜底│ LLM兜底│ LLM兜底
    │   ↓    │   ↓    │   ↓
    └────┬───┴───┬───┴───┬────┘
         │       │       │
         ▼       ▼       ▼
    ┌──────────────────────┐
    │   DataAssembler      │  ← 数据组装器
    │   - 分配ID           │
    │   - 建立关联         │
    │   - 验证数据         │
    └──────────┬───────────┘
               │
        ┌──────┼──────┐
        ▼      ▼      ▼
    routes.json agents.json fees.json
```

---

## 📁 核心文件详解

### 1. BaseExtractor（基础提取器）

**文件**: `extractors/base_extractor.py`

**作用**: 所有提取器的抽象基类，定义标准提取流程

**核心方法**:
```python
def extract(sheet) -> Any:
    """
    标准提取流程：
    1. 规则提取 (_extract_with_rules)
    2. 验证结果 (_is_valid)
    3. 如果失败且满足条件，LLM兜底 (_extract_with_llm)
    4. 返回结果或默认值 (_get_default)
    """
```

**子类需要实现的4个抽象方法**:
- `_extract_with_rules(sheet)`: 规则提取逻辑
- `_extract_with_llm(sheet)`: LLM提取逻辑
- `_is_valid(result)`: 验证结果
- `_get_default()`: 返回默认值

**关键设计**:
```python
def _should_use_llm(result):
    """
    3个条件判断是否使用LLM：
    1. LLM客户端可用
    2. LLM功能已启用
    3. 规则结果无效
    """
```

**统计功能**:
- 记录规则成功次数、LLM成功次数
- 记录LLM调用次数
- 可通过get_stats()获取

**日志级别**:
- DEBUG: 详细的提取步骤
- INFO: LLM兜底通知
- WARNING: 规则失败
- ERROR: LLM调用失败

---

### 2. RouteExtractor v2（路线提取器）

**文件**: `extractors/route_extractor_v2.py`

**作用**: 从sheet提取路线信息（起始地、目的地、途径地等）

**数据结构**:
```python
@dataclass
class Route:
    起始地: str       # 必须
    目的地: str       # 必须
    途径地: str       # 可选
    贸易备注: str     # 可选
    weight: float    # 实际重量
    volume: float    # 总体积
    value: float     # 货值
```

**提取策略**:
```python
def _extract_with_rules(sheet):
    # 1. 优先从内容提取（主要方法）
    route = _extract_from_content(sheet)
    # 扫描前20行，查找"货交XX-YY"等模式
    
    # 2. 如果不完整，从sheet名补充（辅助方法）
    if not route.起始地 or not route.目的地:
        sheet_route = _extract_from_sheet_name(sheet.title)
        # 补充缺失字段
```

**复用现有规则**:
```python
# 完全复用现有的RouteExtractor类
self.legacy_extractor = RouteExtractor()  # from route_extractor.py

# 使用现有的正则模式、清理逻辑
result = self.legacy_extractor.extract_route(row_text)
```

**验证标准**（4个）:
1. 必须有起始地和目的地
2. 起始地不能是无效值（"国内"、"未知"）
3. 起始地≠目的地
4. 至少一个是已知地名（使用location_whitelist）

**LLM兜底**:
```python
# 给LLM完整的sheet内容（前50行）
sheet_content = self._serialize_sheet(sheet, max_rows=50)

# 明确的提取要求
prompt = """
从以下sheet中提取路线信息。
要求：
1. 起始地（具体城市名，不要"国内"）
2. 目的地（具体城市/国家名）
3. 途径地（如果有）
返回JSON格式...
"""
```

**使用示例**:
```python
extractor = RouteExtractorV2(logger=logger, enable_llm=True)
route = extractor.extract(sheet)

print(f"Route: {route.起始地} → {route.目的地}")
# Route: 深圳 → 新加坡
```

---

### 3. AgentExtractor v2（代理提取器）

**文件**: `extractors/agent_extractor_v2.py`

**作用**: 从sheet提取所有代理商信息

**数据结构**:
```python
@dataclass
class Agent:
    代理商: str         # 必须
    代理备注: str       # 可选
    时效: str          # 可选
    是否赔付: str      # 可选
    运输方式: str      # 可选
    贸易类型: str      # 可选
    _column: int       # 内部：列号（用于关联fee）
```

**提取策略**:
```python
def _extract_with_rules(sheet):
    # 1. 查找"代理"行
    agent_row_idx = _find_agent_row(sheet)
    # 支持多种模式：包含"代理"、"报价方"、"供应商"等
    
    # 2. 遍历该行的每一列
    for col in range(2, max_column + 1):
        agent = _parse_agent_column(sheet, agent_row_idx, col)
        # 提取代理商名、备注、时效等
        
        if agent and agent.代理商:
            agents.append(agent)
```

**代理备注处理**:
```python
agent_text = "融迅--双清含税"

# 分离代理商名和备注（"--"分隔）
if '--' in agent_text:
    parts = agent_text.split('--', 1)
    agent.代理商 = parts[0].strip()   # "融迅"
    agent.代理备注 = parts[1].strip()  # "双清含税"
```

**验证标准**（3个）:
1. 代理商名不为空
2. 不是无效值（"未知"、"待定"、"单列报价"）
3. 长度1-20字符，不是纯数字

**关键特点**:
- **独立于route**：agent提取失败不影响route
- **返回列表**：一个sheet可能有多个代理
- **失败返回空列表**：不影响其他数据

**使用示例**:
```python
extractor = AgentExtractorV2(logger=logger)
agents = extractor.extract(sheet)

for agent in agents:
    print(f"Agent: {agent.代理商} ({agent.代理备注})")
# Agent: 融迅 (双清含税)
# Agent: 骐盛 (一般贸易)
```

---

### 4. DataAssembler（数据组装器）

**文件**: `assembler/data_assembler.py`

**作用**: 将各个提取器的结果组装成最终数据

**输入格式**:
```python
sheets_data = [
    {
        'sheet_name': '深圳-新加坡',
        'sheet_index': 0,
        'route': Route(...),
        'agents': [Agent(...), Agent(...)]
    },
    {
        'sheet_name': '深圳-英国',
        'sheet_index': 1,
        'route': Route(...),
        'agents': [Agent(...)]
    },
    ...
]
```

**组装流程**:
```python
def assemble(sheets_data):
    all_routes = []
    all_agents = []
    
    for sheet_data in sheets_data:
        # 1. 为route分配ID
        route_id = len(all_routes) + 1
        route['路线ID'] = route_id
        all_routes.append(route)
        
        # 2. 为agents分配ID并关联route
        for agent in agents:
            agent_id = len(all_agents) + 1
            agent['代理路线ID'] = agent_id
            agent['路线ID'] = route_id  # ← 关联到该sheet的route
            all_agents.append(agent)
    
    # 3. 验证关联正确性
    validate_associations(all_routes, all_agents)
    
    return {'routes': all_routes, 'agents': all_agents}
```

**关联逻辑**（非常简单）:
- 同一个sheet的所有agents自动关联到该sheet的route
- 每个sheet = 1个route（预处理后保证）
- 不需要复杂的推断

**验证功能**:
1. 检查每个agent的路线ID是否存在
2. 检查每个route是否至少有一个agent（警告）

**使用示例**:
```python
assembler = DataAssembler(logger=logger)
result = assembler.assemble(sheets_data)

routes = result['routes']    # 24条
agents = result['agents']    # 35个
errors = result['validation_errors']  # []

# 获取摘要
summary = assembler.get_summary(result)
print(f"总routes: {summary['total_routes']}")
print(f"总agents: {summary['total_agents']}")
```

---

## 📊 数据流说明

### 完整流程

```
1. Excel文件
   ↓
2. 遍历每个sheet
   ├─ RouteExtractor.extract(sheet)
   │  ├─ 从内容提取（扫描前20行）
   │  ├─ 从sheet名补充
   │  ├─ 验证（4个标准）
   │  └─ LLM兜底（如果失败）
   │  
   ├─ AgentExtractor.extract(sheet)
   │  ├─ 查找"代理"行
   │  ├─ 按列提取
   │  ├─ 验证（3个标准）
   │  └─ LLM兜底（如果失败）
   │  
   └─ FeeExtractor.extract(sheet)  [可选]
   ↓
3. 收集所有sheets的数据
   sheets_data = [
       {'route': Route, 'agents': [Agent, ...]},
       ...
   ]
   ↓
4. DataAssembler.assemble(sheets_data)
   ├─ 为routes分配ID
   ├─ 为agents分配ID
   ├─ 建立关联（agent.路线ID = route.路线ID）
   └─ 验证
   ↓
5. 保存JSON
   ├─ routes.json
   └─ agents.json
```

### 单个Sheet的处理

```
Sheet: "深圳-新加坡一般贸易"
│
├─ RouteExtractor
│  ├─ 扫描内容
│  │  行3: "货交深圳-新加坡："  ← 找到！
│  ├─ 提取: 起始地=深圳, 目的地=新加坡
│  ├─ 验证: ✓ 有起始地和目的地
│  │        ✓ 不是无效值
│  │        ✓ 都在白名单中
│  └─ 返回: Route(起始地=深圳, 目的地=新加坡)
│
├─ AgentExtractor
│  ├─ 查找代理行: 第2行包含"代理"
│  ├─ 提取列2: "融迅--双清含税"
│  │  └─ Agent(代理商=融迅, 代理备注=双清含税)
│  ├─ 提取列3: "骐盛"
│  │  └─ Agent(代理商=骐盛)
│  ├─ 验证: ✓ 有2个有效的agents
│  └─ 返回: [Agent(融迅), Agent(骐盛)]
│
└─ 结果:
   {
     'route': Route(深圳→新加坡),
     'agents': [Agent(融迅), Agent(骐盛)]
   }
```

---

## 📖 使用指南

### 快速开始

**1. 基础使用（不使用LLM）**

```python
from openpyxl import load_workbook
from extractors.route_extractor_v2 import RouteExtractorV2
from extractors.agent_extractor_v2 import AgentExtractorV2
from assembler.data_assembler import DataAssembler

# 加载Excel
wb = load_workbook('your_file.xlsx')

# 创建提取器
route_extractor = RouteExtractorV2()
agent_extractor = AgentExtractorV2()

# 提取数据
sheets_data = []
for sheet in wb.worksheets:
    sheets_data.append({
        'sheet_name': sheet.title,
        'route': route_extractor.extract(sheet),
        'agents': agent_extractor.extract(sheet)
    })

# 组装数据
assembler = DataAssembler()
result = assembler.assemble(sheets_data)

# 保存JSON
import json
with open('routes.json', 'w', encoding='utf-8') as f:
    json.dump(result['routes'], f, ensure_ascii=False, indent=2)
```

**2. 使用LLM（需要配置LLM客户端）**

```python
# 配置LLM客户端（示例）
from llm.llm_client import LLMClient
llm_client = LLMClient(api_key="your-api-key")

# 创建提取器并启用LLM
route_extractor = RouteExtractorV2(
    llm_client=llm_client,
    enable_llm=True
)

# 其余相同...
```

**3. 使用日志**

```python
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建提取器并传入logger
route_extractor = RouteExtractorV2(logger=logger)

# 提取时会输出详细日志
route = route_extractor.extract(sheet)
```

**4. 查看统计信息**

```python
# 提取后查看统计
stats = route_extractor.get_stats()
print(f"规则成功率: {stats['rule_success']/stats['total_attempts']*100:.1f}%")
print(f"LLM调用次数: {stats['llm_calls']}")
```

---

## 🔗 与现有代码的关系

### 完全保留（不修改）

这些现有模块被新架构复用，不需要修改：

1. **location_whitelist.py** - 地名白名单
   - `is_valid_location()`
   - `LOCATION_WHITELIST`
   - RouteExtractor v2直接调用

2. **route_extractor.py** - 路线提取规则
   - RouteExtractor类的所有正则、清理逻辑
   - RouteExtractor v2内部创建实例并调用

3. **route_normalizer.py** - 地名标准化
   - 现有的标准化逻辑
   - 可在RouteExtractor v2中使用

4. **fee_parser.py** - 费用解析
   - 可被FeeExtractor v2复用

5. **llm_enhancer.py** - LLM增强
   - 现有的LLM调用逻辑
   - 可集成到新的LLM模块

### 新增模块

1. **extractors/** - 独立提取器
   - base_extractor.py（新）
   - route_extractor_v2.py（新，包装现有规则）
   - agent_extractor_v2.py（新）
   - fee_extractor_v2.py（新）

2. **assembler/** - 数据组装
   - data_assembler.py（新）

3. **validators/** - 验证器
   - route_validator.py（新）
   - agent_validator.py（新）

### 重构模块

1. **horizontal_table_parser_v2.py** - 主解析器
   - 使用新架构重写
   - 调用独立提取器
   - 调用数据组装器

---

## ❓ 常见问题

### Q1: 新架构比旧架构慢吗？

**A**: 不会。规则提取速度相同（复用现有代码），只是重新组织了流程。

**性能对比**:
- 旧架构：一次遍历，绑定提取
- 新架构：独立提取，但复用现有规则
- 预期差异：<5%

### Q2: Agent提取失败会影响Route吗？

**A**: 不会！这是新架构的核心优势。

```python
# 旧架构
if not agent.代理商:
    return None  # ← 整个QuoteBlock丢弃，route也丢失

# 新架构
agents = agent_extractor.extract(sheet)
# 结果: [] (空列表)
# route不受影响 ✓
```

### Q3: 如何添加新的提取器？

**A**: 继承BaseExtractor，实现4个抽象方法。

```python
from extractors.base_extractor import BaseExtractor

class MyExtractor(BaseExtractor):
    def _extract_with_rules(self, sheet):
        # 实现规则提取
        return my_data
    
    def _extract_with_llm(self, sheet):
        # 实现LLM提取
        return my_data
    
    def _is_valid(self, result):
        # 实现验证
        return result is not None
    
    def _get_default(self):
        # 实现默认值
        return {}
```

### Q4: LLM使用率能控制吗？

**A**: 可以。通过3个条件严格控制。

```python
# 完全禁用LLM
extractor = RouteExtractorV2(enable_llm=False)

# 启用LLM但只在规则失败时使用
extractor = RouteExtractorV2(
    llm_client=llm,
    enable_llm=True  # 只在_is_valid()返回False时调用
)
```

**预期LLM使用率**:
- Route: 5-10%（大部分能从内容提取）
- Agent: 10-20%（某些sheet格式特殊）
- 总体: <15%

### Q5: 如何处理多route的sheet？

**A**: 两种方式。

**方式1: 预处理（推荐）**
```bash
# 使用预处理器拆分
python scripts/preprocessor/excel_preprocessor.py
# "国内-新加坡& 英国" → "深圳-新加坡" + "深圳-英国"
```

**方式2: 扩展RouteExtractor**
```python
class MultiRouteExtractor(RouteExtractorV2):
    def _extract_from_content(self, sheet):
        # 扫描所有"货交XX-YY"标记
        # 返回多个routes
        pass
```

### Q6: 验证错误怎么处理？

**A**: DataAssembler会收集所有验证错误。

```python
result = assembler.assemble(sheets_data)
errors = result['validation_errors']

for error in errors:
    print(f"⚠️  {error}")
    # Agent 'XX' 的路线ID 99 不存在
```

人工review错误，修正数据或更新提取规则。

---

## 🎯 总结

### 新架构的优势

1. **数据完整性** ✅
   - Agent失败不影响Route
   - Fee失败不影响其他
   - 每个表独立提取

2. **代码清晰** ✅
   - 职责单一
   - 易于理解
   - 易于扩展

3. **质量可控** ✅
   - 明确的验证标准
   - 详细的日志
   - 统计信息

4. **成本可控** ✅
   - LLM使用率<15%
   - 规则为主
   - 严格的条件判断

5. **兼容现有规则** ✅
   - 复用所有现有逻辑
   - 只改变组织方式
   - 不影响功能

### 预期效果

| 指标 | 当前 | 新架构 |
|------|------|--------|
| Routes数量 | 18-21条 | 24条 ✅ |
| Agents数量 | 27个 | 35个 ✅ |
| Agent失败影响 | 丢失整个sheet | 不影响route ✅ |
| 代码行数 | 987行 | 约600行 ✅ |
| LLM成本 | 不定 | <$0.20/次 ✅ |

---

**使用愉快！如有问题，请查看example_usage.py或提issue。** 🚀
