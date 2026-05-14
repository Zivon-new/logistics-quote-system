# backend/app/services/ctils_scraper.py
"""
贸法通(ctils.com) 航运/贸易预警爬虫
- 抓取 https://www.ctils.com/categories/7/articles 最新公告
- 下载 PDF → pdfplumber 解析正文
- 按条目、按国家拆分写入 route_warnings 表，按标题去重
"""
import re
import json
import logging
import io
from datetime import date, datetime
from typing import Optional

import httpx
import pdfplumber
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

LIST_URL = "https://www.ctils.com/categories/7/articles"
PDF_BASE = "https://www.ctils.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ── 中文国家/地区名 → ISO-3166-1 alpha-2 ─────────────────────────
COUNTRY_MAP = {
    "也门": "YE", "红海": "YE", "亚丁湾": "YE",
    "伊拉克": "IQ", "伊朗": "IR", "叙利亚": "SY",
    "利比亚": "LY", "苏丹": "SD", "南苏丹": "SS",
    "索马里": "SO", "吉布提": "DJ", "厄立特里亚": "ER",
    "乌克兰": "UA", "俄罗斯": "RU", "白俄罗斯": "BY",
    "以色列": "IL", "巴勒斯坦": "PS", "黎巴嫩": "LB",
    "土耳其": "TR", "埃及": "EG", "沙特": "SA", "沙特阿拉伯": "SA",
    "阿联酋": "AE", "迪拜": "AE", "卡塔尔": "QA",
    "科威特": "KW", "阿曼": "OM", "巴林": "BH",
    "巴基斯坦": "PK", "印度": "IN", "斯里兰卡": "LK",
    "孟加拉": "BD", "缅甸": "MM", "马来西亚": "MY",
    "印尼": "ID", "印度尼西亚": "ID",
    "越南": "VN", "菲律宾": "PH",
    "泰国": "TH", "柬埔寨": "KH", "老挝": "LA",
    "尼日利亚": "NG", "肯尼亚": "KE", "埃塞俄比亚": "ET",
    "坦桑尼亚": "TZ", "莫桑比克": "MZ", "南非": "ZA",
    "马里": "ML", "尼日尔": "NE", "布基纳法索": "BF",
    "刚果": "CD", "喀麦隆": "CM", "加纳": "GH",
    "墨西哥": "MX", "巴西": "BR", "阿根廷": "AR",
    "智利": "CL", "秘鲁": "PE", "哥伦比亚": "CO",
    "巴拿马": "PA", "委内瑞拉": "VE", "厄瓜多尔": "EC",
    "美国": "US", "加拿大": "CA",
    "英国": "GB", "伦敦": "GB", "德国": "DE", "法国": "FR",
    "西班牙": "ES", "荷兰": "NL", "比利时": "BE",
    "波兰": "PL", "乌兹别克斯坦": "UZ", "哈萨克斯坦": "KZ",
    "阿塞拜疆": "AZ", "格鲁吉亚": "GE", "亚美尼亚": "AM",
    "日本": "JP", "韩国": "KR", "朝鲜": "KP",
    "台湾": "TW", "香港": "HK", "新加坡": "SG",
    "澳大利亚": "AU", "新西兰": "NZ",
    "欧亚经济联盟": "RU",   # 默认映射到俄罗斯
    "欧盟": "DE",            # 默认映射到德国
}

# 风险等级关键词（收紧，避免泛词误触发）
# 等级3（高）：对贸易/物流有实质性阻断影响
HIGH_KWORDS = ["封锁", "禁运", "禁止进口", "贸易禁令", "战争", "武装冲突",
               "港口封闭", "严重拥堵", "紧急措施", "出口管制升级"]
# 等级2（中）：已生效的贸易限制措施，影响明确
MED_KWORDS = [
    "反倾销税", "反补贴税", "反规避", "制裁", "关税加征",
    "贸易摩擦", "清关延误", "罢工", "港口拥堵", "临时关税"
]

# 各大章节标题（用于文本分段，需要三章都识别才能正确切边界）
# SKIP_SECTIONS 中的章节只用来定位边界，不爬取内容
SECTION_PATTERNS = {
    "贸易政策": re.compile(r'[一１][、.．]\s*对华经贸摩擦'),
    "境外安全": re.compile(r'[二２][、.．]\s*境外安全'),   # 仅用于边界定位，不处理
    "贸易动态": re.compile(r'[三３][、.．]\s*全球经贸'),
}
SKIP_SECTIONS = {"境外安全"}

# 条目分隔符（1、2、3、）
ITEM_SPLIT = re.compile(r'\n\s*(\d+)[、.．]\s*')


def _detect_risk_level(text_: str) -> int:
    for kw in HIGH_KWORDS:
        if kw in text_:
            return 3
    for kw in MED_KWORDS:
        if kw in text_:
            return 2
    return 1


def _detect_risk_type(section: str, text_: str) -> str:
    if section == "贸易政策":
        if any(k in text_ for k in ["罢工", "港口封闭", "港口拥堵"]):
            return "港口拥堵"
        return "贸易政策"
    return "贸易动态"


def _extract_country(text_: str) -> tuple[str, str, str]:
    """从文本提取最匹配的国家，返回 (code, name, keyword)"""
    for name, code in COUNTRY_MAP.items():
        if name in text_:
            return code, name, name
    return "XX", "综合预警", text_[:20]


def _fetch_article_list(page: int = 1) -> list[dict]:
    """获取文章列表，返回 [{id, title, createDate, linkFormatUrl}, ...]"""
    url = f"{LIST_URL}?pageNum={page}"
    with httpx.Client(headers=HEADERS, timeout=20, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        html = resp.text

    m = re.search(r'var\s+newsPage\s*=\s*(\{.*?\})\s*;', html, re.DOTALL)
    if not m:
        logger.warning("ctils: 未找到 newsPage JSON (page=%d)", page)
        return []

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        logger.error("ctils: JSON解析失败: %s", e)
        return []

    return data.get("content", [])


def _download_pdf(pdf_path: str) -> Optional[bytes]:
    """下载 PDF，返回字节流；失败返回 None"""
    url = PDF_BASE + pdf_path if pdf_path.startswith("/") else pdf_path
    try:
        with httpx.Client(headers=HEADERS, timeout=60, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.content
    except Exception as e:
        logger.error("ctils: 下载PDF失败 %s: %s", url, e)
        return None


def _parse_pdf(pdf_bytes: bytes) -> str:
    """用 pdfplumber 提取 PDF 文本，最多前 10 页"""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            parts = []
            for page in pdf.pages[:10]:
                t = page.extract_text()
                if t:
                    parts.append(t)
            return "\n".join(parts)
    except Exception as e:
        logger.error("ctils: PDF解析失败: %s", e)
        return ""


def _split_sections(full_text: str) -> dict[str, str]:
    """
    把全文按章节拆分为 {section_name: text}。
    PDF 中每个章节标题出现两次（目录页 + 正文页），取最后一次出现的位置
    以确保切到正文内容而不是目录行。
    """
    positions = []
    for sname, pattern in SECTION_PATTERNS.items():
        # finditer 取所有匹配，用最后一个（正文中的那次）
        matches = list(pattern.finditer(full_text))
        if matches:
            positions.append((matches[-1].start(), sname))
    positions.sort()

    sections = {}
    for i, (start, name) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(full_text)
        sections[name] = full_text[start:end]

    return sections


def _parse_items(section_text: str, section_name: str, bulletin_title: str,
                 eff_date: date) -> list[dict]:
    """
    把某章节文本按条目(1、2、3、)拆分，每条生成一个预警字典
    """
    # 按条目编号分割
    parts = ITEM_SPLIT.split(section_text)
    # parts: [before_first_item, item_num, item_text, item_num, item_text, ...]
    items = []
    i = 1
    while i + 1 < len(parts):
        item_text = parts[i + 1].strip()
        if not item_text:
            i += 2
            continue

        # 跳过目录行：特征是第一行末尾有省略号+页码（如 "标题..........1"）
        if re.search(r'[.．]{4,}\s*\d+\s*$', item_text.split('\n')[0]):
            i += 2
            continue

        # 提取条目标题（第一行）
        first_line = item_text.split('\n')[0].strip()
        item_title = f"{first_line}"
        full_item_title = f"{bulletin_title} - {item_title}"[:100]

        code, country, keyword = _extract_country(item_text)
        risk_type = _detect_risk_type(section_name, item_text)
        risk_level = _detect_risk_level(item_text)

        items.append({
            "国家代码":    code,
            "国家中文名":  country,
            "目的地关键词": keyword,
            "风险类型":    risk_type,
            "风险等级":    risk_level,
            "预警标题":    full_item_title,
            "预警详情":    item_text[:1000],
            "生效日期":    eff_date,
        })
        i += 2

    return items


def _title_exists(db: Session, title: str) -> bool:
    row = db.execute(
        text("SELECT 1 FROM route_warnings WHERE 预警标题 = :t LIMIT 1"),
        {"t": title}
    ).fetchone()
    return row is not None


def _article_already_scraped(db: Session, bulletin_title: str) -> bool:
    """检查该期公告是否已爬过（主表或归档表中任意一条存在即视为已处理）"""
    prefix = bulletin_title[:40] + "%"
    row = db.execute(
        text("""
            SELECT 1 FROM route_warnings WHERE 预警标题 LIKE :p
            UNION ALL
            SELECT 1 FROM route_warnings_archive WHERE 预警标题 LIKE :p
            LIMIT 1
        """),
        {"p": prefix}
    ).fetchone()
    return row is not None


def run_scrape(db: Session, max_articles: int = 10) -> dict:
    """
    爬取最新公告并写入数据库。
    max_articles: 本次最多处理多少篇新文章
    返回 {新增: n, 跳过: m, 失败: k}
    """
    added = skipped = failed = 0

    articles = _fetch_article_list(page=1)
    if not articles:
        return {"新增": 0, "跳过": 0, "失败": 0, "错误": "获取文章列表失败"}

    processed_articles = 0
    for art in articles:
        if processed_articles >= max_articles:
            break

        title = (art.get("title") or "").strip()
        pdf_url = art.get("linkFormatUrl") or ""
        date_str = art.get("createDate") or ""

        if not title:
            skipped += 1
            continue

        # 跳过已存在的文章（检查该期公告是否已爬过）
        if _article_already_scraped(db, title):
            skipped += 1
            continue

        processed_articles += 1

        # 解析日期
        try:
            eff_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        except Exception:
            eff_date = date.today()

        # 下载并解析 PDF
        if not pdf_url:
            skipped += 1
            continue

        pdf_bytes = _download_pdf(pdf_url)
        if not pdf_bytes:
            failed += 1
            continue

        full_text = _parse_pdf(pdf_bytes)
        if not full_text:
            failed += 1
            continue

        # 按章节拆分，逐条解析
        sections = _split_sections(full_text)
        if not sections:
            # 无法识别章节，作为整体存一条
            code, country, keyword = _extract_country(full_text[:500])
            sections_items = [{
                "国家代码":    code,
                "国家中文名":  country,
                "目的地关键词": keyword,
                "风险类型":    "贸易政策",
                "风险等级":    _detect_risk_level(full_text[:500]),
                "预警标题":    title[:100],
                "预警详情":    full_text[:1000],
                "生效日期":    eff_date,
            }]
        else:
            sections_items = []
            for sname, stext in sections.items():
                if sname in SKIP_SECTIONS:
                    continue
                sections_items.extend(_parse_items(stext, sname, title, eff_date))

        # 写入数据库
        for item in sections_items:
            if _title_exists(db, item["预警标题"]):
                skipped += 1
                continue
            try:
                db.execute(text("""
                    INSERT INTO route_warnings
                        (国家代码, 国家中文名, 目的地关键词, 风险类型, 风险等级,
                         预警标题, 预警详情, 生效日期, 是否有效, 来源)
                    VALUES
                        (:code, :country, :keyword, :rtype, :rlevel,
                         :title, :detail, :eff_date, 1, 'ctils')
                """), {
                    "code":     item["国家代码"],
                    "country":  item["国家中文名"],
                    "keyword":  item["目的地关键词"],
                    "rtype":    item["风险类型"],
                    "rlevel":   item["风险等级"],
                    "title":    item["预警标题"],
                    "detail":   item["预警详情"],
                    "eff_date": item["生效日期"],
                })
                db.commit()
                added += 1
            except Exception as e:
                db.rollback()
                logger.error("ctils: 写入失败 %s: %s", item["预警标题"][:30], e)
                failed += 1

    # ── 自动归档：把30天前的记录移入 route_warnings_archive ──────────
    archived = _auto_archive(db)

    return {"新增": added, "跳过": skipped, "失败": failed, "归档": archived}


def _auto_archive(db: Session) -> int:
    """
    把生效日期超过30天的活跃记录移入归档表，返回归档条数。
    """
    try:
        # 先复制到归档表（忽略已存在的重复标题）
        db.execute(text("""
            INSERT IGNORE INTO route_warnings_archive
                (预警ID, 国家代码, 国家中文名, 目的地关键词, 风险类型, 风险等级,
                 预警标题, 预警详情, 生效日期, 是否有效, 来源, 创建时间, archived_at)
            SELECT
                预警ID, 国家代码, 国家中文名, 目的地关键词, 风险类型, 风险等级,
                预警标题, 预警详情, 生效日期, 是否有效, 来源, 创建时间, NOW()
            FROM route_warnings
            WHERE 生效日期 < DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """))
        # 再从主表删除
        result = db.execute(text("""
            DELETE FROM route_warnings
            WHERE 生效日期 < DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """))
        db.commit()
        count = result.rowcount
        if count:
            logger.info("ctils: 自动归档 %d 条预警", count)
        return count
    except Exception as e:
        db.rollback()
        logger.error("ctils: 归档失败: %s", e)
        return 0
