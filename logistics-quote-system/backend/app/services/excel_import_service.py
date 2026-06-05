# backend/app/services/excel_import_service.py
import sys
import logging as _logging
from pathlib import Path
from typing import Dict, Any

_svc_logger = _logging.getLogger(__name__)

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
        _svc_logger.debug("Found SCRIPTS_DIR: %s", SCRIPTS_DIR)
        break

if SCRIPTS_DIR is None:
    raise RuntimeError("Cannot find scripts directory!")

SCRIPTS_PARENT = SCRIPTS_DIR.parent
_svc_logger.debug("Adding to sys.path: %s", SCRIPTS_PARENT)
sys.path.insert(0, str(SCRIPTS_PARENT))

# 导入HorizontalTableParserV2
try:
    from scripts.modules.horizontal_table_parser_v2 import HorizontalTableParserV2
    _svc_logger.debug("HorizontalTableParserV2 imported")
except ImportError as e:
    _svc_logger.error("Failed to import HorizontalTableParserV2: %s", e)
    raise

# 导入logger
try:
    from scripts.logger_config import get_logger
except ImportError:
    def get_logger(name):
        return _logging.getLogger(name)


class ExcelImportService:
    """Excel导入服务 - 使用HorizontalTableParserV2"""

    def __init__(self, enable_llm: bool = False):
        self.enable_llm = enable_llm
        try:
            self.logger = get_logger(__name__)
        except Exception:
            self.logger = _logging.getLogger(__name__)
        self.logger.debug("ExcelImportService initialized, enable_llm=%s", enable_llm)

    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """从Excel文件提取数据 - 使用HorizontalTableParserV2"""
        self.logger.debug("Extracting from: %s", file_path)

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

            # 解析Excel
            result = parser.parse_excel(file_path)

            # 获取数据
            routes = result.get('routes', [])
            route_agents = result.get('route_agents', [])
            goods_details = result.get('goods_details', [])
            goods_total = result.get('goods_total', [])
            fee_items = result.get('fee_items', [])
            fee_totals = result.get('fee_totals', [])
            summaries = result.get('summary', [])

            self.logger.debug(
                "Extracted: %d routes, %d agents, %d fee_items, %d fee_totals, %d summaries",
                len(routes), len(route_agents), len(fee_items), len(fee_totals), len(summaries)
            )

            # ========== 转换数据格式为前端期望的格式 ==========
            # 前端期望：data.routes（数组）、data.goods_details、data.agents
            # 每个agent需要有路线索引

            # 为每个route添加索引，同时构建 O(1) 查找表（原来用O(n×m)嵌套循环）
            route_id_to_idx = {}
            for idx, route in enumerate(routes):
                if isinstance(route, dict):
                    route['_index'] = idx
                    route['路线索引'] = idx
                    route_id_to_idx[route.get('路线ID')] = idx

            # 将fee_items、fee_totals、summary按代理路线ID分组
            summary_by_agent = {s.get('代理路线ID'): s for s in summaries}

            fee_items_by_agent: dict = {}
            for fi in fee_items:
                fee_items_by_agent.setdefault(fi.get('代理路线ID'), []).append(fi)

            fee_totals_by_agent: dict = {}
            for ft in fee_totals:
                fee_totals_by_agent.setdefault(ft.get('代理路线ID'), []).append(ft)

            # 为每个agent添加路线索引及费用数据（O(n) dict 查找）
            for agent in route_agents:
                if isinstance(agent, dict):
                    agent['路线索引'] = route_id_to_idx.get(agent.get('路线ID'))
                    agent_id = agent.get('代理路线ID')
                    agent['fee_items'] = fee_items_by_agent.get(agent_id, [])
                    agent['fee_total'] = fee_totals_by_agent.get(agent_id, [])
                    agent['summary'] = summary_by_agent.get(agent_id)

            # 为goods添加路线索引（O(1) dict 查找）
            for goods in goods_details:
                if isinstance(goods, dict):
                    goods['路线索引'] = route_id_to_idx.get(goods.get('路线ID'))

            for goods in goods_total:
                if isinstance(goods, dict):
                    goods['路线索引'] = route_id_to_idx.get(goods.get('路线ID'))

            self.logger.debug(
                "数据转换完成: routes=%d, agents=%d, goods_details=%d, goods_total=%d",
                len(routes), len(route_agents), len(goods_details), len(goods_total)
            )

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
            self.logger.error("Extraction failed: %s", e, exc_info=True)
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


def get_excel_import_service(enable_llm: bool = False) -> ExcelImportService:
    return ExcelImportService(enable_llm=enable_llm)
