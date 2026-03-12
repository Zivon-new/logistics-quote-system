# scripts/config.py
"""
项目配置文件

【重要】
1. 将你的智谱API Key填入 ZHIPU_API_KEY
2. 或者设置环境变量 ZHIPU_API_KEY
"""

import os


class Config:
    """项目配置"""
    
    # ========== LLM配置 ==========
    
    # 智谱AI API Key（必填，如果要使用LLM功能）
    # 获取方式：https://open.bigmodel.cn/
    # ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY', '')  # 从环境变量读取
    # 或者直接填写：
    ZHIPU_API_KEY = 'f38983f5cc154ce49cc076eb371e633a.YzSU0QOxagEMxyFb'
    
    # 是否启用LLM增强
    # ⚠️ 智谱API偶尔不稳定，如遇问题请改为False临时禁用
    ENABLE_LLM_ENHANCE = True
    
    # LLM模型
    LLM_MODEL = 'glm-4.7'  # 快速、便宜、够用
    # 其他选项：'glm-4' (更强但更贵)
    
    # LLM温度（控制随机性）
    LLM_TEMPERATURE = 0.1  # 低温度=更确定的结果
    
    # LLM最大token数
    # 全量提取模式需要更多token，建议4000
    LLM_MAX_TOKENS = 4000
    
    # LLM超时设置（秒）
    LLM_TIMEOUT = 60  # 单次调用最长等待60秒
    
    # LLM重试次数（默认3次，可根据API稳定性调整）
    LLM_MAX_RETRIES = 3  # 增加到5会更稳定但更慢
    
    # ========== 数据路径 ==========
    
    # 原始数据目录
    RAW_DATA_DIR = 'data/raw'
    
    # 清洗后数据目录
    CLEAN_DATA_DIR = 'data/clean'
    
    # 日志目录
    LOG_DIR = 'logs'
    
    # ========== 币种配置 ==========
    
    CURRENCY_ALIAS = {
        'RMB': 'RMB',
        'CNY': 'RMB',
        '元': 'RMB',
        '¥': 'RMB',
        'USD': 'USD',
        '美元': 'USD',
        '$': 'USD',
        'EUR': 'EUR',
        '欧元': 'EUR',
        '€': 'EUR'
    }
    
    # ========== 提取器配置 ==========

    # Agent提取质量阈值（低于此值会调用LLM增强）
    AGENT_QUALITY_THRESHOLD = 0.7

    # Route提取质量阈值
    ROUTE_QUALITY_THRESHOLD = 1.0  # Route使用二元评估，所以是1.0

    # Sheet格式置信度阈值
    # 低于此值视为"格式混乱"，直接走LLM全量提取（而不是规则+LLM打补丁）
    # 取值范围：0.0-1.0，越高越严格
    UNSTRUCTURED_FORMAT_THRESHOLD = 0.5
    
    # ========== 日志配置 ==========
    
    LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


# ========== 便捷函数 ==========

def get_zhipu_api_key():
    """获取智谱API Key"""
    key = Config.ZHIPU_API_KEY
    
    if not key:
        raise ValueError(
            "未配置智谱API Key！\n"
            "请在 scripts/config.py 中设置 ZHIPU_API_KEY\n"
            "或设置环境变量: export ZHIPU_API_KEY='your_key'"
        )
    
    return key


def is_llm_enabled():
    """检查LLM是否启用"""
    return Config.ENABLE_LLM_ENHANCE and bool(Config.ZHIPU_API_KEY)


# ========== 导出 ==========

__all__ = ['Config', 'get_zhipu_api_key', 'is_llm_enabled']