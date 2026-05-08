#!/usr/bin/env python3
"""
具身智能周报生成器
每周自动抓取 arXiv 论文、公司动态、行业新闻，并用 Claude API 生成中文总结报告
"""

import os
import json
import datetime
import feedparser
import requests
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ─────────────────────────────────────────────
# 1. 数据源配置
# ─────────────────────────────────────────────

ARXIV_QUERY = (
    "cat:cs.RO+OR+cat:cs.AI"
    "+AND+(embodied+OR+humanoid+OR+robot+learning+OR+manipulation+OR+locomotion)"
)
ARXIV_MAX = 20

COMPANY_RSS = {
    # 国际公司
    "Physical Intelligence": "https://www.physicalintelligence.company/blog/rss.xml",
    "Figure AI":             "https://www.figure.ai/news/rss.xml",
    "Boston Dynamics":       "https://bostondynamics.com/blog/feed/",
    "DeepMind Robotics":     "https://deepmind.google/blog/rss.xml",
    # 国内公司
    "宇树科技 Unitree":       "https://www.unitree.com/news/rss.xml",
    "智元机器人":              "https://www.zhiyuan-robot.com/news/rss.xml",
    "傅利叶智能":              "https://www.fftai.com/news/rss.xml",
    "优必选":                  "https://www.ubtech.com/cn/news/rss.xml",
}

NEWS_RSS = {
    "机器之心":  "https://www.jiqizhixin.com/rss",
    "量子位":    "https://www.qbitai.com/feed",
    "The Robot Report": "https://www.therobotreport.com/feed/",
    "IEEE Spectrum Robotics": "https://spectrum.ieee.org/feeds/topic/robotics.rss",
}

KEYWORDS = [
    "具身智能", "humanoid", "embodied", "robot", "manipulation",
    "locomotion", "VLA", "loco-manipulation", "dexterous", "foundation model robot",
    "人形机器人", "灵巧手", "强化学习机器人"
]


# ─────────────────────────────────────────────
# 2. 数据抓取
# ─────────────────────────────────────────────

def fetch_arxiv(days: int = 7) -> list[dict]:
    """抓取最近 N 天的 arXiv 论文"""
    url = (
        f"https://export.arxiv.org/api/query"
        f"?search_query={ARXIV_QUERY}"
        f"&sortBy=submittedDate&sortOrder=descending"
        f"&max_results={ARXIV_MAX}"
    )
    import xml.etree.ElementTree as ET
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(resp.text)
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)

    papers = []
    for entry in root.findall("atom:entry", ns):
        published_str = entry.find("atom:published", ns).text
        published = datetime.datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        if published < cutoff:
            continue
        papers.append({
            "title":    entry.find("atom:title", ns).text.strip().replace("\n", " "),
            "abstract": entry.find("atom:summary", ns).text.strip()[:500],
            "authors":  ", ".join(
                a.find("atom:name", ns).text
                for a in entry.findall("atom:author", ns)[:3]
            ),
            "url":      entry.find("atom:id", ns).text.strip(),
            "date":     published.strftime("%Y-%m-%d"),
        })
    print(f"[arXiv] 抓取到 {len(papers)} 篇论文")
    return papers


def fetch_rss(sources: dict, days: int = 7) -> list[dict]:
    """抓取 RSS 源，过滤关键词相关条目"""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    items = []
    for source_name, url in sources.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:30]:
                # 时间过滤
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime.datetime(*entry.published_parsed[:6],
                                                  tzinfo=datetime.timezone.utc)
                if published and published < cutoff:
                    continue

                # 关键词过滤
                text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
                if not any(kw.lower() in text for kw in KEYWORDS):
                    continue

                items.append({
                    "source":  source_name,
                    "title":   entry.get("title", "").strip(),
                    "summary": entry.get("summary", "")[:400].strip(),
                    "url":     entry.get("link", ""),
                    "date":    published.strftime("%Y-%m-%d") if published else "unknown",
                })
        except Exception as e:
            print(f"[RSS] {source_name} 抓取失败: {e}")

    print(f"[RSS] 共抓取到 {len(items)} 条相关动态")
    return items


# ─────────────────────────────────────────────
# 3. Claude API 生成报告
# ─────────────────────────────────────────────

def build_prompt(papers: list, company_news: list, industry_news: list) -> str:
    week_str = datetime.datetime.now().strftime("%Y年第%W周")

    papers_text = "\n".join(
        f"- [{p['date']}] {p['title']} ({p['authors']})\n  摘要: {p['abstract']}\n  链接: {p['url']}"
        for p in papers
    ) or "本周暂无相关论文"

    company_text = "\n".join(
        f"- [{item['date']}][{item['source']}] {item['title']}\n  {item['summary']}\n  链接: {item['url']}"
        for item in company_news
    ) or "本周暂无相关公司动态"

    news_text = "\n".join(
        f"- [{item['date']}][{item['source']}] {item['title']}\n  {item['summary']}\n  链接: {item['url']}"
        for item in industry_news
    ) or "本周暂无相关行业新闻"

    return f"""你是具身智能领域的资深研究分析师。请根据以下原始数据，生成一份专业、有洞察力的中文周报。

# 原始数据

## arXiv 论文（{len(papers)} 篇）
{papers_text}

## 公司动态
{company_text}

## 行业新闻
{news_text}

# 输出要求

请生成 Markdown 格式的周报，结构如下：

---
# 具身智能周报 · {week_str}

## 🔬 本周研究亮点
（挑选 3-5 篇最重要的论文，每篇给出：研究问题、方法创新点、实验结果、为什么重要，附原文链接）

## 🏢 公司与产品动态
### 国际前沿
（Figure、Physical Intelligence、DeepMind 等的重要进展）

### 国内生态
（宇树、智元、傅利叶等国内玩家的动态）

## 📰 行业资讯速览
（3-5条值得关注的行业新闻，一句话点评）

## 💡 本周洞察
（200字以内，你对本周整体趋势的判断和预测）

## 📎 完整资料索引
（所有来源的标题+链接，按分类列出）
---

写作要求：
- 语言简洁专业，避免堆砌信息
- 对技术内容给出你自己的判断，不只是复述
- 如果某类数据本周较少，可以适当缩写该章节
- 链接请保留原始 URL
"""


def generate_report_with_claude(papers: list, company_news: list, industry_news: list) -> str:
    prompt = build_prompt(papers, company_news, industry_news)
    print("[Claude] 正在生成报告...")
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


# ─────────────────────────────────────────────
# 4. 保存报告 & 更新 README
# ─────────────────────────────────────────────

def save_report(report: str) -> str:
    """保存周报到 reports/ 目录，并返回文件路径"""
    os.makedirs("reports", exist_ok=True)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    filepath = f"reports/{date_str}.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[Save] 报告已保存至 {filepath}")
    return filepath


def update_readme(report: str, report_path: str):
    """更新 README.md，在顶部插入最新一期报告"""
    week_str = datetime.datetime.now().strftime("%Y年第%W周")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    header = f"""# 🤖 具身智能周报 Embodied AI Weekly

> 每周自动抓取 arXiv、公司博客、行业媒体，由 Claude AI 生成摘要报告。
> 
> 📅 最新一期：**{week_str}**（{date_str}）｜[查看所有历史报告](./reports/)

---

"""
    archive_link = f"\n\n---\n\n> 📂 [查看历史报告归档](./reports/{report_path.split('/')[-1]})\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(header + report + archive_link)
    print("[README] README.md 已更新")


# ─────────────────────────────────────────────
# 5. 主流程
# ─────────────────────────────────────────────

def main():
    print("=" * 50)
    print("具身智能周报生成器启动")
    print("=" * 50)

    # 抓取数据
    papers       = fetch_arxiv(days=7)
    company_news = fetch_rss(COMPANY_RSS, days=7)
    industry_news = fetch_rss(NEWS_RSS, days=7)

    # 生成报告
    report = generate_report_with_claude(papers, company_news, industry_news)

    # 保存
    report_path = save_report(report)
    update_readme(report, report_path)

    # 输出供 GitHub Actions 使用
    print("\n[Done] 报告生成完成！")
    print(f"REPORT_PATH={report_path}")


if __name__ == "__main__":
    main()
