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
    "阿联酋航空", "Emirates",
    # 注：EK 是航司代码（不是代理商名），出现在 "BY HK EK Q45..." 等航班代码中，不纳入白名单
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

    # 服务类型描述（不是公司名）
    "空运专线", "海运专线", "空派专线",

    # 说明类
    "询价", "预估", "待定", "确认",
    
    # 纯业务类型（没有代理商名）
    "一般贸易", "快件", "集运", "拼箱", "整柜", "散货",
    
    # 数字和符号
    "USD", "RMB", "CNY", "EUR", "GBP",
    "/票", "/kg", "/cbm", "/柜",
    
    # 常见无效词
    "如果", "需要", "可以",

    # 状态/备注类（只在单独出现时无效，不应作为子串过滤公司名+备注格式）
    "新代理", "仅合作", "未合作", "暂无", "暂未", "展会新加",
}

# 常见城市名 — 这些是地名而非代理商名，直接拒绝
KNOWN_CITIES = {
    '深圳', '北京', '上海', '广州', '香港', '天津', '成都', '武汉', '杭州', '南京',
    '青岛', '大连', '宁波', '厦门', '苏州', '重庆', '西安', '昆明', '郑州', '福州',
    '澳门', '台北', '台湾', '新加坡', '曼谷', '马尼拉', '雅加达', '吉隆坡', '河内',
    '仁川', '东京', '大阪', '法兰克福', '鹿特丹', '安特卫普', '阿姆斯特丹', '达拉斯',
    '洛杉矶', '纽约', '芝加哥', '多伦多', '悉尼', '墨尔本', '迪拜', '开罗',
}


def is_valid_agent_name(name: str) -> bool:
    """
    判断是否是有效的代理商名称

    Returns:
        True = 可能是代理商名；False = 明确不是代理商名
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

    # 先检查白名单（高优先级，直接返回 True）
    for agent in AGENT_WHITELIST:
        if name == agent or name.startswith(agent):
            return True

    # 已知城市名 — 地名不是代理商
    if name in KNOWN_CITIES:
        return False

    # 精确无效关键词
    for keyword in INVALID_AGENT_KEYWORDS:
        if name == keyword:
            return False

    # 含空格的多词短语通常是句子片段
    # - 双空格：明确的格式问题
    # - 中文名称含空格：中文公司名不用空格分词（英文名如"Air China"已在白名单）
    if '  ' in name:
        return False
    import re as _re
    if ' ' in name and bool(_re.search(r'[一-鿿]', name)):
        return False

    # 算术/数量表达式：含 '+' 且有数字 → 货物规格描述（如"2pa防火墙+5交换机+模块"）
    if '+' in name and bool(_re.search(r'\d', name)):
        return False

    import re
    has_chinese = bool(re.search(r'[一-鿿]', name))
    # 价格检测：支持 "USD100/票" 和 "100USD" 两种顺序
    is_price = bool(re.search(
        r'(USD|RMB|CNY|EUR|GBP|SGD)\s*\d+|\d+\s*(USD|RMB|CNY|EUR|GBP|SGD|/kg|/cbm|/票)',
        name, re.IGNORECASE
    ))

    # 描述性关键词：包含这些关键词的文本不是代理商名
    # 注意：只放"不可能出现在公司名中间"的词。
    # 备注类词（如'新代理'/'仅合作'）已移至 INVALID_AGENT_KEYWORDS（精确匹配），
    # 避免误杀"東捷運通-新代理"这类"公司名-备注"格式。
    is_description = any(kw in name for kw in [
        # 贸易模式
        '方案', '询价', '预估', '待定', '过港', '包税', '双清', '含税', '正清', '贸代', '纯正清',
        # 财务说明
        '缴税', '核算', '货值', '税率',
        # 有效期 / 时间性描述
        '有效',
        # 标签/标题
        '货物信息', '物流指定', '运输信息',
        # 服务类型描述（非公司名）
        '贸易代理',
        # 建议/说明类
        '不建议', '建议使用', '更新',
    ])

    # 注释类开头词（如果、如确认、不建议、已含等）
    note_starters = ('已', '不', '如', '可', '请', '需', '按', '约', '待', '此')
    if name[:1] in note_starters:
        # 短文本（≤6字）：明显的注释词
        # 长文本（>6字）：几乎不可能是公司名
        if len(name) <= 6 or len(name) >= 8:
            return False

    # 尾缀"有效" — 几乎不出现在公司名中
    if name.endswith('有效'):
        return False

    if has_chinese and not is_price and not is_description:
        if 2 <= len(name) <= 20:
            return True

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

            # 白名单直接确认
            if agent_name in AGENT_WHITELIST:
                return (agent_name, remark)

            # 非白名单：若名字部分看起来像公司名，也做拆分
            # 条件：含中文字符、合理长度、不含纯描述性词汇
            import re as _re
            if (2 <= len(agent_name) <= 20 and
                    bool(_re.search(r'[一-鿿]', agent_name)) and
                    not any(kw in agent_name for kw in ['方案', '过港', '双清', '包税', '正清', '缴税'])):
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