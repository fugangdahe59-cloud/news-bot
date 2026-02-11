import os
import asyncio
import aiohttp
import feedparser
import random
from datetime import datetime, timezone, timedelta
from openai import OpenAI

# ====== 環境変数 ======
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
SUMMARY_IT = os.getenv("SUMMARY_IT")
SUMMARY_BUSINESS = os.getenv("SUMMARY_BUSINESS")
SUMMARY_DAILY = os.getenv("SUMMARY_DAILY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai = OpenAI(api_key=OPENAI_API_KEY)

# ====== 記録用 ======
posted_news = set()
daily_news = []

# ====== RSSフィード ======
FEEDS = {
    "IT": "https://example.com/it_rss.xml",
    "BUSINESS": "https://example.com/business_rss.xml"
}

# JST取得
def now_jst():
    return datetime.now(timezone(timedelta(hours=9)))

# OpenAIでニュース要約生成
async def generate_summary(title, link):
    prompt = f"""ニュースタイトル: {title}
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
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
    )
    return response.choices[0].message.content

# aiohttpでDiscord Webhookに送信
async def send_webhook(url, content):
    async with aiohttp.ClientSession() as session:
        await session.post(url, json={"content": content})

# RSS取得＋ニュース投稿
async def fetch_and_post():
    global daily_news
    for category, feed_url in FEEDS.items():
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            news_id = getattr(entry, 'id', entry.link)
            if news_id in posted_news:
                continue
            posted_news.add(news_id)

            title = entry.title
            link = entry.link

            # 投稿
            target_webhook = WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS
            await send_webhook(target_webhook, f"[{category}] 投稿: {title} ({link})")

            # 待機(10～30分)
            await asyncio.sleep(random.randint(600, 1800))

            # 要約生成
            summary = await generate_summary(title, link)
            summary_webhook = SUMMARY_IT if category == "IT" else SUMMARY_BUSINESS
            await send_webhook(summary_webhook, summary)

            daily_news.append((category, title, link))

# 22時に振り返りまとめ投稿
async def post_daily_summary():
    global daily_news
    if not daily_news:
        return

    now = now_jst()
    content = f"【今日の振り返り】{now.year}年{now.month}月{now.day}日\n\n"
    for c, t, l in daily_news:
        content += f"[{c}] {t} ({l})\n"
    await send_webhook(SUMMARY_DAILY, content)
    daily_news.clear()

# メインループ
async def main_loop():
    print("ニュースBot起動")
    while True:
        now = now_jst()

        # 22時の振り返りチェック
        if now.hour == 22 and now.minute == 0:
            await post_daily_summary()
            # 1分待機して再投稿を防止
            await asyncio.sleep(60)

        # 6時～22時のニュース取得
        if 6 <= now.hour < 22:
            await fetch_and_post()

        await asyncio.sleep(60)  # 1分ごとにループ

if __name__ == "__main__":
    asyncio.run(main_loop())
