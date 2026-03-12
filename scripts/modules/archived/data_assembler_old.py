# scripts/modules/assembler/data_assembler.py
"""
数据组装器 v1.0

【架构角色】
负责将各个独立提取器的结果组装成最终的数据结构

【核心功能】
1. 为routes分配ID
2. 为agents分配ID并关联到route
3. 验证数据完整性
4. 输出标准的JSON格式

【关键设计】
- 简单的关联逻辑：同一个sheet的agents自动关联到该sheet的route
- 每个sheet = 1个route（预处理后保证）

【使用示例】
```python
assembler = DataAssembler(logger=logger)

# sheets_data是一个列表，每个元素对应一个sheet的提取结果
sheets_data = [
    {
        'sheet_name': '深圳-新加坡',
        'sheet_index': 0,
        'route': Route(...),
        'agents': [Agent(...), Agent(...)]
    },
    ...
]

result = assembler.assemble(sheets_data)

# result = {
#     'routes': [Route(...), ...],      # 24条
#     'agents': [Agent(...), ...],      # 35个
#     'validation_errors': [...]        # 验证错误（如果有）
# }
```
"""

import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict


class DataAssembler:
    """
    数据组装器
    
    【职责】
    1. 分配ID
    2. 建立关联
    3. 验证数据
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化数据组装器
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
        self.validation_errors = []
    
    def assemble(self, sheets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        组装数据
        
        【组装流程】
        1. 为每个sheet的route分配路线ID
        2. 为每个sheet的agents分配代理路线ID并关联到route
        3. 验证关联正确性
        4. 返回组装后的数据
        
        Args:
            sheets_data: 每个sheet的提取结果列表
                [
                    {
                        'sheet_name': str,
                        'sheet_index': int,
                        'route': Route对象,
                        'agents': [Agent对象, ...]
                    },
                    ...
                ]
        
        Returns:
            {
                'routes': [Route对象, ...],
                'agents': [Agent对象, ...],
                'validation_errors': [错误信息, ...]
            }
        """
        if self.logger:
            self.logger.info(f"开始组装数据，共{len(sheets_data)}个sheets")
        
        self.validation_errors = []
        all_routes = []
        all_agents = []
        
        # ========== 遍历每个sheet的数据 ==========
        for sheet_data in sheets_data:
            sheet_name = sheet_data.get('sheet_name', 'Unknown')
            sheet_index = sheet_data.get('sheet_index', 0)
            route = sheet_data.get('route')
            agents = sheet_data.get('agents', [])
            
            if self.logger:
                self.logger.debug(f"  处理sheet: {sheet_name}")
            
            # ========== 1. 为route分配ID ==========
            if route:
                # 路线ID = 当前索引 + 1（1-based）
                route_id = len(all_routes) + 1
                
                # 将ID添加到route对象
                route_dict = route.to_dict() if hasattr(route, 'to_dict') else route
                route_dict['路线ID'] = route_id
                route_dict['_sheet_name'] = sheet_name
                route_dict['_sheet_index'] = sheet_index
                
                all_routes.append(route_dict)
                
                if self.logger:
                    self.logger.debug(f"    Route ID={route_id}: {route_dict.get('起始地')} → {route_dict.get('目的地')}")
            else:
                if self.logger:
                    self.logger.warning(f"    ⚠️  Sheet '{sheet_name}' 没有route")
                route_id = None
            
            # ========== 2. 为agents分配ID并关联route ==========
            if agents:
                for agent in agents:
                    # 代理路线ID = 全局agent计数器 + 1
                    agent_id = len(all_agents) + 1
                    
                    # 转换为字典
                    agent_dict = agent.to_dict() if hasattr(agent, 'to_dict') else agent
                    
                    # 分配ID
                    agent_dict['代理路线ID'] = agent_id
                    
                    # 关联到route（同一个sheet的agents关联到该sheet的route）
                    if route_id:
                        agent_dict['路线ID'] = route_id
                    else:
                        agent_dict['路线ID'] = None
                        self.validation_errors.append(
                            f"Agent '{agent_dict.get('代理商')}' (Sheet: {sheet_name}) 没有有效的路线ID"
                        )
                    
                    # 添加sheet信息
                    agent_dict['_sheet_name'] = sheet_name
                    agent_dict['_sheet_index'] = sheet_index
                    
                    all_agents.append(agent_dict)
                
                if self.logger:
                    self.logger.debug(f"    添加{len(agents)}个agents，关联到Route ID={route_id}")
            else:
                if self.logger:
                    self.logger.debug(f"    该sheet没有agents")
        
        # ========== 3. 验证关联正确性 ==========
        self._validate_associations(all_routes, all_agents)
        
        # ========== 4. 返回结果 ==========
        result = {
            'routes': all_routes,
            'agents': all_agents,
            'validation_errors': self.validation_errors
        }
        
        if self.logger:
            self.logger.info(f"组装完成: {len(all_routes)}条routes, {len(all_agents)}个agents")
            if self.validation_errors:
                self.logger.warning(f"发现{len(self.validation_errors)}个验证错误")
        
        return result
    
    def _validate_associations(self, routes: List[Dict], agents: List[Dict]):
        """
        验证关联正确性
        
        【验证项】
        1. 每个agent的路线ID都存在于routes中
        2. 每个route至少有一个agent（警告，不是错误）
        
        Args:
            routes: Route字典列表
            agents: Agent字典列表
        """
        if self.logger:
            self.logger.debug("  验证关联正确性...")
        
        # 收集所有有效的路线ID
        valid_route_ids = {r['路线ID'] for r in routes if r.get('路线ID')}
        
        # 验证1: 每个agent的路线ID都存在
        for agent in agents:
            agent_route_id = agent.get('路线ID')
            if agent_route_id and agent_route_id not in valid_route_ids:
                error = f"Agent '{agent.get('代理商')}' 的路线ID {agent_route_id} 不存在"
                self.validation_errors.append(error)
                if self.logger:
                    self.logger.error(f"    ❌ {error}")
        
        # 验证2: 每个route至少有一个agent（警告）
        agents_by_route = defaultdict(list)
        for agent in agents:
            route_id = agent.get('路线ID')
            if route_id:
                agents_by_route[route_id].append(agent.get('代理商'))
        
        for route in routes:
            route_id = route.get('路线ID')
            if route_id not in agents_by_route:
                warning = f"Route ID={route_id} ({route.get('起始地')}→{route.get('目的地')}) 没有agent"
                if self.logger:
                    self.logger.warning(f"    ⚠️  {warning}")
                # 注意：这是警告，不是错误，不添加到validation_errors
    
    def get_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取数据摘要
        
        Args:
            result: assemble()的返回结果
            
        Returns:
            摘要信息
        """
        routes = result.get('routes', [])
        agents = result.get('agents', [])
        
        # 统计agents按route分布
        agents_by_route = defaultdict(int)
        for agent in agents:
            route_id = agent.get('路线ID')
            if route_id:
                agents_by_route[route_id] += 1
        
        return {
            'total_routes': len(routes),
            'total_agents': len(agents),
            'routes_without_agents': sum(1 for r in routes if r.get('路线ID') not in agents_by_route),
            'avg_agents_per_route': len(agents) / len(routes) if routes else 0,
            'validation_errors_count': len(result.get('validation_errors', []))
        }


# ========== 便捷函数 ==========

def assemble_data(sheets_data: List[Dict], logger=None) -> Dict[str, Any]:
    """
    组装数据的便捷函数
    
    Args:
        sheets_data: 每个sheet的提取结果
        logger: 日志记录器
        
    Returns:
        组装后的数据
    """
    assembler = DataAssembler(logger=logger)
    return assembler.assemble(sheets_data)


__all__ = ['DataAssembler', 'assemble_data']
