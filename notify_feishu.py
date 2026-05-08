#!/usr/bin/env python3
"""
飞书群机器人通知
使用飞书自定义 webhook，发送周报摘要 + 跳转链接
"""

import os
import glob
import json
import datetime
import requests
import re


def load_latest_report() -> str:
    files = sorted(glob.glob("reports/*.md"), reverse=True)
    if not files:
        raise FileNotFoundError("未找到任何报告文件")
    with open(files[0], encoding="utf-8") as f:
        return f.read()


def extract_highlights(report_md: str, max_chars: int = 800) -> str:
    """从报告中提取'本周洞察'部分作为飞书消息摘要"""
    # 尝试提取「本周洞察」章节
    match = re.search(r"##\s*💡\s*本周洞察\n+([\s\S]+?)(?=\n##|\Z)", report_md)
    if match:
        return match.group(1).strip()[:max_chars]
    # fallback：取前 max_chars 字符
    return report_md[:max_chars] + "..."


def send_feishu():
    webhook = os.environ.get("FEISHU_WEBHOOK")
    if not webhook:
        print("[飞书] 未配置 FEISHU_WEBHOOK，跳过")
        return

    # GitHub 仓库地址（从环境变量读取，Actions 中自动注入）
    repo = os.environ.get("GITHUB_REPOSITORY", "your-username/embodied-ai-weekly")
    repo_url = f"https://github.com/{repo}"
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    week_str = datetime.datetime.now().strftime("%Y年第%W周")

    report_md = load_latest_report()
    highlight = extract_highlights(report_md)

    # 飞书富文本卡片消息
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"🤖 具身智能周报 · {week_str}"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**📅 日期：** {date_str}\n\n**💡 本周洞察**\n\n{highlight}"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "📖 查看完整报告"},
                            "type": "primary",
                            "url": f"{repo_url}/blob/main/reports/{date_str}.md"
                        },
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "📂 历史报告"},
                            "type": "default",
                            "url": f"{repo_url}/tree/main/reports"
                        }
                    ]
                }
            ]
        }
    }

    resp = requests.post(webhook, json=payload, timeout=15)
    resp.raise_for_status()
    result = resp.json()
    if result.get("code") == 0 or result.get("StatusCode") == 0:
        print("[飞书] 消息发送成功")
    else:
        print(f"[飞书] 发送失败: {result}")


if __name__ == "__main__":
    send_feishu()
