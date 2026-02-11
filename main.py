import os
import feedparser
import asyncio
import datetime
import random
import aiohttp
from discord import Webhook, AsyncWebhookAdapter
from openai import OpenAI

WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
SUMMARY_IT = os.getenv("SUMMARY_IT")
SUMMARY_BUSINESS = os.getenv("SUMMARY_BUSINESS")
SUMMARY_DAILY = os.getenv("SUMMARY_DAILY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai = OpenAI(api_key=OPENAI_API_KEY)

posted_news = set()
daily_news = []

FEEDS = {
    "IT": "https://example.com/it_rss.xml",
    "BUSINESS": "https://example.com/business_rss.xml"
}

def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

async def generate_summary(title, link):
    prompt = f"ニュースタイトル: {title}\nURL: {link}\n\n以下のテンプレでニュースをまとめてください。人間っぽく、具体的に。\n【ニュース要約】\n〜〜〜\n\n【影響】\n〜〜〜\n\n【チャンス】\n〜〜〜\n\n【ひとこと解説】\n〜〜〜"
    response = await openai.chat.completions.acreate(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

async def send_webhook(url, content):
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(url, adapter=AsyncWebhookAdapter(session))
        await webhook.send(content)

async def fetch_and_post():
    global daily_news
    for category, feed_url in FEEDS.items():
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            news_id = getattr(entry, 'id', entry.link)
            if news_id in posted_news:
                continue
            posted_news.add(news_id)

            title, link = entry.title, entry.link
            target_webhook = WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS
            await send_webhook(target_webhook, f"[{category}] 投稿: {title} ({link})")

            await asyncio.sleep(random.randint(600, 1800))  # 10~30分ランダム
            summary = await generate_summary(title, link)
            summary_webhook = SUMMARY_IT if category == "IT" else SUMMARY_BUSINESS
            await send_webhook(summary_webhook, summary)

            daily_news.append((category, title, link))

async def daily_summary_task():
    while True:
        now = now_jst()
        # 22:00〜22:05の間でまとめ投稿
        if now.hour == 22 and 0 <= now.minute < 5 and daily_news:
            content = f"【今日の振り返り】{now.year}年{now.month}月{now.day}日\n\n"
            content += "\n".join([f"[{c}] {t} ({l})" for c, t, l in daily_news])
            await send_webhook(SUMMARY_DAILY, content)
            daily_news.clear()
            await asyncio.sleep(300)  # 5分待機して再投稿防止
        else:
            await asyncio.sleep(30)

async def main_loop():
    print("ニュースBot起動")
    asyncio.create_task(daily_summary_task())
    while True:
        now = now_jst()
        if 6 <= now.hour < 22:
            await fetch_and_post()
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main_loop())
