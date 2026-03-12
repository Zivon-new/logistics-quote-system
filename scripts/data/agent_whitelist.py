# scripts/data/agent_whitelist.py
"""
物流代理商白名单 v1.1

【用途】
验证提取的代理商名称是否有效

【命名规则】
- 只包含代理商主体名称
- 不包含备注、方案说明等
- 支持简称和全称

【更新方式】
发现新的有效代理商时，添加到此白名单
"""

AGENT_WHITELIST = {
    # ========== 大型物流公司 ==========
    "融迅", "融迅物流",
    "银顺达", "银顺达物流",
    "根顺达", "根顺达物流",  # ← 新增
    "嘉里", "嘉里物流", "嘉里大通",
    "多信达", "多信达物流",  # ← 移到这里
    "DHL", "DHL国际", "敦豪",
    "UPS", "UPS国际",
    "FedEx", "联邦快递",
    "TNT", "TNT快递",
    "顺丰", "顺丰速运", "顺丰国际",
    "中通", "中通国际",
    "圆通", "圆通速递",
    "申通", "申通快递",
    "韵达", "韵达快递",
    "EMS", "中国邮政",
    
    # ========== 海运专线公司 ==========
    "澳凯", "澳凯物流",
    "蓝鹰", "蓝鹰物流",
    "越海", "越海速达", "越海专线",
    "海阳", "海阳中港", "海阳物流",
    "骐盛", "骐盛物流",
    "拓宇", "拓宇物流",
    "雄展", "雄展货运",
    "启文", "启文物流",
    "华平", "华平物流", "华平专线",
    "彩鹤", "彩鹤物流",  # ← 新增
    
    # ========== 区域专线 ==========
    "欧洲专线", "欧洲专线集团",
    "美国专线",
    "日本专线",
    "东南亚专线",
    "中东专线",
    "澳洲专线",
    
    # ========== 综合物流 ==========
    "一诺", "一诺物流",
    "安达", "安达物流",
    "通达", "通达物流",
    
    # ========== 国际知名货代 ==========
    "马士基", "Maersk",
    "中远", "COSCO",
    "长荣", "Evergreen",
    "阳明", "YangMing",
    "赫伯罗特", "Hapag-Lloyd",
    "达飞", "CMA-CGM",
    "地中海航运", "MSC",
    "汉堡南美", "Hamburg Sud",
    
    # ========== 航空货代 ==========
    "中国国航", "国航货运", "Air China",
    "东方航空", "东航货运", "China Eastern",
    "南方航空", "南航货运", "China Southern",
    "海南航空", "海航货运",
    "国泰", "国泰航空", "Cathay Pacific",
    "新加坡航空", "Singapore Airlines",
    "阿联酋航空", "Emirates", "EK",
    "汉莎", "汉莎航空", "Lufthansa",
    "法航", "法国航空", "Air France",
    
    # ========== 综合服务商 ==========
    "德邦", "德邦物流",
    "安能", "安能物流",
    "天地华宇",
    "佳吉", "佳吉物流",
    "远成", "远成物流",
    "华宇", "华宇物流",
    "盛辉", "盛辉物流",
    "佳怡", "佳怡物流",
    
    # ========== 跨境电商物流 ==========
    "万色", "万色速递",
    "递四方", "4PX",
    "云途", "云途物流",
    "出口易",
    "俄速通",
    "燕文", "燕文物流",
    
    # ========== 其他常见代理 ==========
    "中外运", "中外运敦豪", "Sinotrans",
    "宝供", "宝供物流",
    "招商局", "招商物流",
    "中铁", "中铁快运",
    "海晨", "海晨物流",
    "万邦", "万邦物流",
    "飞力达",
    "嘉宏", "嘉宏物流",
}

# 无效关键词（用于过滤纯描述性文本，不是代理商名）
# 注意：这些关键词只在文本中【单独出现】或【完全匹配】时才过滤
# 不会过滤"银顺达--专线方案"这种有代理商名的情况
INVALID_AGENT_KEYWORDS = {
    # 纯方案类（没有代理商名）
    "双清方案", "包税方案", "贸代方案", "一般贸易过港",
    
    # 说明类
    "询价", "预估", "待定", "确认",
    
    # 纯业务类型（没有代理商名）
    "一般贸易", "快件", "集运", "拼箱", "整柜", "散货",
    
    # 数字和符号
    "USD", "RMB", "CNY", "EUR", "GBP",
    "/票", "/kg", "/cbm", "/柜",
    
    # 常见无效词
    "如果", "需要", "可以",
}

def is_valid_agent_name(name: str) -> bool:
    """
    判断是否是有效的代理商名称
    
    Args:
        name: 代理商名称
    
    Returns:
        True/False
    """
    if not name or not isinstance(name, str):
        return False
    
    name = name.strip()
    
    # 长度检查
    if len(name) < 2 or len(name) > 50:
        return False
    
    # 纯数字
    if name.isdigit():
        return False
    
    # 先检查是否在白名单中
    for agent in AGENT_WHITELIST:
        if name == agent or name.startswith(agent):
            return True
    
    # 如果不在白名单中，检查是否是纯无效关键词
    for keyword in INVALID_AGENT_KEYWORDS:
        if name == keyword:  # 完全匹配才过滤
            return False
    
    # 不在白名单中，返回False（严格模式）
    return False


def extract_agent_name_and_remark(text: str) -> tuple:
    """
    从文本中分离代理商名称和备注
    
    分离规则：
    - "融迅-快递+贸代方案" → ("融迅", "快递+贸代方案")
    - "澳凯-海运专线" → ("澳凯", "海运专线")
    - "华平  专线   协议过期" → ("华平", "专线 协议过期")
    - "根顺达--仅合作快运" → ("根顺达", "仅合作快运")
    
    Args:
        text: 包含代理商名和备注的文本
    
    Returns:
        (agent_name, remark) 元组
    """
    if not text:
        return (None, None)
    
    text = text.strip()
    
    # 方法1: 使用"-"、"--"、"——"分隔
    if '-' in text or '—' in text or '－' in text:
        # 统一替换为单个"-"
        normalized = text.replace('——', '-').replace('--', '-').replace('—', '-').replace('－', '-')
        parts = normalized.split('-', 1)
        if len(parts) == 2:
            agent_name = parts[0].strip()
            remark = parts[1].strip()
            
            # 验证agent_name是否在白名单
            if agent_name in AGENT_WHITELIST:
                return (agent_name, remark)
    
    # 方法2: 使用空格分隔（多个空格）
    if '  ' in text:  # 至少2个空格
        parts = text.split(None, 1)  # split(None)会按任意空白分割
        if len(parts) == 2:
            agent_name = parts[0].strip()
            remark = parts[1].strip()
            
            # 验证agent_name是否在白名单
            if agent_name in AGENT_WHITELIST:
                return (agent_name, remark)
    
    # 方法3: 找到白名单中的代理商，剩余部分作为备注
    for agent in sorted(AGENT_WHITELIST, key=len, reverse=True):  # 从长到短匹配
        if text.startswith(agent):
            remark = text[len(agent):].strip()
            remark = remark.lstrip('-—－:：').strip()  # 去除开头的分隔符
            if remark:
                return (agent, remark)
            else:
                return (agent, None)
    
    # 无法分离，返回原文作为代理商名
    return (text, None)


# 测试代码
if __name__ == '__main__':
    test_cases = [
        "融迅",
        "融迅-快递+贸代方案",
        "银顺达--专线方案",
        "银顺达--快递方案",
        "根顺达--仅合作快运，不合作红专线",
        "欧洲专线集团",
        "多信达",
        "澳凯-海运专线",
        "华平  专线   协议过期，未合作过",
        "一诺物流-新代理，未合作",
        "一般贸易过港+双清方案",  # 应该被过滤
        "USD100/票",  # 应该被过滤
        "如果需要",  # 应该被过滤
        "100",  # 应该被过滤
    ]
    
    print("🧪 测试代理商名称提取和验证:\n")
    for text in test_cases:
        agent_name, remark = extract_agent_name_and_remark(text)
        is_valid = is_valid_agent_name(agent_name) if agent_name else False
        
        print(f"原文: {text}")
        print(f"  → 代理商: {agent_name}")
        print(f"  → 备注: {remark}")
        print(f"  → 有效: {'✅' if is_valid else '❌'}")
        print()