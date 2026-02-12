import os
import feedparser
import asyncio
import datetime
import discord
import random
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
WEBHOOK_IT_SUMMARY = os.getenv("WEBHOOK_IT_SUMMARY")
WEBHOOK_BUSINESS_SUMMARY = os.getenv("WEBHOOK_BUSINESS_SUMMARY")
WEBHOOK_DAILY_REVIEW = os.getenv("WEBHOOK_DAILY_REVIEW")

FEEDS = {
    "IT": [
        "https://news.yahoo.co.jp/rss/topics/it.xml"
    ],
    "BUSINESS": [
        "https://news.yahoo.co.jp/rss/topics/business.xml",
        "https://news.yahoo.co.jp/rss/topics/economy.xml"
    ]
}

def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def send_webhook(url, content):
    if not url:
        print("[WARNING] Webhook未設定")
        return
    try:
        webhook = discord.SyncWebhook.from_url(url)
        webhook.send(content)
        print("[OK] 投稿:", content[:60])
    except Exception as e:
        print("[ERROR] 投稿失敗:", e)

def post_news(category, entry):
    url = WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS
    send_webhook(url, f"{category}トピック: {entry.title}\n{entry.link}")

async def generate_summary(entry):
    prompt = f"""
次のニュースを短く要約してください。

タイトル: {entry.title}
URL: {entry.link}

🧠 要約:
👉 ポイント:
"""

    try:
        print("[AI] 要約生成中...")
        response = client.responses.create(
            model="gpt-5-mini",
            input=prompt
        )
        text = response.output_text
        print("[AI] 要約完了")
        return text
    except Exception as e:
        print("[AI ERROR]", e)
        return "🧠 要約\nAI要約失敗\n👉 ポイント\n・再試行予定"

def post_summary(category, text):
    url = WEBHOOK_IT_SUMMARY if category == "IT" else WEBHOOK_BUSINESS_SUMMARY
    send_webhook(url, text)

def post_daily_review(daily_news):
    now = now_jst().strftime("%Y-%m-%d")
    content = f"📝 1日の振り返り ({now})\n"

    for category, entries in daily_news.items():
        content += f"\n--- {category} ---\n"
        for entry in entries:
            content += f"- {entry.title}\n{entry.link}\n"

    send_webhook(WEBHOOK_DAILY_REVIEW, content)

async def fetch_category(category, urls, daily_news):
    for feed_url in urls:
        print(f"🔍 {category} RSS取得: {feed_url}")
        feed = feedparser.parse(feed_url)

        if not feed.entries:
            print(f"[WARNING] {category} RSS空")
            continue

        for entry in feed.entries[:5]:
            post_news(category, entry)
            daily_news[category].append(entry)

            await asyncio.sleep(random.randint(60, 120))

            summary = await generate_summary(entry)
            post_summary(category, summary)

        return

    print(f"[ERROR] {category} RSS取得失敗")

async def main_loop():
    daily_news = {"IT": [], "BUSINESS": []}
    print("🔍 AIニュースBot起動")

    while True:
        now = now_jst()

        if 6 <= now.hour < 22:
            for category, urls in FEEDS.items():
                await fetch_category(category, urls, daily_news)
        else:
            print(f"🔒 {now.hour}時 → 停止中")

        if now.hour >= 22 and any(daily_news.values()):
            post_daily_review(daily_news)
            daily_news = {"IT": [], "BUSINESS": []}
            await asyncio.sleep(3600)
        else:
            await asyncio.sleep(600)

if __name__ == "__main__":
    asyncio.run(main_loop())
