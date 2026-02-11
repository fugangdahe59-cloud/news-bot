import os
import feedparser
import asyncio
import datetime
import discord
import openai

# ====== 環境変数 ======
WEBHOOK_IT = os.getenv("WEBHOOK_IT")                 # ITニュースチャンネル
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")     # ビジネスニュースチャンネル
SUMMARY_IT = os.getenv("SUMMARY_IT")                 # IT解説チャンネル
SUMMARY_BUSINESS = os.getenv("SUMMARY_BUSINESS")     # ビジネス解説チャンネル
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# RSSフィード
FEEDS = {
    "IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "BUSINESS": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

# 既に投稿済みニュースを管理
posted_news = set()
daily_news = []  # 日次振り返り用

# JST時間取得
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

# ニュース要約生成
async def generate_summary(title, link):
    try:
        prompt = f"この記事を簡潔に要約してください：\n{title}\n{link}"
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        print("[ERROR] 要約生成失敗:", e)
        return None  # 失敗した場合はNone

# ニュース取得＆投稿
async def fetch_and_post():
    for category, feed_url in FEEDS.items():
        print(f"--- {category} RSS 取得開始 ({feed_url}) ---")
        feed = feedparser.parse(feed_url)

        print(f"[{category}] entries count:", len(feed.entries))
        if not feed.entries:
            send_webhook(WEBHOOK_IT if category=="IT" else WEBHOOK_BUSINESS,
                         f"[{category}] ニュース取得失敗（entries 0）")
            continue

        for entry in feed.entries[:5]:  # 最新5件だけ投稿（調整可能）
            news_id = getattr(entry, "id", entry.link)
            if news_id in posted_news:
                continue
            posted_news.add(news_id)

            title = entry.title
            link = entry.link

            # 1️⃣ ニュース本体は必ず投稿
            send_webhook(WEBHOOK_IT if category=="IT" else WEBHOOK_BUSINESS,
                         f"[{category}] {title}\n{link}")

            # 2️⃣ 要約生成して成功した場合のみ解説チャンネルに投稿
            summary = await generate_summary(title, link)
            if summary:
                send_webhook(SUMMARY_IT if category=="IT" else SUMMARY_BUSINESS, f"[{category}] {title}\n{summary}")
                daily_news.append((category, title, link, summary))

# 日次振り返り作成
def daily_summary():
    if not daily_news:
        return "今日のニュースはありませんでした。"
    text = "📝 今日のニュース振り返り\n\n"
    for category, title, link, summary in daily_news:
        text += f"【{category}】 {title}\n{summary}\n{link}\n\n"
    return text

# メイン
async def main():
    print("🔍 ニュースBot起動")
    await fetch_and_post()
    print("🔍 投稿完了")

if __name__ == "__main__":
    asyncio.run(main())
