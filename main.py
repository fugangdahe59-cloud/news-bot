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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # 任意で要約を使う場合

openai = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

posted_news = set()
daily_news = []

# Yahoo!RSS
FEEDS = {
    "IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "BUSINESS": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# ====== 要約生成 ======
async def generate_summary(title, link):
    if not openai:
        return f"{title}\n{link}"  # APIキーなしなら簡易出力
    prompt = f"ニュースタイトル: {title}\nURL: {link}\n\n以下のテンプレでまとめてください。\n【ニュース要約】\n〜〜〜\n\n【影響】\n〜〜〜\n\n【チャンス】\n〜〜〜\n\n【ひとこと解説】\n〜〜〜"
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    ))
    return response.choices[0].message.content

# ====== Webhook送信 ======
async def send_webhook(url, content):
    webhook = discord.SyncWebhook.from_url(url)
    webhook.send(content)

# ====== ニュース取得と投稿 ======
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

            # まず投稿
            target_webhook = WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS
            await send_webhook(target_webhook, f"[{category}] 投稿: {title} ({link})")

            # 10〜30分ランダム待機して要約投稿
            await asyncio.sleep(random.randint(600, 1800))
            summary = await generate_summary(title, link)
            summary_webhook = SUMMARY_IT if category == "IT" else SUMMARY_BUSINESS
            await send_webhook(summary_webhook, summary)

            # 1日の振り返り用に保存
            daily_news.append((category, title, link))

# ====== 22時に1日まとめ投稿 ======
async def daily_summary():
    global daily_news
    if not daily_news:
        return
    now = now_jst()
    content = f"【今日の振り返り】{now.year}年{now.month}月{now.day}日\n\n"
    for c, t, l in daily_news:
        content += f"[{c}] {t} ({l})\n"
    await send_webhook(SUMMARY_DAILY, content)
    daily_news.clear()

# ====== メインループ ======
async def main_loop():
    print("ニュースBot起動")
    # 起動後すぐに初回投稿
    await fetch_and_post()

    while True:
        now = now_jst()

        # 22時ちょうどなら1日まとめ投稿
        if now.hour == 22 and now.minute == 0:
            await daily_summary()
            await asyncio.sleep(60)  # 1分待機

        # 6時〜22時にニュース取得
        if 6 <= now.hour < 22:
            await fetch_and_post()

        await asyncio.sleep(60)  # 1分ごとにループ

if __name__ == "__main__":
    asyncio.run(main_loop())
