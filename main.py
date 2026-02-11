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
    "IT": "https://example.com/it_rss.xml",
    "BUSINESS": "https://example.com/business_rss.xml"
}

def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# ====== OpenAI要約（クォータ切れ対応） ======
async def generate_summary(title, link):
    prompt = f"ニュースタイトル: {title}\nURL: {link}\n\n以下のテンプレでニュースをまとめてください。人間っぽく具体的に。\n【ニュース要約】\n〜〜〜\n\n【影響】\n〜〜〜\n\n【チャンス】\n〜〜〜\n\n【ひとこと解説】\n〜〜〜"
    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(None, lambda: openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        ))
        return response.choices[0].message.content
    except Exception as e:
        print(f"[OpenAI要約失敗] {e}")
        return "【要約取得失敗】APIクォータ不足かエラー発生"

# ====== Webhook送信 ======
async def send_webhook(url, content):
    # SyncWebhookで簡単に送信
    webhook = discord.SyncWebhook.from_url(url)
    webhook.send(content)

# ====== ニュース取得＆投稿 ======
async def fetch_and_post(initial=False):
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
            target_webhook = WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS

            # 起動直後も必ず投稿
            await send_webhook(target_webhook, f"[{category}] 投稿: {title} ({link})")

            daily_news.append((category, title, link))

            # 初回起動かつ時間内のみ要約を取得
            if 6 <= now_jst().hour < 22 and not initial:
                await asyncio.sleep(random.randint(600, 1800))  # 10~30分待機
                summary = await generate_summary(title, link)
                summary_webhook = SUMMARY_IT if category == "IT" else SUMMARY_BUSINESS
                await send_webhook(summary_webhook, summary)

# ====== 日次振り返り ======
async def daily_summary():
    now = now_jst()
    if daily_news:
        content = f"【今日の振り返り】{now.year}年{now.month}月{now.day}日\n\n"
        for c, t, l in daily_news:
            content += f"[{c}] {t} ({l})\n"
        await send_webhook(SUMMARY_DAILY, content)
        daily_news.clear()

# ====== メインループ ======
async def main_loop():
    print("ニュースBot起動")
    # 起動直後は初期投稿のみ
    await fetch_and_post(initial=True)

    while True:
        now = now_jst()

        # 22時の日次振り返り
        if now.hour == 22 and now.minute == 0:
            await daily_summary()
            await asyncio.sleep(60)  # 1分待機して重複防止

        # 6時〜22時のニュース取得
        if 6 <= now.hour < 22:
            await fetch_and_post()

        await asyncio.sleep(60)  # 1分ごとにループ

if __name__ == "__main__":
    asyncio.run(main_loop())
