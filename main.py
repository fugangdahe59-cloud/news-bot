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

openai = OpenAI(api_key=OPENAI_API_KEY)

posted_news = set()
daily_news = []

FEEDS = {
    "IT": "https://www.itmedia.co.jp/rss/news.xml",
    "BUSINESS": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

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
〜〜〜"""
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    ))
    return response.choices[0].message.content

# Webhook送信（同期）
async def send_webhook(url, content):
    webhook = discord.SyncWebhook.from_url(url)
    webhook.send(content)

async def fetch_and_post():
    global daily_news
    for category, feed_url in FEEDS.items():
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            print(f"[{category}] ニュースが取得できません")
            continue

        for entry in feed.entries:
            news_id = entry.id if 'id' in entry else entry.link
            if news_id in posted_news:
                continue
            posted_news.add(news_id)

            title = entry.title
            link = entry.link

            target_webhook = WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS
            await send_webhook(target_webhook, f"[{category}] 投稿: {title} ({link})")

            # 待機と要約
            await asyncio.sleep(random.randint(600, 1800))
            try:
                summary = await generate_summary(title, link)
                summary_webhook = SUMMARY_IT if category == "IT" else SUMMARY_BUSINESS
                await send_webhook(summary_webhook, summary)
            except Exception as e:
                print(f"[{category}] 要約生成失敗: {e}")

            daily_news.append((category, title, link))

async def initial_post():
    # 起動後すぐに投稿
    await fetch_and_post()

async def main_loop():
    print("ニュースBot起動")
    await initial_post()
    while True:
        now = now_jst()

        # 22時の振り返り
        if now.hour == 22 and now.minute == 0:
            if daily_news:
                content = f"【今日の振り返り】{now.year}年{now.month}月{now.day}日\n\n"
                content += "\n".join([f"[{c}] {t} ({l})" for c, t, l in daily_news])
                await send_webhook(SUMMARY_DAILY, content)
                daily_news.clear()
            await asyncio.sleep(60)

        # 6時〜22時のニュース取得
        if 6 <= now.hour < 22:
            await fetch_and_post()

        await asyncio.sleep(60)  # 1分ごとにループ

if __name__ == "__main__":
    asyncio.run(main_loop())
