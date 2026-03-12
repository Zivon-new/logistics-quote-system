# scripts/modules/validators/route_validator.py
"""
Route验证器 v1.0

【架构角色】
验证Route对象的有效性，提供明确的验证标准。

【核心功能】
定义4个明确的Route验证标准：
1. 必须有起始地和目的地
2. 不能是无效值（"国内"、"未知"等）
3. 起始地≠目的地
4. 至少一个是已知地名（白名单验证）

【使用方式】
```python
from validators.route_validator import RouteValidator

validator = RouteValidator()
is_valid = validator.validate_route(route)
if not is_valid:
    errors = validator.get_validation_errors(route)
    print(errors)
```

【依赖】
- location_whitelist.is_valid_location (地名白名单)
"""

from typing import List, Optional
from dataclasses import dataclass

# 导入地名白名单
try:
    from scripts.data.location_whitelist import is_valid_location
except ImportError:
    try:
        from data.location_whitelist import is_valid_location
    except ImportError:
        # Fallback: 如果找不到白名单，使用简单验证
        def is_valid_location(location):
            return location and len(location) >= 2


@dataclass
class Route:
    """
    Route数据类
    
    【注意】这是一个简化版，实际使用时应该使用项目中定义的Route类
    """
    起始地: str = None
    目的地: str = None
    途径地: str = None
    贸易备注: str = None


class RouteValidator:
    """
    Route验证器
    
    提供明确的Route验证标准和验证方法。
    """
    
    def __init__(self):
        """初始化验证器"""
        # 无效地名列表（这些值被认为是无效的）
        self.invalid_locations = {
            # '国内',    # 注释掉：在业务中"国内"是有效的起始地
            '未知',      # 明确的未知
            '待定',      # 未确定
            '',          # 空字符串
            'None',      # 字符串None
            'null',      # 字符串null
            '无',        # 无
            '暂无',      # 暂无
            'N/A',       # N/A
            'TBD',       # To Be Determined
        }
    
    def validate_route(self, route: Route) -> bool:
        """
        验证Route是否有效
        
        【4个验证标准】
        1. ✅ 必须有起始地和目的地
        2. ✅ 不能是无效值
        3. ✅ 起始地≠目的地  
        4. ✅ 至少一个是已知地名
        
        Args:
            route: Route对象
            
        Returns:
            True: Route有效
            False: Route无效
        """
        if not route:
            return False
        
        # 标准1: 必须有起始地和目的地
        if not route.起始地 or not route.目的地:
            return False
        
        # 标准2: 不能是无效值
        if route.起始地 in self.invalid_locations:
            return False
        if route.目的地 in self.invalid_locations:
            return False
        
        # 标准3: 起始地≠目的地
        if route.起始地 == route.目的地:
            return False
        
        # 标准4: 至少一个是已知地名（使用白名单验证）
        origin_valid = is_valid_location(route.起始地)
        dest_valid = is_valid_location(route.目的地)
        
        if not origin_valid and not dest_valid:
            return False
        
        # 全部通过
        return True
    
    def get_validation_errors(self, route: Route) -> List[str]:
        """
        获取Route的验证错误列表
        
        【用途】
        当Route验证失败时，获取具体的错误原因，用于调试或日志记录。
        
        Args:
            route: Route对象
            
        Returns:
            错误列表，如果没有错误则返回空列表
            
        【示例】
        ```python
        errors = validator.get_validation_errors(route)
        # ['起始地为无效值: 国内', '目的地不在白名单中']
        ```
        """
        errors = []
        
        if not route:
            errors.append("Route对象为None")
            return errors
        
        # 检查1: 是否有起始地
        if not route.起始地:
            errors.append("缺少起始地")
        elif route.起始地 in self.invalid_locations:
            errors.append(f"起始地为无效值: {route.起始地}")
        
        # 检查2: 是否有目的地
        if not route.目的地:
            errors.append("缺少目的地")
        elif route.目的地 in self.invalid_locations:
            errors.append(f"目的地为无效值: {route.目的地}")
        
        # 检查3: 起始地≠目的地
        if route.起始地 and route.目的地 and route.起始地 == route.目的地:
            errors.append(f"起始地和目的地相同: {route.起始地}")
        
        # 检查4: 白名单验证
        if route.起始地 and route.起始地 not in self.invalid_locations:
            if not is_valid_location(route.起始地):
                errors.append(f"起始地不在白名单中: {route.起始地}")
        
        if route.目的地 and route.目的地 not in self.invalid_locations:
            if not is_valid_location(route.目的地):
                errors.append(f"目的地不在白名单中: {route.目的地}")
        
        return errors
    
    def validate_routes(self, routes: List[Route]) -> dict:
        """
        批量验证Routes
        
        【功能】
        验证一批Routes，返回统计信息和无效的Routes列表。
        
        Args:
            routes: Route对象列表
            
        Returns:
            {
                'total': int,           # 总数
                'valid': int,           # 有效数量
                'invalid': int,         # 无效数量
                'invalid_routes': [     # 无效的routes详情
                    {
                        'route': Route,
                        'errors': [str]
                    }
                ]
            }
        """
        total = len(routes)
        valid_count = 0
        invalid_routes = []
        
        for route in routes:
            if self.validate_route(route):
                valid_count += 1
            else:
                errors = self.get_validation_errors(route)
                invalid_routes.append({
                    'route': route,
                    'errors': errors
                })
        
        return {
            'total': total,
            'valid': valid_count,
            'invalid': total - valid_count,
            'invalid_routes': invalid_routes
        }


# ========== 便捷函数 ==========

def quick_validate_route(起始地: str, 目的地: str, 途径地: str = None) -> bool:
    """
    快速验证route（便捷函数）
    
    【用途】
    不需要创建Route对象，直接验证起始地和目的地。
    
    Args:
        起始地: 起始地名
        目的地: 目的地名
        途径地: 途径地名（可选）
        
    Returns:
        True: 有效
        False: 无效
        
    【示例】
    ```python
    is_valid = quick_validate_route("深圳", "新加坡")
    ```
    """
    route = Route(起始地=起始地, 目的地=目的地, 途径地=途径地)
    validator = RouteValidator()
    return validator.validate_route(route)


__all__ = ['RouteValidator', 'Route', 'quick_validate_route']
