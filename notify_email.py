#!/usr/bin/env python3
"""
邮件通知：将最新周报发送到指定邮箱
支持 Gmail（需开启两步验证并生成应用专用密码）
"""

import os
import glob
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import markdown  # pip install markdown


def load_latest_report() -> tuple[str, str]:
    """加载最新报告，返回 (markdown文本, 文件名)"""
    files = sorted(glob.glob("reports/*.md"), reverse=True)
    if not files:
        raise FileNotFoundError("未找到任何报告文件")
    with open(files[0], encoding="utf-8") as f:
        return f.read(), files[0]


def md_to_html(md_text: str) -> str:
    """将 Markdown 转为带样式的 HTML"""
    body_html = markdown.markdown(md_text, extensions=["extra", "toc"])
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         max-width: 800px; margin: 40px auto; padding: 0 20px;
         color: #333; line-height: 1.7; }}
  h1   {{ color: #1a1a2e; border-bottom: 3px solid #e94560; padding-bottom: 8px; }}
  h2   {{ color: #16213e; margin-top: 32px; }}
  h3   {{ color: #0f3460; }}
  a    {{ color: #e94560; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 4px; }}
  pre  {{ background: #f4f4f4; padding: 16px; border-radius: 8px; overflow-x: auto; }}
  blockquote {{ border-left: 4px solid #e94560; margin: 0; padding-left: 16px; color: #666; }}
  hr   {{ border: none; border-top: 1px solid #eee; margin: 32px 0; }}
</style>
</head>
<body>
{body_html}
<hr>
<p style="color:#999;font-size:12px;">
  本报告由 <a href="https://github.com">具身智能周报</a> 自动生成 · 
  Powered by Claude AI · {datetime.datetime.now().strftime("%Y-%m-%d")}
</p>
</body>
</html>"""


def send_email():
    sender   = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    receiver = os.environ.get("EMAIL_RECEIVER")

    if not all([sender, password, receiver]):
        print("[Email] 未配置邮件环境变量，跳过")
        return

    report_md, filename = load_latest_report()
    week_str = datetime.datetime.now().strftime("%Y年第%W周")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🤖 具身智能周报 · {week_str}"
    msg["From"]    = sender
    msg["To"]      = receiver

    # 纯文本备用
    msg.attach(MIMEText(report_md, "plain", "utf-8"))
    # HTML 正文
    msg.attach(MIMEText(md_to_html(report_md), "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver.split(","), msg.as_string())
        print(f"[Email] 已成功发送至 {receiver}")
    except Exception as e:
        print(f"[Email] 发送失败: {e}")
        raise


if __name__ == "__main__":
    send_email()
