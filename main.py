import os
import discord
import feedparser
import asyncio
import datetime
import random
import aiohttp
from openai import AsyncOpenAI

# ====== 環境変数 ======
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
SUMMARY_IT = os.getenv("SUMMARY_IT")
SUMMARY_BUSINESS = os.getenv("SUMMARY_BUSINESS")
SUMMARY_DAILY = os.getenv("SUMMARY_DAILY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 非同期版クライアントの初期化
openai = AsyncOpenAI(api_key=OPENAI_API_KEY)

posted_news = set()
daily_news = []

FEEDS = {
    "IT": "https://news.yahoo.co.jp",
    "BUSINESS": "https://news.yahoo.co.jp"
}

def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# 非同期Webhook送信
async def send_webhook(url, content):
    if not url: return
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(url, session=session)
        await webhook.send(content)

# AI要約＋個別投稿タスク
async def summarize_and_post(category, title, link):
    # 待機（10〜30分）
    wait_time = random.randint(600, 1800)
    await asyncio.sleep(wait_time)
    
    prompt = f"""
ニュースタイトル: {title}
URL: {link}

以下のテンプレでニュースをまとめてください。人間っぽく具体的に。
【ニュース要約】
〜〜〜
【影響】
〜〜〜
【チャンス】
〜〜〜
【ひとこと解説】
〜〜〜
"""
    try:
        response = await openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        summary = response.choices[0].message.content
        
        summary_webhook = SUMMARY_IT if category == "IT" else SUMMARY_BUSINESS
        await send_webhook(summary_webhook, summary)
    except Exception as e:
        print(f"要約生成エラー: {e}")

# ニュース取得・投稿
async def fetch_and_post(is_initial=False):
    global daily_news
    for category, feed_url in FEEDS.items():
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            continue
            
        for entry in feed.entries:
            news_id = entry.id if 'id' in entry else entry.link
            if news_id in posted_news:
                continue
            
            # IDを記録
            posted_news.add(news_id)

            # 初回起動時は「過去のニュース」として扱い、投稿はスキップ
            if is_initial:
                continue

            title = entry.title
            link = entry.link

            # 1. 元ニュースを即時投稿
            target_webhook = WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS
            await send_webhook(target_webhook, f"[{category}] 投稿: {title}\n{link}")

            # 2. 22時振り返り用に追加
            daily_news.append((category, title, link))

            # 3. 要約投稿をバックグラウンドで予約（ループを止めない）
            asyncio.create_task(summarize_and_post(category, title, link))

# メインループ
async def main_loop():
    print(f"[{now_jst()}] ニュースBot起動中...")
    
    # 初回起動：現在のニュースを既読に設定（通知爆発防止）
    await fetch_and_post(is_initial=True)
    print("初回読み込み完了。監視を開始します。")

    while True:
        now = now_jst()
        
        # 22時に振り返り投稿
        if now.hour == 22 and now.minute == 0 and daily_news:
            content = f"【今日の振り返り】{now.year}/{now.month}/{now.day}\n\n"
            content += "\n".join([f"[{c}] {t}\n{l}" for c, t, l in daily_news])
            await send_webhook(SUMMARY_DAILY, content)
            daily_news.clear()
            await asyncio.sleep(60)

        # 6時〜22時の間にニュース取得（15分おきにチェック）
        if 6 <= now.hour < 22:
            await fetch_and_post()
        
        await asyncio.sleep(900)  # 15分待機

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("停止しました")
