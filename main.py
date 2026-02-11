import os
import feedparser
import asyncio
import datetime
import discord
import openai

# ====== 環境変数 ======
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
WEBHOOK_IT_SUMMARY = os.getenv("WEBHOOK_IT_SUMMARY")
WEBHOOK_BUSINESS_SUMMARY = os.getenv("WEBHOOK_BUSINESS_SUMMARY")
WEBHOOK_DAILY_SUMMARY = os.getenv("WEBHOOK_DAILY_SUMMARY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# RSS フィード
FEEDS = {
    "IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "BUSINESS": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

# JST 時間取得
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

# ニュース要約生成
async def generate_summary(title, link):
    prompt = f"以下のニュースタイトルの要約を簡潔に書いてください:\n{title}\nリンク: {link}"
    try:
        response = await asyncio.to_thread(
            lambda: openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        print("[ERROR] 要約生成失敗:", e)
        return "【要約生成失敗】"

# ニュース取得と個別投稿
async def fetch_and_post():
    daily_news = {"IT": [], "BUSINESS": []}
    for category, feed_url in FEEDS.items():
        print(f"--- {category} RSS 取得開始 ({feed_url}) ---")
        feed = feedparser.parse(feed_url)
        entries = feed.entries
        print(f"[{category}] entries count:", len(entries))

        if not entries:
            send_webhook(WEBHOOK_IT if category=="IT" else WEBHOOK_BUSINESS,
                         f"{category}トピック: ニュースが取得できません")
            continue

        for entry in entries:
            title = entry.title
            link = entry.link

            # 個別ニュース投稿
            send_webhook(WEBHOOK_IT if category=="IT" else WEBHOOK_BUSINESS,
                         f"{category}トピック: {title}\n{link}")

            # 要約生成
            summary_text = await generate_summary(title, link)
            send_webhook(WEBHOOK_IT_SUMMARY if category=="IT" else WEBHOOK_BUSINESS_SUMMARY,
                         f"{category}トピック: {title}\n要約: {summary_text}")

            # 日次まとめ用
            daily_news[category].append((title, link, summary_text))

    return daily_news

# 日次まとめ投稿（ブログ風）
def post_daily_summary(daily_news):
    content = f"📝 {now_jst().strftime('%Y/%m/%d')} ニュース振り返り\n\n"

    for category in ["IT", "BUSINESS"]:
        content += f"=== {category}トピック ===\n"
        if not daily_news[category]:
            content += "ニュースなし\n\n"
            continue
        for idx, (title, link, summary) in enumerate(daily_news[category], 1):
            content += f"{idx}. {title}\n{link}\n要約: {summary}\n\n"

    send_webhook(WEBHOOK_DAILY_SUMMARY, content)

async def main():
    print("🔍 ニュースBot起動")
    daily_news = await fetch_and_post()
    post_daily_summary(daily_news)
    print("🔍 投稿完了")

if __name__ == "__main__":
    asyncio.run(main())
