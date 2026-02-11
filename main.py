import os
import feedparser
import asyncio
import datetime
import discord
import random

# ====== 環境変数 ======
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
WEBHOOK_IT_SUMMARY = os.getenv("WEBHOOK_IT_SUMMARY")
WEBHOOK_BUSINESS_SUMMARY = os.getenv("WEBHOOK_BUSINESS_SUMMARY")
WEBHOOK_DAILY_REVIEW = os.getenv("WEBHOOK_DAILY_REVIEW")

# RSS フィード
FEEDS = {
    "IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "BUSINESS": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

# JST 時間取得
def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# Discord Webhook 送信
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

# ニュース投稿
def post_news(category, entry):
    url = WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS
    send_webhook(url, f"{category}トピック: {entry.title}\n{entry.link}")

# 要約投稿（失敗でも投稿）
def post_summary(category, entry, summary_text):
    url = WEBHOOK_IT_SUMMARY if category == "IT" else WEBHOOK_BUSINESS_SUMMARY
    send_webhook(url, f"{category}要約: {summary_text}\n{entry.title}\n{entry.link}")

# ダミー要約生成
def generate_summary(entry):
    # 実際はOpenAI APIなどを呼ぶ
    try:
        # ここで要約生成
        # raise Exception("dummy failure")  # テスト用失敗
        return "【要約生成失敗】"  # 現状は失敗扱い
    except:
        return "【要約生成失敗】"

# 1日の振り返り投稿
def post_daily_review(daily_news):
    now = now_jst().strftime("%Y-%m-%d")
    content = f"📝 1日の振り返り ({now})\n"
    for category, entries in daily_news.items():
        content += f"--- {category} ---\n"
        for entry in entries:
            content += f"- {entry.title}\n{entry.link}\n"
    send_webhook(WEBHOOK_DAILY_REVIEW, content)

async def main_loop():
    daily_news = {"IT": [], "BUSINESS": []}

    print("🔍 ニュースBot起動")
    while True:
        now = now_jst()
        if 6 <= now.hour < 22:
            for category, feed_url in FEEDS.items():
                print(f"--- {category} RSS 取得開始 ({feed_url}) ---")
                feed = feedparser.parse(feed_url)
                if not feed.entries:
                    print(f"[{category}] ニュース取得失敗")
                    continue
                for entry in feed.entries:
                    # ニュース投稿
                    post_news(category, entry)
                    daily_news[category].append(entry)

                    # 要約投稿（失敗でも要約チャンネルに送信）
                    summary = generate_summary(entry)
                    # ランダム遅延で投稿（10〜30分）
                    await asyncio.sleep(random.randint(10*60, 30*60))
                    post_summary(category, entry, summary)
        else:
            print(f"🔍 {now.hour}時なので配信停止中")

        # 日次振り返りは22時以降に1回だけ送信
        if now.hour >= 23:
            if any(daily_news.values()):  # 1日分ニュースがある場合のみ
                post_daily_review(daily_news)
                print("🔍 1日の振り返り投稿完了")
                daily_news = {"IT": [], "BUSINESS": []}  # リセット
            await asyncio.sleep(60*60)  # 1時間スリープ
        else:
            await asyncio.sleep(10*60)  # 10分スリープ

if __name__ == "__main__":
    asyncio.run(main_loop())
