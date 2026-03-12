# 新架构部署指南

## 🚀 快速部署（3步完成）

### Step 1: 复制文件到你的项目

```bash
# 解压新架构文件
unzip new_architecture.zip
cd new_architecture/

# 复制核心模块到你的项目
cp -r scripts/modules/extractors YOUR_PROJECT/scripts/modules/
cp -r scripts/modules/assembler YOUR_PROJECT/scripts/modules/
cp -r scripts/modules/validators YOUR_PROJECT/scripts/modules/
cp scripts/modules/horizontal_table_parser_v2.py YOUR_PROJECT/scripts/modules/
```

### Step 2: 修改导入路径（如果需要）

在你的代码中：

```python
# 导入新架构的模块
from scripts.modules.extractors.route_extractor_v2 import RouteExtractorV2
from scripts.modules.extractors.agent_extractor_v2 import AgentExtractorV2
from scripts.modules.assembler.data_assembler import DataAssembler
from scripts.modules.horizontal_table_parser_v2 import HorizontalTableParserV2
```

### Step 3: 开始使用

```python
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建解析器
parser = HorizontalTableParserV2(
    enable_llm=False,  # 不使用LLM
    logger=logger,
    output_dir='data/clean'
)

# 解析Excel
result = parser.parse_excel('your_file.xlsx')

# 查看结果
print(f"Routes: {len(result['routes'])}")
print(f"Agents: {len(result['agents'])}")
```

---

## 📁 文件对应关系

### 核心文件（必须复制）

```
new_architecture/                    →  YOUR_PROJECT/
├── scripts/modules/extractors/      →  scripts/modules/extractors/
│   ├── __init__.py                  →  （必须）
│   ├── base_extractor.py            →  （必须，基础抽象类）
│   ├── route_extractor_v2.py        →  （必须，路线提取）
│   └── agent_extractor_v2.py        →  （必须，代理提取）
│
├── scripts/modules/assembler/       →  scripts/modules/assembler/
│   ├── __init__.py                  →  （必须）
│   └── data_assembler.py            →  （必须，数据组装）
│
├── scripts/modules/validators/      →  scripts/modules/validators/
│   ├── __init__.py                  →  （可选）
│   ├── route_validator.py           →  （可选，但推荐）
│   └── agent_validator.py           →  （可选，但推荐）
│
└── scripts/modules/                 →  scripts/modules/
    └── horizontal_table_parser_v2.py →  （必须，主解析器）
```

### 现有文件（保持不变）

这些文件被新架构复用，不需要修改：

```
YOUR_PROJECT/
├── scripts/data/
│   └── location_whitelist.py        ← 保持不变（被route_extractor_v2使用）
│
└── scripts/modules/
    ├── route_extractor.py           ← 保持不变（被route_extractor_v2复用）
    ├── route_normalizer.py          ← 保持不变
    ├── fee_parser.py                ← 保持不变
    └── llm_enhancer.py              ← 保持不变
```

---

## 🔧 集成方式

### 方式1: 完全替换（推荐）

创建新的入口脚本：

```python
# scripts/dryrun_v2.py
"""
新架构的dryrun脚本
"""
import logging
from modules.horizontal_table_parser_v2 import HorizontalTableParserV2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/parser_v2.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建解析器
parser = HorizontalTableParserV2(
    enable_llm=False,
    logger=logger,
    output_dir='data/clean'
)

# 解析Excel
result = parser.parse_excel('data/raw/your_file.xlsx')

print(f"\n✅ 解析完成:")
print(f"  Routes: {len(result['routes'])}")
print(f"  Agents: {len(result['agents'])}")
print(f"  验证错误: {len(result.get('validation_errors', []))}")
```

### 方式2: 渐进式迁移

保留旧代码，逐步迁移：

```python
# 方式2a: 只使用新的提取器，保留旧的组装逻辑
from extractors.route_extractor_v2 import RouteExtractorV2
from extractors.agent_extractor_v2 import AgentExtractorV2

route_extractor = RouteExtractorV2()
agent_extractor = AgentExtractorV2()

# ... 使用旧的组装逻辑

# 方式2b: 对比新旧结果
result_old = old_parser.parse_excel(file)
result_new = new_parser.parse_excel(file)

# 对比差异
compare_results(result_old, result_new)
```

---

## ⚙️ 配置说明

### 1. 日志配置

```python
import logging

# 基础配置
logging.basicConfig(
    level=logging.INFO,  # 级别：DEBUG/INFO/WARNING/ERROR
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/parser.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 创建logger
logger = logging.getLogger('my_parser')

# 传给解析器
parser = HorizontalTableParserV2(logger=logger)
```

**日志级别说明**:
- `DEBUG`: 详细的提取步骤（每个cell的处理）
- `INFO`: 主要流程（sheet处理，提取成功/失败）
- `WARNING`: 警告信息（验证失败，使用默认值）
- `ERROR`: 错误信息（LLM调用失败，异常）

### 2. LLM配置（可选）

如果要启用LLM功能：

```python
# 创建LLM客户端（示例）
class SimpleLLMClient:
    def __init__(self, api_key):
        self.api_key = api_key
        # 初始化LLM SDK
    
    def generate(self, prompt):
        # 调用LLM API
        # 返回生成的文本
        pass

# 使用
llm_client = SimpleLLMClient(api_key="your-api-key")

parser = HorizontalTableParserV2(
    enable_llm=True,
    llm_client=llm_client,
    logger=logger
)
```

### 3. 输出目录配置

```python
parser = HorizontalTableParserV2(
    output_dir='data/clean'  # JSON文件保存位置
)

# 会创建：
# - data/clean/routes.json
# - data/clean/route_agents.json
# - （其他JSON文件）
```

---

## ✅ 验证部署

### 1. 运行测试

```python
# test_new_architecture.py
import logging
from modules.horizontal_table_parser_v2 import HorizontalTableParserV2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 测试解析器
parser = HorizontalTableParserV2(logger=logger)

# 使用测试文件
result = parser.parse_excel('test_data.xlsx')

# 验证结果
assert len(result['routes']) > 0, "没有提取到routes"
assert len(result['agents']) > 0, "没有提取到agents"

print("✅ 测试通过")
```

### 2. 检查输出文件

```bash
# 检查routes数量
python3 -c "
import json
routes = json.load(open('data/clean/routes.json'))
print(f'Routes: {len(routes)}')
"

# 检查agents数量
python3 -c "
import json
agents = json.load(open('data/clean/route_agents.json'))
print(f'Agents: {len(agents)}')
"

# 检查关联正确性
python3 -c "
import json
routes = json.load(open('data/clean/routes.json'))
agents = json.load(open('data/clean/route_agents.json'))

route_ids = {r['路线ID'] for r in routes}
for agent in agents:
    if agent['路线ID'] not in route_ids:
        print(f'错误: Agent {agent[\"代理商\"]} 的路线ID不存在')
"
```

### 3. 对比新旧结果

```python
# compare_results.py
import json

# 加载新旧结果
routes_old = json.load(open('data/clean/routes_old.json'))
routes_new = json.load(open('data/clean/routes.json'))

print(f"旧架构: {len(routes_old)} routes")
print(f"新架构: {len(routes_new)} routes")
print(f"增加: {len(routes_new) - len(routes_old)} routes")

# 检查每个route
for r_new in routes_new:
    found = False
    for r_old in routes_old:
        if (r_new['起始地'] == r_old['起始地'] and 
            r_new['目的地'] == r_old['目的地']):
            found = True
            break
    
    if not found:
        print(f"新增route: {r_new['起始地']} → {r_new['目的地']}")
```

---

## 🐛 常见问题

### Q1: 导入错误：ModuleNotFoundError

**问题**:
```
ModuleNotFoundError: No module named 'extractors'
```

**解决**:
```python
# 方式1: 修改sys.path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

# 方式2: 使用绝对导入
from scripts.modules.extractors.route_extractor_v2 import RouteExtractorV2
```

### Q2: location_whitelist找不到

**问题**:
```
ImportError: cannot import name 'is_valid_location'
```

**解决**:
确保你的项目有`scripts/data/location_whitelist.py`文件，这是现有文件，应该已经存在。

### Q3: 结果与预期不符

**调试步骤**:

```python
# 1. 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 2. 查看提取器统计
stats = parser.route_extractor.get_stats()
print(f"规则成功率: {stats['rule_success']/stats['total_attempts']*100:.1f}%")

# 3. 查看验证错误
errors = result.get('validation_errors', [])
for error in errors:
    print(error)
```

---

## 📊 性能优化

### 1. 禁用不需要的功能

```python
# 如果不需要验证器
parser = HorizontalTableParserV2(
    enable_llm=False,  # 禁用LLM
)

# 设置日志级别为WARNING（减少日志输出）
logging.basicConfig(level=logging.WARNING)
```

### 2. 批量处理

```python
# 处理多个文件
files = ['file1.xlsx', 'file2.xlsx', 'file3.xlsx']

parser = HorizontalTableParserV2()

for file in files:
    result = parser.parse_excel(file)
    # 处理结果...
```

---

## 🎯 完成检查清单

部署完成后，检查以下项目：

- [ ] 所有核心文件已复制到项目
- [ ] 导入路径正确
- [ ] 日志配置正确
- [ ] 输出目录存在
- [ ] 测试文件解析成功
- [ ] 输出JSON文件格式正确
- [ ] Routes数量符合预期
- [ ] Agents数量符合预期
- [ ] 关联正确（agent.路线ID存在于routes中）
- [ ] 统计信息正确

---

## 📞 获取帮助

如遇问题：

1. 查看代码注释（所有文件都有详细注释）
2. 查看CODE_GUIDE.md（详细文档）
3. 查看example_usage.py（完整示例）
4. 启用DEBUG日志查看详细信息

---

**祝部署顺利！** 🎉
