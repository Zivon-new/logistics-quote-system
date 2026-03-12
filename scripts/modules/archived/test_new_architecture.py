#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新架构快速测试脚本

【功能】
快速测试新架构的效果，与旧架构对比

【运行】
cd project_root
python test_new_architecture.py
"""

import sys
import os
import logging
import json
from pathlib import Path

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_new_arch.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def test_new_architecture():
    """测试新架构"""
    logger.info("="*60)
    logger.info("🚀 新架构测试开始")
    logger.info("="*60)
    
    # 导入新架构的主解析器
    from scripts.modules.horizontal_table_parser_v2 import HorizontalTableParserV2
    
    # 查找Excel文件（过滤Excel临时文件）
    raw_dir = 'data/raw'
    excel_files = [
        f for f in os.listdir(raw_dir) 
        if f.endswith('.xlsx') and not f.startswith('~$')  # ← 过滤临时文件
    ]
    
    if not excel_files:
        logger.error("❌ 没有找到Excel文件")
        return
    
    excel_file = os.path.join(raw_dir, excel_files[0])
    logger.info(f"📁 Excel文件: {excel_files[0][:50]}...")
    
    # 创建解析器
    parser = HorizontalTableParserV2(
        enable_llm=False,  # 不使用LLM（快速测试）
        logger=logger,
        output_dir='data/clean'
    )
    
    # 解析Excel
    logger.info("\n开始解析...")
    result = parser.parse_excel(excel_file)
    
    # 显示结果
    logger.info("\n" + "="*60)
    logger.info("📊 测试结果")
    logger.info("="*60)
    
    routes = result['routes']
    route_agents = result.get('route_agents', [])  # 使用新的字段名
    stats = result.get('stats', {})
    errors = result.get('validation_errors', [])
    
    logger.info(f"\n✅ 数据提取:")
    logger.info(f"  Routes: {len(routes)} 条")
    logger.info(f"  Agents: {len(route_agents)} 个")
    
    # 显示前3个routes
    logger.info(f"\n📍 Routes示例 (前3个):")
    for i, route in enumerate(routes[:3], 1):
        logger.info(f"  {i}. {route.get('起始地', '?')} → {route.get('目的地', '?')}")
    
    # 显示前5个agents
    logger.info(f"\n👥 Agents示例 (前5个):")
    for i, agent in enumerate(route_agents[:5], 1):
        logger.info(f"  {i}. {agent.get('代理商', '?')} (关联Route ID: {agent.get('路线ID', '?')})")
    
    # 显示提取器统计
    if 'route_extractor' in stats:
        route_stats = stats['route_extractor']
        logger.info(f"\n🔍 RouteExtractor统计:")
        if route_stats['total_attempts'] > 0:
            success_rate = route_stats['rule_success'] / route_stats['total_attempts'] * 100
            logger.info(f"  规则成功率: {success_rate:.1f}%")
            logger.info(f"  LLM调用次数: {route_stats['llm_calls']}")
    
    if 'agent_extractor' in stats:
        agent_stats = stats['agent_extractor']
        logger.info(f"\n🔍 AgentExtractor统计:")
        if agent_stats['total_attempts'] > 0:
            success_rate = agent_stats['rule_success'] / agent_stats['total_attempts'] * 100
            logger.info(f"  规则成功率: {success_rate:.1f}%")
            logger.info(f"  LLM调用次数: {agent_stats['llm_calls']}")
    
    # 显示验证错误
    if errors:
        logger.warning(f"\n⚠️  验证错误 ({len(errors)}个):")
        for error in errors[:5]:
            logger.warning(f"  - {error}")
        if len(errors) > 5:
            logger.warning(f"  ... 还有{len(errors)-5}个错误")
    
    # 保存结果摘要
    summary = {
        'total_routes': len(routes),
        'total_agents': len(route_agents),
        'validation_errors_count': len(errors),
        'stats': stats
    }
    
    with open('data/clean/test_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n" + "="*60)
    logger.info("✅ 测试完成")
    logger.info("="*60)
    logger.info(f"\n结果文件:")
    logger.info(f"  - data/clean/routes.json")
    logger.info(f"  - data/clean/route_agents.json")
    logger.info(f"  - data/clean/test_summary.json")
    logger.info(f"  - logs/test_new_arch.log")
    
    return result


def compare_with_old():
    """与旧结果对比（可选）"""
    logger.info("\n" + "="*60)
    logger.info("📊 与旧架构对比")
    logger.info("="*60)
    
    try:
        # 加载新结果
        with open('data/clean/routes.json', 'r', encoding='utf-8') as f:
            routes_new = json.load(f)
        with open('data/clean/route_agents.json', 'r', encoding='utf-8') as f:
            agents_new = json.load(f)
        
        logger.info(f"\n新架构:")
        logger.info(f"  Routes: {len(routes_new)}")
        logger.info(f"  Agents: {len(agents_new)}")
        
        # 如果有旧结果，进行对比
        old_routes_file = 'data/clean/routes_old.json'
        old_agents_file = 'data/clean/route_agents_old.json'
        
        if os.path.exists(old_routes_file):
            with open(old_routes_file, 'r', encoding='utf-8') as f:
                routes_old = json.load(f)
            with open(old_agents_file, 'r', encoding='utf-8') as f:
                agents_old = json.load(f)
            
            logger.info(f"\n旧架构:")
            logger.info(f"  Routes: {len(routes_old)}")
            logger.info(f"  Agents: {len(agents_old)}")
            
            logger.info(f"\n差异:")
            logger.info(f"  Routes增加: {len(routes_new) - len(routes_old)}")
            logger.info(f"  Agents增加: {len(agents_new) - len(agents_old)}")
        else:
            logger.info("\n💡 提示: 如果要对比，请先将当前的routes.json重命名为routes_old.json")
    
    except Exception as e:
        logger.error(f"对比失败: {e}")


def main():
    """主函数"""
    try:
        # 测试新架构
        result = test_new_architecture()
        
        # 对比（可选）
        # compare_with_old()
        
        print("\n" + "="*60)
        print("✅ 测试成功！")
        print("="*60)
        print("\n接下来可以:")
        print("1. 查看 data/clean/routes.json")
        print("2. 查看 data/clean/route_agents.json")
        print("3. 查看 logs/test_new_arch.log（详细日志）")
        print("4. 查看 data/clean/test_summary.json（摘要）")
        
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print("\n❌ 测试失败，请查看日志")


if __name__ == '__main__':
    main()
