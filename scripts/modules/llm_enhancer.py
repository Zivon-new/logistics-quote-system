# scripts/modules/llm_enhancer.py
"""
LLM增强提取器 - 基于智谱GLM-4
用于提取正则无法准确识别的复杂字段
"""

from zhipuai import ZhipuAI
import json
import re
import logging
from typing import Dict, Optional, List


class LLMEnhancer:
    """
    LLM增强提取器
    
    使用场景：
    1. 正则提取失败或置信度低时
    2. 复杂语义理解（如"不含"字段）
    3. 非标准格式的数据
    """
    
    def __init__(self, api_key: str, model: str = None, max_tokens: int = None, temperature: float = None):
        """
        初始化LLM增强器
        
        Args:
            api_key: 智谱AI的API密钥
            model: 模型名称（None=从config读取）
            max_tokens: 最大token数（None=从config读取）
            temperature: 温度参数（None=从config读取）
        """
        from scripts.config import Config
        
        self.client = ZhipuAI(api_key=api_key)
        
        # ✅ 从config读取，而不是硬编码
        self.model = model or Config.LLM_MODEL
        self.max_tokens = max_tokens or Config.LLM_MAX_TOKENS or 4000  # 增加默认值
        self.temperature = temperature or Config.LLM_TEMPERATURE
        
        self.logger = logging.getLogger(__name__)
        
        # 统计信息
        self.total_calls = 0
        self.total_tokens = 0
        self.successful_calls = 0
        self.failed_calls = 0
        
        self.logger.info("LLM增强器初始化成功")
        self.logger.info(f"   模型: {self.model}")
        self.logger.info(f"   max_tokens: {self.max_tokens}")
        self.logger.info(f"   temperature: {self.temperature}")
    
    
    def chat(self, prompt: str, system_prompt: str = None, temperature: float = None, max_tokens: int = None, max_retries: int = 3) -> str:
        """
        简单的聊天接口（适配新架构的BaseExtractor）
        
        【用途】
        为了兼容 BaseExtractor v2.0 的 _enhance_with_llm 方法
        
        【v2.1 修复】
        ✅ 添加重试机制（max_retries=3）
        ✅ 检测空响应并自动重试
        ✅ 失败时抛出异常（由BaseExtractor捕获）
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            temperature: 温度参数
            max_tokens: 最大token数
            max_retries: 最大重试次数（默认3次）
        
        Returns:
            LLM的文本响应
        
        Raises:
            Exception: 所有重试都失败时抛出异常
        """
        # ✅ 使用self的默认值
        if temperature is None:
            temperature = self.temperature
        if max_tokens is None:
            max_tokens = self.max_tokens
        
        # ✅ 添加调试输出
        if self.logger:
            self.logger.info(f"      🔧 LLM参数: max_tokens={max_tokens}, temp={temperature}")
            self.logger.info(f"      📝 Prompt长度: {len(prompt)} 字符")
        
        messages = []
        
        # 添加系统提示词
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        else:
            messages.append({
                "role": "system",
                "content": "你是专业的物流数据提取助手。请严格按JSON格式返回结果。"
            })
        
        # 添加用户提示词
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # ✅ 重试循环
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # 获取响应内容
                content = response.choices[0].message.content
                
                # ✅ 检查是否为空响应
                if not content or len(content.strip()) == 0:
                    if self.logger:
                        self.logger.warning(f"      ⚠️  LLM返回空响应，尝试重试 ({attempt+1}/{max_retries})")
                    
                    # 如果不是最后一次尝试，等待后重试
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(2)  # 等待2秒后重试
                        continue
                    else:
                        # 最后一次也失败，抛出异常
                        raise Exception("LLM返回空响应（所有重试都失败）")
                
                # ✅ v3 FINAL修复：100%避免None+int错误
                self.total_calls = (self.total_calls or 0) + 1
                
                # ✅ 多重安全防护
                try:
                    if (hasattr(response, 'usage') and 
                        response.usage is not None and 
                        hasattr(response.usage, 'total_tokens') and 
                        response.usage.total_tokens is not None):
                        token_count = int(response.usage.total_tokens)
                        self.total_tokens = (self.total_tokens or 0) + token_count
                except (TypeError, ValueError, AttributeError) as e:
                    if self.logger:
                        self.logger.debug(f"      统计tokens失败(已忽略): {e}")
                
                self.successful_calls = (self.successful_calls or 0) + 1
                
                if self.logger and attempt > 0:
                    self.logger.info(f"      ✅ 重试成功（第{attempt+1}次尝试）")
                
                return content
                
            except Exception as e:
                last_error = e
                # ✅ 彻底修复：使用安全方式（避免None错误）
                self.total_calls = (self.total_calls or 0) + 1
                self.failed_calls = (self.failed_calls or 0) + 1
                
                if self.logger:
                    self.logger.error(f"      ❌ LLM调用失败 (尝试{attempt+1}/{max_retries}): {e}")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2)  # 等待2秒后重试
                    continue
                else:
                    # 最后一次也失败，抛出异常
                    raise Exception(f"LLM调用失败（所有重试都失败）: {last_error}")
    def extract_agent_info(
        self, 
        text: str, 
        regex_result: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        提取代理商信息
        
        Args:
            text: 原始文本（多行）
            regex_result: 正则提取的结果（用于对比和补充）
            
        Returns:
            {
                "代理商": "XX物流有限公司",
                "运输方式": "海运",
                "贸易类型": "DDP",
                "时效": "5-7天",
                "不含": "目的港清关费",
                "是否赔付": "是"
            }
        """
        prompt = self._build_agent_prompt(text, regex_result)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是物流数据提取专家。请严格按JSON格式返回结果，字段值为null时表示未找到。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # 低温度，减少随机性
                max_tokens=self.max_tokens,
            )
            
            # 统计
            self.total_calls += 1
            self.total_tokens += response.usage.total_tokens
            
            # 解析JSON
            content = response.choices[0].message.content
            result = self._parse_json_response(content)
            
            if result:
                self.successful_calls += 1
                self.logger.info(f"[OK] LLM提取成功: 代理商={result.get('代理商')}")
            else:
                self.failed_calls += 1
                self.logger.warning("[WARN] LLM返回结果解析失败")
            
            return result
            
        except Exception as e:
            self.failed_calls += 1
            self.logger.error(f"[ERROR] LLM调用失败: {e}")
            return None
    
    def _build_agent_prompt(self, text: str, regex_result: Optional[Dict]) -> str:
        """构建代理商信息提取的prompt"""
        
        # 基础提示词
        prompt = f"""请从以下物流报价文本中提取代理商信息。

【文本内容】
{text}

【提取字段】
1. 代理商: 公司名称（如"深圳市XX货运代理有限公司"）
2. 运输方式: 海运/空运/铁路/快递 四选一
3. 贸易类型: DDP/DAP/DDU/FOB/CIF等
4. 时效: 运输时效（如"5-7天"、"3-5个工作日"）
5. 不含: 不包含的服务项目（如"不含目的港清关费"）
6. 是否赔付: 如果提到赔付/理赔/保险返回"是"，否则返回"否"

【返回格式】（严格JSON，不要其他文字）
{{
  "代理商": "...",
  "运输方式": "...",
  "贸易类型": "...",
  "时效": "...",
  "不含": "...",
  "是否赔付": "..."
}}

注意：如果某个字段无法确定，返回null而不是空字符串。
"""
        
        # 如果有正则结果，加入参考信息
        if regex_result:
            prompt += f"\n\n【参考】正则表达式已提取到部分信息：\n{json.dumps(regex_result, ensure_ascii=False, indent=2)}\n请验证并补充遗漏的字段。"
        
        return prompt
    
    def extract_fee_info(
        self, 
        text: str,
        regex_result: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        提取费用信息
        
        Args:
            text: 费用描述文本
            regex_result: 正则提取的结果
            
        Returns:
            {
                "费用类型": "海运费",
                "单价": 25.5,
                "单位": "kg",
                "数量": 1740,
                "币种": "RMB"
            }
        """
        prompt = f"""请从以下文本中提取费用信息。

【文本】
{text}

【提取字段】
1. 费用类型: 如"海运费"、"报关费"、"THC"、"文件费"等
2. 单价: 数字，如25.5
3. 单位: 如"kg"、"cbm"、"票"、"柜"等
4. 数量: 数字
5. 币种: RMB/USD/EUR等

【返回格式】
{{
  "费用类型": "...",
  "单价": ...,
  "单位": "...",
  "数量": ...,
  "币种": "..."
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是费用数据提取专家，返回标准JSON。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=self.max_tokens,
            )
            
            self.total_calls += 1
            self.total_tokens += response.usage.total_tokens
            
            content = response.choices[0].message.content
            result = self._parse_json_response(content)
            
            if result:
                self.successful_calls += 1
                self.logger.info(f"[OK] 费用提取成功: {result.get('费用类型')}")
            else:
                self.failed_calls += 1
            
            return result
            
        except Exception as e:
            self.failed_calls += 1
            self.logger.error(f"[ERROR] 费用提取失败: {e}")
            return None
    
    
    def extract_route_info(
        self, 
        text: str,
        regex_result: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        提取路线信息
        
        Args:
            text: 原始文本
            regex_result: 正则提取的结果
            
        Returns:
            {
                "起始地": "深圳",
                "途径地": "香港",
                "目的地": "洛杉矶",
                "实际重量": 1740.0,
                "计费重量": 1740.0,
                "总体积": 5.46,
                "货值": 50000.0
            }
        """
        prompt = f"""请从以下物流报价文本中提取路线信息。

【文本内容】
{text}

【提取字段】
1. 起始地: 出发城市/港口（如"深圳"、"上海"、"广州"）
2. 途径地: 中转城市/港口（如"香港"、"新加坡"，可能为null）
3. 目的地: 目的城市/港口（如"洛杉矶"、"纽约"、"汉堡"）
4. 实际重量: 实际货物重量(kg)，提取数字
5. 计费重量: 计费重量(kg)，如果没有则等于实际重量
6. 总体积: 总体积(cbm)，提取数字
7. 货值: 货物价值，提取数字（可能为null）

【返回格式】（严格JSON，不要其他文字）
{{
  "起始地": "...",
  "途径地": "...",
  "目的地": "...",
  "实际重量": ...,
  "计费重量": ...,
  "总体积": ...,
  "货值": ...
}}

注意：如果某个字段无法确定，返回null。重量和体积必须是数字，不是字符串。
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是物流路线信息提取专家，返回标准JSON。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=self.max_tokens,
            )
            
            self.total_calls += 1
            self.total_tokens += response.usage.total_tokens
            
            content = response.choices[0].message.content
            result = self._parse_json_response(content)
            
            if result:
                self.successful_calls += 1
                self.logger.info(f"[OK] 路线提取成功: {result.get('起始地')} → {result.get('目的地')}")
            else:
                self.failed_calls += 1
            
            return result
            
        except Exception as e:
            self.failed_calls += 1
            self.logger.error(f"[ERROR] 路线提取失败: {e}")
            return None
    
    def extract_goods_total(
        self, 
        sheet_content: str
    ) -> Optional[List[Dict]]:
        """
        使用LLM提取整单货物信息（完全用LLM，不依赖规则）
        
        【重要】这个方法用于处理格式混乱的货物描述，如：
        - "2件展示柜/5.46cbm/910kg"
        - "4台Dell PowerEdge R7625 预估重量150KGS"
        - "粮食标本: 3.68*3.68*3.68mm"
        
        Args:
            sheet_content: sheet的文本内容
            
        Returns:
            [
                {
                    "货物名称": "展示柜",
                    "实际重量": 910.0,
                    "总体积": 5.46,
                    "货值": None
                },
                ...
            ]
        """
        prompt = f"""请从以下Excel内容中提取货物信息。

【文本内容】
{sheet_content}

【提取规则】
1. 只提取真实的货物名称（如"展示柜"、"Dell服务器"、"粮食标本"）
2. 忽略以下内容：
   - 代理商名称（如"银顺达"、"欧力物流"）
   - 费用项目（如"海运费"、"报关费"、"操作费"）
   - 时效说明（如"3-5天"、"8-12个工作日"）
   - 赔付标准、不含说明
   - 专线名称（如"国内-西班牙海运专线"）
3. 提取货物的：
   - 实际重量(kg) - 提取数字，如果没有返回null
   - 总体积(cbm) - 提取数字，如果没有返回null
   - 货值 - 提取数字，如果没有返回null

【返回格式】（严格JSON数组，不要其他文字）
[
  {{
    "货物名称": "...",
    "实际重量": ...,
    "总体积": ...,
    "货值": ...
  }}
]

注意：
- 如果没有找到任何货物，返回空数组 []
- 货物名称必须具体，不能是"货物"、"物品"这种泛称
- 重量、体积、货值必须是数字或null，不是字符串
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是货物信息提取专家。请仔细区分货物名称和费用项目、代理商名称。返回标准JSON数组。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=self.max_tokens,
            )
            
            self.total_calls += 1
            self.total_tokens += response.usage.total_tokens
            
            content = response.choices[0].message.content
            
            # 解析JSON数组
            result = self._parse_json_array_response(content)
            
            if result is not None:
                self.successful_calls += 1
                self.logger.info(f"[OK] 货物提取成功: {len(result)}个货物")
            else:
                self.failed_calls += 1
                self.logger.warning("[WARN] 货物提取失败: 无法解析JSON")
            
            return result
            
        except Exception as e:
            self.failed_calls += 1
            self.logger.error(f"[ERROR] 货物提取失败: {e}")
            return None
    
    def _parse_json_array_response(self, content: str) -> Optional[List[Dict]]:
        """
        解析LLM返回的JSON数组
        
        LLM可能返回：
        1. 纯JSON数组: [{"key": "value"}]
        2. Markdown代码块: ```json\n[...]\n```
        3. 带说明文字: "这是结果：[...]"
        """
        try:
            # 尝试1: 直接解析
            result = json.loads(content)
            if isinstance(result, list):
                return result
        except:
            pass
        
        try:
            # 尝试2: 提取markdown代码块中的JSON数组
            match = re.search(r'```json\s*(\[.*?\])\s*```', content, re.DOTALL)
            if match:
                result = json.loads(match.group(1))
                if isinstance(result, list):
                    return result
        except:
            pass
        
        try:
            # 尝试3: 提取第一个JSON数组
            match = re.search(r'\[[^\[\]]*(?:\{[^{}]*\}[^\[\]]*)*\]', content, re.DOTALL)
            if match:
                result = json.loads(match.group(0))
                if isinstance(result, list):
                    return result
        except:
            pass
        
        # 解析失败
        self.logger.warning(f"无法解析LLM返回的数组: {content[:100]}...")
        return None
    
    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """
        解析LLM返回的JSON
        
        LLM可能返回：
        1. 纯JSON: {"key": "value"}
        2. Markdown代码块: ```json\n{...}\n```
        3. 带说明文字: "这是结果：{...}"
        """
        try:
            # 尝试1: 直接解析
            return json.loads(content)
        except:
            pass
        
        try:
            # 尝试2: 提取markdown代码块中的JSON
            match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except:
            pass
        
        try:
            # 尝试3: 提取第一个JSON对象
            match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except:
            pass
        
        # 解析失败
        self.logger.warning(f"无法解析LLM返回: {content[:100]}...")
        return None
    
    def get_usage_stats(self) -> Dict:
        """
        获取使用统计
        
        Returns:
            {
                "total_calls": 10,
                "successful_calls": 9,
                "failed_calls": 1,
                "total_tokens": 5000,
                "estimated_cost": "¥0.50"
            }
        """
        cost = self.total_tokens / 1000 * 0.1  # ¥0.1/千tokens
        
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "total_tokens": self.total_tokens,
            "estimated_cost": f"¥{cost:.2f}"
        }
    
    def print_stats(self):
        """打印统计信息（修复编码问题）"""
        stats = self.get_usage_stats()
        
        print("\n" + "=" * 60)
        print("LLM Usage Statistics")  # 移除中文，避免GBK编码问题
        print("=" * 60)
        print(f"Total calls: {stats['total_calls']}")
        print(f"  Success: {stats['successful_calls']}")
        print(f"  Failed: {stats['failed_calls']}")
        print(f"Total tokens: {stats['total_tokens']}")
        print(f"Estimated cost: {stats['estimated_cost']}")
        print("=" * 60)