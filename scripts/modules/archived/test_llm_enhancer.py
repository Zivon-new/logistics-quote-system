#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试LLM增强器功能
在集成到主流程前，先单独测试LLM模块
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.modules.llm_enhancer import LLMEnhancer

# ============================================================
# 配置API Key
# ============================================================
API_KEY = "f38983f5cc154ce49cc076eb371e633a.YzSU0QOxagEMxyFb"  # 替换成你的密钥
# ============================================================

if API_KEY == "your-api-key-here":
    print("❌ 请先配置API Key!")
    exit(1)

print("=" * 60)
print("测试LLM增强器")
print("=" * 60)

# 初始化
print("\n[1] 初始化LLM增强器...")
llm = LLMEnhancer(api_key=API_KEY)
print("✅ 初始化成功")

# 测试1: 提取代理商信息
print("\n" + "=" * 60)
print("[2] 测试代理商信息提取")
print("=" * 60)

test_text_1 = """
深圳市融迅国际货运代理有限公司
运输方式：海运
贸易条款：DDP
时效：5-7个工作日
不含目的港清关费和关税
提供货物保险和理赔服务
"""

print(f"\n测试文本:\n{test_text_1}")
print("\n正在调用LLM...")

result = llm.extract_agent_info(test_text_1)

if result:
    print("\n✅ 提取成功!")
    print("\n提取结果:")
    for key, value in result.items():
        print(f"  {key}: {value}")
else:
    print("\n❌ 提取失败")

# 测试2: 复杂case
print("\n" + "=" * 60)
print("[3] 测试复杂格式")
print("=" * 60)

test_text_2 = """
客户指定代理：XX物流
空运服务
时效大约3-5天
本报价不包含：
- 目的港清关费
- 目的港派送费
- 关税和增值税
"""

print(f"\n测试文本:\n{test_text_2}")
print("\n正在调用LLM...")

result2 = llm.extract_agent_info(test_text_2)

if result2:
    print("\n✅ 提取成功!")
    print("\n提取结果:")
    for key, value in result2.items():
        print(f"  {key}: {value}")
else:
    print("\n❌ 提取失败")

# 打印统计
print("\n" + "=" * 60)
print("[4] 使用统计")
print("=" * 60)
llm.print_stats()

print("\n" + "=" * 60)
print("✅ 测试完成!")
print("=" * 60)
print("\n下一步:")
print("1. 如果测试成功，可以集成到主流程")
print("2. 将 llm_enhancer.py 复制到 scripts/modules/")
print("3. 修改 dryrun_horizontal_parser.py 集成LLM")
print("=" * 60)