#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试智谱API - 简化版
运行: python test_api_simple.py
"""

from zhipuai import ZhipuAI

# ============================================================
# 在这里填写你的API Key
# ============================================================
API_KEY = "f38983f5cc154ce49cc076eb371e633a.YzSU0QOxagEMxyFb"  # 替换成你的密钥
# ============================================================

if API_KEY == "your-api-key-here":
    print("[ERROR] 请先配置API Key!")
    print("\n步骤:")
    print("1. 访问: https://open.bigmodel.cn/")
    print("2. 获取API Key")
    print("3. 替换上面的 'your-api-key-here'")
    exit(1)

print("正在测试API连接...")
print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]}")

try:
    client = ZhipuAI(api_key=API_KEY)
    
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=[{"role": "user", "content": "你好"}],
    )
    
    print("\n[OK] API连接成功!")
    print(f"[NOTE] 回复: {response.choices[0].message.content}")
    print(f" Token: {response.usage.total_tokens}")
    print("\n 可以开始开发了!")
    
except Exception as e:
    print(f"\n[ERROR] 连接失败: {e}")
    print("\n请检查:")
    print("1. API Key是否正确")
    print("2. 网络是否正常")