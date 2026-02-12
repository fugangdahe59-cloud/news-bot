import os
import feedparser
import asyncio
import datetime
import discord
import random

# ===== 環境変数 =====
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
WEBHOOK_IT_SUMMARY = os.getenv("WEBHOOK_IT_SUMMARY")
WEBHOOK_BUSINESS_SUMMARY = os.getenv("WEBHOOK_BUSINESS_SUMMARY")
WEBHOOK_DAILY_REVIEW = os.getenv("WEBHOOK_DAILY_REVIEW")

# RSS
FEEDS = {
    "IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "BUSINESS": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

# JST時間
def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# Webhook送信
def send_webhook(url, content):
    if not url:
        print("[WARNING] Webhook未設定")
        return
    try:
        webhook = discord.SyncWebhook.from_url(url)
        webhook.send(content)
        print("[OK] 投稿:", content[:80])
    except Exception as e:
        print("[ERROR] 投稿失敗:", e)

# ニュース投稿（URL検証付き）
def post_news(category, entry):
    url = WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS

    link = getattr(entry, "link", None)
    if not link or not link.startswith("http"):
        print("[SKIP] 不正URL:", entry.title)
        return False

    send_webhook(url, f"{category}トピック: {entry.title}\n{link}")
    return True

# 要約テンプレ（安全版）
def format_summary(summary, points, url):
    text = (
        "🧠 要約\n\n"
        f"{summary}\n\n"
        "👉 ポイント\n"
        f"・{points[0]}\n"
        f"・{points[1]}\n"
        f"・{points[2]}\n\n"
        f"🔗 {url}"
    )
    return text

# ダミー要約生成
def generate_summary(entry):
    summary = "この記事の重要ポイントを短くまとめました。"
    points = [
        "社会的な影響が大きい話題",
        "今後の動きに注目",
        "生活やビジネスに関係あり"
    ]
    return summary, points

# 要約投稿
def post_summary(category, entry, summary_text):
    url = WEBHOOK_IT_SUMMARY if category == "IT" else WEBHOOK_BUSINESS_SUMMARY
    send_webhook(url, summary_text)

# 1日の振り返り
def post_daily_review(daily_news):
    now = now_jst().strftime("%Y-%m-%d")
    content = f"📝 1日の振り返り ({now})\n"

    for category, entries in daily_news.items():
        content += f"\n--- {category} ---\n"
        for entry in entries:
            content += f"- {entry.title}\n{entry.link}\n"

    send_webhook(WEBHOOK_DAILY_REVIEW, content)

# 並列処理
async def process_entry(category, entry):
    link = getattr(entry, "link", None)
    if not link or not link.startswith("http"):
        return

    success = post_news(category, entry)
    if not success:
        return

    delay = random.randint(600, 1800)
    await asyncio.sleep(delay)

    summary, points = generate_summary(entry)
    formatted = format_summary(summary, points, link)
    post_summary(category, entry, formatted)

# メインループ
async def main_loop():
    daily_news = {"IT": [], "BUSINESS": []}
    posted_links = set()

    print("🔍 ニュースBot起動")

    while True:
        now = now_jst()

        if 6 <= now.hour < 22:
            for category, feed_url in FEEDS.items():
                print(f"--- {category} RSS取得 ---")
                feed = feedparser.parse(feed_url)

                if not feed.entries:
                    print(f"[{category}] RSS取得失敗")
                    continue

                for entry in feed.entries:
                    link = getattr(entry, "link", None)
                    if not link or link in posted_links:
                        continue

                    posted_links.add(link)
                    daily_news[category].append(entry)

                    asyncio.create_task(process_entry(category, entry))

        else:
            print(f"🌙 {now.hour}時：新規投稿停止中")

        if now.hour >= 22 and any(daily_news.values()):
            await asyncio.sleep(5)
            post_daily_review(daily_news)
            print("📝 振り返り投稿完了")

            daily_news = {"IT": [], "BUSINESS": []}
            posted_links.clear()

            await asyncio.sleep(3600)
        else:
            await asyncio.sleep(600)

# 実行
if __name__ == "__main__":
    asyncio.run(main_loop())
