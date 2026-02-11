import os
import feedparser
import asyncio
import datetime
import discord
import openai

# ====== 環境変数 ======
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
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
def send_webhook(url, category, title, link, summary=None):
    if not url:
        print("[WARNING] Webhook URL が未設定です")
        return

    display_category = f"{category}トピック"
    content = f"{display_category}: {title}\n{link}"
    if summary:
        content += f"\n\n要約: {summary}"

    try:
        webhook = discord.SyncWebhook.from_url(url)
        webhook.send(content)
        print("[OK] Discord 投稿:", content[:100])
    except Exception as e:
        print("[ERROR] Discord 投稿失敗:", e)

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
            print(f"[{category}] ニュースが取得できません")
            send_webhook(WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS,
                         category, "ニュースが取得できません（entries 0）", "")
            continue

        # 複数件投稿（必要に応じて変更可能）
        for entry in feed.entries[:5]:  # 先頭5件まで投稿
            title = entry.title
            link = entry.link

            # 要約生成
            summary = await generate_summary(title, link)

            send_webhook(
                WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS,
                category,
                title,
                link,
                summary
            )

# メイン関数
async def main():
    print("🔍 ニュースBot 起動")
    await fetch_and_post()
    print("🔍 投稿完了")

if __name__ == "__main__":
    asyncio.run(main())
