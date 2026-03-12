# scripts/modules/validators/agent_validator.py
"""
Agent验证器 v1.0

【架构角色】
验证Agent对象的有效性，提供明确的验证标准。

【核心功能】
定义3个明确的Agent验证标准：
1. 代理商名不为空
2. 不是无效值（"未知"、"待定"、"单列报价"等）
3. 长度合理（1-20字符），不是纯数字

【使用方式】
```python
from validators.agent_validator import AgentValidator

validator = AgentValidator()
is_valid = validator.validate_agent(agent)
if not is_valid:
    errors = validator.get_validation_errors(agent)
    print(errors)
```
"""

import re
from typing import List
from dataclasses import dataclass


@dataclass
class Agent:
    """
    Agent数据类
    
    【注意】这是一个简化版，实际使用时应该使用项目中定义的Agent类
    """
    代理商: str = None
    代理备注: str = None
    时效: str = None
    是否赔付: str = None


class AgentValidator:
    """
    Agent验证器
    
    提供明确的Agent验证标准和验证方法。
    """
    
    def __init__(self):
        """初始化验证器"""
        # 无效代理商名列表
        self.invalid_agent_names = {
            # 明确的无效值
            '未知', '待定', '', 'None', 'null', '无', '暂无', 'N/A', 'TBD',
            
            # 特殊的假代理（从实际数据中发现的）
            '单列报价',          # 不是代理商名
            'sheet名提取',       # 提取错误
            '未指定代理',        # 未指定
            '/',                # 分隔符
            '-',                # 分隔符
            '.',                # 句号
            '…',                # 省略号
            '....',             # 多个点
            
            # 常见的非代理商文字
            '代理',             # 列标题
            '报价方',           # 列标题
            '供应商',           # 列标题
            '备注',             # 其他标题
            '说明',             # 其他标题
        }
    
    def validate_agent(self, agent: Agent) -> bool:
        """
        验证Agent是否有效
        
        【3个验证标准】
        1. ✅ 代理商名不为空
        2. ✅ 不是无效值
        3. ✅ 长度合理（1-20字符），不是纯数字
        
        Args:
            agent: Agent对象
            
        Returns:
            True: Agent有效
            False: Agent无效
        """
        if not agent:
            return False
        
        # 标准1: 代理商名不为空
        if not agent.代理商:
            return False
        
        agent_name = agent.代理商.strip()
        
        # 标准2: 不是无效值
        if agent_name in self.invalid_agent_names:
            return False
        
        # 检查是否包含无效值（部分匹配）
        for invalid in ['未知', '待定', '暂无']:
            if invalid in agent_name:
                return False
        
        # 标准3a: 长度合理（1-20字符）
        if len(agent_name) < 1 or len(agent_name) > 20:
            return False
        
        # 标准3b: 不是纯数字或特殊字符
        if re.match(r'^[\d\W]+$', agent_name):
            return False
        
        # 全部通过
        return True
    
    def get_validation_errors(self, agent: Agent) -> List[str]:
        """
        获取Agent的验证错误列表
        
        【用途】
        当Agent验证失败时，获取具体的错误原因，用于调试或日志记录。
        
        Args:
            agent: Agent对象
            
        Returns:
            错误列表，如果没有错误则返回空列表
        """
        errors = []
        
        if not agent:
            errors.append("Agent对象为None")
            return errors
        
        # 检查1: 是否有代理商名
        if not agent.代理商:
            errors.append("代理商名为空")
            return errors
        
        agent_name = agent.代理商.strip()
        
        # 检查2: 是否为无效值
        if agent_name in self.invalid_agent_names:
            errors.append(f"代理商名为无效值: {agent_name}")
        
        # 检查是否包含无效值
        for invalid in ['未知', '待定', '暂无']:
            if invalid in agent_name:
                errors.append(f"代理商名包含无效值: {agent_name} (含'{invalid}')")
                break
        
        # 检查3: 长度
        if len(agent_name) < 1:
            errors.append("代理商名长度为0")
        elif len(agent_name) > 20:
            errors.append(f"代理商名过长: {len(agent_name)}字符 (限制20字符)")
        
        # 检查4: 不是纯数字或特殊字符
        if re.match(r'^[\d\W]+$', agent_name):
            errors.append(f"代理商名为纯数字或特殊字符: {agent_name}")
        
        return errors
    
    def validate_agents(self, agents: List[Agent]) -> dict:
        """
        批量验证Agents
        
        【功能】
        验证一批Agents，返回统计信息和无效的Agents列表。
        
        Args:
            agents: Agent对象列表
            
        Returns:
            {
                'total': int,           # 总数
                'valid': int,           # 有效数量
                'invalid': int,         # 无效数量
                'invalid_agents': [     # 无效的agents详情
                    {
                        'agent': Agent,
                        'errors': [str]
                    }
                ]
            }
        """
        total = len(agents)
        valid_count = 0
        invalid_agents = []
        
        for agent in agents:
            if self.validate_agent(agent):
                valid_count += 1
            else:
                errors = self.get_validation_errors(agent)
                invalid_agents.append({
                    'agent': agent,
                    'errors': errors
                })
        
        return {
            'total': total,
            'valid': valid_count,
            'invalid': total - valid_count,
            'invalid_agents': invalid_agents
        }


# ========== 便捷函数 ==========

def quick_validate_agent(代理商: str) -> bool:
    """
    快速验证agent（便捷函数）
    
    【用途】
    不需要创建Agent对象，直接验证代理商名。
    
    Args:
        代理商: 代理商名称
        
    Returns:
        True: 有效
        False: 无效
        
    【示例】
    ```python
    is_valid = quick_validate_agent("融迅")  # True
    is_valid = quick_validate_agent("未知")  # False
    ```
    """
    agent = Agent(代理商=代理商)
    validator = AgentValidator()
    return validator.validate_agent(agent)


__all__ = ['AgentValidator', 'Agent', 'quick_validate_agent']
