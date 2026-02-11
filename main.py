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
WEBHOOK_DAILY_REVIEW = os.getenv("WEBHOOK_DAILY_REVIEW")  # 1日の振り返り

# ニュースRSS
FEEDS = {
    "IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "BUSINESS": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

# JST時間取得
def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# Discord Webhook送信（同期）
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

# ニュース取得・投稿
async def fetch_and_post():
    daily_news = {"IT": [], "BUSINESS": []}  # 振り返り用

    for category, feed_url in FEEDS.items():
        print(f"--- {category} RSS 取得開始 ({feed_url}) ---")
        feed = feedparser.parse(feed_url)
        print(f"[{category}] entries count:", len(feed.entries))

        for entry in feed.entries:
            title = entry.title
            link = entry.link

            # トピックとしてニュースチャンネルに投稿
            send_webhook(
                WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS,
                f"{category}トピック: {title}\n{link}"
            )

            # 振り返り用に保存
            daily_news[category].append(f"- {title}\n{link}")

            # 要約を解説チャンネルに投稿
            try:
                # ここで要約を生成（省略：OpenAI API呼び出し）
                summary = "【要約生成失敗】"  # APIクォータ切れなどの場合
                send_webhook(
                    WEBHOOK_IT_SUMMARY if category == "IT" else WEBHOOK_BUSINESS_SUMMARY,
                    f"{category}要約: {summary}\n{title}\n{link}"
                )
            except Exception as e:
                print("[ERROR] 要約生成失敗:", e)

    return daily_news

# 1日の振り返り投稿
def post_daily_review(daily_news):
    today_str = now_jst().strftime("%Y-%m-%d")
    content = f"📝 1日の振り返り ({today_str})\n"
    for category in ["IT", "BUSINESS"]:
        content += f"--- {category} ---\n"
        content += "\n".join(daily_news[category]) + "\n"
    send_webhook(WEBHOOK_DAILY_REVIEW, content)

# メインループ
async def main():
    print("🔍 ニュースBot起動")
    daily_news = await fetch_and_post()

    # 22時までの時間制御（例: 22時を超えたら終了）
    now = now_jst()
    end_hour = 22
    if now.hour >= end_hour:
        print("🔍 22時を超えたため配信停止")
        return

    # ここで1日の振り返りは配信後に投稿
    post_daily_review(daily_news)
    print("🔍 投稿完了")

if __name__ == "__main__":
    asyncio.run(main())
