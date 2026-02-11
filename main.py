import os
import feedparser
import asyncio
import datetime
import discord

# ====== 環境変数 ======
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")

# RSS フィード
FEEDS = {
    "IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "BUSINESS": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

# JST 時間取得
def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# Discord Webhook 送信（同期）
def send_webhook(url, category, title, link):
    if not url:
        print("[WARNING] Webhook URL が未設定です")
        return

    display_category = f"{category}トピック"  # IT -> ITトピック, BUSINESS -> BUSINESSトピック
    content = f"{display_category}: {title}\n{link}"

    try:
        webhook = discord.SyncWebhook.from_url(url)
        webhook.send(content)
        print("[OK] Discord 投稿:", content[:100])
    except Exception as e:
        print("[ERROR] Discord 投稿失敗:", e)

# ニュース取得と投稿（テスト・デバッグ用）
async def fetch_and_post():
    for category, feed_url in FEEDS.items():
        print(f"--- {category} RSS 取得開始 ({feed_url}) ---")
        feed = feedparser.parse(feed_url)

        print(f"[{category}] entries count:", len(feed.entries))
        if not feed.entries:
            print(f"[{category}] ニュースが取得できません")
            send_webhook(WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS,
                         category, "ニュースが取得できません（entries 0）", "")
            continue

        # 先頭1件だけ投稿（テスト）
        entry = feed.entries[0]
        title = entry.title
        link = entry.link

        send_webhook(WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS,
                     category, title, link)

# メイン関数
async def main():
    print("🔍 ニュースBot 起動")
    await fetch_and_post()
    print("🔍 投稿完了")

if __name__ == "__main__":
    asyncio.run(main())
