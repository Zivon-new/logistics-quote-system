# backend/app/api/v1/agent_check.py
"""
AI 企业背调助手
数据来源：用户从天眼查/企查查等平台复制粘贴
AI职责：结构化解析 + 风险推理 + 生成报告
"""
import time
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from zhipuai import ZhipuAI
from ...database import get_db
from ...core.deps import get_current_user
from ...models.user import User
from ...config import settings

router = APIRouter(prefix="/agent-check", tags=["AI企业背调"])

CACHE_DAYS = 7
MODEL_NAME = "glm-4-flash"

SYSTEM_PROMPT = """你是一位专业的国际物流行业企业背调分析师。

用户会粘贴从天眼查、企查查等平台获取的企业原始信息，你需要对其进行深度解读与风险评估，输出结构化背调报告。

报告必须严格按照以下 JSON 格式返回，不要输出任何额外内容：
{
  "公司名称": "公司全称",
  "成立背景": "成立时间、注册地、法定代表人、股东背景、营业期限等工商核心信息",
  "主营业务": "核心业务范围，结合经营范围分析实际主营方向",
  "经营规模": "注册资本、实缴资本、员工规模、参保人数、分支机构等规模信息",
  "服务网络": "服务覆盖地区、合作伙伴、所属集团、认证资质（如WCA/ISO等）",
  "合规资质": "海关资质（AEO/NVOCC等）、税务评级、高新认证、行业许可证等",
  "风险提示": "经营异常、司法涉诉、行政处罚、关联风险、注册资本与实缴差距、业务集中度等潜在风险",
  "综合评价": "基于以上信息的综合判断，100字以内",
  "风险评级": "低风险或中等风险或高风险或无法评估",
  "摘要": "不超过150字的总结"
}

风险评级标准：
- 低风险：信息完整、无违规、资质良好、纳税信用A级
- 中等风险：有轻微负面记录、信息不完整、或存在关联风险
- 高风险：严重违规/失联/黑名单/大量司法纠纷
- 无法评估：提供信息过少，无法做出判断

要求：
- 严格基于用户提供的原始数据进行分析，不要编造数据
- 对风险点要具体指出，不要泛泛而谈
- 注册资本与实缴资本差距大时，须在风险提示中说明"""


class CheckRequest(BaseModel):
    keyword: str              # 公司名称
    raw_text: str             # 用户粘贴的原始企业信息
    force_refresh: bool = False


def _get_cache(db: Session, keyword: str):
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


def _parse_report(content: str):
    """解析 GLM 返回的 JSON，容错处理 markdown 代码块"""
    try:
        if "```" in content:
            parts = content.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    content = part
                    break
        return json.loads(content)
    except Exception:
        return {"原始输出": content}


@router.post("/check")
async def check_agent(
    req: CheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    keyword = req.keyword.strip()
    raw_text = req.raw_text.strip()

    if not keyword:
        raise HTTPException(status_code=400, detail="公司名称不能为空")
    if not raw_text:
        raise HTTPException(status_code=400, detail="请粘贴企业信息后再分析")
    if not settings.ZHIPU_API_KEY:
        raise HTTPException(status_code=503, detail="GLM API Key 未配置")

    # 有粘贴文本时强制刷新（数据变了就重新分析）
    if not req.force_refresh and not raw_text:
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

    # 调用 GLM 进行分析（无需联网，基于用户提供的数据）
    client = ZhipuAI(api_key=settings.ZHIPU_API_KEY)
    t0 = time.time()

    user_msg = (
        f"请对以下企业信息进行背调分析，生成完整的背调报告JSON。\n\n"
        f"公司名称：{keyword}\n\n"
        f"原始企业信息（来自天眼查/企查查）：\n"
        f"{raw_text}\n\n"
        f"请严格基于以上信息进行分析，输出JSON格式报告，不要输出任何额外内容。"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.2,
            max_tokens=2000,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GLM调用失败：{str(e)}")

    elapsed = time.time() - t0
    raw_content = response.choices[0].message.content
    if not raw_content:
        raise HTTPException(status_code=502, detail="GLM返回内容为空，请重试")

    tokens = response.usage.total_tokens if response.usage else 0
    report = _parse_report(raw_content.strip())

    risk_level = report.get("风险评级", "无法评估")
    if risk_level not in {"低风险", "中等风险", "高风险", "无法评估"}:
        risk_level = "无法评估"

    summary = report.get("摘要", raw_content[:150])

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
    rows = db.execute(text("""
        SELECT 查调ID, 查询关键词, 风险评级, 报告摘要, llm模型,
               token消耗, 查调耗时秒, 操作用户, 创建时间
        FROM agent_check_history
        ORDER BY 创建时间 DESC
        LIMIT 50
    """)).fetchall()
    return [
        {
            "id": r[0], "keyword": r[1], "risk_level": r[2],
            "summary": r[3], "model": r[4], "tokens": r[5],
            "elapsed": float(r[6]) if r[6] else None,
            "user": r[7], "created_at": str(r[8]),
        }
        for r in rows
    ]


@router.get("/history/{check_id}")
async def get_history_detail(
    check_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    row = db.execute(text("""
        SELECT 查调ID, 查询关键词, 风险评级, 报告摘要, 完整报告,
               llm模型, token消耗, 查调耗时秒, 操作用户, 创建时间
        FROM agent_check_history WHERE 查调ID = :id
    """), {"id": check_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")

    return {
        "id": row[0], "keyword": row[1], "risk_level": row[2],
        "summary": row[3], "report": json.loads(row[4]) if row[4] else {},
        "model": row[5], "tokens": row[6],
        "elapsed": float(row[7]) if row[7] else None,
        "user": row[8], "created_at": str(row[9]),
    }
