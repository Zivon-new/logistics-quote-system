# test_new_architecture_with_llm.py
"""
新架构测试运行器 - 启用LLM版本

【功能】
1. 使用新架构（BaseExtractor v2.0 + 质量驱动）
2. 启用LLM功能（智谱GLM-4）
3. 完整测试流程
4. 生成详细报告

【使用方法】
python test_new_architecture_with_llm.py
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入配置
from scripts.config import Config

# 导入新架构的解析器
from scripts.modules.horizontal_table_parser_v2 import HorizontalTableParserV2

# 导入LLM增强器
from scripts.modules.llm_enhancer import LLMEnhancer


def setup_logger() -> logging.Logger:
    """设置日志系统"""
    # 创建logs目录
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # 日志文件
    log_file = log_dir / f'test_llm_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"日志文件: {log_file}")
    
    return logger


def test_with_llm(excel_file: str = None, enable_llm: bool = None):
    """
    测试新架构（启用LLM）
    
    Args:
        excel_file: Excel文件路径（如果为None，使用默认测试文件）
        enable_llm: 是否启用LLM功能
    
    Returns:
        测试结果字典
    """
    logger = setup_logger()
    
    # ✅ 如果没有明确指定enable_llm，从config读取
    if enable_llm is None:
        enable_llm = Config.ENABLE_LLM_ENHANCE
        logger.info("=" * 60)
        logger.info("🚀 新架构测试 - LLM状态从config.py读取")
        logger.info("=" * 60)
        logger.info(f"   Config.ENABLE_LLM_ENHANCE = {enable_llm}")
    else:
        logger.info("=" * 60)
        logger.info("🚀 新架构测试 - LLM状态由参数指定")
        logger.info("=" * 60)
        logger.info(f"   enable_llm = {enable_llm}")
    
    # ========== 1. 准备测试文件 ==========
    if not excel_file:
        # 使用默认测试文件
        raw_dir = project_root / 'data' / 'raw'
        
        # 查找Excel文件
        excel_files = list(raw_dir.glob('*.xlsx'))
        if not excel_files:
            logger.error("❌ 在 data/raw/ 目录下没有找到Excel文件")
            return None
        
        # 使用第一个文件
        excel_file = str(excel_files[0])
        logger.info(f"📁 使用测试文件: {Path(excel_file).name}")
    
    # ========== 2. 初始化LLM客户端 ==========
    llm_client = None
    if enable_llm:
        try:
            # 检查API key
            if not hasattr(Config, 'ZHIPU_API_KEY') or not Config.ZHIPU_API_KEY:
                logger.error("❌ 未配置智谱API Key（Config.ZHIPU_API_KEY）")
                logger.info("💡 在 scripts/config.py 中添加:")
                logger.info("   ZHIPU_API_KEY = 'your_api_key_here'")
                enable_llm = False
            else:
                llm_client = LLMEnhancer(api_key=Config.ZHIPU_API_KEY)
                logger.info("✅ LLM增强器初始化成功")
                logger.info(f"   模型: {llm_client.model}")
        except Exception as e:
            logger.error(f"❌ LLM初始化失败: {e}")
            logger.info("💡 请安装: pip install zhipuai")
            enable_llm = False
    
    # ========== 3. 初始化解析器 ==========
    output_dir = project_root / 'data' / 'clean'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("\n" + "=" * 60)
    logger.info("初始化解析器")
    logger.info("=" * 60)
    
    parser = HorizontalTableParserV2(
        enable_llm=enable_llm,
        llm_client=llm_client,
        logger=logger,
        output_dir=str(output_dir),
        excel_filename=excel_file  # ✅ v2.5: 传递文件名以创建子文件夹
    )
    
    logger.info(f"LLM状态: {'✅ 启用' if enable_llm else '❌ 禁用'}")
    logger.info(f"输出目录: {output_dir}")
    
    # ========== 4. 解析Excel ==========
    logger.info("\n" + "=" * 60)
    logger.info("开始解析...")
    logger.info("=" * 60)
    
    try:
        result = parser.parse_excel(excel_file)
        
        # ========== 5. 显示结果 ==========
        logger.info("\n" + "=" * 60)
        logger.info("📊 解析结果")
        logger.info("=" * 60)
        
        routes = result.get('routes', [])
        agents = result.get('route_agents', [])
        errors = result.get('validation_errors', [])
        
        logger.info(f"\n✅ 数据提取:")
        logger.info(f"   Routes: {len(routes)} 条")
        logger.info(f"   Agents: {len(agents)} 个")
        
        if errors:
            logger.info(f"\n⚠️  验证错误:")
            for error in errors[:5]:  # 只显示前5个
                logger.info(f"   - {error}")
            if len(errors) > 5:
                logger.info(f"   ... 还有 {len(errors)-5} 个错误")
        
        # ========== 6. 显示示例数据 ==========
        logger.info(f"\n📍 Routes示例 (前3个):")
        for i, route in enumerate(routes[:3], 1):
            origin = route.get('起始地', '?')
            destination = route.get('目的地', '?')
            logger.info(f"   {i}. {origin} → {destination}")
        
        logger.info(f"\n👥 Agents示例 (前5个):")
        for i, agent in enumerate(agents[:5], 1):
            agent_name = agent.get('代理商', '?')
            timeliness = agent.get('时效', '?')
            logger.info(f"   {i}. {agent_name} - 时效: {timeliness}")
        
        # ========== 7. 显示提取器统计 ==========
        logger.info(f"\n🔍 RouteExtractor统计:")
        route_stats = parser.route_extractor.get_stats()
        total_r = route_stats['total_attempts']
        success_rate_r = route_stats['rule_success'] / total_r * 100 if total_r > 0 else 0
        logger.info(f"   规则尝试次数: {total_r}")
        logger.info(f"   规则成功率: {success_rate_r:.1f}%")
        logger.info(f"   LLM调用次数: {route_stats['llm_calls']}")

        logger.info(f"\n🔍 AgentExtractor统计:")
        agent_stats = parser.agent_extractor.get_stats()
        total_a = agent_stats['total_attempts']
        success_rate_a = agent_stats['rule_success'] / total_a * 100 if total_a > 0 else 0
        logger.info(f"   规则尝试次数: {total_a}")
        logger.info(f"   规则成功率: {success_rate_a:.1f}%")
        logger.info(f"   LLM调用次数: {agent_stats['llm_calls']}")
        
        # 如果启用了LLM，显示质量分数统计
        if enable_llm and agent_stats.get('quality_scores'):
            scores = agent_stats['quality_scores']
            avg_score = sum(scores) / len(scores)
            logger.info(f"   平均质量分数: {avg_score:.2f}")
            logger.info(f"   质量 < 0.7 的次数: {sum(1 for s in scores if s < 0.7)}")
        
        # ========== 8. LLM使用统计 ==========
        if enable_llm and llm_client:
            logger.info("\n" + "=" * 60)
            logger.info("💰 LLM使用统计")
            logger.info("=" * 60)
            
            stats = llm_client.get_usage_stats()
            logger.info(f"   总调用次数: {stats['total_calls']}")
            logger.info(f"   成功: {stats['successful_calls']}")
            logger.info(f"   失败: {stats['failed_calls']}")
            logger.info(f"   总Token数: {stats['total_tokens']}")
            logger.info(f"   预估费用: {stats['estimated_cost']}")
        
        # ========== 9. 输出文件 ==========
        logger.info("\n" + "=" * 60)
        logger.info("✅ 测试完成")
        logger.info("=" * 60)
        
        logger.info(f"\n结果文件:")
        logger.info(f"   - {output_dir}/routes.json")
        logger.info(f"   - {output_dir}/route_agents.json")
        
        return result
    
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def compare_with_without_llm():
    """
    对比测试：有LLM vs 无LLM
    """
    logger = setup_logger()
    
    logger.info("\n" + "=" * 60)
    logger.info("🔬 对比测试：LLM vs 纯规则")
    logger.info("=" * 60)
    
    # 测试1: 不启用LLM
    logger.info("\n📊 测试1: 纯规则提取（无LLM）")
    logger.info("-" * 60)
    result1 = test_with_llm(enable_llm=False)
    
    # 测试2: 启用LLM
    logger.info("\n📊 测试2: 启用LLM增强")
    logger.info("-" * 60)
    result2 = test_with_llm(enable_llm=True)
    
    # 对比结果
    if result1 and result2:
        logger.info("\n" + "=" * 60)
        logger.info("📊 对比结果")
        logger.info("=" * 60)
        
        agents1 = len(result1.get('route_agents', []))
        agents2 = len(result2.get('route_agents', []))
        
        logger.info(f"\nAgents数量:")
        logger.info(f"   无LLM: {agents1}")
        logger.info(f"   有LLM: {agents2}")
        logger.info(f"   差异: {agents2 - agents1} ({(agents2-agents1)/agents1*100:.1f}%)")
        
        # 质量对比（如果有质量分数）
        # 这里可以添加更详细的质量对比


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="新架构测试 - 启用LLM版本"
    )
    
    parser.add_argument(
        '--file', 
        type=str, 
        help='Excel文件路径（默认使用data/raw下的文件）'
    )
    
    parser.add_argument(
        '--no-llm',
        action='store_true',
        help='禁用LLM功能'
    )
    
    parser.add_argument(
        '--compare',
        action='store_true',
        help='对比测试（LLM vs 无LLM）'
    )
    
    args = parser.parse_args()

    try:
        if args.compare:
            # 对比测试
            compare_with_without_llm()
        else:
            # ✅ 修复：根据参数决定enable_llm
            # 如果传了--no-llm，禁用LLM；否则从config读取
            if args.no_llm:
                enable_llm = False
            else:
                # ✅ 没有明确指定时，从config读取
                enable_llm = None  # None表示从config读取
            
            test_with_llm(
                excel_file=args.file,
                enable_llm=enable_llm
            )
    
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断")
    
    except Exception as e:
        print(f"\n\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()