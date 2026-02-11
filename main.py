import os
import feedparser
import asyncio
import datetime
import discord

# ====== 環境変数 ======
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")

# 実際に動く可能性の高い RSS
FEEDS = {
    "IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "BUSINESS": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

# JST 時間取得
def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# Discord Webhook 送信（同期で確実）
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

async def debug_fetch_and_post():
    for category, feed_url in FEEDS.items():
        print(f"--- {category} RSS 取得開始 ({feed_url}) ---")
        feed = feedparser.parse(feed_url)

        # デバッグ情報
        print(f"[{category}] feed.bozo:", getattr(feed, "bozo", None))
        print(f"[{category}] status:", getattr(feed, "status", None))
        print(f"[{category}] parse keys:", list(feed.keys()))
        print(f"[{category}] entries count:", len(feed.entries))

        if not feed.entries:
            # 取得失敗 or 空の場合
            print(f"[{category}] ニュースが取得できません")
            send_webhook(WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS,
                         f"[{category}] ニュースが取得できません（entries 0）")
            continue

        # 取得できた場合は先頭1件だけ投稿（テスト）
        entry = feed.entries[0]
        title = entry.title
        link = entry.link
        print(f"[{category}] 1件目タイトル:", title)
        print(f"[{category}] 1件目リンク:", link)

        send_webhook(WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS,
                     f"[{category}] 投稿テスト: {title}\n{link}")

async def main():
    print("🔍 ニュースBot デバッグ起動")
    await debug_fetch_and_post()
    print("🔍 投稿テスト完了")

if __name__ == "__main__":
    asyncio.run(main())
