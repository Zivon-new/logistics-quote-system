# scripts/modules/base_extractor.py
"""
BaseExtractor - 提取器基类 v2.0

【核心改进】
✅ 质量驱动的LLM增强策略
✅ 添加2秒延迟避免429
✅ 完整的调试日志
✅ _serialize_sheet异常处理
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
import json


class BaseExtractor(ABC):
    """
    提取器基类 v2.0
    
    【核心流程】
    1. 规则提取 → 2. 质量评估 → 3. LLM增强（如果质量不达标）
    """
    
    # 质量阈值（子类可覆盖）
    QUALITY_THRESHOLD = 0.7
    
    def __init__(self, logger=None, llm_client=None, enable_llm=True):
        """
        初始化提取器
        
        Args:
            logger: 日志记录器
            llm_client: LLM客户端（LLMEnhancer实例）
            enable_llm: 是否启用LLM增强
        """
        self.logger = logger
        self.llm_client = llm_client if enable_llm else None
        self.enable_llm = enable_llm
        
        # 统计信息
        self.stats = {
            'total_attempts': 0,      # 总尝试次数
            'rule_success': 0,         # 规则成功次数
            'llm_calls': 0,            # LLM调用次数
            'llm_success': 0,          # LLM成功次数
            'default_used': 0,         # 使用默认值次数
            'quality_scores': []       # 质量分数列表
        }
    
    def extract(self, sheet, **kwargs) -> Any:
        """
        标准提取流程（v2.0 质量驱动版）
        
        【v2.0 新流程】
        规则提取 → 质量评估 → LLM增强（如果质量不达标） → 返回结果
        
        【与v1.0的区别】
        - v1.0: 规则失败 → LLM兜底
        - v2.0: 规则提取 → 质量评估 → LLM增强
        
        Args:
            sheet: Excel sheet对象
            **kwargs: 额外参数
            
        Returns:
            提取结果（类型由子类决定）
        """
        self.stats['total_attempts'] += 1
        
        if self.logger:
            self.logger.debug(f"  开始提取: {self.__class__.__name__}")
        
        # ========== 阶段1: 规则提取 ==========
        try:
            result = self._extract_with_rules(sheet, **kwargs)
            
            if self.logger:
                self.logger.debug(f"    ✅ 规则提取完成")
        
        except Exception as e:
            if self.logger:
                self.logger.warning(f"    ❌ 规则提取异常: {str(e)[:100]}")
            result = None
        
        # ========== 阶段2: 质量评估 ==========
        quality_score = self._evaluate_quality(result, sheet, **kwargs)
        self.stats['quality_scores'].append(quality_score)
        
        if self.logger:
            self.logger.debug(f"    📊 质量分数: {quality_score:.2f}")
        
        # ========== 阶段3: 判断是否需要LLM增强 ==========
        if quality_score < self.QUALITY_THRESHOLD:
            if self.logger:
                self.logger.debug(f"    ⚠️  质量不达标（阈值: {self.QUALITY_THRESHOLD}）")
            
            # 检查LLM是否可用
            if self.enable_llm and self.llm_client:
                self.stats['llm_calls'] += 1
                try:
                    if self.logger:
                        self.logger.info(f"    🤖 使用LLM增强...")
                    
                    # 使用LLM增强结果
                    result = self._enhance_with_llm(result, sheet, **kwargs)
                    
                    # 再次评估质量
                    new_quality_score = self._evaluate_quality(result, sheet, **kwargs)
                    if self.logger:
                        self.logger.debug(f"    📊 增强后质量分数: {new_quality_score:.2f}")
                    
                    # 验证增强后的结果
                    if self._is_valid(result):
                        self.stats['llm_success'] += 1
                        if self.logger:
                            self.logger.debug(f"    ✅ LLM增强成功")
                    else:
                        if self.logger:
                            self.logger.warning(f"    ⚠️  LLM增强后仍不达标")
                
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"      LLM增强失败: {e}")
                    # LLM失败时保留规则结果
        
        # ========== 阶段4: 最终验证 ==========
        if self._is_valid(result):
            self.stats['rule_success'] += 1
            return result
        else:
            # 使用默认值
            self.stats['default_used'] += 1
            if self.logger:
                self.logger.warning(f"    ⚠️  最终验证失败，使用默认值")
            return self._get_default()
    
    def _enhance_with_llm(self, result, sheet, **kwargs):
        """
        使用LLM增强/修复提取结果（v2.0 新增）
        
        【策略】
        1. 将规则提取的结果作为参考
        2. 让LLM验证和补充
        3. 合并两者的结果
        
        Args:
            result: 规则提取的结果
            sheet: Excel sheet对象
            **kwargs: 额外参数
        
        Returns:
            增强后的结果
        """
        if not self.llm_client:
            return result
        
        try:
            # 构建提示词：包含规则提取的结果
            prompt = self._build_enhancement_prompt(result, sheet, **kwargs)
            
            # ✅ 检查prompt是否为空
            if self.logger:
                self.logger.info(f"      📝 Prompt长度: {len(prompt) if prompt else 0} 字符")
            
            if not prompt or len(prompt.strip()) == 0:
                if self.logger:
                    self.logger.info(f"      ⚠️  Prompt为空，跳过LLM增强")
                return result
            
            # ✅ 添加延迟，避免429错误
            import time
            if self.logger:
                self.logger.info(f"      ⏰ 等待2秒避免429错误...")
            time.sleep(2.0)  # 2秒延迟
            
            # 调用LLM
            llm_response = self.llm_client.chat(prompt)
            
            # ✅ 添加调试日志
            if self.logger:
                self.logger.info(f"      📊 LLM响应长度: {len(llm_response) if llm_response else 0} 字符")
                if llm_response and len(llm_response) > 0:
                    preview = llm_response[:100].replace('\n', ' ')
                    self.logger.info(f"      📄 LLM响应前100字符: {preview}")
                else:
                    self.logger.warning(f"      ⚠️  LLM返回空响应")
            
            # 解析LLM返回的结果
            llm_result = self._parse_llm_response(llm_response)
            
            # 合并结果
            enhanced_result = self._merge_results(result, llm_result)
            
            return enhanced_result
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"      LLM增强失败: {e}")
            return result  # 失败时返回原结果
    
    def _parse_llm_response(self, response: str):
        """
        解析LLM返回的JSON格式结果（v2.0 新增）
        
        【处理要点】
        1. 去除Markdown代码块标记（```json）
        2. 解析JSON
        3. 容错处理
        
        Args:
            response: LLM返回的文本
        
        Returns:
            解析后的对象（通常是dict或list）
        """
        try:
            # 去除可能的```json标记
            response = response.strip()
            if response.startswith('```'):
                # 去除第一行
                lines = response.split('\n')
                response = '\n'.join(lines[1:])
            if response.endswith('```'):
                # 去除最后一行
                lines = response.split('\n')
                response = '\n'.join(lines[:-1])
            
            # 解析JSON
            import json
            return json.loads(response)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"      解析LLM响应失败: {e}")
            return None
    
    def get_stats(self) -> dict:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        for key in self.stats:
            if isinstance(self.stats[key], list):
                self.stats[key] = []
            else:
                self.stats[key] = 0
    
    # ========== 抽象方法（子类必须实现） ==========
    
    @abstractmethod
    def _extract_with_rules(self, sheet, **kwargs) -> Any:
        """
        规则提取
        
        【子类实现】
        使用正则表达式、关键词匹配等规则方法提取数据。
        
        Args:
            sheet: Excel sheet对象
            **kwargs: 额外参数
            
        Returns:
            提取结果（类型由子类定义）
            
        【示例】
        - Route: Route(起始地="深圳", 目的地="香港")
        - Agent: [Agent(...), Agent(...)]
        """
        pass
    
    @abstractmethod
    def _evaluate_quality(self, result, sheet, **kwargs) -> float:
        """
        评估提取质量
        
        【子类实现】
        根据提取结果的完整性、准确性等指标，返回0-1之间的分数。
        
        Args:
            result: 规则提取的结果
            sheet: Excel sheet对象
            **kwargs: 额外参数
            
        Returns:
            质量分数（0.0-1.0）
            
        【评分建议】
        - 1.0: 完美提取，所有字段都有值
        - 0.7-0.9: 良好，主要字段都有
        - 0.5-0.7: 一般，部分字段缺失
        - 0.0-0.5: 较差，大量字段缺失
        """
        pass
    
    @abstractmethod
    def _build_enhancement_prompt(self, result, sheet, **kwargs) -> str:
        """
        构建LLM增强提示词
        
        【子类实现】
        根据规则提取的结果和sheet内容，构建LLM提示词。
        
        Args:
            result: 规则提取的结果
            sheet: Excel sheet对象
            **kwargs: 额外参数
            
        Returns:
            LLM提示词（字符串）
            
        【提示词要点】
        1. 包含sheet的文本内容
        2. 说明规则提取的结果（如果有）
        3. 明确LLM需要提取什么
        4. 指定返回格式（通常是JSON）
        """
        pass
    
    @abstractmethod
    def _merge_results(self, rule_result, llm_result) -> Any:
        """
        合并规则和LLM的结果
        
        【子类实现】
        将规则提取的结果和LLM提取的结果合并。
        
        Args:
            rule_result: 规则提取的结果
            llm_result: LLM提取的结果（已解析）
            
        Returns:
            合并后的结果
            
        【合并策略】
        - 简单策略: LLM优先（LLM结果覆盖规则结果）
        - 复杂策略: 字段级合并（LLM补充规则未提取的字段）
        """
        pass
    
    @abstractmethod
    def _extract_with_llm(self, sheet, **kwargs) -> Any:
        """
        纯LLM提取（可选）
        
        【子类实现】
        直接使用LLM提取，不依赖规则。
        通常不使用，保留此接口用于特殊场景。
        
        Args:
            sheet: Excel sheet对象
            **kwargs: 额外参数
            
        Returns:
            提取结果
        """
        pass
    
    @abstractmethod
    def _is_valid(self, result) -> bool:
        """
        验证结果是否有效
        
        【子类实现】
        检查提取结果是否满足最低要求。
        
        Args:
            result: 提取结果
            
        Returns:
            是否有效
            
        【验证要点】
        - 必填字段是否存在
        - 值是否合理（如起始地不能是"未知"）
        """
        pass
    
    @abstractmethod
    def _get_default(self) -> Any:
        """
        获取默认值
        
        【子类实现】
        当规则和LLM都失败时，返回一个默认值。
        
        Returns:
            默认值
            
        【示例】
        - Route: Route(起始地="未知", 目的地="未知")
        - Agent: [] (空列表)
        """
        pass
    
    # ========== 辅助方法 ==========
    
    def _serialize_sheet(self, sheet, max_rows: int = 50) -> str:
        """
        将sheet序列化为文本（给LLM使用）
        
        【功能】
        将Excel sheet转换为易读的文本格式，包含：
        - Sheet名称
        - 前N行的内容（默认50行）
        - 格式化为 "行X: cell1 | cell2 | cell3"
        
        Args:
            sheet: Excel sheet对象
            max_rows: 最多序列化多少行
            
        Returns:
            序列化后的文本
        """
        try:
            lines = [f"Sheet名称: {sheet.title}", ""]
            
            for row_idx, row in enumerate(sheet.iter_rows(max_row=max_rows), 1):
                try:
                    cells = [str(cell.value or '') for cell in row]
                    # 过滤掉全空的行
                    if any(cell.strip() for cell in cells):
                        line = f"行{row_idx}: " + " | ".join(cells)
                        lines.append(line)
                except Exception as e:
                    # 某一行出错，跳过
                    if self.logger:
                        self.logger.debug(f"      序列化第{row_idx}行失败: {e}")
                    continue
            
            result = "\n".join(lines)
            
            # ✅ 限制长度，避免prompt太长
            if len(result) > 2000:
                result = result[:2000] + "\n... (内容过长，已截断)"
                if self.logger:
                    self.logger.debug(f"      ⚠️  Sheet内容过长，已截断到2000字符")
            
            return result
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"      序列化sheet失败: {e}")
            return f"Sheet名称: {sheet.title if hasattr(sheet, 'title') else '未知'}"


# ========== 便捷函数 ==========

def create_extractor(extractor_class, logger=None, llm_client=None, enable_llm=False):
    """
    创建提取器的便捷函数
    
    Args:
        extractor_class: 提取器类
        logger: 日志记录器
        llm_client: LLM客户端
        enable_llm: 是否启用LLM
        
    Returns:
        提取器实例
    """
    return extractor_class(logger=logger, llm_client=llm_client, enable_llm=enable_llm)


__all__ = ['BaseExtractor', 'create_extractor']