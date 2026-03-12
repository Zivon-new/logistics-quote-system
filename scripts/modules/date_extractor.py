# scripts/modules/date_extractor.py
"""
日期提取器
从文件名中提取交易日期

【支持的日期格式】
1. 2025.10.20-2025.10.24
2. 2025-10-20-2025-10-24
3. 20251020-20251024
4. 2025年10月20日-2025年10月24日
"""

import re
from datetime import datetime
from typing import Optional, Tuple


def extract_dates_from_filename(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    从文件名中提取交易开始日期和结束日期
    
    Args:
        filename: 文件名（如：国际部成本汇总2025.10.20-2025.10.24.xlsx）
    
    Returns:
        (start_date, end_date) 格式为 YYYY-MM-DD，如果提取失败返回 (None, None)
    
    Examples:
        >>> extract_dates_from_filename("国际部成本汇总2025.10.20-2025.10.24.xlsx")
        ('2025-10-20', '2025-10-24')
        
        >>> extract_dates_from_filename("报价单2025-01-15-2025-01-20.xlsx")
        ('2025-01-15', '2025-01-20')
    """
    
    # 模式1: YYYY.MM.DD-YYYY.MM.DD 或 YYYY-MM-DD-YYYY-MM-DD
    pattern1 = r'(\d{4})[.-](\d{1,2})[.-](\d{1,2})[.-](\d{4})[.-](\d{1,2})[.-](\d{1,2})'
    match = re.search(pattern1, filename)
    if match:
        year1, month1, day1, year2, month2, day2 = match.groups()
        try:
            start_date = f"{year1}-{int(month1):02d}-{int(day1):02d}"
            end_date = f"{year2}-{int(month2):02d}-{int(day2):02d}"
            
            # 验证日期有效性
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
            
            return (start_date, end_date)
        except ValueError:
            pass
    
    # 模式2: YYYYMMDD-YYYYMMDD
    pattern2 = r'(\d{8})-(\d{8})'
    match = re.search(pattern2, filename)
    if match:
        date1_str, date2_str = match.groups()
        try:
            start_date = datetime.strptime(date1_str, '%Y%m%d').strftime('%Y-%m-%d')
            end_date = datetime.strptime(date2_str, '%Y%m%d').strftime('%Y-%m-%d')
            return (start_date, end_date)
        except ValueError:
            pass
    
    # 模式3: YYYY年MM月DD日-YYYY年MM月DD日
    pattern3 = r'(\d{4})年(\d{1,2})月(\d{1,2})日[至到-](\d{4})年(\d{1,2})月(\d{1,2})日'
    match = re.search(pattern3, filename)
    if match:
        year1, month1, day1, year2, month2, day2 = match.groups()
        try:
            start_date = f"{year1}-{int(month1):02d}-{int(day1):02d}"
            end_date = f"{year2}-{int(month2):02d}-{int(day2):02d}"
            
            # 验证日期有效性
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
            
            return (start_date, end_date)
        except ValueError:
            pass
    
    # 没有找到有效日期
    return (None, None)


def format_date_for_db(date_str: Optional[str]) -> Optional[str]:
    """
    格式化日期为数据库格式（YYYY-MM-DD）
    
    Args:
        date_str: 日期字符串
    
    Returns:
        格式化后的日期字符串，或None
    """
    if not date_str:
        return None
    
    # 已经是YYYY-MM-DD格式
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    
    # 尝试其他格式
    formats = [
        '%Y/%m/%d',
        '%Y.%m.%d',
        '%Y%m%d',
        '%Y年%m月%d日'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None


# 测试代码
if __name__ == '__main__':
    test_filenames = [
        "国际部成本汇总2025.10.20-2025.10.24.xlsx",
        "报价单2025-01-15-2025-01-20.xlsx",
        "成本表20251020-20251024.xlsx",
        "报价2025年10月20日-2025年10月24日.xlsx",
        "无日期文件.xlsx"
    ]
    
    for filename in test_filenames:
        start, end = extract_dates_from_filename(filename)
        print(f"{filename}")
        print(f"  开始: {start}, 结束: {end}\n")