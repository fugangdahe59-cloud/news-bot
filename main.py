import os
import feedparser
import asyncio
import datetime
import discord
import random

# ====== 環境変数 ======
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
SUMMARY_DAILY = os.getenv("SUMMARY_DAILY")

# RSSフィード
FEEDS = {
    "IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "BUSINESS": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

# 投稿済みニュース管理
posted_news = set()
daily_news = []

# JST時間取得
def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# Discord Webhook送信（同期）
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

# ニュース取得とDiscord投稿
async def fetch_and_post():
    global daily_news
    for category, feed_url in FEEDS.items():
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            print(f"[{category}] ニュースが取得できません")
            send_webhook(WEBHOOK_IT if category=="IT" else WEBHOOK_BUSINESS,
                         f"[{category}] ニュースが取得できません")
            continue

        for entry in feed.entries:
            news_id = entry.id if "id" in entry else entry.link
            if news_id in posted_news:
                continue
            posted_news.add(news_id)

            title = entry.title
            link = entry.link
            target_webhook = WEBHOOK_IT if category=="IT" else WEBHOOK_BUSINESS
            send_webhook(target_webhook, f"[{category}] {title}\n{link}")

            # daily_news に保存
            daily_news.append((category, title, link))

            # ランダム待機（スパム防止）
            await asyncio.sleep(random.randint(1,3))  # テスト時は短く

# 1日の振り返りブログ生成
def generate_daily_blog(daily_news):
    today = now_jst()
    content = f"📅 今日のニュースまとめ – {today.year}年{today.month}月{today.day}日\n\n"

    categories = {}
    for cat, title, link in daily_news:
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((title, link))

    for cat, items in categories.items():
        content += f"### {cat}トピック\n"
        for title, link in items:
            content += f"**{title}**\n{link}\n\n"

    content += "💡 今日のひとこと解説\n"
    content += "ニュースを通して感じたこと: 「情報管理と透明性が今後ますます重要になる」。個人・企業問わず、リスクに備えた行動が必要です。\n"

    return content

# 22時に自動振り返り投稿
async def daily_summary_loop():
    global daily_news
    posted_today = False
    while True:
        now = now_jst()
        if now.hour == 22 and not posted_today:
            if daily_news:
                blog_content = generate_daily_blog(daily_news)
                send_webhook(SUMMARY_DAILY, blog_content)
                daily_news.clear()
            posted_today = True
        elif now.hour < 22:
            posted_today = False
        await asyncio.sleep(60)

# メインループ
async def main_loop():
    print("ニュースBot起動")
    # 起動後すぐ最新ニュースを投稿
    await fetch_and_post()

    while True:
        now = now_jst()
        if 6 <= now.hour < 22:
            await fetch_and_post()
        await asyncio.sleep(300)  # 5分ごとにチェック

# 起動
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(daily_summary_loop())
    loop.run_until_complete(main_loop())
