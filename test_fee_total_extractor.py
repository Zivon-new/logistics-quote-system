#!/usr/bin/env python3
# 测试FeeTotalExtractor

import sys
import openpyxl

# 添加路径
sys.path.insert(0, 'scripts/modules/extractors')
sys.path.insert(0, 'scripts/modules')
sys.path.insert(0, 'scripts')

from scripts.modules.extractors.fee_total_extractor import FeeTotalExtractor

# 加载Excel
wb = openpyxl.load_workbook(r'data\raw\国际部成本汇总2025.10.20-2025.10.24.xlsx')

# 创建提取器
extractor = FeeTotalExtractor()

# 测试前3个sheet
for sheet_idx in range(min(3, len(wb.worksheets))):
    sheet = wb.worksheets[sheet_idx]
    print(f"\n{'='*60}")
    print(f"Sheet {sheet_idx+1}: {sheet.title}")
    print('='*60)
    
    # 测试前3个agent（列2-4）
    for agent_idx in range(3):
        agent_col_idx = agent_idx + 2
        
        print(f"\n代理 {agent_idx+1} (第{agent_col_idx}列)：")
        
        try:
            # 调用提取器
            fee_totals = extractor._extract_with_rules(sheet, agent_col_idx=agent_col_idx)
            
            print(f"  提取到 {len(fee_totals)} 个整单费用")
            
            for i, ft in enumerate(fee_totals):
                print(f"  {i+1}. 费用名称: {ft.费用名称}, 原币金额: {ft.原币金额}, 币种: {ft.币种}")
        
        except Exception as e:
            print(f"  ❌ 提取失败: {e}")

print(f"\n{'='*60}")
print("测试完成")
print('='*60)