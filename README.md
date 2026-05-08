# 🤖 具身智能周报 Embodied AI Weekly

> 每周自动抓取 arXiv 最新论文、国内外公司动态、行业新闻，由 Claude AI 生成中文摘要报告。

---

## 📋 项目说明

| 项目 | 说明 |
|------|------|
| ⏰ 更新频率 | 每周一 09:00（北京时间） |
| 🔬 论文来源 | arXiv cs.RO / cs.AI |
| 🏢 追踪公司 | Figure、Physical Intelligence、DeepMind、宇树、智元、傅利叶、优必选 |
| 📰 新闻来源 | 机器之心、量子位、IEEE Spectrum、The Robot Report |
| 🤖 AI 引擎 | Claude (Anthropic) |

---

## 🚀 部署指南

### 第一步：Fork 或 Clone 本仓库

```bash
git clone https://github.com/your-username/embodied-ai-weekly.git
cd embodied-ai-weekly
```

### 第二步：配置 GitHub Secrets

进入仓库 `Settings → Secrets and variables → Actions`，添加以下 Secret：

| Secret 名称 | 说明 | 是否必填 |
|-------------|------|---------|
| `ANTHROPIC_API_KEY` | Claude API 密钥，从 [console.anthropic.com](https://console.anthropic.com) 获取 | ✅ 必填 |
| `EMAIL_SENDER` | 发件人 Gmail 地址 | 可选 |
| `EMAIL_PASSWORD` | Gmail 应用专用密码（不是登录密码） | 可选 |
| `EMAIL_RECEIVER` | 收件人邮箱，多个用逗号分隔 | 可选 |
| `FEISHU_WEBHOOK` | 飞书群机器人 Webhook URL | 可选 |

### 第三步：手动触发测试

进入 `Actions → 生成具身智能周报 → Run workflow`，点击运行，验证配置是否正确。

---

## 📧 邮件配置说明（Gmail）

1. 开启 Gmail **两步验证**
2. 前往 [Google 账号安全](https://myaccount.google.com/security) → 应用专用密码
3. 生成一个新的应用专用密码，填入 `EMAIL_PASSWORD`

---

## 🔔 飞书机器人配置

1. 在飞书群中添加「自定义机器人」
2. 复制 Webhook URL，填入 `FEISHU_WEBHOOK`
3. 安全设置可选择「自定义关键词」，添加关键词：`具身智能`

---

## 📂 历史报告

所有报告存储在 [`reports/`](./reports/) 目录，按日期命名。

---

*Powered by [Claude AI](https://www.anthropic.com) · Auto-generated weekly*
