import os
import discord
import feedparser
import asyncio
import datetime
import random
from openai import OpenAI

# ====== 環境変数 ======
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
SUMMARY_IT = os.getenv("SUMMARY_IT")
SUMMARY_BUSINESS = os.getenv("SUMMARY_BUSINESS")
SUMMARY_DAILY = os.getenv("SUMMARY_DAILY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = discord.Client(intents=discord.Intents.default())
openai = OpenAI(api_key=OPENAI_API_KEY)

# ニュースID保存（重複投稿防止）
posted_news = set()
daily_news = []

# ニュースRSSリスト
FEEDS = {
    "IT": "https://example.com/it_rss.xml",
    "BUSINESS": "https://example.com/business_rss.xml"
}

# JST現在時刻取得
def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# AIで要約＋解説生成
async def generate_summary(title, link):
    prompt = f"""
ニュースタイトル: {title}
URL: {link}

以下のテンプレでニュースをまとめてください。人間っぽく、具体的に。
【ニュース要約】
〜〜〜

【影響】
〜〜〜

【チャンス】
〜〜〜

【ひとこと解説】
〜〜〜
"""
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

# Webhook送信
async def send_webhook(url, content):
    webhook = discord.Webhook.from_url(url, adapter=discord.AsyncWebhookAdapter(client.http.session))
    await webhook.send(content)

# ニュース取得・投稿
async def fetch_and_post():
    global daily_news
    for category, feed_url in FEEDS.items():
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            news_id = entry.id if 'id' in entry else entry.link
            if news_id in posted_news:
                continue
            posted_news.add(news_id)

            title = entry.title
            link = entry.link
            # 元ニュース投稿
            if category == "IT":
                await send_webhook(WEBHOOK_IT, f"[{category}] 投稿: {title} ({link})")
            else:
                await send_webhook(WEBHOOK_BUSINESS, f"[{category}] 投稿: {title} ({link})")

            # 要約投稿（10~30分ランダム）
            await asyncio.sleep(random.randint(600, 1800))
            summary = await generate_summary(title, link)
            if category == "IT":
                await send_webhook(SUMMARY_IT, summary)
            else:
                await send_webhook(SUMMARY_BUSINESS, summary)

            # 22時振り返り用保存
            daily_news.append((category, title, link))

# 22時の振り返り投稿
async def daily_summary():
    while True:
        now = now_jst()
        if now.hour == 22 and now.minute == 0:
            content = f"【今日の振り返り】{now.year}年{now.month}月{now.day}日\n\n"
            for category, title, link in daily_news:
                content += f"[{category}] {title} ({link})\n"
            await send_webhook(SUMMARY_DAILY, content)
            daily_news = []
            await asyncio.sleep(60)  # 1分待機して次回をスキップ
        else:
            await asyncio.sleep(30)

# メインループ
@client.event
async def on_ready():
    print("ニュースBot起動")
    while True:
        now = now_jst()
        # 6時〜22時のみニュース取得
        if 6 <= now.hour < 22:
            await fetch_and_post()
        await asyncio.sleep(3600)  # 1時間ごとにチェック

# 22時振り返りタスク起動
client.loop.create_task(daily_summary())
client.run("dummy")  # 通常はTOKEN不要、Webhookのみで送信

