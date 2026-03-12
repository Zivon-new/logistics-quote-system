# 冗余代码清理说明

## 🗑️ 可删除的冗余文件

### 旧架构文件（已被新架构替代）

| 文件名 | 说明 | 替代方案 |
|--------|------|---------|
| horizontal_table_parser.py | 旧的主解析器 | horizontal_table_parser_v2.py |
| block_parser.py | 旧的block解析器 | 新架构不使用block概念 |
| block_splitter.py | 旧的block分割器 | 新架构不使用block概念 |
| route_blocks_detector.py | 旧的route block检测器 | 新架构不使用block概念 |
| route_detector.py | 旧的route检测器 | route_extractor_v2.py |
| route_fields_enhancer.py | 旧的route字段增强器 | route_extractor_v2.py |
| agent_parser.py | 旧的agent解析器 | agent_extractor_v2.py |
| test_zhipu_api.py | 测试文件 | 可删除 |

**总计**: 8个文件

---

## ✅ 保留的文件

### 核心文件（新架构需要）

**提取器**:
- `extractors/base_extractor.py` - 基础提取器
- `extractors/route_extractor_v2.py` - 路线提取器
- `extractors/agent_extractor_v2.py` - 代理提取器

**组装器**:
- `assembler/data_assembler.py` - 数据组装器

**验证器**:
- `validators/route_validator.py` - 路线验证器
- `validators/agent_validator.py` - 代理验证器

**主解析器**:
- `horizontal_table_parser_v2.py` - 主解析器v2

### 支持文件（被新架构复用）

- `route_extractor.py` - 被route_extractor_v2复用（保留）
- `route_normalizer.py` - 路线标准化（保留）
- `text_cleaner.py` - 文本清理（保留）

### 功能解析器（需要继续使用）

- `fee_parser.py` - 费用解析器
- `goods_parser.py` - 货物解析器
- `goods_table_detector.py` - 货物表检测器
- `summary_parser.py` - 汇总解析器
- `sheet_goods_scanner.py` - sheet货物扫描器
- `llm_enhancer.py` - LLM增强器

---

## 📦 建议操作

### 方案1: 移动到archived目录（推荐）
```bash
# 创建归档目录
mkdir -p scripts/modules/archived

# 移动旧文件
mv scripts/modules/horizontal_table_parser.py scripts/modules/archived/
mv scripts/modules/block_parser.py scripts/modules/archived/
mv scripts/modules/block_splitter.py scripts/modules/archived/
mv scripts/modules/route_blocks_detector.py scripts/modules/archived/
mv scripts/modules/route_detector.py scripts/modules/archived/
mv scripts/modules/route_fields_enhancer.py scripts/modules/archived/
mv scripts/modules/agent_parser.py scripts/modules/archived/
mv scripts/modules/test_zhipu_api.py scripts/modules/archived/
```

### 方案2: 直接删除
```bash
# 删除旧文件（谨慎！）
rm scripts/modules/horizontal_table_parser.py
rm scripts/modules/block_parser.py
rm scripts/modules/block_splitter.py
rm scripts/modules/route_blocks_detector.py
rm scripts/modules/route_detector.py
rm scripts/modules/route_fields_enhancer.py
rm scripts/modules/agent_parser.py
rm scripts/modules/test_zhipu_api.py
```

---

## 🔍 清理后的目录结构

```
scripts/modules/
├── extractors/                    # 新架构：独立提取器
│   ├── base_extractor.py
│   ├── route_extractor_v2.py
│   └── agent_extractor_v2.py
│
├── assembler/                     # 新架构：数据组装器
│   └── data_assembler.py
│
├── validators/                    # 新架构：验证器
│   ├── route_validator.py
│   └── agent_validator.py
│
├── horizontal_table_parser_v2.py  # 新架构：主解析器
│
├── route_extractor.py             # 保留：被v2复用
├── route_normalizer.py            # 保留：标准化
├── text_cleaner.py                # 保留：文本清理
│
├── fee_parser.py                  # 保留：费用解析
├── goods_parser.py                # 保留：货物解析
├── goods_table_detector.py        # 保留：货物表检测
├── summary_parser.py              # 保留：汇总解析
├── sheet_goods_scanner.py         # 保留：货物扫描
└── llm_enhancer.py                # 保留：LLM增强

archived/                          # 归档：旧代码（可选）
├── horizontal_table_parser.py
├── block_parser.py
├── block_splitter.py
├── route_blocks_detector.py
├── route_detector.py
├── route_fields_enhancer.py
├── agent_parser.py
└── test_zhipu_api.py
```

---

## ⚠️ 注意事项

1. **检查依赖**: 删除前确认没有其他文件引用这些旧文件
2. **测试验证**: 删除后运行测试确保系统正常
3. **建议备份**: 先移动到archived目录，确认无误后再删除

---

**更新时间**: 2026-01-22
