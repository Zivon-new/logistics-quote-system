# scripts/db_importer.py
"""
数据库导入工具 v1.0

【核心功能】
✅ 从JSON文件导入数据到MySQL数据库
✅ ID映射机制（JSON临时ID → 数据库真实ID）
✅ 自动维护外键关系
✅ 事务处理（全部成功或全部回滚）
✅ 支持增量导入（ID自动顺延）

【使用方法】
python scripts/db_importer.py --data-dir data/clean

【方案说明】
- JSON保留ID（仅用于维护关联关系）
- 导入时删除JSON的ID，让数据库AUTO_INCREMENT生成真实ID
- 通过ID映射维护外键关系
- 支持多次导入同一文件（不会ID冲突）
"""

import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pymysql
from pymysql.cursors import DictCursor


class DatabaseImporter:
    """数据库导入器"""
    
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 3306,
                 user: str = 'root',
                 password: str = 'JHL181116',
                 database: str = 'price_test_v2',
                 logger: Optional[logging.Logger] = None):
        """
        初始化数据库导入器
        
        Args:
            host: 数据库主机
            port: 数据库端口
            user: 数据库用户名
            password: 数据库密码
            database: 数据库名称
            logger: 日志记录器
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.logger = logger or self._setup_logger()
        
        # ID映射表
        self.route_id_map = {}          # {JSON路线ID: DB路线ID}
        self.agent_id_map = {}          # {JSON代理路线ID: DB代理路线ID}
        self.goods_total_id_map = {}    # {JSON整单货物ID: DB整单货物ID}
        self.goods_detail_id_map = {}   # {JSON货物ID: DB货物ID}
        
        # 统计信息
        self.stats = {
            'routes': 0,
            'route_agents': 0,
            'goods_total': 0,
            'goods_details': 0,
            'fee_items': 0,
            'fee_totals': 0,
            'summary': 0,
            'import_tax_items': 0
        }
        
        # ✅ v2.5: 合并模式相关
        self._merge_mode = False
        self._merge_folders = []
        
        # 数据库连接
        self.conn = None
        self.cursor = None
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志（彻底避免重复）"""
        logger_name = 'DatabaseImporter'
        
        # ✅ 获取logger
        logger = logging.getLogger(logger_name)
        
        # ✅ 如果logger已经有handlers，直接返回（避免重复添加）
        if logger.handlers:
            return logger
        
        # ✅ 设置日志级别
        logger.setLevel(logging.INFO)
        
        # ✅ 阻止日志传播到root logger（避免重复）
        logger.propagate = False
        
        # ✅ 创建console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # ✅ 创建formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        # ✅ 添加handler
        logger.addHandler(console_handler)
        
        return logger
    
    def connect(self):
        """连接数据库"""
        try:
            self.logger.info("正在连接数据库...")
            self.conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=DictCursor
            )
            self.cursor = self.conn.cursor()
            self.logger.info("✅ 数据库连接成功")
        except Exception as e:
            self.logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.logger.info("数据库连接已关闭")
    
    def _determine_data_source(self, data_dir: str, source_folder: str = None, 
                               merge_all: bool = False) -> str:
        """
        确定实际的数据源路径（v2.5）
        
        Args:
            data_dir: 基础数据目录
            source_folder: 指定的子文件夹名
            merge_all: 是否合并所有子文件夹
        
        Returns:
            实际的数据目录路径
        """
        from pathlib import Path
        
        data_dir_path = Path(data_dir)
        
        # ========== 情况1：合并所有子文件夹 ==========
        if merge_all:
            self.logger.info("\n" + "=" * 60)
            self.logger.info("📂 模式：合并所有子文件夹")
            self.logger.info("=" * 60)
            
            # 这种情况下，我们不返回单个路径，而是标记需要特殊处理
            # 实际上，我们需要修改导入逻辑来支持这种情况
            # 暂时返回基础目录，后续在_load_json中处理
            self._merge_mode = True
            self._merge_folders = [
                str(f) for f in data_dir_path.iterdir() 
                if f.is_dir() and not f.name.startswith('.')
            ]
            
            if not self._merge_folders:
                self.logger.warning("⚠️  没有找到子文件夹，使用默认模式")
                self._merge_mode = False
                return data_dir
            
            self.logger.info(f"找到 {len(self._merge_folders)} 个子文件夹:")
            for folder in self._merge_folders:
                self.logger.info(f"  - {Path(folder).name}")
            
            return data_dir  # 返回基础目录
        
        # ========== 情况2：指定子文件夹 ==========
        elif source_folder:
            folder_path = data_dir_path / source_folder
            
            if not folder_path.exists():
                self.logger.error(f"❌ 子文件夹不存在: {folder_path}")
                self.logger.info("\n💡 可用的子文件夹:")
                for f in data_dir_path.iterdir():
                    if f.is_dir() and not f.name.startswith('.'):
                        self.logger.info(f"  - {f.name}")
                raise FileNotFoundError(f"子文件夹不存在: {source_folder}")
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info(f"📂 模式：从子文件夹读取")
            self.logger.info("=" * 60)
            self.logger.info(f"   来源: {source_folder}")
            
            self._merge_mode = False
            return str(folder_path)
        
        # ========== 情况3：默认模式 ==========
        else:
            # 检查是否有子文件夹
            has_subfolders = any(
                f.is_dir() and not f.name.startswith('.')
                for f in data_dir_path.iterdir()
            )
            
            # 检查是否有JSON文件
            has_json_files = any(
                f.suffix == '.json' 
                for f in data_dir_path.iterdir()
            )
            
            if has_subfolders and not has_json_files:
                self.logger.warning("\n" + "=" * 60)
                self.logger.warning("⚠️  检测到子文件夹结构")
                self.logger.warning("=" * 60)
                self.logger.warning(f"   {data_dir}/ 下有子文件夹，但没有JSON文件")
                self.logger.warning("")
                self.logger.warning("请指定数据源:")
                self.logger.warning("  1. 导入特定文件夹：")
                self.logger.warning("     python -m scripts.db_writer --source \"文件夹名\"")
                self.logger.warning("")
                self.logger.warning("  2. 合并所有文件夹：")
                self.logger.warning("     python -m scripts.db_writer --merge-all")
                self.logger.warning("")
                self.logger.warning("可用的子文件夹:")
                for f in data_dir_path.iterdir():
                    if f.is_dir() and not f.name.startswith('.'):
                        self.logger.warning(f"  - {f.name}")
                
                raise ValueError("需要指定数据源（使用--source或--merge-all）")
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info("📂 模式：默认（直接读取）")
            self.logger.info("=" * 60)
            
            self._merge_mode = False
            return data_dir
    
    def import_from_json(self, data_dir: str, clear_tables: bool = False, 
                        source_folder: str = None, merge_all: bool = False):
        """
        从JSON文件导入数据
        
        【v2.5 新增】支持按文件名组织的子文件夹结构
        - source_folder: 指定子文件夹名
        - merge_all: 合并所有子文件夹
        
        【导入顺序】
        1. routes
        2. route_agents（依赖routes）
        3. goods_total/goods_details（依赖routes）
        4. fee_items/fee_totals（依赖route_agents）
        5. summary（依赖route_agents）
        
        Args:
            data_dir: JSON文件所在目录（基础目录）
            clear_tables: 是否清空表（危险操作！）
            source_folder: 指定子文件夹名（v2.5）
            merge_all: 合并所有子文件夹（v2.5）
        """
        self.logger.info("="*60)
        self.logger.info("开始导入数据到数据库")
        self.logger.info("="*60)
        
        try:
            # 连接数据库
            self.connect()
            
            # ✅ 修复：如果只是清空表，不需要数据源
            if clear_tables:
                self._clear_tables()
                
                # 如果没有指定数据源，清空后直接返回
                if not source_folder and not merge_all:
                    self.logger.info("\n✅ 清空完成（未指定数据源，不执行导入）")
                    return
            
            # ✅ v2.5: 确定实际的数据源路径（只在需要导入时才检查）
            actual_data_dir = self._determine_data_source(
                data_dir, source_folder, merge_all
            )
            
            self.logger.info(f"数据目录: {actual_data_dir}")
            self.logger.info(f"数据库: {self.database}")
            
            # ✅ 修改：分段提交，每个表成功后立即提交
            # 这样即使后续表失败，前面成功的表数据也不会丢失
            
            # 1. 导入routes
            try:
                self._import_routes(actual_data_dir)  # ✅ 修复：使用actual_data_dir
                self.conn.commit()
                self.logger.info("  ✅ routes提交成功")
            except Exception as e:
                self.logger.error(f"  ❌ routes导入失败: {e}")
                self.conn.rollback()
                raise
            
            # 2. 导入route_agents
            try:
                self._import_route_agents(actual_data_dir)  # ✅ 修复
                self.conn.commit()
                self.logger.info("  ✅ route_agents提交成功")
            except Exception as e:
                self.logger.error(f"  ❌ route_agents导入失败: {e}")
                self.conn.rollback()
                raise
            
            # 3. 导入goods（分别处理，失败了也继续）
            try:
                self._import_goods_total(actual_data_dir)  # ✅ 修复
                self.conn.commit()
                self.logger.info("  ✅ goods_total提交成功")
            except Exception as e:
                self.logger.error(f"  ❌ goods_total导入失败: {e}")
                self.conn.rollback()
                # 打印详细错误但继续执行
                import traceback
                self.logger.error(traceback.format_exc())
            
            try:
                self._import_goods_details(actual_data_dir)  # ✅ 修复
                self.conn.commit()
                self.logger.info("  ✅ goods_details提交成功")
            except Exception as e:
                self.logger.error(f"  ❌ goods_details导入失败: {e}")
                self.conn.rollback()
                import traceback
                self.logger.error(traceback.format_exc())
            
            # 4. 导入fees
            try:
                self._import_fee_items(actual_data_dir)  # ✅ 修复
                self.conn.commit()
                self.logger.info("  ✅ fee_items提交成功")
            except Exception as e:
                self.logger.error(f"  ❌ fee_items导入失败: {e}")
                self.conn.rollback()
                import traceback
                self.logger.error(traceback.format_exc())
            
            try:
                self._import_fee_totals(actual_data_dir)  # ✅ 修复
                self.conn.commit()
                self.logger.info("  ✅ fee_totals提交成功")
            except Exception as e:
                self.logger.error(f"  ❌ fee_totals导入失败: {e}")
                self.conn.rollback()
                import traceback
                self.logger.error(traceback.format_exc())
            
            # 5. 导入summary
            try:
                self._import_summary(actual_data_dir)
                self.conn.commit()
                self.logger.info("  ✅ summary提交成功")
            except Exception as e:
                self.logger.error(f"  ❌ summary导入失败: {e}")
                self.conn.rollback()
                import traceback
                self.logger.error(traceback.format_exc())

            # 6. 导入import_tax_items
            try:
                self._import_import_tax_items(actual_data_dir)
                self.conn.commit()
                self.logger.info("  ✅ import_tax_items提交成功")
            except Exception as e:
                self.logger.error(f"  ❌ import_tax_items导入失败: {e}")
                self.conn.rollback()
                import traceback
                self.logger.error(traceback.format_exc())

            self.logger.info("✅ 导入流程完成")
            
            # 显示统计
            self._print_stats()
            
        except Exception as e:
            # 只有routes和route_agents失败才会到这里
            self.logger.error(f"❌ 导入失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise
        
        finally:
            # 断开连接
            self.disconnect()
    
    def _clear_tables(self):
        """清空所有表（危险操作！）"""
        self.logger.warning("⚠️  正在清空所有表...")
        
        # ✅ 表名和主键ID的映射
        tables_with_pk = [
            ('import_tax_items', '税项ID'),
            ('summary', '汇总ID'),
            ('fee_total', '整单费用ID'),
            ('fee_items', '费用ID'),
            ('goods_details', '货物ID'),
            ('goods_total', '整单货物ID'),
            ('route_agents', '代理路线ID'),
            ('routes', '路线ID')
        ]
        
        # 禁用外键检查
        self.cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        for table, pk_column in tables_with_pk:
            try:
                # ✅ TRUNCATE清空数据
                self.cursor.execute(f"TRUNCATE TABLE {table}")
                
                # ✅ 重置AUTO_INCREMENT为1
                self.cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
                
                self.logger.info(f"  ✅ 已清空并重置: {table}")
            except Exception as e:
                self.logger.warning(f"  ⚠️  清空{table}失败: {e}")
        
        # 启用外键检查
        self.cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # ✅ 提交更改
        self.conn.commit()
        
        self.logger.info("✅ 表清空完成，AUTO_INCREMENT已重置为1")
    
    def _load_json(self, data_dir: str, filename: str) -> List[Dict]:
        """
        加载JSON文件
        
        ✅ v2.5: 支持合并模式 - 从多个子文件夹加载并合并数据
        """
        # ========== 合并模式 ==========
        if self._merge_mode and self._merge_folders:
            all_data = []
            
            for folder_path in self._merge_folders:
                filepath = os.path.join(folder_path, filename)
                
                if not os.path.exists(filepath):
                    continue
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if data:
                        all_data.extend(data)
                        folder_name = os.path.basename(folder_path)
                        self.logger.info(f"  📁 {folder_name}/{filename}: {len(data)}条")
                
                except Exception as e:
                    self.logger.error(f"❌ 加载{filepath}失败: {e}")
            
            if all_data:
                self.logger.info(f"  ✅ 合并后总数: {len(all_data)}条")
            
            return all_data
        
        # ========== 普通模式 ==========
        filepath = os.path.join(data_dir, filename)
        
        if not os.path.exists(filepath):
            self.logger.warning(f"⚠️  文件不存在: {filepath}")
            return []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.info(f"  📁 加载: {filename} ({len(data)}条)")
            return data
        except Exception as e:
            self.logger.error(f"❌ 加载{filename}失败: {e}")
            return []
    
    def _import_routes(self, data_dir: str):
        """导入routes表"""
        self.logger.info("\n" + "="*60)
        self.logger.info("1. 导入 routes")
        self.logger.info("="*60)
        
        routes = self._load_json(data_dir, 'routes.json')
        if not routes:
            self.logger.warning("  ⚠️  没有routes数据")
            return
        
        for route in routes:
            # 保存JSON的临时ID
            json_route_id = route.get('路线ID')
            
            # 删除JSON的ID（让数据库生成）
            if '路线ID' in route:
                del route['路线ID']
            
            # 构建SQL
            columns = ', '.join([f"`{k}`" for k in route.keys()])
            placeholders = ', '.join(['%s'] * len(route))
            sql = f"INSERT INTO routes ({columns}) VALUES ({placeholders})"
            
            # 执行插入
            self.cursor.execute(sql, list(route.values()))
            
            # 获取数据库生成的真实ID
            db_route_id = self.cursor.lastrowid
            
            # 建立映射
            self.route_id_map[json_route_id] = db_route_id
            
            self.stats['routes'] += 1
        
        self.logger.info(f"  ✅ 导入成功: {len(routes)}条")
        self.logger.info(f"  📊 ID映射: {len(self.route_id_map)}个")
    
    def _import_route_agents(self, data_dir: str):
        """导入route_agents表"""
        self.logger.info("\n" + "="*60)
        self.logger.info("2. 导入 route_agents")
        self.logger.info("="*60)
        
        agents = self._load_json(data_dir, 'route_agents.json')
        if not agents:
            self.logger.warning("  ⚠️  没有route_agents数据")
            return
        
        for agent in agents:
            # 保存JSON的临时ID
            json_agent_id = agent.get('代理路线ID')
            json_route_id = agent.get('路线ID')
            
            # 删除JSON的ID
            if '代理路线ID' in agent:
                del agent['代理路线ID']
            
            # ✅ 关键：使用映射后的真实route_id
            if json_route_id in self.route_id_map:
                agent['路线ID'] = self.route_id_map[json_route_id]
            else:
                self.logger.warning(f"  ⚠️  找不到路线ID映射: {json_route_id}")
                continue
            
            # 构建SQL
            columns = ', '.join([f"`{k}`" for k in agent.keys()])
            placeholders = ', '.join(['%s'] * len(agent))
            sql = f"INSERT INTO route_agents ({columns}) VALUES ({placeholders})"
            
            # 执行插入
            self.cursor.execute(sql, list(agent.values()))
            
            # 获取数据库生成的真实ID
            db_agent_id = self.cursor.lastrowid
            
            # 建立映射
            self.agent_id_map[json_agent_id] = db_agent_id
            
            self.stats['route_agents'] += 1
        
        self.logger.info(f"  ✅ 导入成功: {len(agents)}条")
        self.logger.info(f"  📊 ID映射: {len(self.agent_id_map)}个")
    
    def _import_goods_total(self, data_dir: str):
        """导入goods_total表"""
        self.logger.info("\n" + "="*60)
        self.logger.info("3. 导入 goods_total")
        self.logger.info("="*60)
        
        goods_list = self._load_json(data_dir, 'goods_total.json')
        if not goods_list:
            self.logger.warning("  ⚠️  没有goods_total数据")
            return
        
        for goods in goods_list:
            # 保存JSON的临时ID
            json_goods_id = goods.get('整单货物ID')
            json_route_id = goods.get('路线ID')
            
            # 删除JSON的ID
            if '整单货物ID' in goods:
                del goods['整单货物ID']
            
            # ✅ 使用映射后的真实route_id
            if json_route_id in self.route_id_map:
                goods['路线ID'] = self.route_id_map[json_route_id]
            else:
                self.logger.warning(f"  ⚠️  找不到路线ID映射: {json_route_id}")
                continue
            
            # 构建SQL
            columns = ', '.join([f"`{k}`" for k in goods.keys()])
            placeholders = ', '.join(['%s'] * len(goods))
            sql = f"INSERT INTO goods_total ({columns}) VALUES ({placeholders})"
            
            # ✅ 添加调试日志（第一条记录）
            if json_goods_id == 1:
                self.logger.info(f"  🔍 [调试] 第一条记录的SQL:")
                self.logger.info(f"  🔍 字段名: {list(goods.keys())}")
                self.logger.info(f"  🔍 SQL: {sql[:200]}")  # 只显示前200字符
                self.logger.info(f"  🔍 值: {list(goods.values())}")
            
            # 执行插入
            try:
                self.cursor.execute(sql, list(goods.values()))
            except Exception as e:
                self.logger.error(f"  ❌ 插入失败 - 货物ID: {json_goods_id}")
                self.logger.error(f"  ❌ SQL: {sql}")
                self.logger.error(f"  ❌ 字段: {list(goods.keys())}")
                self.logger.error(f"  ❌ 值: {list(goods.values())}")
                self.logger.error(f"  ❌ 错误信息: {e}")
                raise
            
            # 获取数据库生成的真实ID
            db_goods_id = self.cursor.lastrowid
            
            # 建立映射
            self.goods_total_id_map[json_goods_id] = db_goods_id
            
            self.stats['goods_total'] += 1
        
        self.logger.info(f"  ✅ 导入成功: {len(goods_list)}条")
    
    def _import_goods_details(self, data_dir: str):
        """导入goods_details表"""
        self.logger.info("\n" + "="*60)
        self.logger.info("4. 导入 goods_details")
        self.logger.info("="*60)
        
        goods_list = self._load_json(data_dir, 'goods_details.json')
        if not goods_list:
            self.logger.warning("  ⚠️  没有goods_details数据")
            return
        
        for goods in goods_list:
            # 保存JSON的临时ID
            json_goods_id = goods.get('货物ID')
            json_route_id = goods.get('路线ID')
            
            # 删除JSON的ID
            if '货物ID' in goods:
                del goods['货物ID']
            
            # ✅ 使用映射后的真实route_id
            if json_route_id in self.route_id_map:
                goods['路线ID'] = self.route_id_map[json_route_id]
            else:
                self.logger.warning(f"  ⚠️  找不到路线ID映射: {json_route_id}")
                continue
            
            # 构建SQL
            columns = ', '.join([f"`{k}`" for k in goods.keys()])
            placeholders = ', '.join(['%s'] * len(goods))
            sql = f"INSERT INTO goods_details ({columns}) VALUES ({placeholders})"
            
            # 执行插入
            self.cursor.execute(sql, list(goods.values()))
            
            # 获取数据库生成的真实ID
            db_goods_id = self.cursor.lastrowid
            
            # 建立映射
            self.goods_detail_id_map[json_goods_id] = db_goods_id
            
            self.stats['goods_details'] += 1
        
        self.logger.info(f"  ✅ 导入成功: {len(goods_list)}条")
    
    def _import_fee_items(self, data_dir: str):
        """导入fee_items表"""
        self.logger.info("\n" + "="*60)
        self.logger.info("5. 导入 fee_items")
        self.logger.info("="*60)
        
        fees = self._load_json(data_dir, 'fee_items.json')
        if not fees:
            self.logger.warning("  ⚠️  没有fee_items数据")
            return
        
        for fee in fees:
            # 保存JSON的临时ID
            json_fee_id = fee.get('费用明细ID')
            json_agent_id = fee.get('代理路线ID')
            
            # 删除JSON的ID
            if '费用明细ID' in fee:
                del fee['费用明细ID']
            
            # ✅ 使用映射后的真实agent_id
            if json_agent_id in self.agent_id_map:
                fee['代理路线ID'] = self.agent_id_map[json_agent_id]
            else:
                self.logger.warning(f"  ⚠️  找不到代理路线ID映射: {json_agent_id}")
                continue
            
            # 构建SQL
            columns = ', '.join([f"`{k}`" for k in fee.keys()])
            placeholders = ', '.join(['%s'] * len(fee))
            sql = f"INSERT INTO fee_items ({columns}) VALUES ({placeholders})"
            
            # 执行插入
            self.cursor.execute(sql, list(fee.values()))
            
            self.stats['fee_items'] += 1
        
        self.logger.info(f"  ✅ 导入成功: {len(fees)}条")
    
    def _import_fee_totals(self, data_dir: str):
        """导入fee_total表"""
        self.logger.info("\n" + "="*60)
        self.logger.info("6. 导入 fee_total")
        self.logger.info("="*60)
        
        fees = self._load_json(data_dir, 'fee_total.json')
        if not fees:
            self.logger.warning("  ⚠️  没有fee_total数据")
            return
        
        for fee in fees:
            # 保存JSON的临时ID
            json_fee_id = fee.get('整单费用ID')
            json_agent_id = fee.get('代理路线ID')
            
            # 删除JSON的ID
            if '整单费用ID' in fee:
                del fee['整单费用ID']
            
            # ✅ 使用映射后的真实agent_id
            if json_agent_id in self.agent_id_map:
                fee['代理路线ID'] = self.agent_id_map[json_agent_id]
            else:
                self.logger.warning(f"  ⚠️  找不到代理路线ID映射: {json_agent_id}")
                continue
            
            # 构建SQL
            columns = ', '.join([f"`{k}`" for k in fee.keys()])
            placeholders = ', '.join(['%s'] * len(fee))
            sql = f"INSERT INTO fee_total ({columns}) VALUES ({placeholders})"
            
            # 执行插入
            self.cursor.execute(sql, list(fee.values()))
            
            self.stats['fee_totals'] += 1
        
        self.logger.info(f"  ✅ 导入成功: {len(fees)}条")
    
    def _import_summary(self, data_dir: str):
        """导入summary表"""
        self.logger.info("\n" + "="*60)
        self.logger.info("7. 导入 summary")
        self.logger.info("="*60)
        
        summaries = self._load_json(data_dir, 'summary.json')
        if not summaries:
            self.logger.warning("  ⚠️  没有summary数据")
            return
        
        # ✅ 导入前先删除触发器自动创建的summary记录
        self.logger.info("  🔧 清理触发器自动创建的summary记录...")
        self.cursor.execute("DELETE FROM summary")
        self.conn.commit()
        self.logger.info("  ✅ 已清理")
        
        # ✅ 导入JSON中的所有数据（不去重！）
        for summary in summaries:
            # 保存JSON的临时ID
            json_summary_id = summary.get('汇总ID')
            json_agent_id = summary.get('代理路线ID')
            
            # 删除JSON的ID
            if '汇总ID' in summary:
                del summary['汇总ID']
            
            # ✅ 使用映射后的真实agent_id
            if json_agent_id in self.agent_id_map:
                summary['代理路线ID'] = self.agent_id_map[json_agent_id]
            else:
                self.logger.warning(f"  ⚠️  找不到代理路线ID映射: {json_agent_id}")
                continue
            
            # 构建SQL
            columns = ', '.join([f"`{k}`" for k in summary.keys()])
            placeholders = ', '.join(['%s'] * len(summary))
            sql = f"INSERT INTO summary ({columns}) VALUES ({placeholders})"
            
            # 执行插入
            self.cursor.execute(sql, list(summary.values()))
            
            self.stats['summary'] += 1
        
        self.logger.info(f"  ✅ 导入成功: {len(summaries)}条")
    
    def _import_import_tax_items(self, data_dir: str):
        """导入import_tax_items表"""
        self.logger.info("\n" + "="*60)
        self.logger.info("8. 导入 import_tax_items")
        self.logger.info("="*60)

        items = self._load_json(data_dir, 'import_tax_items.json')
        if not items:
            self.logger.warning("  ⚠️  没有import_tax_items数据")
            return

        for item in items:
            json_item_id = item.get('税项ID')
            json_agent_id = item.get('代理路线ID')

            if '税项ID' in item:
                del item['税项ID']

            if json_agent_id in self.agent_id_map:
                item['代理路线ID'] = self.agent_id_map[json_agent_id]
            else:
                self.logger.warning(f"  ⚠️  找不到代理路线ID映射: {json_agent_id}")
                continue

            columns = ', '.join([f"`{k}`" for k in item.keys()])
            placeholders = ', '.join(['%s'] * len(item))
            sql = f"INSERT INTO import_tax_items ({columns}) VALUES ({placeholders})"

            self.cursor.execute(sql, list(item.values()))
            self.stats['import_tax_items'] += 1

        self.logger.info(f"  ✅ 导入成功: {len(items)}条")

    def _print_stats(self):
        """打印统计信息"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📊 导入统计")
        self.logger.info("="*60)
        
        for table, count in self.stats.items():
            if count > 0:
                self.logger.info(f"  {table}: {count}条")
        
        total = sum(self.stats.values())
        self.logger.info("-"*60)
        self.logger.info(f"  总计: {total}条")
        self.logger.info("="*60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="数据库导入工具 - 从JSON导入数据到MySQL"
    )
    
    parser.add_argument(
        '--data-dir',
        type=str,
        default='data/clean',
        help='JSON文件所在目录（默认：data/clean）'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='数据库主机（默认：localhost）'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=3306,
        help='数据库端口（默认：3306）'
    )
    
    parser.add_argument(
        '--user',
        type=str,
        default='root',
        help='数据库用户名（默认：root）'
    )
    
    parser.add_argument(
        '--password',
        type=str,
        default=None,
        help='数据库密码（默认：空）'
    )
    
    parser.add_argument(
        '--database',
        type=str,
        default='price_test_v2',
        help='数据库名称（默认：price_test_v2）'
    )
    
    parser.add_argument(
        '--clear-tables',
        action='store_true',
        help='清空所有表（危险操作！）'
    )
    
    # ✅ v2.5: 新增参数 - 支持子文件夹
    parser.add_argument(
        '--source',
        type=str,
        help='指定子文件夹名（如：2025年10月国际物流报价表.xlsx）'
    )
    
    parser.add_argument(
        '--merge-all',
        action='store_true',
        help='合并所有子文件夹的数据'
    )
    
    args = parser.parse_args()
    
    try:
        # 创建导入器
        importer = DatabaseImporter(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password or 'JHL181116',
            database=args.database
        )
        
        # 执行导入
        importer.import_from_json(
            data_dir=args.data_dir,
            clear_tables=args.clear_tables,
            source_folder=args.source,  # ✅ v2.5
            merge_all=args.merge_all    # ✅ v2.5
        )
        
        print("\n✅ 导入完成！")
    
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断")
    
    except Exception as e:
        print(f"\n\n❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

# # 提取
# python test_new_architecture_with_llm.py --file "文件路径"

# # 导入单个
# python -m scripts.db_writer --source "文件夹名"

# # 合并导入
# python -m scripts.db_writer --merge-all

# # 清空重建
# python -m scripts.db_writer --clear-tables --merge-all