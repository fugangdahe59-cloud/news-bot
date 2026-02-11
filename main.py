import os
import feedparser
import asyncio
import datetime
import discord

# ====== 環境変数 ======
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")

# RSS URL
FEEDS = {
    "IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "BUSINESS": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

# 投稿済みニュース管理
posted_news = set()

# JST 時間取得
def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# Discord Webhook 送信（同期）
def send_webhook(url, content):
    if not url:
        print("[WARNING] Webhook URL が未設定です")
        return
    try:
        webhook = discord.SyncWebhook.from_url(url)
        webhook.send(content)
        print("[OK] Discord 投稿:", content[:100])
    except Exception as e:
        print("[ERROR] Discord 投稿失敗:", e)

# RSS 取得＆投稿
async def fetch_and_post():
    for category, feed_url in FEEDS.items():
        print(f"--- {category} RSS 取得開始 ({feed_url}) ---")
        feed = feedparser.parse(feed_url)

        # デバッグ情報
        print(f"[{category}] feed.bozo:", getattr(feed, "bozo", None))
        print(f"[{category}] status:", getattr(feed, "status", None))
        print(f"[{category}] entries count:", len(feed.entries))

        if not feed.entries:
            print(f"[{category}] ニュースが取得できません")
            send_webhook(WEBHOOK_IT if category=="IT" else WEBHOOK_BUSINESS,
                         f"[{category}] ニュースが取得できません（entries 0）")
            continue

        # 上位5件チェックして未投稿を送信
        for entry in feed.entries[:5]:
            link = entry.link
            if link in posted_news:
                continue
            posted_news.add(link)
            title = entry.title
            send_webhook(WEBHOOK_IT if category=="IT" else WEBHOOK_BUSINESS,
                         f"[{category}] 投稿テスト: {title}\n{link}")

async def main_loop():
    print("🔍 ニュースBot 起動")
    while True:
        now = now_jst()
        # 6時〜22時だけ動作
        if 6 <= now.hour < 22:
            await fetch_and_post()
        await asyncio.sleep(300)  # 5分ごとにチェック

if __name__ == "__main__":
    asyncio.run(main_loop())
