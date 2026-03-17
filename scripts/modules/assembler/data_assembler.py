# scripts/modules/assembler/data_assembler.py
"""
数据组装器 v2.2 - 新增summary组装

【v2.2 更新】
✅ 支持 summary 组装
✅ 每个代理商对应一个summary记录

【v2.1 更新】
✅ 支持 goods_details 组装
✅ 支持 goods_total 组装
✅ 自动关联 goods 到 routes

【架构角色】
负责将各个独立提取器的结果组装成符合数据库字段格式的JSON数据

【核心功能】
1. 为routes分配路线ID
2. 为agents分配代理路线ID并关联到route
3. 为goods分配货物ID并关联到route
4. 为summary分配汇总ID并关联到agent ✅ 新增
5. 输出完全匹配数据库表结构的JSON
6. 验证数据完整性

【数据库表对应关系】
- routes.json → routes表
- route_agents.json → route_agents表
- goods_details.json → goods_details表
- goods_total.json → goods_total表
- fee_items.json → fee_items表
- fee_total.json → fee_total表
- summary.json → summary表 ✅ 新增
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from collections import defaultdict

from scripts.modules.extractors.import_tax_extractor import parse_import_tax_text


class DataAssembler:
    """
    数据组装器 v2.1
    
    输出完全符合数据库字段格式的JSON数据
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化数据组装器
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
        self.validation_errors = []
    
    def assemble(
        self, 
        sheets_data: List[Dict[str, Any]], 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        组装数据
        
        【组装流程】
        1. 提取routes数据并分配路线ID
        2. 提取agents数据并分配代理路线ID
        3. 提取goods数据并分配货物ID ✅ 新增
        4. 建立关联关系
        5. 返回符合数据库格式的数据
        
        Args:
            sheets_data: 每个sheet的提取结果列表
        
        Returns:
            {
                'routes': [Route字典, ...],
                'route_agents': [Agent字典, ...],
                'goods_details': [GoodsDetail字典, ...], ✅ 新增
                'goods_total': [GoodsTotal字典, ...],   ✅ 新增
                'validation_errors': [错误信息, ...]
            }
        """
        if self.logger:
            self.logger.info(f"开始组装数据，共{len(sheets_data)}个sheets")
        
        self.validation_errors = []

        # 保存日期到实例变量
        self.transaction_start_date = start_date
        self.transaction_end_date = end_date

        # ========== 1. 组装routes数据 ==========
        routes = []
        route_id_counter = 1
        
        # 记录每个sheet_index对应的路线ID（用于关联）
        sheet_to_route_id = {}
        
        for sheet_data in sheets_data:
            route_obj = sheet_data.get('route')
            if not route_obj:
                continue
            
            # 转换为符合数据库字段的格式
            route_dict = self._convert_route_to_db_format(
                route_obj, 
                route_id_counter
            )
            
            routes.append(route_dict)
            
            # 记录映射关系
            sheet_index = sheet_data.get('sheet_index', len(sheet_to_route_id))
            sheet_to_route_id[sheet_index] = route_id_counter
            
            route_id_counter += 1
        
        if self.logger:
            self.logger.info(f"  组装了{len(routes)}条routes")
        
        # ========== 2. 组装route_agents数据 ==========
        route_agents = []
        agent_id_counter = 1
        
        for sheet_data in sheets_data:
            agents_list = sheet_data.get('agents', [])
            sheet_index = sheet_data.get('sheet_index', 0)
            
            # 获取该sheet对应的路线ID
            route_id = sheet_to_route_id.get(sheet_index)
            if not route_id:
                continue
            
            for agent_obj in agents_list:
                # 转换为符合数据库字段的格式
                agent_dict = self._convert_agent_to_db_format(
                    agent_obj,
                    agent_id_counter,
                    route_id
                )
                
                route_agents.append(agent_dict)
                agent_id_counter += 1
        
        if self.logger:
            self.logger.info(f"  组装了{len(route_agents)}个route_agents")
        
        # ========== ✅ 3. 新增：组装goods_details和goods_total ==========
        goods_details_all = []
        goods_total_all = []
        goods_detail_id_counter = 1
        goods_total_id_counter = 1
        
        for sheet_data in sheets_data:
            goods_result = sheet_data.get('goods')
            sheet_index = sheet_data.get('sheet_index', 0)
            
            # 获取该sheet对应的路线ID
            route_id = sheet_to_route_id.get(sheet_index)
            if not route_id or not goods_result:
                continue
            
            # 判断货物类型
            goods_type = goods_result.get('type')
            
            if goods_type == 'details':
                # 多个货物明细
                goods_list = goods_result.get('goods_details', [])
                for goods_obj in goods_list:
                    goods_dict = self._convert_goods_detail_to_db_format(
                        goods_obj,
                        goods_detail_id_counter,
                        route_id
                    )
                    goods_details_all.append(goods_dict)
                    goods_detail_id_counter += 1
            
            elif goods_type == 'total':
                # ✅ 修改：支持goods_total返回List
                goods_data = goods_result.get('goods_total')
                
                # 兼容两种情况：单个对象 或 列表
                if goods_data:
                    # 如果是列表，遍历处理
                    if isinstance(goods_data, list):
                        for goods_obj in goods_data:
                            goods_dict = self._convert_goods_total_to_db_format(
                                goods_obj,
                                goods_total_id_counter,
                                route_id
                            )
                            goods_total_all.append(goods_dict)
                            goods_total_id_counter += 1
                    else:
                        # 如果是单个对象，直接处理（向后兼容）
                        goods_dict = self._convert_goods_total_to_db_format(
                            goods_data,
                            goods_total_id_counter,
                            route_id
                        )
                        goods_total_all.append(goods_dict)
                        goods_total_id_counter += 1
        
        if self.logger:
            self.logger.info(f"  组装了{len(goods_details_all)}个goods_details")
            self.logger.info(f"  组装了{len(goods_total_all)}个goods_total")
        
        # ========== ✅ 4. 新增：组装fee_items和fee_totals ==========
        fee_items_all = []
        fee_totals_all = []
        fee_item_id_counter = 1
        fee_total_id_counter = 1
        
        # 记录每个sheet_index对应的agent_id（用于关联费用）
        sheet_agent_to_id = {}
        
        # 先建立映射关系
        for sheet_data in sheets_data:
            agents_list = sheet_data.get('agents', [])
            sheet_index = sheet_data.get('sheet_index', 0)
            
            for agent_idx, agent_obj in enumerate(agents_list):
                # 计算agent_id（与前面的agent_id_counter保持一致）
                # 累加前面所有sheets的agents数量
                prev_sheets = sheets_data[:sheets_data.index(sheet_data)]
                prev_agent_count = sum(len(s.get('agents', [])) for s in prev_sheets)
                agent_id = prev_agent_count + agent_idx + 1
                
                key = (sheet_index, agent_idx)
                sheet_agent_to_id[key] = agent_id
        
        # 组装费用数据
        for sheet_data in sheets_data:
            fees_list = sheet_data.get('fees', [])
            sheet_index = sheet_data.get('sheet_index', 0)
            
            for agent_idx, fees_dict in enumerate(fees_list):
                if not fees_dict:
                    continue
                
                # 获取该agent对应的agent_id
                key = (sheet_index, agent_idx)
                agent_id = sheet_agent_to_id.get(key)
                
                if not agent_id:
                    continue
                
                # 组装fee_items
                fee_items = fees_dict.get('fee_items', [])
                for fee_item_obj in fee_items:
                    fee_item_dict = self._convert_fee_item_to_db_format(
                        fee_item_obj,
                        fee_item_id_counter,
                        agent_id
                    )
                    fee_items_all.append(fee_item_dict)
                    fee_item_id_counter += 1
                
                # 组装fee_totals
                fee_totals = fees_dict.get('fee_totals', [])
                for fee_total_obj in fee_totals:
                    fee_total_dict = self._convert_fee_total_to_db_format(
                        fee_total_obj,
                        fee_total_id_counter,
                        agent_id
                    )
                    fee_totals_all.append(fee_total_dict)
                    fee_total_id_counter += 1
        
        if self.logger:
            self.logger.info(f"  组装了{len(fee_items_all)}个fee_items")
            self.logger.info(f"  组装了{len(fee_totals_all)}个fee_totals")
        
        # ========== ✅ 5. 新增：组装summary ==========
        summaries_all = []
        summary_id_counter = 1
        
        for sheet_data in sheets_data:
            summaries_list = sheet_data.get('summaries', [])
            sheet_index = sheet_data.get('sheet_index', 0)
            
            for agent_idx, summary_obj in enumerate(summaries_list):
                if not summary_obj:
                    continue
                
                # 获取该agent对应的agent_id
                key = (sheet_index, agent_idx)
                agent_id = sheet_agent_to_id.get(key)
                
                if not agent_id:
                    continue
                
                # 转换为符合数据库字段的格式
                summary_dict = self._convert_summary_to_db_format(
                    summary_obj,
                    summary_id_counter,
                    agent_id
                )
                
                summaries_all.append(summary_dict)
                summary_id_counter += 1
        
        if self.logger:
            self.logger.info(f"  组装了{len(summaries_all)}个summary")

        # ========== ✅ 6. 新增：从进口税率原文解析 import_tax_items ==========
        import_tax_items_all = []
        import_tax_item_id_counter = 1

        for summary_idx, summary_dict in enumerate(summaries_all):
            raw_text = summary_dict.get('进口税率原文')
            if not raw_text:
                continue
            agent_id_for_tax = summary_dict.get('代理路线ID')
            items = parse_import_tax_text(raw_text)
            for item in items:
                d = item.to_dict()
                d['税项ID'] = import_tax_item_id_counter
                d['代理路线ID'] = agent_id_for_tax
                import_tax_items_all.append(d)
                import_tax_item_id_counter += 1

        if self.logger:
            self.logger.info(f"  解析了{len(import_tax_items_all)}条import_tax_items")

        # ========== 8. 验证数据 ==========
        self._validate_data(routes, route_agents, goods_details_all, goods_total_all)

        # ========== 9. 返回结果 ==========
        result = {
            'routes': routes,
            'route_agents': route_agents,
            'goods_details': goods_details_all,
            'goods_total': goods_total_all,
            'fee_items': fee_items_all,
            'fee_totals': fee_totals_all,
            'summary': summaries_all,
            'import_tax_items': import_tax_items_all,
            'validation_errors': self.validation_errors
        }
        
        return result
    
    def _convert_route_to_db_format(self, route_obj, route_id: int) -> Dict[str, Any]:
        """
        将Route对象转换为符合routes表字段的字典
        
        【v2.0增强】兼容Route对象和字典两种格式
        
        【routes表字段】
        - 路线ID (int)
        - 起始地 (varchar(100))
        - 途径地 (varchar(100))
        - 目的地 (varchar(100))
        - 交易开始日期 (date)
        - 交易结束日期 (date)
        - 实际重量(/kg) (decimal(18,2))
        - 计费重量(/kg) (decimal(18,2))
        - 总体积(/cbm) (decimal(18,3))
        - 货值 (decimal(18,2))
        
        Args:
            route_obj: Route对象或字典
            route_id: 分配的路线ID
        
        Returns:
            符合routes表字段的字典
        """
        # 兼容对象和字典两种格式
        def get_value(obj, *keys):
            """从对象或字典中获取值（支持多个key尝试）"""
            for key in keys:
                if isinstance(obj, dict):
                    value = obj.get(key)
                else:
                    value = getattr(obj, key, None)
                if value is not None:
                    return value
            return None
        
        # 获取route的各个字段
        origin = get_value(route_obj, '起始地', 'origin')
        destination = get_value(route_obj, '目的地', 'destination')
        via = get_value(route_obj, '途径地', 'via')
        
        # 重量、体积、货值
        weight = get_value(route_obj, 'weight', '实际重量')
        volume = get_value(route_obj, 'volume', '总体积')
        value = get_value(route_obj, 'value', '货值')
        value_currency = get_value(route_obj, 'value_currency', '货值币种') or 'RMB'
        
        # 交易日期（优先使用route对象的日期，否则使用文件名提取的日期）
        start_date = get_value(route_obj, '交易开始日期') or getattr(self, 'transaction_start_date', None)
        end_date = get_value(route_obj, '交易结束日期') or getattr(self, 'transaction_end_date', None)
        
        # 构建符合数据库字段的字典
        route_dict = {
            '路线ID': route_id,
            '起始地': origin or '',
            '途径地': via,
            '目的地': destination or '',
            '交易开始日期': self._format_date(start_date),
            '交易结束日期': self._format_date(end_date),
            '实际重量(/kg)': self._format_decimal(weight, 2),
            '计费重量(/kg)': self._format_decimal(weight, 2),  # 默认等于实际重量
            '总体积(/cbm)': self._format_decimal(volume, 3),
            '货值': self._format_decimal(value, 2),
            '货值币种': value_currency
        }
        
        return route_dict
    
    def _convert_agent_to_db_format(self, agent_obj, agent_id: int, route_id: int) -> Dict[str, Any]:
        """
        将Agent对象转换为符合route_agents表字段的字典
        
        【v2.0增强】兼容Agent对象和字典两种格式
        
        【route_agents表字段】
        - 代理路线ID (int)
        - 路线ID (int)
        - 代理商 (varchar(200))
        - 运输方式 (varchar(100))
        - 贸易类型 (varchar(100))
        - 代理备注 (varchar(255))
        - 时效 (varchar(50))
        - 时效备注 (varchar(255))
        - 不含 (varchar(511))
        - 是否赔付 (varchar(255))
        - 赔付内容 (varchar(255))
        
        Args:
            agent_obj: Agent对象或字典
            agent_id: 分配的代理路线ID
            route_id: 关联的路线ID
        
        Returns:
            符合route_agents表字段的字典
        """
        # 兼容对象和字典两种格式
        def get_value(obj, *keys):
            """从对象或字典中获取值（支持多个key尝试）"""
            for key in keys:
                if isinstance(obj, dict):
                    value = obj.get(key)
                else:
                    value = getattr(obj, key, None)
                if value is not None:
                    return value
            return None
        
        # 获取agent的各个字段
        agent_name = get_value(agent_obj, '代理商', 'agent_name')
        remark = get_value(agent_obj, '代理备注', 'remark')

        # 时效相关
        timeliness = get_value(agent_obj, '时效', 'timeliness')
        timeliness_remark = get_value(agent_obj, '时效备注', 'timeliness_remark')
        timeliness_days = get_value(agent_obj, '时效天数')

        # 赔付相关
        is_compensate = get_value(agent_obj, '是否赔付', 'is_compensate')
        compensate_content = get_value(agent_obj, '赔付内容', 'compensate_content')

        # 不含内容
        not_include = get_value(agent_obj, '不含', 'not_include')

        # 运输方式和贸易类型
        transport_method = get_value(agent_obj, '运输方式')
        trade_type = get_value(agent_obj, '贸易类型')

        # 构建符合数据库字段的字典
        agent_dict = {
            '代理路线ID': agent_id,
            '路线ID': route_id,
            '代理商': agent_name or '',
            '运输方式': transport_method,
            '贸易类型': trade_type,
            '代理备注': remark,
            '时效': timeliness,
            '时效备注': timeliness_remark,
            '时效天数': timeliness_days,
            '不含': not_include,
            '是否赔付': self._format_boolean(is_compensate),
            '赔付内容': compensate_content
        }

        return agent_dict
    
    def _convert_goods_detail_to_db_format(self, goods_obj, goods_id: int, route_id: int) -> Dict[str, Any]:
        """
        ✅ 新增：将GoodsDetail对象转换为符合goods_details表字段的字典
        
        【goods_details表字段】
        - 货物ID (int)
        - 路线ID (int)
        - 货物名称 (varchar(200))
        - 是否新品 (tinyint(1))
        - 货物种类 (varchar(100))
        - 数量 (decimal(18,3))
        - 单价 (decimal(18,4))
        - 币种 (varchar(20))
        - 重量(/kg) (decimal(18,3)) - 单个重量
        - 总重量(/kg) (decimal(18,3)) - 数量×单重
        - 总价 (decimal(18,2))
        - 备注 (varchar(255))
        
        Args:
            goods_obj: GoodsDetail对象
            goods_id: 分配的货物ID
            route_id: 关联的路线ID
        
        Returns:
            符合goods_details表字段的字典
        """
        def get_value(obj, *keys):
            for key in keys:
                if isinstance(obj, dict):
                    value = obj.get(key)
                else:
                    value = getattr(obj, key, None)
                if value is not None:
                    return value
            return None
        
        # 计算原币金额 = 单价 × 数量（若未直接提供）
        unit_price = self._format_decimal(get_value(goods_obj, '单价'), 4)
        qty = self._format_decimal(get_value(goods_obj, '数量'), 3)
        total_price = self._format_decimal(get_value(goods_obj, '总价'), 2)
        if total_price is None and unit_price and qty:
            total_price = self._format_decimal(unit_price * qty, 2)

        goods_dict = {
            '货物ID': goods_id,
            '路线ID': route_id,
            '货物名称': get_value(goods_obj, '货物名称') or '',
            'SKU': get_value(goods_obj, 'SKU'),
            'HS编码': get_value(goods_obj, 'HS编码'),
            '原产国': get_value(goods_obj, '原产国'),
            '货物大类': get_value(goods_obj, '货物大类'),
            '是否新品': get_value(goods_obj, '是否新品') or 0,
            '货物种类': get_value(goods_obj, '货物种类'),
            '数量': qty,
            '单价': unit_price,
            '币种': get_value(goods_obj, '币种') or 'RMB',
            '重量(/kg)': self._format_decimal(get_value(goods_obj, '重量'), 3),
            '总重量(/kg)': self._format_decimal(get_value(goods_obj, '总重量'), 3),
            '总价': total_price,
            '备注': get_value(goods_obj, '备注')
        }

        return goods_dict
    
    def _convert_goods_total_to_db_format(self, goods_obj, goods_id: int, route_id: int) -> Dict[str, Any]:
        """
        ✅ 新增：将GoodsTotal对象转换为符合goods_total表字段的字典
        
        【goods_total表字段】
        - 整单货物ID (int)
        - 路线ID (int)
        - 货物名称 (varchar(255))
        - 实际重量(/kg) (decimal(18,2))
        - 货值 (decimal(18,2))
        - 总体积(/cbm) (decimal(18,3))
        - 备注 (varchar(255))
        
        Args:
            goods_obj: GoodsTotal对象
            goods_id: 分配的整单货物ID
            route_id: 关联的路线ID
        
        Returns:
            符合goods_total表字段的字典
        """
        def get_value(obj, *keys):
            for key in keys:
                if isinstance(obj, dict):
                    value = obj.get(key)
                else:
                    value = getattr(obj, key, None)
                if value is not None:
                    return value
            return None
        
        goods_dict = {
            '整单货物ID': goods_id,
            '路线ID': route_id,
            '货物名称': get_value(goods_obj, '货物名称') or '',
            '实际重量(/kg)': self._format_decimal(get_value(goods_obj, '实际重量'), 2),
            '货值': self._format_decimal(get_value(goods_obj, '货值'), 2),
            '总体积(/cbm)': self._format_decimal(get_value(goods_obj, '总体积'), 3),
            '备注': get_value(goods_obj, '备注')
        }
        
        return goods_dict
    
    def _convert_fee_item_to_db_format(self, fee_obj, fee_id: int, agent_id: int) -> Dict[str, Any]:
        """
        ✅ 新增：将FeeItem对象转换为符合fee_items表字段的字典
        
        【fee_items表字段】
        - 费用明细ID (int)
        - 代理路线ID (int)
        - 费用类型 (varchar(100))  ✅ 不是费用名称！
        - 单价 (decimal(18,2))
        - 单位 (varchar(20))
        - 币种 (varchar(10))
        - 备注 (varchar(255))
        
        Args:
            fee_obj: FeeItem对象
            fee_id: 分配的费用ID
            agent_id: 关联的代理路线ID
        
        Returns:
            符合fee_items表字段的字典
        """
        def get_value(obj, *keys):
            for key in keys:
                if isinstance(obj, dict):
                    value = obj.get(key)
                else:
                    value = getattr(obj, key, None)
                if value is not None:
                    return value
            return None
        
        fee_dict = {
            '费用明细ID': fee_id,
            '代理路线ID': agent_id,
            '费用类型': get_value(fee_obj, '费用类型') or '海运费',  # ✅ 费用类型
            '单价': self._format_decimal(get_value(fee_obj, '单价'), 2),
            '单位': get_value(fee_obj, '单位'),
            '数量': self._format_decimal(get_value(fee_obj, '数量'), 2),  # ✅ 数量
            '币种': get_value(fee_obj, '币种') or 'RMB',
            '备注': get_value(fee_obj, '备注')
        }
        
        return fee_dict
    
    def _convert_fee_total_to_db_format(self, fee_obj, fee_id: int, agent_id: int) -> Dict[str, Any]:
        """
        ✅ 新增：将FeeTotal对象转换为符合fee_totals表字段的字典
        
        【fee_totals表字段】
        - 整单费用ID (int)
        - 代理路线ID (int)
        - 费用名称 (varchar(100))
        - 原币金额 (decimal(18,2))  ✅ 不是金额！
        - 币种 (varchar(10))
        - 备注 (varchar(255))
        
        Args:
            fee_obj: FeeTotal对象
            fee_id: 分配的费用ID
            agent_id: 关联的代理路线ID
        
        Returns:
            符合fee_totals表字段的字典
        """
        def get_value(obj, *keys):
            for key in keys:
                if isinstance(obj, dict):
                    value = obj.get(key)
                else:
                    value = getattr(obj, key, None)
                if value is not None:
                    return value
            return None
        
        fee_dict = {
            '整单费用ID': fee_id,
            '代理路线ID': agent_id,
            '费用名称': get_value(fee_obj, '费用名称') or '',
            '原币金额': self._format_decimal(get_value(fee_obj, '原币金额'), 2),  # ✅ 原币金额
            '币种': get_value(fee_obj, '币种') or 'RMB',
            '备注': get_value(fee_obj, '备注')
        }
        
        return fee_dict
    
    def _convert_summary_to_db_format(self, summary_obj, summary_id: int, agent_id: int) -> Dict[str, Any]:
        """
        ✅ 新增：将Summary对象转换为符合summary表字段的字典
        
        【summary表字段】
        - 汇总ID (int)
        - 代理路线ID (int)
        - 税率 (decimal(10,4))
        - 汇损率 (decimal(10,6))
        - 备注 (varchar(255))
        
        注意：小计、税金、汇损、总计 由数据库触发器自动计算
        
        Args:
            summary_obj: Summary对象
            summary_id: 分配的汇总ID
            agent_id: 关联的代理路线ID
        
        Returns:
            符合summary表字段的字典
        """
        def get_value(obj, *keys):
            for key in keys:
                if isinstance(obj, dict):
                    value = obj.get(key)
                else:
                    value = getattr(obj, key, None)
                if value is not None:
                    return value
            return None
        
        summary_dict = {
            '汇总ID': summary_id,
            '代理路线ID': agent_id,
            '运费小计': self._format_decimal(get_value(summary_obj, '运费小计', '小计'), 2),
            '税金金额': self._format_decimal(get_value(summary_obj, '税金金额', '税金'), 2),
            '总计金额': self._format_decimal(get_value(summary_obj, '总计金额', '总计'), 2),
            '税率': self._format_decimal(get_value(summary_obj, '税率'), 4),
            '汇损率': self._format_decimal(get_value(summary_obj, '汇损率'), 6),
            '进口税率原文': get_value(summary_obj, '进口税率原文'),
            '备注': get_value(summary_obj, '备注')
        }

        return summary_dict
    
    def _format_date(self, date_value: Any) -> Optional[str]:
        """
        格式化日期为数据库格式 (YYYY-MM-DD)
        
        Args:
            date_value: 日期值（可以是datetime, date, str等）
        
        Returns:
            格式化后的日期字符串，或None
        """
        if not date_value:
            return None
        
        if isinstance(date_value, datetime):
            return date_value.strftime('%Y-%m-%d')
        elif isinstance(date_value, date):
            return date_value.strftime('%Y-%m-%d')
        elif isinstance(date_value, str):
            # 已经是字符串，尝试验证格式
            try:
                datetime.strptime(date_value, '%Y-%m-%d')
                return date_value
            except:
                return None
        
        return None
    
    def _format_decimal(self, value: Any, decimal_places: int) -> Optional[float]:
        """
        格式化为decimal类型
        
        Args:
            value: 数值
            decimal_places: 小数位数
        
        Returns:
            格式化后的浮点数，或None
        """
        if value is None:
            return None
        
        try:
            # 转换为浮点数
            num = float(value)
            # 四舍五入到指定小数位
            return round(num, decimal_places)
        except (ValueError, TypeError):
            return None
    
    def _format_boolean(self, value: Any) -> str:
        """
        格式化布尔值为字符串 ('0' 或 '1')
        
        Args:
            value: 布尔值或其他类型
        
        Returns:
            '0' 或 '1'
        """
        if value is None:
            return '0'
        
        if isinstance(value, bool):
            return '1' if value else '0'
        
        if isinstance(value, str):
            # 处理字符串 '是'/'否', 'true'/'false', '1'/'0'
            value_lower = value.lower()
            if value_lower in ['是', 'yes', 'true', '1']:
                return '1'
            else:
                return '0'
        
        # 其他类型，尝试转为bool
        try:
            return '1' if bool(value) else '0'
        except:
            return '0'
    
    def _validate_data(self, routes: List[Dict], route_agents: List[Dict], 
                      goods_details: List[Dict], goods_total: List[Dict]):
        """
        验证数据完整性
        
        【验证内容】
        1. routes必须有起始地和目的地
        2. route_agents的路线ID必须存在于routes中
        3. goods的路线ID必须存在于routes中 ✅ 新增
        4. agent的代理商名不能为空
        5. goods的货物名称不能为空 ✅ 新增
        
        Args:
            routes: routes数据列表
            route_agents: route_agents数据列表
            goods_details: goods_details数据列表 ✅ 新增
            goods_total: goods_total数据列表 ✅ 新增
        """
        # 获取所有有效的路线ID
        valid_route_ids = {r['路线ID'] for r in routes}
        
        # 验证routes
        for route in routes:
            if not route.get('起始地'):
                self.validation_errors.append(
                    f"Route ID {route['路线ID']}: 缺少起始地"
                )
            if not route.get('目的地'):
                self.validation_errors.append(
                    f"Route ID {route['路线ID']}: 缺少目的地"
                )
        
        # 验证route_agents
        for agent in route_agents:
            # 检查路线ID是否有效
            if agent['路线ID'] not in valid_route_ids:
                self.validation_errors.append(
                    f"Agent ID {agent['代理路线ID']}: 关联的路线ID {agent['路线ID']} 不存在"
                )
            
            # 检查代理商名
            if not agent.get('代理商'):
                self.validation_errors.append(
                    f"Agent ID {agent['代理路线ID']}: 缺少代理商名"
                )
        
        # ✅ 新增：验证goods_details
        for goods in goods_details:
            # 检查路线ID是否有效
            if goods['路线ID'] not in valid_route_ids:
                self.validation_errors.append(
                    f"Goods Detail ID {goods['货物ID']}: 关联的路线ID {goods['路线ID']} 不存在"
                )
            
            # 检查货物名称
            if not goods.get('货物名称'):
                self.validation_errors.append(
                    f"Goods Detail ID {goods['货物ID']}: 缺少货物名称"
                )
        
        # ✅ 新增：验证goods_total
        for goods in goods_total:
            # 检查路线ID是否有效
            if goods['路线ID'] not in valid_route_ids:
                self.validation_errors.append(
                    f"Goods Total ID {goods['整单货物ID']}: 关联的路线ID {goods['路线ID']} 不存在"
                )
            
            # 检查货物名称
            if not goods.get('货物名称'):
                self.validation_errors.append(
                    f"Goods Total ID {goods['整单货物ID']}: 缺少货物名称"
                )
        
        if self.validation_errors and self.logger:
            self.logger.warning(f"  发现{len(self.validation_errors)}个验证错误")
    
    def get_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取数据摘要
        
        Args:
            result: assemble()的返回结果
        
        Returns:
            数据摘要字典
        """
        routes = result.get('routes', [])
        agents = result.get('route_agents', [])
        goods_details = result.get('goods_details', [])  # ✅ 新增
        goods_total = result.get('goods_total', [])      # ✅ 新增
        summaries = result.get('summary', [])            # ✅ 新增 summary
        
        # 统计有agents的routes
        routes_with_agents = set()
        for agent in agents:
            routes_with_agents.add(agent['路线ID'])
        
        # ✅ 新增：统计有货物的routes
        routes_with_goods = set()
        for goods in goods_details:
            routes_with_goods.add(goods['路线ID'])
        for goods in goods_total:
            routes_with_goods.add(goods['路线ID'])
        
        return {
            'total_routes': len(routes),
            'total_agents': len(agents),
            'total_goods_details': len(goods_details),    # ✅ 新增
            'total_goods_total': len(goods_total),        # ✅ 新增
            'total_summaries': len(summaries),            # ✅ 新增 summary统计
            'routes_with_agents': len(routes_with_agents),
            'routes_with_goods': len(routes_with_goods),  # ✅ 新增
            'routes_without_agents': len(routes) - len(routes_with_agents),
            'routes_without_goods': len(routes) - len(routes_with_goods),  # ✅ 新增
            'avg_agents_per_route': len(agents) / len(routes) if routes else 0,
            'validation_errors_count': len(result.get('validation_errors', []))
        }


__all__ = ['DataAssembler']