import os
import feedparser
import asyncio
import datetime
import discord

# ====== 環境変数 ======
WEBHOOK_IT = os.getenv("WEBHOOK_IT")          # ITニュース用Webhook
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")  # ビジネスニュース用Webhook

# ====== RSS設定 ======
FEEDS = {
    "IT": "https://your_actual_it_rss_url.xml",          # ←ここを実際のRSSに変更
    "BUSINESS": "https://your_actual_business_rss_url.xml"
}

def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# ====== Webhook送信（同期版で簡単にテスト）=====
def send_webhook(url, content):
    webhook = discord.SyncWebhook.from_url(url)
    webhook.send(content)
    print(f"送信済み: {content}")

# ====== 起動直後に最新1件を投稿 =====
async def post_latest_news():
    for category, feed_url in FEEDS.items():
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            print(f"[{category}] ニュースが取得できません")
            continue
        
        latest = feed.entries[0]
        title = latest.title
        link = latest.link
        
        target_webhook = WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS
        send_webhook(target_webhook, f"[{category}] 投稿テスト: {title} ({link})")

async def main():
    print("ニュースBotテスト起動")
    await post_latest_news()
    print("投稿テスト完了")

if __name__ == "__main__":
    asyncio.run(main())
