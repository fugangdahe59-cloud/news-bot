import os
import feedparser
import asyncio
import datetime
import discord
import requests
import openai
from bs4 import BeautifulSoup
import random

# ===== 環境変数 =====
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
WEBHOOK_IT_SUMMARY = os.getenv("WEBHOOK_IT_SUMMARY")
WEBHOOK_BUSINESS_SUMMARY = os.getenv("WEBHOOK_BUSINESS_SUMMARY")
WEBHOOK_DAILY_REVIEW = os.getenv("WEBHOOK_DAILY_REVIEW")
openai.api_key = os.getenv("OPENAI_API_KEY")

# ===== 制限 =====
AI_LIMIT_PER_HOUR = 10
ai_calls_this_hour = 0
last_reset_hour = -1

summary_cache = {}

# RSS
FEEDS = {
    "IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "BUSINESS": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

# JST時間
def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# 起動クールダウン（5〜10分）
STARTUP_DELAY = random.randint(300, 600)

# ===== Webhook送信 =====
def send_webhook(url, content):
    if not url:
        return
    try:
        webhook = discord.SyncWebhook.from_url(url)
        webhook.send(content)
        print("[OK] 投稿:", content[:80])
    except Exception as e:
        print("[ERROR]", e)

# ===== 記事本文取得 =====
def fetch_article_text(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text() for p in paragraphs)
        return text[:4000]
    except:
        return ""

# ===== AI要約 =====
def generate_summary(entry):
    global ai_calls_this_hour, last_reset_hour

    now = now_jst()
    if now.hour != last_reset_hour:
        ai_calls_this_hour = 0
        last_reset_hour = now.hour

    if entry.link in summary_cache:
        return summary_cache[entry.link]

    if ai_calls_this_hour >= AI_LIMIT_PER_HOUR:
        return "要約制限中", ["次の時間に再開", "", ""]

    article = fetch_article_text(entry.link)
    if not article:
        return "本文取得失敗", ["リンク参照", "", ""]

    prompt = f"""
ニュースを短く要約してください。
3行以内＋ポイント3つ。

{article}
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.choices[0].message.content.strip()
        lines = text.split("\n")

        summary = lines[0]
        points = [l.replace("・", "").strip() for l in lines[1:4]]
        while len(points) < 3:
            points.append("")

        result = (summary, points)
        summary_cache[entry.link] = result
        ai_calls_this_hour += 1
        return result

    except Exception as e:
        print("[AI ERROR]", e)
        return "AI要約失敗", ["再試行予定", "", ""]

# ===== 要約テンプレ =====
def format_summary(summary, points, url):
    return (
        "🧠 要約\n\n"
        f"{summary}\n\n"
        "👉 ポイント\n"
        f"・{points[0]}\n"
        f"・{points[1]}\n"
        f"・{points[2]}\n\n"
        f"🔗 {url}"
    )

# ===== ニュース投稿 =====
def pos
