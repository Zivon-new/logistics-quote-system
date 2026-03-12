# scripts/modules/horizontal_table_parser_v2_enhanced.py
"""
横向表格解析器 v2.4（增强版：进度条 + 断点续传）

【v2.4 更新】✅ 新增
✅ 详细进度条（tqdm）- 每个sheet、每个步骤都可视化
✅ 断点续传机制 - 每处理完一个sheet立即保存
✅ Resume功能 - 程序中断后可以继续运行
✅ 实时保存 - 不会因为中断丢失已处理的数据

【v2.3 更新】
✅ 集成 SummaryExtractor（汇总提取器）
✅ 自动提取税率、汇损率、备注
✅ 支持每个agent对应一个summary记录

【架构说明】
✅ 完全兼容 v2.3 的所有功能
✅ 不破坏现有代码架构
✅ 只是增加了进度显示和断点续传

【使用示例】
```python
from scripts.modules.horizontal_table_parser_v2_enhanced import HorizontalTableParserV2Enhanced

parser = HorizontalTableParserV2Enhanced(
    enable_llm=True,
    llm_client=llm_client,
    logger=logger,
    enable_checkpoint=True,  # ✅ 新增：启用断点续传
    checkpoint_dir='data/checkpoints'  # ✅ 新增：checkpoint目录
)

# 正常解析（会显示进度条）
result = parser.parse_excel('your_file.xlsx')

# 或者从checkpoint恢复
result = parser.resume_from_checkpoint('checkpoint_xxxxx.json')
```
"""

import sys
import os
import json
import logging
import pickle
from typing import Dict, List, Any, Optional
from openpyxl import load_workbook
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 导入独立提取器
from scripts.modules.extractors.route_extractor_v2 import RouteExtractorV2
from scripts.modules.extractors.agent_extractor_v2 import AgentExtractorV2
from scripts.modules.extractors.goods_extractor import GoodsExtractor
from scripts.modules.extractors.fee_extractor import FeeExtractor
from scripts.modules.extractors.summary_extractor import SummaryExtractor

# 导入格式检测器和LLM全量提取器
from scripts.modules.extractors.sheet_format_detector import SheetFormatDetector
from scripts.modules.extractors.llm_full_extractor import LLMFullExtractor

# 导入数据组装器
from scripts.modules.assembler.data_assembler import DataAssembler

# 导入验证器（可选）
try:
    from scripts.modules.validators.route_validator import RouteValidator
    from scripts.modules.validators.agent_validator import AgentValidator
except ImportError:
    RouteValidator = None
    AgentValidator = None


# ========== 辅助函数 ==========

def get_agent_attr(agent, attr_name, default=None):
    """安全地获取agent的属性（兼容对象和字典）"""
    if hasattr(agent, attr_name):
        return getattr(agent, attr_name, default)
    elif isinstance(agent, dict):
        return agent.get(attr_name, default)
    else:
        return default


def get_route_attr(route, attr_name, default=None):
    """安全地获取route的属性（兼容对象和字典）"""
    if hasattr(route, attr_name):
        return getattr(route, attr_name, default)
    elif isinstance(route, dict):
        return route.get(attr_name, default)
    else:
        return default


class HorizontalTableParserV2:
    """
    横向表格解析器 v2.4（增强版）
    
    【v2.4 新增功能】
    ✅ 详细进度条（每个sheet、每个步骤）
    ✅ 断点续传（每个sheet处理完立即保存）
    ✅ Resume功能（中断后可继续）
    """
    
    def __init__(self, 
                 enable_llm: bool = False,
                 llm_client: Optional[Any] = None,
                 logger: Optional[logging.Logger] = None,
                 output_dir: str = 'data/clean',
                 enable_checkpoint: bool = True,
                 checkpoint_dir: str = 'data/checkpoints',
                 excel_filename: str = None):  # ✅ v2.5 新增
        """
        初始化解析器
        
        Args:
            enable_llm: 是否启用LLM功能
            llm_client: LLM客户端
            logger: 日志记录器
            output_dir: 基础输出目录
            enable_checkpoint: 是否启用断点续传（默认True）
            checkpoint_dir: checkpoint保存目录
            excel_filename: Excel文件名（用于创建子文件夹）✅ v2.5
        """
        self.enable_llm = enable_llm
        self.llm_client = llm_client
        self.logger = logger or logging.getLogger(__name__)
        
        # ✅ v2.5: 保存原始参数
        self.base_output_dir = output_dir
        self.excel_filename = excel_filename
        
        # ✅ v2.5: 根据文件名创建子文件夹
        if excel_filename:
            file_basename = os.path.basename(excel_filename)
            self.output_dir = os.path.join(output_dir, file_basename)
        else:
            self.output_dir = output_dir
        
        # ✅ checkpoint配置
        self.enable_checkpoint = enable_checkpoint
        self.checkpoint_dir = checkpoint_dir
        
        # 创建输出目录和checkpoint目录
        os.makedirs(self.output_dir, exist_ok=True)
        if enable_checkpoint:
            os.makedirs(checkpoint_dir, exist_ok=True)
        
        # 创建独立提取器
        self.route_extractor = RouteExtractorV2(
            logger=self.logger,
            llm_client=llm_client,
            enable_llm=enable_llm
        )
        
        self.agent_extractor = AgentExtractorV2(
            logger=self.logger,
            llm_client=llm_client,
            enable_llm=enable_llm
        )
        
        self.goods_extractor = GoodsExtractor(
            logger=self.logger,
            llm_client=llm_client,
            enable_llm=enable_llm
        )
        
        self.fee_extractor = FeeExtractor(
            logger=self.logger,
            llm_client=llm_client,
            enable_llm=enable_llm
        )
        
        self.summary_extractor = SummaryExtractor(
            logger=self.logger,
            llm_client=llm_client,
            enable_llm=enable_llm
        )
        
        # 创建数据组装器
        self.assembler = DataAssembler(logger=self.logger)

        # 创建验证器（可选）
        self.route_validator = RouteValidator() if RouteValidator else None
        self.agent_validator = AgentValidator() if AgentValidator else None

        # 格式检测器（始终启用）
        self.format_detector = SheetFormatDetector()

        # LLM全量提取器（仅在LLM启用时创建）
        self.llm_full_extractor = None
        if enable_llm and llm_client:
            self.llm_full_extractor = LLMFullExtractor(
                llm_client=llm_client,
                logger=self.logger
            )

        # 读取格式置信度阈值（低于此值走LLM全量提取）
        try:
            from scripts.config import Config
            self._format_threshold = getattr(Config, 'UNSTRUCTURED_FORMAT_THRESHOLD', 0.5)
        except Exception:
            self._format_threshold = 0.5
        
        self.logger.info("="*60)
        self.logger.info("横向表格解析器 v2.5（按文件名组织输出）")  # ✅ v2.5
        self.logger.info(f"LLM: {'启用' if enable_llm else '禁用'}")
        self.logger.info(f"断点续传: {'启用' if enable_checkpoint else '禁用'}")
        # ✅ v2.5: 显示输出目录信息
        if excel_filename:
            self.logger.info(f"输出目录: {self.output_dir}")
            self.logger.info(f"  (按文件名组织: {os.path.basename(excel_filename)})")
        else:
            self.logger.info(f"输出目录: {self.output_dir}")
        self.logger.info("="*60)
    
    def parse_excel(self, file_path: str, resume: bool = False) -> Dict[str, Any]:
        """
        解析Excel文件（主入口）
        
        【完整流程】
        1. 加载Excel文件
        2. 检查checkpoint（如果resume=True）
        3. 遍历每个sheet，独立提取数据（显示进度条）
        4. 每个sheet处理完立即保存checkpoint
        5. 组装数据（分配ID，建立关联）
        6. 保存JSON文件
        7. 返回结果和统计信息
        
        Args:
            file_path: Excel文件路径
            resume: 是否从checkpoint恢复
            
        Returns:
            完整结果字典
        """
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"开始解析Excel文件")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"文件: {file_path}")

        # 提取文件名
        file_name = os.path.basename(file_path)
        
        # ✅ v2.5: 如果初始化时没有指定文件名，现在自动设置
        if not self.excel_filename:
            self.excel_filename = file_path
            # 更新输出目录为子文件夹
            self.output_dir = os.path.join(self.base_output_dir, file_name)
            os.makedirs(self.output_dir, exist_ok=True)
            self.logger.info(f"✅ 自动设置输出目录: {self.output_dir}")
        
        # ========== 1. 加载Excel ==========
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        wb = load_workbook(file_path, data_only=True)
        total_sheets = len(wb.worksheets)
        self.logger.info(f"加载成功，共{total_sheets}个sheets")

        # ========== 1.5. 从文件名提取交易日期 ==========
        try:
            from scripts.modules.date_extractor import extract_dates_from_filename
        except ImportError:
            try:
                from modules.date_extractor import extract_dates_from_filename
            except ImportError:
                def extract_dates_from_filename(fn):
                    return None, None
        
        start_date, end_date = extract_dates_from_filename(file_name)
        if start_date and end_date:
            self.logger.info(f"📅 提取到交易日期: {start_date} 至 {end_date}")
        
        self.transaction_start_date = start_date
        self.transaction_end_date = end_date
        
        # ========== ✅ 2. 检查checkpoint ==========
        checkpoint_file = None
        start_sheet_idx = 0
        sheets_data = []
        
        if resume and self.enable_checkpoint:
            checkpoint_file, sheets_data, start_sheet_idx = self._load_checkpoint(file_name)
            if checkpoint_file:
                self.logger.info(f"✅ 从checkpoint恢复: {checkpoint_file}")
                self.logger.info(f"   已完成: {start_sheet_idx}/{total_sheets} sheets")
        
        # ========== 3. 提取每个sheet的数据（带进度条）==========
        self.logger.info(f"\n{'='*60}")
        self.logger.info("开始提取数据")
        self.logger.info(f"{'='*60}")
        
        # ✅ 创建总进度条
        pbar = tqdm(
            total=total_sheets,
            desc="总进度",
            position=0,
            initial=start_sheet_idx,
            bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} sheets [{elapsed}<{remaining}]'
        )
        
        for idx, sheet in enumerate(wb.worksheets):
            # 跳过已处理的sheets
            if idx < start_sheet_idx:
                continue
            
            # 更新进度条描述
            pbar.set_description(f"处理: {sheet.title[:30]}")
            
            # 处理单个sheet（带子进度）
            sheet_data = self._process_sheet_with_progress(sheet, idx, total_sheets)
            sheets_data.append(sheet_data)
            
            # ✅ 每个sheet处理完立即保存checkpoint
            if self.enable_checkpoint:
                self._save_checkpoint(file_name, sheets_data, idx + 1)
            
            # 更新总进度条
            pbar.update(1)
        
        pbar.close()
        
        # ========== 4. 组装数据 ==========
        self.logger.info(f"\n{'='*60}")
        self.logger.info("组装数据")
        self.logger.info(f"{'='*60}")
        
        result = self.assembler.assemble(
            sheets_data,
            start_date=self.transaction_start_date,
            end_date=self.transaction_end_date
        )
        
        routes = result['routes']
        route_agents = result['route_agents']
        goods_details = result.get('goods_details', [])
        goods_total = result.get('goods_total', [])
        
        self.logger.info(f"组装了{len(sheets_data)}个sheets")
        self.logger.info(f"  组装了{len(routes)}条routes")
        self.logger.info(f"  组装了{len(route_agents)}个route_agents")
        self.logger.info(f"  组装了{len(goods_details)}个goods_details")
        self.logger.info(f"  组装了{len(goods_total)}个goods_total")
        
        # ========== 5. 保存JSON ==========
        self.logger.info(f"\n{'='*60}")
        self.logger.info("保存JSON文件")
        self.logger.info(f"{'='*60}")
        
        self._save_results(result)
        
        # ========== 6. 生成统计信息 ==========
        stats = self._generate_stats(result)
        result['stats'] = stats
        
        # ========== 7. 清理checkpoint ==========
        if self.enable_checkpoint and checkpoint_file:
            self._cleanup_checkpoint(checkpoint_file)
        
        # ========== 8. 显示最终统计 ==========
        self._print_final_stats(stats)
        
        return result
    
    def _process_sheet_with_progress(self, sheet, index: int, total: int) -> Dict[str, Any]:
        """
        处理单个sheet（带子进度条）
        
        Args:
            sheet: Excel sheet对象
            index: Sheet索引
            total: 总sheets数
            
        Returns:
            sheet_data字典
        """
        sheet_data = {
            'sheet_name': sheet.title,
            'sheet_index': index
        }

        # ── 格式检测：决定走规则路径还是LLM全量路径 ──
        fmt_type, fmt_confidence = self.format_detector.detect(sheet)
        self.logger.info(
            f"  📋 格式检测: {fmt_type} (置信度={fmt_confidence:.2f}, 阈值={self._format_threshold})"
        )

        # 如果格式混乱且LLM全量提取器可用 → 直接走LLM全量路径
        if fmt_type == 'unstructured' and self.llm_full_extractor is not None:
            self.logger.info(f"  🔀 格式混乱，切换至LLM全量提取模式")
            try:
                llm_result = self.llm_full_extractor.extract(sheet)
                sheet_data.update(llm_result)
                return sheet_data
            except Exception as e:
                self.logger.error(f"  ❌ LLM全量提取失败，回退到规则提取: {e}")
                # 失败时继续走规则提取，不直接返回

        # ── 标准规则提取路径（原有逻辑不变）──

        # ✅ 定义所有提取步骤
        steps = [
            ('Route', lambda: self.route_extractor.extract(sheet)),
            ('Agents', lambda: self.agent_extractor.extract(sheet)),
            ('Goods', lambda: self.goods_extractor.extract(sheet)),
            ('Fees', lambda: self._extract_fees_for_agents(sheet, sheet_data.get('agents', []))),
            ('Summary', lambda: self._extract_summaries_for_agents(sheet, sheet_data.get('agents', [])))
        ]
        
        # ✅ 创建子进度条
        step_pbar = tqdm(
            total=len(steps),
            desc=f"  [{index+1}/{total}] {sheet.title[:20]}",
            position=1,
            leave=False,
            bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} 步骤'
        )
        
        try:
            for step_name, step_func in steps:
                step_pbar.set_description(f"  [{index+1}/{total}] {sheet.title[:20]} - {step_name}")
                
                try:
                    if step_name == 'Route':
                        route = step_func()
                        sheet_data['route'] = route
                    elif step_name == 'Agents':
                        agents = step_func()
                        sheet_data['agents'] = agents
                    elif step_name == 'Goods':
                        goods_result = step_func()
                        sheet_data['goods'] = goods_result
                    elif step_name == 'Fees':
                        fees_list = step_func()
                        sheet_data['fees'] = fees_list
                    elif step_name == 'Summary':
                        summaries_list = step_func()
                        sheet_data['summaries'] = summaries_list
                
                except Exception as e:
                    self.logger.error(f"  ❌ {step_name}提取失败: {e}")
                
                step_pbar.update(1)
            
            step_pbar.close()
        
        except Exception as e:
            step_pbar.close()
            self.logger.error(f"  ❌ Sheet处理失败: {e}")
            
            # 返回空数据
            sheet_data['route'] = None
            sheet_data['agents'] = []
            sheet_data['goods'] = {'type': None, 'goods_details': None, 'goods_total': None}
            sheet_data['fees'] = []
            sheet_data['summaries'] = []
        
        return sheet_data
    
    def _extract_fees_for_agents(self, sheet, agents: List) -> List[Dict]:
        """为所有agents提取费用"""
        fees_list = []
        
        if not agents:
            return fees_list
        
        for agent_idx, agent in enumerate(agents):
            agent_col_idx = agent_idx + 2
            
            try:
                fees_result = self.fee_extractor.extract(
                    sheet, 
                    agent_col_idx=agent_col_idx
                )
                fees_list.append(fees_result)
            
            except Exception as e:
                self.logger.error(f"    ❌ Agent {agent_idx+1} 费用提取失败: {e}")
                fees_list.append({'fee_items': [], 'fee_totals': []})
        
        return fees_list
    
    def _extract_summaries_for_agents(self, sheet, agents: List) -> List:
        """为所有agents提取summary"""
        summaries_list = []
        
        if not agents:
            return summaries_list
        
        for agent_idx, agent in enumerate(agents):
            try:
                agent_start_row = get_agent_attr(agent, 'start_row')
                agent_end_row = get_agent_attr(agent, 'end_row')
                
                summary = self.summary_extractor.extract(
                    sheet,
                    agent_start_row=agent_start_row,
                    agent_end_row=agent_end_row
                )
                
                summaries_list.append(summary)
            
            except Exception as e:
                self.logger.error(f"    ❌ Agent {agent_idx+1} summary提取失败: {e}")
                from scripts.modules.extractors.summary_extractor import Summary
                summaries_list.append(Summary())
        
        return summaries_list
    
    # ========== ✅ Checkpoint相关方法 ==========
    
    def _save_checkpoint(self, file_name: str, sheets_data: List[Dict], completed_sheets: int):
        """
        保存checkpoint
        
        Args:
            file_name: Excel文件名
            sheets_data: 已处理的sheets数据
            completed_sheets: 已完成的sheets数量
        """
        if not self.enable_checkpoint:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_name = f"checkpoint_{file_name}_{timestamp}.json"
        checkpoint_path = os.path.join(self.checkpoint_dir, checkpoint_name)
        
        checkpoint_data = {
            'file_name': file_name,
            'completed_sheets': completed_sheets,
            'timestamp': timestamp,
            'sheets_data': sheets_data
        }
        
        try:
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            self.logger.warning(f"⚠️  保存checkpoint失败: {e}")
    
    def _load_checkpoint(self, file_name: str):
        """
        加载最新的checkpoint
        
        Args:
            file_name: Excel文件名
            
        Returns:
            (checkpoint_file, sheets_data, completed_sheets)
        """
        if not self.enable_checkpoint:
            return None, [], 0
        
        # 查找所有相关的checkpoint
        checkpoints = []
        for f in os.listdir(self.checkpoint_dir):
            if f.startswith(f"checkpoint_{file_name}_") and f.endswith('.json'):
                checkpoints.append(f)
        
        if not checkpoints:
            return None, [], 0
        
        # 选择最新的checkpoint
        latest_checkpoint = sorted(checkpoints)[-1]
        checkpoint_path = os.path.join(self.checkpoint_dir, latest_checkpoint)
        
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return (
                checkpoint_path,
                data.get('sheets_data', []),
                data.get('completed_sheets', 0)
            )
        
        except Exception as e:
            self.logger.error(f"❌ 加载checkpoint失败: {e}")
            return None, [], 0
    
    def _cleanup_checkpoint(self, checkpoint_file: str):
        """清理checkpoint文件"""
        try:
            if os.path.exists(checkpoint_file):
                os.remove(checkpoint_file)
                self.logger.info(f"✅ 已清理checkpoint: {checkpoint_file}")
        except Exception as e:
            self.logger.warning(f"⚠️  清理checkpoint失败: {e}")
    
    def resume_from_checkpoint(self, checkpoint_file: str) -> Dict[str, Any]:
        """
        从指定的checkpoint恢复
        
        Args:
            checkpoint_file: checkpoint文件路径
            
        Returns:
            完整结果字典
        """
        self.logger.info(f"从checkpoint恢复: {checkpoint_file}")
        
        # 加载checkpoint数据
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        file_name = data['file_name']
        
        # 重新运行解析（会自动从checkpoint恢复）
        return self.parse_excel(file_name, resume=True)
    
    # ========== 保持与v2.3兼容的方法 ==========
    
    def _save_results(self, result: Dict[str, Any]):
        """保存结果为JSON文件（与v2.3相同）"""
        # routes
        routes = result.get('routes', [])
        if routes:
            routes_file = os.path.join(self.output_dir, 'routes.json')
            with open(routes_file, 'w', encoding='utf-8') as f:
                json.dump(routes, f, ensure_ascii=False, indent=2)
            self.logger.info(f"  ✅ 已保存: {routes_file} ({len(routes)}条)")
        
        # route_agents
        route_agents = result.get('route_agents', [])
        if route_agents:
            agents_file = os.path.join(self.output_dir, 'route_agents.json')
            with open(agents_file, 'w', encoding='utf-8') as f:
                json.dump(route_agents, f, ensure_ascii=False, indent=2)
            self.logger.info(f"  ✅ 已保存: {agents_file} ({len(route_agents)}个)")
        
        # goods_details
        goods_details = result.get('goods_details', [])
        if goods_details:
            goods_details_file = os.path.join(self.output_dir, 'goods_details.json')
            with open(goods_details_file, 'w', encoding='utf-8') as f:
                json.dump(goods_details, f, ensure_ascii=False, indent=2)
            self.logger.info(f"  ✅ 已保存: {goods_details_file} ({len(goods_details)}个)")
        
        # goods_total
        goods_total = result.get('goods_total', [])
        if goods_total:
            goods_total_file = os.path.join(self.output_dir, 'goods_total.json')
            with open(goods_total_file, 'w', encoding='utf-8') as f:
                json.dump(goods_total, f, ensure_ascii=False, indent=2)
            self.logger.info(f"  ✅ 已保存: {goods_total_file} ({len(goods_total)}个)")
        
        # fee_items
        fee_items = result.get('fee_items', [])
        if fee_items:
            fee_items_file = os.path.join(self.output_dir, 'fee_items.json')
            with open(fee_items_file, 'w', encoding='utf-8') as f:
                json.dump(fee_items, f, ensure_ascii=False, indent=2)
            self.logger.info(f"  ✅ 已保存: {fee_items_file} ({len(fee_items)}项)")
        
        # fee_total
        fee_totals = result.get('fee_totals', [])
        if fee_totals:
            fee_total_file = os.path.join(self.output_dir, 'fee_total.json')
            with open(fee_total_file, 'w', encoding='utf-8') as f:
                json.dump(fee_totals, f, ensure_ascii=False, indent=2)
            self.logger.info(f"  ✅ 已保存: {fee_total_file} ({len(fee_totals)}项)")
        
        # summary
        summary = result.get('summary', [])
        if summary:
            summary_file = os.path.join(self.output_dir, 'summary.json')
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            self.logger.info(f"  ✅ 已保存: {summary_file} ({len(summary)}项)")
    
    def _generate_stats(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """生成统计信息（与v2.3相同）"""
        routes = result.get('routes', [])
        agents = result.get('route_agents', [])
        goods_details = result.get('goods_details', [])
        goods_total = result.get('goods_total', [])
        
        routes_with_agents = set()
        for agent in agents:
            routes_with_agents.add(agent['路线ID'])
        
        routes_with_goods = set()
        for goods in goods_details:
            routes_with_goods.add(goods['路线ID'])
        for goods in goods_total:
            routes_with_goods.add(goods['路线ID'])
        
        stats = {
            'total_routes': len(routes),
            'total_agents': len(agents),
            'total_goods_details': len(goods_details),
            'total_goods_total': len(goods_total),
            'routes_with_agents': len(routes_with_agents),
            'routes_with_goods': len(routes_with_goods),
            'routes_without_agents': len(routes) - len(routes_with_agents),
            'routes_without_goods': len(routes) - len(routes_with_goods),
            'avg_agents_per_route': len(agents) / len(routes) if routes else 0,
        }
        
        return stats
    
    def _print_final_stats(self, stats: Dict[str, Any]):
        """打印最终统计信息（与v2.3相同）"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info("最终统计")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Routes总数: {stats['total_routes']}")
        self.logger.info(f"  - 有Agents: {stats['routes_with_agents']}")
        self.logger.info(f"  - 无Agents: {stats['routes_without_agents']}")
        self.logger.info(f"  - 有Goods: {stats['routes_with_goods']}")
        self.logger.info(f"  - 无Goods: {stats['routes_without_goods']}")
        self.logger.info(f"Agents总数: {stats['total_agents']}")
        self.logger.info(f"  - 平均每条Route: {stats['avg_agents_per_route']:.2f}个")
        self.logger.info(f"Goods Details总数: {stats['total_goods_details']}")
        self.logger.info(f"Goods Total总数: {stats['total_goods_total']}")
        self.logger.info(f"{'='*60}\n")


__all__ = ['HorizontalTableParserV2Enhanced']