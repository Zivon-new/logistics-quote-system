# backend/app/services/excel_import_service.py
import sys
from pathlib import Path
from typing import Dict, Any, List

# 找到scripts目录的父目录
possible_scripts_dirs = [
    Path(__file__).parent.parent.parent.parent / "scripts",
    Path(__file__).parent.parent.parent.parent.parent / "scripts",
    Path("D:/project_root/scripts"),
]

SCRIPTS_DIR = None
for path in possible_scripts_dirs:
    if path.exists():
        SCRIPTS_DIR = path
        print(f"[DEBUG] ✓ Found SCRIPTS_DIR: {SCRIPTS_DIR}")
        break

if SCRIPTS_DIR is None:
    raise RuntimeError("Cannot find scripts directory!")

SCRIPTS_PARENT = SCRIPTS_DIR.parent
print(f"[DEBUG] Adding to sys.path: {SCRIPTS_PARENT}")
sys.path.insert(0, str(SCRIPTS_PARENT))

# 导入HorizontalTableParserV2
try:
    from scripts.modules.horizontal_table_parser_v2 import HorizontalTableParserV2
    print("[DEBUG] ✓ HorizontalTableParserV2 imported")
except ImportError as e:
    print(f"[ERROR] Failed to import HorizontalTableParserV2: {e}")
    raise

# 导入logger
try:
    from scripts.logger_config import get_logger
    print("[DEBUG] ✓ Logger imported")
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)


class ExcelImportService:
    """Excel导入服务 - 使用HorizontalTableParserV2"""
    
    def __init__(self, enable_llm: bool = False):
        print(f"[DEBUG] Initializing ExcelImportService, enable_llm={enable_llm}")
        self.enable_llm = enable_llm
        
        try:
            self.logger = get_logger(__name__)
        except:
            import logging
            self.logger = logging.getLogger(__name__)
        
        print("[DEBUG] ✓ ExcelImportService initialized")
    
    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """从Excel文件提取数据 - 使用HorizontalTableParserV2"""
        print(f"[DEBUG] Extracting from: {file_path}")
        
        try:
            if not Path(file_path).exists():
                return {
                    "success": False,
                    "message": f"文件不存在: {file_path}",
                    "data": None
                }
            
            # 创建临时输出目录
            temp_output_dir = Path(file_path).parent / "temp_output"
            temp_output_dir.mkdir(exist_ok=True)
            
            # 使用HorizontalTableParserV2解析
            parser = HorizontalTableParserV2(
                enable_llm=self.enable_llm,
                llm_client=None,  # 暂不启用LLM
                logger=self.logger,
                output_dir=str(temp_output_dir),
                excel_filename=file_path
            )
            
            print("[DEBUG] ✓ HorizontalTableParserV2 created")
            
            # 解析Excel
            result = parser.parse_excel(file_path)
            print("[DEBUG] ✓ parse_excel completed")
            
            # 获取数据
            routes = result.get('routes', [])
            route_agents = result.get('route_agents', [])
            goods_details = result.get('goods_details', [])
            goods_total = result.get('goods_total', [])
            
            print(f"[DEBUG] Extracted: {len(routes)} routes, {len(route_agents)} agents")
            
            # ========== 转换数据格式为前端期望的格式 ==========
            # 前端期望：data.routes（数组）、data.goods_details、data.agents
            # 每个agent需要有路线索引
            
            # 为每个route添加索引
            for idx, route in enumerate(routes):
                if isinstance(route, dict):
                    route['_index'] = idx
                    route['路线索引'] = idx
            
            # 为每个agent添加路线索引
            for agent in route_agents:
                if isinstance(agent, dict):
                    # route_agents已经有路线ID，需要转换为索引
                    route_id = agent.get('路线ID')
                    # 查找对应的索引
                    for idx, route in enumerate(routes):
                        route_dict = route if isinstance(route, dict) else route.__dict__
                        if route_dict.get('路线ID') == route_id:
                            agent['路线索引'] = idx
                            break
            
            # 为每个goods_details添加路线索引
            for goods in goods_details:
                if isinstance(goods, dict):
                    route_id = goods.get('路线ID')
                    for idx, route in enumerate(routes):
                        route_dict = route if isinstance(route, dict) else route.__dict__
                        if route_dict.get('路线ID') == route_id:
                            goods['路线索引'] = idx
                            break
            
            # 为每个goods_total添加路线索引  
            for goods in goods_total:
                if isinstance(goods, dict):
                    route_id = goods.get('路线ID')
                    for idx, route in enumerate(routes):
                        route_dict = route if isinstance(route, dict) else route.__dict__
                        if route_dict.get('路线ID') == route_id:
                            goods['路线索引'] = idx
                            break
            
            print(f"\n[DEBUG] 数据转换完成:")
            print(f"  routes: {len(routes)} 条（已添加索引）")
            print(f"  agents: {len(route_agents)} 个（已添加路线索引）")
            print(f"  goods_details: {len(goods_details)} 个")
            print(f"  goods_total: {len(goods_total)} 个\n")
            
            # ✅ 返回前端期望的格式
            return {
                "success": True,
                "message": "提取成功",
                "data": {
                    "routes": routes,  # ✅ 注意是复数，数组
                    "goods_details": goods_details,
                    "goods_total": goods_total,
                    "agents": route_agents  # ✅ 已添加路线索引
                }
            }
            
        except Exception as e:
            print(f"[ERROR] Extraction failed: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "message": f"提取失败: {str(e)}",
                "data": None
            }
    
    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证提取的数据"""
        errors = []
        warnings = []
        
        routes = data.get('routes', [])
        
        if not routes:
            errors.append("未提取到路线信息")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings
            }
        
        # 检查每个route
        for idx, route in enumerate(routes):
            # 兼容dict和对象两种格式
            def get_value(obj, key, default=None):
                if isinstance(obj, dict):
                    return obj.get(key, default)
                else:
                    return getattr(obj, key, default)
            
            if not get_value(route, '起始地'):
                warnings.append(f"路线{idx+1}缺少起始地")
            if not get_value(route, '目的地'):
                warnings.append(f"路线{idx+1}缺少目的地")
        
        agents = data.get('agents', [])
        if not agents:
            warnings.append("未提取到代理商信息")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


_excel_import_service = None

def get_excel_import_service(enable_llm: bool = False):
    global _excel_import_service
    if _excel_import_service is None:
        _excel_import_service = ExcelImportService(enable_llm=enable_llm)
    return _excel_import_service