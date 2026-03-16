# backend/app/api/v1/agent_check.py
"""
AI 企业背调助手 — 调用 GLM-4-Flash，结果缓存到 agent_check_history
"""
import time
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from zhipuai import ZhipuAI
from ...database import get_db
from ...core.deps import get_current_user
from ...models.user import User
from ...config import settings

router = APIRouter(prefix="/agent-check", tags=["AI企业背调"])

CACHE_DAYS = 7          # 缓存有效期
MODEL_NAME = "glm-4-flash"

# ── Prompt 模板 ────────────────────────────────────────────────
SYSTEM_PROMPT = """你是一位专业的国际物流行业企业背调顾问，擅长通过联网搜索获取公司最新公开信息。

任务：对用户给出的货运代理/供应链公司进行背景调查。
请先通过联网搜索获取该公司的工商信息、官网、新闻、行业口碑等公开资料，再综合分析后输出报告。

报告必须严格按照以下 JSON 格式返回，不要输出任何额外内容：
{
  "公司名称": "公司全称",
  "成立背景": "成立时间、注册地、股东背景等工商信息",
  "主营业务": "核心业务范围，如国际货代、海运/空运/陆运代理、供应链管理等",
  "经营规模": "注册资本、员工规模、年营业额（如有）、分支机构等",
  "服务网络": "服务覆盖国家/地区、主要合作伙伴、港口代理网络",
  "合规资质": "是否持有无船承运人资质、NVOCC、海关AEO认证、IATA等相关资质",
  "风险提示": "经营异常、法律纠纷、负面新闻、信用黑名单等风险点",
  "综合评价": "基于以上信息的综合判断，100字以内",
  "风险评级": "低风险或中等风险或高风险或无法评估",
  "摘要": "不超过150字的总结"
}

要求：
- 必须先联网搜索再作答，优先从企查查、天眼查、海关总署、官网等权威来源获取信息
- 如果搜索到具体信息，请填写真实内容；如确实无法获取某项，填写"未查询到相关信息"
- 风险评级标准：有严重违规/失联/黑名单→高风险；有轻微负面/信息不完整→中等风险；信息齐全无异常→低风险；信息极度缺乏→无法评估
- 禁止在信息可搜索到时填写"信息不详"
"""


class CheckRequest(BaseModel):
    keyword: str        # 公司名称或关键词
    force_refresh: bool = False  # 是否强制重新调用（忽略缓存）


def _get_cache(db: Session, keyword: str):
    """查询7天内的缓存记录"""
    row = db.execute(text("""
        SELECT 查调ID, 报告摘要, 完整报告, 风险评级, 创建时间, llm模型, 查调耗时秒
        FROM agent_check_history
        WHERE 查询关键词 = :kw
          AND 创建时间 >= DATE_SUB(NOW(), INTERVAL :days DAY)
        ORDER BY 创建时间 DESC
        LIMIT 1
    """), {"kw": keyword, "days": CACHE_DAYS}).fetchone()
    return row


def _save_cache(db: Session, keyword: str, report_json: dict,
                risk_level: str, summary: str, tokens: int,
                elapsed: float, username: str):
    """保存背调结果到历史表"""
    db.execute(text("""
        INSERT INTO agent_check_history
            (查询关键词, llm模型, 报告摘要, 完整报告, 风险评级, token消耗, 查调耗时秒, 操作用户)
        VALUES
            (:kw, :model, :summary, :report, :risk, :tokens, :elapsed, :user)
    """), {
        "kw": keyword,
        "model": MODEL_NAME,
        "summary": summary,
        "report": json.dumps(report_json, ensure_ascii=False),
        "risk": risk_level,
        "tokens": tokens,
        "elapsed": round(elapsed, 2),
        "user": username,
    })
    db.commit()


@router.post("/check")
async def check_agent(
    req: CheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    对指定公司进行AI背调。
    - 7天内有缓存则直接返回缓存，不消耗 token
    - force_refresh=True 时强制重新调用
    """
    keyword = req.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="公司名称不能为空")

    if not settings.ZHIPU_API_KEY:
        raise HTTPException(status_code=503, detail="GLM API Key 未配置")

    # 命中缓存
    if not req.force_refresh:
        cached = _get_cache(db, keyword)
        if cached:
            report = json.loads(cached[2]) if cached[2] else {}
            return {
                "from_cache": True,
                "check_id": cached[0],
                "keyword": keyword,
                "summary": cached[1],
                "report": report,
                "risk_level": cached[3],
                "created_at": str(cached[4]),
                "model": cached[5],
                "elapsed": float(cached[6]) if cached[6] else None,
            }

    # 调用 GLM-4-Flash
    # 第一步：开启联网搜索，获取公司公开信息
    client = ZhipuAI(api_key=settings.ZHIPU_API_KEY)
    t0 = time.time()
    try:
        step1 = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": f"请联网搜索【{keyword}】这家公司的工商信息、主营业务、经营规模、合规资质、风险记录等公开信息，整理成详细的文字摘要。"},
            ],
            tools=[{"type": "web_search", "web_search": {"enable": True}}],
            temperature=0.3,
            max_tokens=1500,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GLM联网搜索失败：{str(e)}")

    search_summary = (step1.choices[0].message.content or "").strip()
    tokens = step1.usage.total_tokens if step1.usage else 0

    # 第二步：基于搜索结果，生成结构化 JSON 报告
    try:
        step2 = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"以下是关于【{keyword}】的公开信息搜索结果：\n\n{search_summary}\n\n请基于以上信息生成完整的背调报告JSON，不要输出任何额外内容。"},
            ],
            temperature=0.2,
            max_tokens=1500,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GLM报告生成失败：{str(e)}")

    elapsed = time.time() - t0
    raw_content = step2.choices[0].message.content
    if not raw_content:
        raise HTTPException(status_code=502, detail="GLM返回内容为空，请重试")
    content = raw_content.strip()
    tokens += step2.usage.total_tokens if step2.usage else 0

    # 解析 JSON 报告
    try:
        # 去掉可能包裹的 markdown 代码块
        if "```" in content:
            parts = content.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    content = part
                    break
        report = json.loads(content)
    except Exception:
        # 解析失败时保留原始文本
        report = {"原始输出": content}

    risk_level = report.get("风险评级", "无法评估")
    # 确保风险评级在枚举范围内
    valid_risks = {"低风险", "中等风险", "高风险", "无法评估"}
    if risk_level not in valid_risks:
        risk_level = "无法评估"

    summary = report.get("摘要", content[:150])

    # 存缓存
    _save_cache(db, keyword, report, risk_level, summary, tokens, elapsed,
                current_user.username)

    return {
        "from_cache": False,
        "keyword": keyword,
        "summary": summary,
        "report": report,
        "risk_level": risk_level,
        "model": MODEL_NAME,
        "tokens": tokens,
        "elapsed": round(elapsed, 2),
    }


@router.get("/history")
async def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取最近50条背调历史记录"""
    rows = db.execute(text("""
        SELECT 查调ID, 查询关键词, 风险评级, 报告摘要, llm模型,
               token消耗, 查调耗时秒, 操作用户, 创建时间
        FROM agent_check_history
        ORDER BY 创建时间 DESC
        LIMIT 50
    """)).fetchall()

    return [
        {
            "id": r[0],
            "keyword": r[1],
            "risk_level": r[2],
            "summary": r[3],
            "model": r[4],
            "tokens": r[5],
            "elapsed": float(r[6]) if r[6] else None,
            "user": r[7],
            "created_at": str(r[8]),
        }
        for r in rows
    ]


@router.get("/history/{check_id}")
async def get_history_detail(
    check_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取某条历史背调的完整报告"""
    row = db.execute(text("""
        SELECT 查调ID, 查询关键词, 风险评级, 报告摘要, 完整报告,
               llm模型, token消耗, 查调耗时秒, 操作用户, 创建时间
        FROM agent_check_history
        WHERE 查调ID = :id
    """), {"id": check_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")

    report = json.loads(row[4]) if row[4] else {}
    return {
        "id": row[0],
        "keyword": row[1],
        "risk_level": row[2],
        "summary": row[3],
        "report": report,
        "model": row[5],
        "tokens": row[6],
        "elapsed": float(row[7]) if row[7] else None,
        "user": row[8],
        "created_at": str(row[9]),
    }
