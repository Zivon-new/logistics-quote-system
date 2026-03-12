# scripts/dryrun_horizontal_parser.py
"""
横向表格解析器的测试运行器（LLM增强版 v2.0）
修复：LLM增强时传递完整原始文本，而不是只传递已提取的字段
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import json

from scripts.config import Config
from scripts.excel_reader import ExcelReader
from scripts.json_writer import JSONWriter
from scripts.logger_config import get_logger

# 导入解析模块
from scripts.modules.horizontal_table_parser import HorizontalTableParser
from scripts.modules.sheet_goods_scanner import SheetGoodsScanner
from scripts.modules.route_fields_enhancer import RouteFieldsEnhancer
from scripts.modules.llm_enhancer import LLMEnhancer


class HorizontalParserRunner:
    """横向表格解析器运行器（LLM增强版）"""
    
    def __init__(self, enable_llm: bool = True):
        """
        Args:
            enable_llm: 是否启用LLM增强
        """
        self.logger = get_logger(__name__)
        self.enable_llm = enable_llm and Config.ENABLE_LLM_ENHANCE
        
        # 初始化组件
        self.reader = ExcelReader()
        self.horizontal_parser = HorizontalTableParser()
        self.goods_scanner = SheetGoodsScanner()
        self.route_enhancer = RouteFieldsEnhancer()
        
        # [OK] 初始化LLM增强器
        if self.enable_llm:
            try:
                self.llm_enhancer = LLMEnhancer(api_key=Config.ZHIPU_API_KEY)
                self.logger.info("LLM增强器初始化成功")
                self.logger.info("[OK] LLM增强器已启用")
            except Exception as e:
                self.logger.error(f"LLM增强器初始化失败: {e}")
                self.enable_llm = False
                self.llm_enhancer = None
        else:
            self.llm_enhancer = None
            self.logger.info("[ERROR] LLM增强器未启用")
        
        # 全局计数器
        self.route_id_counter = 0
        self.agent_id_counter = 0
        self.goods_detail_id_counter = 0
        self.goods_total_id_counter = 0
        self.fee_item_id_counter = 0
        self.fee_total_id_counter = 0
        self.summary_id_counter = 0
        
        # LLM统计
        self.llm_enhanced_count = 0
        self.llm_success_count = 0
        
        self.logger.info("[OK] HorizontalParserRunner 初始化完成")
    
    def run(self, excel_path: str) -> Dict:
        """
        运行解析流程
        
        Args:
            excel_path: Excel文件路径
            
        Returns:
            包含所有表数据的字典
        """
        self.logger.info("=" * 60)
        self.logger.info(" 横向对比表格解析器 v4.0 (LLM增强版)")
        self.logger.info("=" * 60)
        
        # 读取Excel
        sheets_data = self.reader.read_excel_structured(excel_path)
        self.logger.info(f" 找到 {len(sheets_data)} 个 Excel 文件")
        
        # 初始化结果
        all_routes = []
        all_agents = []
        all_goods_details = []
        all_goods_total = []
        all_fee_items = []
        all_fee_total = []
        all_summaries = []
        
        # 提取文件名（用于日期提取）
        filename = os.path.basename(excel_path)
        
        # 处理每个sheet
        sheet_count = 0
        for sheet_name, sheet_rows in sheets_data.items():
            sheet_count += 1
            self.logger.info("")
            self.logger.info("  " + "=" * 60)
            self.logger.info(f"  [LIST] Sheet {sheet_count}/{len(sheets_data)}: {sheet_name}")
            self.logger.info("  " + "=" * 60)
            
            result = self._parse_single_sheet(
                sheet_name, 
                sheet_rows, 
                filename
            )
            
            # 合并结果
            all_routes.extend(result["routes"])
            all_agents.extend(result["route_agents"])
            all_goods_details.extend(result["goods_details"])
            all_goods_total.extend(result["goods_total"])
            all_fee_items.extend(result["fee_items"])
            all_fee_total.extend(result["fee_total"])
            all_summaries.extend(result["summaries"])
            
            self.logger.info("  [OK] 此 Sheet 处理完成")
            self.logger.info("")
        
        # 汇总统计
        summary_counts = {
            "routes": len(all_routes),
            "route_agents": len(all_agents),
            "goods_details": len(all_goods_details),
            "goods_total": len(all_goods_total),
            "fee_items": len(all_fee_items),
            "fee_total": len(all_fee_total),
            "summaries": len(all_summaries),
            "llm_enhanced": self.llm_enhanced_count,
            "llm_success": self.llm_success_count,
            "llm_success_rate": f"{self.llm_success_count/max(self.llm_enhanced_count, 1)*100:.1f}%"
        }
        
        return {
            "routes": all_routes,
            "route_agents": all_agents,
            "goods_details": all_goods_details,
            "goods_total": all_goods_total,
            "fee_items": all_fee_items,
            "fee_total": all_fee_total,
            "summary": all_summaries,
            "summary_counts": summary_counts
        }
    
    def _parse_single_sheet(
        self, 
        sheet_name: str, 
        sheet_rows: List[List[str]], 
        filename: str
    ) -> Dict:
        """解析单个sheet"""
        
        # 1. 扫描货物信息（在表格外）
        goods_scan = self.goods_scanner.scan_sheet(sheet_rows, sheet_name)
        if goods_scan:
            self.logger.info(f"      [PACK] Sheet扫描结果: 重量={goods_scan.get('weight')}, "
                           f"计费重量={goods_scan.get('chargeable_weight')}, "
                           f"体积={goods_scan.get('volume')}, "
                           f"货值={goods_scan.get('value')}")
            
            # 检测货物表格
            goods_table = goods_scan.get('goods_table')
            if goods_table:
                table_type = goods_table['table_type']
                goods_count = len(goods_table['goods_list'])
                self.logger.info(f"      [LIST] 检测到{table_type}货物表格: {goods_count}种货物")
        
        # 2. 解析横向表格
        quote_blocks = self.horizontal_parser.parse_sheet(sheet_rows, sheet_name, filename)
        
        if not quote_blocks:
            self.logger.warning(f"  [WARN] Sheet '{sheet_name}' 未发现有效的横向表格")
            return self._empty_result()
        
        self.logger.info(f"  [LIST] 解析Sheet: {sheet_name}, 行数: {len(sheet_rows)}")
        self.logger.info(f"  发现 {len(quote_blocks)} 个横向表格")
        
        # 3. 转换为数据库格式
        routes = []
        agents = []
        goods_details = []
        goods_total = []
        fee_items = []
        fee_total = []
        summaries = []
        
       # [NEW] 为每个QuoteBlock生成记录，使用shared route_id机制
        route_id_map = {}  # (起始地, 目的地, 途径地) -> route_id
        
        for qb in quote_blocks:
            # 3.1 Routes表 - 去重机制
            route_key = (qb.route.起始地, qb.route.目的地, qb.route.途径地)
            
            if route_key not in route_id_map:
                # 新路线，创建route记录
                route_dict = self._route_to_dict(qb.route, goods_scan, filename)
                routes.append(route_dict)
                route_id_map[route_key] = route_dict["路线ID"]
                
                if self.logger:
                    self.logger.debug(f"    [NEW] 新路线: {qb.route.起始地} -> {qb.route.目的地}, RouteID={route_dict['路线ID']}")
            else:
                # 路线已存在，使用共享的route_id
                if self.logger:
                    self.logger.debug(f"    [REUSE] 复用路线: {qb.route.起始地} -> {qb.route.目的地}, RouteID={route_id_map[route_key]}")
            
            # 获取共享的route_id
            shared_route_id = route_id_map[route_key]
            
            # 3.2 Route_Agents表 - 每个agent使用共享的route_id
            agent_dict = self._agent_to_dict(qb.agent, shared_route_id)
            
            # [OK] LLM增强（如果启用）
            if self.enable_llm and self._should_enhance(agent_dict):
                agent_dict = self._enhance_agent_with_llm(agent_dict, qb)
            
            agents.append(agent_dict)
            
            if self.logger:
                self.logger.debug(f"    [AGENT] 代理商={qb.agent.代理商}, AgentID={agent_dict['代理路线ID']}, 关联RouteID={shared_route_id}")
            
            # 3.3 Fee_Items表
            for fi in qb.fee_items:
                item_dict = self._fee_item_to_dict(fi, agent_dict["代理路线ID"])
                fee_items.append(item_dict)
            
            # 3.4 Fee_Total表
            if qb.fee_total:
                total_dict = self._fee_total_to_dict(qb.fee_total, agent_dict["代理路线ID"])
                fee_total.append(total_dict)
            
            # 3.5 Summary表
            if qb.summary:
                summary_dict = self._summary_to_dict(qb.summary, agent_dict["代理路线ID"])
                summaries.append(summary_dict)
        
        # 4. 添加交易日期（批量）
        if self.route_enhancer and routes:
            self.logger.info("  [DEBUG] [日期提取] 检查条件:")
            self.logger.info(f"      filename = {filename}")
            self.logger.info(f"      route_enhancer = {self.route_enhancer}")
            self.logger.info(f"      all_quotes数量 = {len(routes)}")
            
            start_date, end_date = self.route_enhancer.extract_transaction_dates(filename)
            
            if start_date and end_date:
                self.logger.info(f"  [DEBUG] [日期提取] 开始提取文件名: {filename}")
                self.logger.info(f"  [DEBUG] [日期提取] 提取结果: {start_date} 至 {end_date}")
                
                for route in routes:
                    route["交易开始日期"] = start_date
                    route["交易结束日期"] = end_date
                
                self.logger.info(f"  [OK] [日期提取] 已为 {len(routes)} 个routes添加交易日期: {start_date} 至 {end_date}")
            else:
                self.logger.warning(f"  [WARN] [日期提取] 无法从文件名提取日期: {filename}")
        
        # 5. 去重处理
        routes = self._deduplicate_routes(routes)
        self.logger.info(f"  [OK] Sheet解析完成: 提取 {len(routes)} 个QuoteBlock (去重后)")
        
        # 6. 从货物表格创建goods_details（如果有）
        if goods_scan and goods_scan.get('goods_table'):
            goods_table = goods_scan['goods_table']
            table_type = goods_table['table_type']
            
            # 确定要关联的route_id（使用第一个route）
            if routes:
                target_route_id = routes[0]["路线ID"]
                
                if table_type == "simple":
                    # 简单表格：只有名称、规格、重量
                    self.logger.info(f"  [PACK] 解析到 {len(goods_table['goods_list'])} 个报价块")
                    for goods in goods_table['goods_list']:
                        self.goods_detail_id_counter += 1
                        goods_details.append({
                            "货物明细ID": self.goods_detail_id_counter,
                            "路线ID": target_route_id,
                            "货物名称": goods.get('货物名称', '未知货物'),
                            "是否新品": None,
                            "货物种类": None,
                            "数量": 1,
                            "单价": None,
                            "币种": None,
                            "重量(/kg)": goods.get('重量'),
                            "总重量(/kg)": None,
                            "总价": None,
                            "备注": goods.get('规格')
                        })
                    self.logger.info(f"      [OK] 创建{len(goods_table['goods_list'])}条goods_details记录(simple表格)")
                
                elif table_type == "complex":
                    # 复杂表格：有新/旧、货物种类、型号、数量、单价等
                    for goods in goods_table['goods_list']:
                        self.goods_detail_id_counter += 1
                        
                        # 判断是否新品
                        is_new = goods.get('新/旧') == '新' if '新/旧' in goods else None
                        
                        goods_details.append({
                            "货物明细ID": self.goods_detail_id_counter,
                            "路线ID": target_route_id,
                            "货物名称": goods.get('货物种类', '未知货物'),
                            "是否新品": is_new,
                            "货物种类": goods.get('型号'),
                            "数量": goods.get('数量', 1),
                            "单价": goods.get('单价'),
                            "币种": None,
                            "重量(/kg)": None,
                            "总重量(/kg)": None,
                            "总价": None,
                            "备注": goods.get('物流地址')
                        })
                    self.logger.info(f"      [OK] 创建{len(goods_table['goods_list'])}条goods_details记录(complex表格)")
        
        return {
            "routes": routes,
            "route_agents": agents,
            "goods_details": goods_details,
            "goods_total": goods_total,
            "fee_items": fee_items,
            "fee_total": fee_total,
            "summaries": summaries
        }
    
    # ========== [OK] 修复的方法 ==========
    
    def _extract_agent_text(self, quote_block) -> List[str]:
        """
        提取代理商相关的原始文本（修复版）
        
        修复策略：
        1. 使用route._raw作为主要上下文（包含完整路线行信息）
        2. 添加agent的已提取字段
        3. 为缺失字段添加提示，让LLM知道需要提取
        """
        lines = []
        
        # [OK] 策略1: 使用route._raw（最重要的上下文）
        if hasattr(quote_block, 'route') and hasattr(quote_block.route, '_raw'):
            route_raw = quote_block.route._raw
            if route_raw:
                lines.append("【路线原始文本】")
                lines.append(route_raw)
                lines.append("")  # 空行分隔
        
        # [OK] 策略2: 添加路线结构化信息作为上下文
        if hasattr(quote_block, 'route'):
            route = quote_block.route
            lines.append("【路线信息】")
            if hasattr(route, '起始地') and route.起始地:
                lines.append(f"起始地: {route.起始地}")
            if hasattr(route, '目的地') and route.目的地:
                lines.append(f"目的地: {route.目的地}")
            if hasattr(route, '途径地') and route.途径地:
                lines.append(f"途径地: {route.途径地}")
            if hasattr(route, '贸易备注') and route.贸易备注:
                lines.append(f"备注: {route.贸易备注}")
            lines.append("")  # 空行分隔
        
        # [OK] 策略3: 添加agent的已知信息（包括空字段）
        agent = quote_block.agent
        lines.append("【代理商信息】")
        
        # 已知字段
        if agent.代理商:
            lines.append(f"代理商: {agent.代理商}")
        else:
            lines.append("代理商: (待提取)")
        
        if agent.运输方式:
            lines.append(f"运输方式: {agent.运输方式}")
        else:
            lines.append("运输方式: (待提取)")
        
        if agent.贸易类型:
            lines.append(f"贸易类型: {agent.贸易类型}")
        else:
            lines.append("贸易类型: (待提取)")
        
        if agent.时效:
            lines.append(f"时效: {agent.时效}")
        else:
            lines.append("时效: (待提取)")
        
        if agent.不含:
            lines.append(f"不含: {agent.不含}")
        else:
            lines.append("不含: (待提取)")
        
        if agent.代理备注:
            lines.append(f"代理备注: {agent.代理备注}")
        
        if agent.是否赔付 == "1":
            lines.append(f"是否赔付: 是")
            if agent.赔付内容:
                lines.append(f"赔付内容: {agent.赔付内容}")
        
        # 如果lines为空，至少给一些提示
        if not lines:
            lines = ["(无可用文本信息，请根据代理商名称推断)"]
        
        self.logger.debug(f"  [NOTE] 为LLM准备了 {len(lines)} 行上下文")
        
        return lines
    
    def _should_enhance(self, agent_dict: Dict) -> bool:
        """
        判断是否需要LLM增强
        
        条件：有任一关键字段为空
        """
        key_fields = ["代理商", "运输方式", "贸易类型", "时效", "不含"]
        
        # 计算置信度：非空字段数 / 总字段数
        filled_count = sum(1 for field in key_fields if agent_dict.get(field))
        confidence = filled_count / len(key_fields)
        
        # 置信度低于0.8时启用LLM
        should_enhance = confidence < 0.8
        
        if should_enhance:
            self.logger.debug(f"   置信度: {confidence:.2f}, 需要LLM增强")
        
        return should_enhance
    
    def _enhance_agent_with_llm(self, agent_dict: Dict, quote_block) -> Dict:
        """使用LLM增强代理商信息（修复版）"""
        self.llm_enhanced_count += 1
        
        # [OK] 使用修复后的方法获取完整文本
        agent_lines = self._extract_agent_text(quote_block)
        text = "\n".join(agent_lines)
        
        # [OK] 添加调试日志
        self.logger.debug(f"  [NOTE] 传递给LLM的文本 ({len(agent_lines)}行):")
        for i, line in enumerate(agent_lines[:10], 1):  # 只显示前10行
            self.logger.debug(f"    {i}. {line[:100]}")
        
        self.logger.info(f"  [AI] 置信度较低调用LLM增强 (#{self.llm_enhanced_count})")
        
        try:
            llm_result = self.llm_enhancer.extract_agent_info(
                text=text,
                regex_result=agent_dict
            )
            
            if llm_result:
                # [OK] 添加调试：查看LLM返回了什么
                self.logger.debug(f"  [DEBUG] LLM返回结果:")
                for key, value in llm_result.items():
                    self.logger.debug(f"    {key}: {value}")
                
                # 合并结果
                merged = self._merge_agent_results(agent_dict, llm_result)
                
                # [OK] 添加调试：查看合并后的结果
                self.logger.debug(f"  [DEBUG] 合并后结果:")
                for key, value in merged.items():
                    if key not in ["代理路线ID", "路线ID", "赔付内容", "时效备注"]:
                        self.logger.debug(f"    {key}: {value}")
                
                self.llm_success_count += 1
                self.logger.info(f"  [OK] LLM增强成功")
                return merged
            else:
                self.logger.warning(f"  [WARN] LLM返回空结果使用正则结果")
                return agent_dict
        
        except Exception as e:
            self.logger.error(f"  [ERROR] LLM增强失败: {e}", exc_info=True)
            return agent_dict
    
    def _merge_agent_results(self, regex_result: Dict, llm_result: Dict) -> Dict:
        """
        合并正则和LLM结果
        
        策略：
        1. LLM提取的非空值优先
        2. 正则的值作为fallback
        """
        merged = regex_result.copy()
        
        # LLM提取的字段列表
        llm_fields = ["代理商", "运输方式", "贸易类型", "时效", "不含", "是否赔付"]
        
        for field in llm_fields:
            if field in llm_result:
                llm_value = llm_result[field]
                # 只有LLM返回了有效值才覆盖
                if llm_value is not None and llm_value != "" and llm_value != "null":
                    merged[field] = llm_value
                    self.logger.debug(f"    [OK] LLM提取 {field}: {llm_value}")
        
        return merged
    
    # ========== 数据转换方法 ==========
    
    def _route_to_dict(self, route, goods_scan: Dict, filename: str) -> Dict:
        """Route对象 -> routes表字典"""
        self.route_id_counter += 1
        
        # 基础路线信息
        result = {
            "路线ID": self.route_id_counter,
            "起始地": route.起始地 if hasattr(route, '起始地') else None,
            "目的地": route.目的地 if hasattr(route, '目的地') else None,
            "途径地": route.途径地 if hasattr(route, '途径地') else None,
            "交易开始日期": None,
            "交易结束日期": None,
            "实际重量(/kg)": None,
            "计费重量(/kg)": None,
            "总体积(/cbm)": None,
            "货值": None
        }
        
        # 从goods_scan补充信息
        if goods_scan:
            result["实际重量(/kg)"] = goods_scan.get('weight')
            result["计费重量(/kg)"] = goods_scan.get('chargeable_weight')
            result["总体积(/cbm)"] = goods_scan.get('volume')
            result["货值"] = goods_scan.get('value')
        
        return result
    
    def _agent_to_dict(self, agent, route_id: int) -> Dict:
        """Agent对象 -> route_agents表字典"""
        self.agent_id_counter += 1
        
        return {
            "代理路线ID": self.agent_id_counter,
            "路线ID": route_id,
            "代理商": agent.代理商 if hasattr(agent, '代理商') else None,
            "运输方式": agent.运输方式 if hasattr(agent, '运输方式') else None,
            "贸易类型": agent.贸易类型 if hasattr(agent, '贸易类型') else None,
            "代理备注": agent.代理备注 if hasattr(agent, '代理备注') else None,
            "时效": agent.时效 if hasattr(agent, '时效') else None,
            "时效备注": agent.时效备注 if hasattr(agent, '时效备注') else None,
            "不含": agent.不含 if hasattr(agent, '不含') else None,
            "是否赔付": agent.是否赔付 if hasattr(agent, '是否赔付') else "0",
            "赔付内容": agent.赔付内容 if hasattr(agent, '赔付内容') else None
        }
    
    def _goods_detail_to_dict(self, goods_detail, route_id: int) -> Dict:
        """GoodsDetail对象 -> goods_details表字典"""
        self.goods_detail_id_counter += 1
        
        return {
            "货物明细ID": self.goods_detail_id_counter,
            "路线ID": route_id,
            "货物名称": getattr(goods_detail, '货物名称', '未知货物'),
            "是否新品": getattr(goods_detail, '是否新品', None),
            "货物种类": getattr(goods_detail, '货物种类', None),
            "数量": getattr(goods_detail, '数量', None),
            "单价": getattr(goods_detail, '单价', None),
            "币种": getattr(goods_detail, '币种', None),
            "重量(/kg)": getattr(goods_detail, '重量', None),
            "总重量(/kg)": None,
            "总价": None,
            "备注": getattr(goods_detail, '备注', None)
        }
    
    def _goods_total_to_dict(self, goods_total, route_id: int) -> Dict:
        """GoodsTotal对象 -> goods_total表字典"""
        self.goods_total_id_counter += 1
        
        return {
            "整单货物ID": self.goods_total_id_counter,
            "路线ID": route_id,
            "货物名称": getattr(goods_total, '货物名称', '混合货物'),
            "实际重量(/kg)": getattr(goods_total, '实际重量', None),
            "总体积(/cbm)": getattr(goods_total, '总体积', 0.0),
            "备注": getattr(goods_total, '备注', None)
        }
    
    def _fee_item_to_dict(self, fee_item, agent_id: int) -> Dict:
        """FeeItem对象 -> fee_items表字典"""
        self.fee_item_id_counter += 1
        
        return {
            "费用明细ID": self.fee_item_id_counter,
            "代理路线ID": agent_id,
            "费用类型": getattr(fee_item, '费用类型', None),
            "单价": getattr(fee_item, '单价', None),
            "单位": getattr(fee_item, '单位', None),
            "数量": getattr(fee_item, '数量', None),
            "币种": getattr(fee_item, '币种', 'RMB'),
            "备注": getattr(fee_item, '备注', None)
        }
    
    def _fee_total_to_dict(self, fee_total, agent_id: int) -> Dict:
        """FeeTotal对象 -> fee_total表字典"""
        self.fee_total_id_counter += 1
        
        return {
            "整单费用ID": self.fee_total_id_counter,
            "代理路线ID": agent_id,
            "费用名称": getattr(fee_total, '费用名称', None),
            "原币金额": getattr(fee_total, '原币金额', None),
            "币种": getattr(fee_total, '币种', 'RMB'),
            "备注": getattr(fee_total, '备注', None)
        }
    
    def _summary_to_dict(self, summary, agent_id: int) -> Dict:
        """Summary对象 -> summary表字典"""
        self.summary_id_counter += 1
        
        return {
            "汇总ID": self.summary_id_counter,
            "代理路线ID": agent_id,
            "小计": None,
            "税率": getattr(summary, '税率', None),
            "税金": None,
            "汇损率": getattr(summary, '汇损率', None),
            "汇损": getattr(summary, '汇损', None),
            "总计": None,
            "备注": getattr(summary, '备注', None)
        }
    
    def _deduplicate_routes(self, routes: List[Dict]) -> List[Dict]:
        if self.logger:
            self.logger.info(f"  [INFO] routes已在生成时去重，共{len(routes)}条唯一路线")
        return routes
    
    def _empty_result(self) -> Dict:
        """返回空结果"""
        return {
            "routes": [],
            "route_agents": [],
            "goods_details": [],
            "goods_total": [],
            "fee_items": [],
            "fee_total": [],
            "summaries": []
        }


# ========== 主程序入口 ==========

def main():
    """主函数"""
    # 设置日志
    from scripts.logger_config import LoggerConfig
    LoggerConfig.setup(log_level="INFO", console_output=True, file_output=True)
    
    logger = get_logger(__name__)
    
    # Excel文件路径
    excel_file = Path(Config.RAW_DATA_DIR) / "国际部成本汇总2025.10.20-2025.10.24.xlsx"
    
    if not excel_file.exists():
        logger.error(f"[ERROR] Excel文件不存在: {excel_file}")
        logger.info("请将Excel文件放在 data/raw/ 目录下")
        return
    
    # 运行解析器（启用LLM）
    runner = HorizontalParserRunner(enable_llm=True)
    result = runner.run(str(excel_file))
    
    # 写入JSON
    logger.info("=" * 60)
    logger.info(" 输出结果")
    logger.info("=" * 60)
    
    writer = JSONWriter(Config.CLEAN_DATA_DIR)
    
    # 写入各个表
    writer.write_table("routes", result["routes"])
    writer.write_table("route_agents", result["route_agents"])
    writer.write_table("goods_details", result["goods_details"])
    writer.write_table("goods_total", result["goods_total"])
    writer.write_table("fee_items", result["fee_items"])
    writer.write_table("fee_total", result["fee_total"])
    writer.write_table("summary", result["summary"])
    
    # 写入统计信息
    summary_path = Path(Config.CLEAN_DATA_DIR) / "summary_counts.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(result["summary_counts"], f, ensure_ascii=False, indent=2)
    
    logger.info(f"[OK] 统计数据: {summary_path}")
    
    # 打印LLM使用统计
    if runner.enable_llm and runner.llm_enhancer:
        runner.llm_enhancer.print_stats()


if __name__ == "__main__":
    main()