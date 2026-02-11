import os
import feedparser
import asyncio
import datetime
import discord
import openai

# ====== 環境変数 ======
WEBHOOK_IT = os.getenv("WEBHOOK_IT")                  # ITニュース投稿用
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")      # BUSINESSニュース投稿用
WEBHOOK_SUMMARY_IT = os.getenv("WEBHOOK_SUMMARY_IT")  # IT要約用
WEBHOOK_SUMMARY_BUSINESS = os.getenv("WEBHOOK_SUMMARY_BUSINESS")  # BUSINESS要約用
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

# Discord Webhook 送信（ニュース用）
def send_news_webhook(url, category, title, link):
    if not url:
        print("[WARNING] Webhook URL が未設定です")
        return
    display_category = f"{category}トピック"
    content = f"{display_category}: {title}\n{link}"
    try:
        webhook = discord.SyncWebhook.from_url(url)
        webhook.send(content)
        print("[OK] Discord ニュース投稿:", content[:100])
    except Exception as e:
        print("[ERROR] Discord 投稿失敗:", e)

# Discord Webhook 送信（要約/解説用）
def send_summary_webhook(category, title, link, summary):
    if category == "IT":
        url = WEBHOOK_SUMMARY_IT
    else:
        url = WEBHOOK_SUMMARY_BUSINESS
    if not url:
        print(f"[WARNING] {category}要約 Webhook 未設定")
        return

    display_category = f"{category}トピック 要約"
    content = f"{display_category}: {title}\n{link}\n\n要約: {summary}"
    try:
        webhook = discord.SyncWebhook.from_url(url)
        webhook.send(content)
        print(f"[OK] Discord {category}要約投稿:", content[:100])
    except Exception as e:
        print(f"[ERROR] Discord {category}要約投稿失敗:", e)

# OpenAIで要約生成
async def generate_summary(title, link):
    prompt = f"以下のニュースを1-2文で簡潔に要約してください。\nタイトル: {title}\nリンク: {link}"
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
            )
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        print("[ERROR] 要約生成失敗:", e)
        return "【要約生成失敗】"

# ニュース取得と投稿
async def fetch_and_post():
    for category, feed_url in FEEDS.items():
        print(f"--- {category} RSS 取得開始 ({feed_url}) ---")
        feed = feedparser.parse(feed_url)
        print(f"[{category}] entries count:", len(feed.entries))
        if not feed.entries:
            send_news_webhook(
                WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS,
                category, "ニュースが取得できません（entries 0）", ""
            )
            continue

        for entry in feed.entries[:5]:  # 先頭5件
            title = entry.title
            link = entry.link

            # ニュース投稿（要約なし）
            send_news_webhook(
                WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS,
                category,
                title,
                link
            )

            # 要約生成（解説用チャンネルに送信、IT/Business別）
            summary = await generate_summary(title, link)
            send_summary_webhook(category, title, link, summary)

# メイン関数
async def main():
    print("🔍 ニュースBot 起動")
    await fetch_and_post()
    print("🔍 投稿完了")

if __name__ == "__main__":
    asyncio.run(main())
