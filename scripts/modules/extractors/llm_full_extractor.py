# scripts/modules/extractors/llm_full_extractor.py
"""
LLM全量提取器

【适用场景】
Sheet格式混乱，规则提取效果差。

【策略】
将整个Sheet序列化后，用一次LLM调用提取所有业务数据：
路线、代理商、费用明细、整单费用、货物信息。

【输出格式】
返回与 horizontal_table_parser_v2._process_sheet_with_progress 兼容的 sheet_data 字典：
{
    'route': Route,
    'agents': [Agent, ...],
    'goods': {'type': 'total', 'goods_total': SimpleGoodsTotal},
    'fees': [{'fee_items': [...], 'fee_totals': [...]}, ...],  # 与agents一一对应
    'summaries': [Summary, ...],
    '_extracted_by': 'llm_full'
}
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from .route_extractor_v2 import Route
from .agent_extractor_v2 import Agent
from .summary_extractor import Summary


# ── 轻量数据类（避免循环导入，且与DataAssembler的get_value兼容）──

class SimpleFeeItem:
    """单价费用项（如 海运费 25元/kg）"""
    def __init__(self, 费用类型=None, 单价=None, 单位=None, 数量=None, 币种='RMB', 备注=None):
        self.费用类型 = 费用类型
        self.单价 = 单价
        self.单位 = 单位
        self.数量 = 数量
        self.币种 = 币种
        self.备注 = 备注


class SimpleFeeTotal:
    """整单费用（如 操作费 300元）"""
    def __init__(self, 费用名称=None, 原币金额=None, 币种='RMB', 备注=None):
        self.费用名称 = 费用名称
        self.原币金额 = 原币金额
        self.币种 = 币种
        self.备注 = 备注


class SimpleGoodsTotal:
    """整单货物汇总"""
    def __init__(self, 货物名称='', 实际重量=None, 货值=None, 总体积=None, 备注=None):
        self.货物名称 = 货物名称
        self.实际重量 = 实际重量
        self.货值 = 货值
        self.总体积 = 总体积
        self.备注 = 备注


# ── 主类 ─────────────────────────────────────────────────────────

class LLMFullExtractor:
    """
    LLM全量提取器

    对格式混乱的Sheet，用一次LLM调用提取所有数据。
    比"规则提取 + LLM打补丁"的组合效果好得多。
    """

    MAX_ROWS = 80    # 序列化时最多读取的行数
    MAX_COLS = 15    # 序列化时最多读取的列数

    def __init__(self, llm_client, logger: Optional[logging.Logger] = None):
        self.llm_client = llm_client
        self.logger = logger or logging.getLogger(__name__)

    def extract(self, sheet) -> Dict[str, Any]:
        """
        主入口：从Sheet中全量提取所有数据

        Returns:
            sheet_data dict（与主解析器兼容）
        """
        self.logger.info(f"    🤖 [LLM全量提取] Sheet: {sheet.title}")

        # 1. 序列化整个Sheet
        sheet_content = self._serialize_full_sheet(sheet)

        # 2. 构建Prompt，调用LLM
        prompt = self._build_prompt(sheet, sheet_content)
        try:
            response = self.llm_client.chat(prompt)
            llm_data = self._parse_response(response)
        except Exception as e:
            self.logger.error(f"    ❌ [LLM全量提取] LLM调用失败: {e}")
            return self._empty_result()

        if not llm_data:
            self.logger.warning("    ⚠️  [LLM全量提取] 响应解析失败，返回空结果")
            return self._empty_result()

        # 3. 转换为兼容的 sheet_data 结构
        result = self._convert_to_sheet_data(llm_data)
        agent_count = len(result.get('agents', []))
        self.logger.info(f"    ✅ [LLM全量提取] 完成：{agent_count}个代理商")
        return result

    # ── 序列化 ───────────────────────────────────────────────────

    def _serialize_full_sheet(self, sheet) -> str:
        """将Sheet全部内容序列化为文本"""
        lines = [f"【Sheet名称】: {sheet.title}", ""]
        for row_idx, row in enumerate(sheet.iter_rows(max_row=self.MAX_ROWS), 1):
            cells = []
            for col_idx, cell in enumerate(row, 1):
                if col_idx > self.MAX_COLS:
                    break
                cells.append(str(cell.value or '').strip())
            if any(c for c in cells):
                lines.append(f"行{row_idx}: " + " | ".join(cells))
        return "\n".join(lines)

    # ── Prompt ───────────────────────────────────────────────────

    def _build_prompt(self, sheet, content: str) -> str:
        return f"""你是专业的国际物流数据提取助手。请从以下Excel Sheet内容中提取所有物流报价信息。

【Excel内容】
{content}

【提取任务】
请提取以下所有信息，严格按照JSON格式返回：

1. **路线信息**（route）：起始地、目的地、途径地、货物重量(kg)、体积(cbm)、货值
2. **代理商列表**（agents）：Sheet中可能有多个代理商（每列一个），请全部提取：
   - 代理商：公司名称
   - 运输方式：海运/空运/铁路/快递（四选一）
   - 贸易类型：DDP/DAP/DDU/FOB/CIF/一般贸易/双清/正清等
   - 时效：如"15-20天"
   - 时效备注：更详细的时效说明
   - 不含：该报价不含的费用项目（如"目的港清关费、仓储费"）
   - 是否赔付："是"或"否"
   - 赔付内容：赔付的具体描述
   - 代理备注：其他备注
   - 费用明细：按单价计费的费用列表（如25元/kg的海运费）
   - 整单费用：固定金额的费用列表（如操作费300元）
3. **货物信息**（goods）：货物名称、实际重量(kg)、总体积(cbm)、货值、备注

【返回格式】（严格JSON，不要任何其他文字或解释）
{{
  "route": {{
    "起始地": "深圳",
    "目的地": "新加坡",
    "途径地": null,
    "weight": 1000.0,
    "volume": 5.5,
    "value": null
  }},
  "agents": [
    {{
      "代理商": "XX物流",
      "运输方式": "海运",
      "贸易类型": "DDP",
      "时效": "15-20天",
      "时效备注": "门到门包关包税",
      "不含": "目的港仓储费",
      "是否赔付": "是",
      "赔付内容": "按货值1%赔付",
      "代理备注": null,
      "费用明细": [
        {{"费用类型": "海运费", "单价": 25.0, "单位": "kg", "数量": null, "币种": "RMB"}}
      ],
      "整单费用": [
        {{"费用名称": "操作费", "原币金额": 300.0, "币种": "RMB"}}
      ]
    }}
  ],
  "goods": {{
    "货物名称": "电子产品",
    "实际重量": 1000.0,
    "总体积": 5.5,
    "货值": null,
    "备注": null
  }}
}}

注意：
- 无法提取的字段返回null，不要返回空字符串
- 费用明细是按单价计费（如25元/kg），整单费用是固定金额（如操作费300元）
- 没有代理商信息时agents返回[]，没有货物信息时goods返回null
- 数字类型字段必须是数字，不能是字符串"""

    # ── 解析 ─────────────────────────────────────────────────────

    def _parse_response(self, response: str) -> Optional[Dict]:
        """解析LLM响应，支持多种格式容错"""
        if not response:
            return None

        text = response.strip()

        # 尝试1：直接解析
        try:
            return json.loads(text)
        except Exception:
            pass

        # 尝试2：提取markdown代码块中的JSON
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        # 尝试3：提取响应中第一个完整JSON对象（贪婪匹配）
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

        self.logger.warning(f"    ⚠️  无法解析LLM响应: {text[:100]}...")
        return None

    # ── 类型转换 ─────────────────────────────────────────────────

    def _convert_to_sheet_data(self, llm_data: Dict) -> Dict[str, Any]:
        """将LLM结果转换为与解析器兼容的 sheet_data 格式"""
        route = self._convert_route(llm_data.get('route'))
        agents_data = llm_data.get('agents') or []

        agents, fees, summaries = [], [], []
        for agent_data in agents_data:
            agents.append(self._convert_agent(agent_data))
            fees.append({
                'fee_items': self._convert_fee_items(agent_data.get('费用明细')),
                'fee_totals': self._convert_fee_totals(agent_data.get('整单费用')),
            })
            summaries.append(Summary())  # LLM暂不提取税率/汇损率，保留空对象

        goods = self._convert_goods(llm_data.get('goods'))

        return {
            'route': route,
            'agents': agents,
            'goods': goods,
            'fees': fees,
            'summaries': summaries,
            '_extracted_by': 'llm_full',
        }

    def _convert_route(self, data: Optional[Dict]) -> Optional[Route]:
        if not data:
            return None
        return Route(
            起始地=data.get('起始地'),
            目的地=data.get('目的地'),
            途径地=data.get('途径地'),
            weight=self._to_float(data.get('weight')),
            volume=self._to_float(data.get('volume')),
            value=self._to_float(data.get('value')),
        )

    def _convert_agent(self, data: Dict) -> Agent:
        return Agent(
            代理商=data.get('代理商'),
            代理备注=data.get('代理备注'),
            时效=data.get('时效'),
            时效备注=data.get('时效备注'),
            不含=data.get('不含'),
            是否赔付=data.get('是否赔付'),
            赔付内容=data.get('赔付内容'),
            运输方式=data.get('运输方式'),
            贸易类型=data.get('贸易类型'),
        )

    def _convert_fee_items(self, items: Optional[List]) -> List[SimpleFeeItem]:
        if not items:
            return []
        result = []
        for item in items:
            if isinstance(item, dict):
                result.append(SimpleFeeItem(
                    费用类型=item.get('费用类型'),
                    单价=self._to_float(item.get('单价')),
                    单位=item.get('单位'),
                    数量=self._to_float(item.get('数量')),
                    币种=item.get('币种') or 'RMB',
                    备注=item.get('备注'),
                ))
        return result

    def _convert_fee_totals(self, items: Optional[List]) -> List[SimpleFeeTotal]:
        if not items:
            return []
        result = []
        for item in items:
            if isinstance(item, dict):
                result.append(SimpleFeeTotal(
                    费用名称=item.get('费用名称'),
                    原币金额=self._to_float(item.get('原币金额')),
                    币种=item.get('币种') or 'RMB',
                    备注=item.get('备注'),
                ))
        return result

    def _convert_goods(self, data: Optional[Dict]) -> Dict:
        if not data:
            return {'type': None, 'goods_details': None, 'goods_total': None}
        return {
            'type': 'total',
            'goods_details': None,
            'goods_total': SimpleGoodsTotal(
                货物名称=data.get('货物名称') or '',
                实际重量=self._to_float(data.get('实际重量')),
                货值=self._to_float(data.get('货值')),
                总体积=self._to_float(data.get('总体积')),
                备注=data.get('备注'),
            ),
        }

    def _empty_result(self) -> Dict[str, Any]:
        return {
            'route': None,
            'agents': [],
            'goods': {'type': None, 'goods_details': None, 'goods_total': None},
            'fees': [],
            'summaries': [],
            '_extracted_by': 'llm_full_failed',
        }

    @staticmethod
    def _to_float(val) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None


__all__ = ['LLMFullExtractor', 'SimpleFeeItem', 'SimpleFeeTotal', 'SimpleGoodsTotal']
