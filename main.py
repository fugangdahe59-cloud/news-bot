import os
import feedparser
import asyncio
import datetime
import discord

# ====== 環境変数 ======
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
WEBHOOK_IT_SUMMARY = os.getenv("WEBHOOK_IT_SUMMARY")
WEBHOOK_BUSINESS_SUMMARY = os.getenv("WEBHOOK_BUSINESS_SUMMARY")
WEBHOOK_DAILY_REVIEW = os.getenv("WEBHOOK_DAILY_REVIEW")

FEEDS = {
    "IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "BUSINESS": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

# JST時間取得
def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# Discord Webhook 送信（同期）
def send_webhook(url, content):
    if not url:
        print("[WARNING] Webhook URL 未設定")
        return
    try:
        webhook = discord.SyncWebhook.from_url(url)
        webhook.send(content)
        print("[OK] Discord 投稿:", content[:100])
    except Exception as e:
        print("[ERROR] Discord 投稿失敗:", e)

# ニュース取得＆投稿
async def fetch_and_post_news():
    daily_news = {"IT": [], "BUSINESS": []}

    for category, feed_url in FEEDS.items():
        print(f"--- {category} RSS 取得開始 ({feed_url}) ---")
        feed = feedparser.parse(feed_url)
        print(f"[{category}] entries count:", len(feed.entries))

        if not feed.entries:
            send_webhook(WEBHOOK_IT if category=="IT" else WEBHOOK_BUSINESS,
                         f"{category}トピック: ニュースが取得できません")
            continue

        for entry in feed.entries:
            title = entry.title
            link = entry.link
            daily_news[category].append(f"{title}\n{link}")
            send_webhook(WEBHOOK_IT if category=="IT" else WEBHOOK_BUSINESS,
                         f"{category}トピック: {title}\n{link}")

    return daily_news

# 要約生成（簡易ダミー）
async def generate_summaries(daily_news):
    for category in ["IT", "BUSINESS"]:
        summary_webhook = WEBHOOK_IT_SUMMARY if category=="IT" else WEBHOOK_BUSINESS_SUMMARY
        for news in daily_news[category]:
            # 本番ではOpenAI APIで要約生成
            try:
                summary_text = "【要約生成失敗】"  # ダミー
                send_webhook(summary_webhook, f"{category}要約: {summary_text}\n{news}")
            except Exception as e:
                print("[ERROR] 要約生成失敗:", e)
                send_webhook(summary_webhook, f"【要約生成失敗】\n{news}")

# 1日の振り返り生成（ブログ風）
def generate_daily_review(daily_news):
    review = f"📝 1日の振り返り ({now_jst().strftime('%Y-%m-%d')})\n\n"
    for category in ["IT", "BUSINESS"]:
        review += f"--- {category} ---\n"
        for news in daily_news[category]:
            review += f"- {news}\n"
        review += "\n"
    return review

async def main():
    print("🔍 ニュースBot起動")

    # 22時を過ぎたら配信停止
    if now_jst().hour >= 23:
        print("🔹 22時以降のため配信停止")
        return

    # ニュース取得＆投稿
    daily_news = await fetch_and_post_news()

    # 要約解説
    await generate_summaries(daily_news)

    # 1日の振り返り
    review_text = generate_daily_review(daily_news)
    send_webhook(WEBHOOK_DAILY_REVIEW, review_text)

    print("🔍 投稿完了")

if __name__ == "__main__":
    asyncio.run(main())
