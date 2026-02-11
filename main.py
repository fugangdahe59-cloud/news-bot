import os
import feedparser
import datetime
import time
import discord
from openai import OpenAI

# ====== 環境変数 ======
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
SUMMARY_IT = os.getenv("SUMMARY_IT")
SUMMARY_BUSINESS = os.getenv("SUMMARY_BUSINESS")
SUMMARY_DAILY = os.getenv("SUMMARY_DAILY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai = OpenAI(api_key=OPENAI_API_KEY)

posted_news = set()
daily_news = []

# ====== RSS FEEDS ======
FEEDS = {
    "IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "BUSINESS": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

# ====== JST時間取得 ======
def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# ====== Discord Webhook送信 ======
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

# ====== OpenAIでニュース要約生成 ======
def generate_summary(title, link):
    prompt = f"""
ニュースタイトル: {title}
URL: {link}

以下のテンプレでまとめてください。人間らしく具体的に。

【ニュース要約】
〜〜〜

【影響】
〜〜〜

【チャンス】
〜〜〜

【ひとこと解説】
〜〜〜
"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print("[ERROR] 要約生成失敗:", e)
        return f"【要約生成失敗】\n{title}\n{link}"

# ====== ニュース取得と投稿 ======
def fetch_and_post():
    for category, feed_url in FEEDS.items():
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            print(f"[{category}] ニュース取得失敗")
            send_webhook(WEBHOOK_IT if category=="IT" else WEBHOOK_BUSINESS,
                         f"[{category}] ニュース取得失敗")
            continue

        for entry in feed.entries:
            news_id = entry.id if 'id' in entry else entry.link
            if news_id in posted_news:
                continue
            posted_news.add(news_id)

            title = entry.title
            link = entry.link

            # Discordにタイトル＋リンクを即投稿
            send_webhook(WEBHOOK_IT if category=="IT" else WEBHOOK_BUSINESS,
                         f"[{category}] {title}\n{link}")

            # 要約生成
            summary = generate_summary(title, link)
            send_webhook(SUMMARY_IT if category=="IT" else SUMMARY_BUSINESS, summary)

            # 日次用に保存
            daily_news.append((category, title, link, summary))

# ====== 22時 日次振り返り投稿 ======
def post_daily_summary():
    if not daily_news:
        print("[INFO] 本日のニュースなし")
        return

    today = now_jst()
    content = f"📝 **今日のニュース振り返り - {today.year}/{today.month}/{today.day}**\n\n"
    for c, t, l, s in daily_news:
        content += f"**[{c}] {t}**\n{s}\nリンク: {l}\n\n"

    send_webhook(SUMMARY_DAILY, content)
    daily_news.clear()
    print("[OK] 1日振り返り投稿完了")

# ====== メインループ ======
def main_loop():
    print("ニュースBot起動")
    while True:
        now = now_jst()
        # 6時〜22時にニュース取得
        if 6 <= now.hour < 22:
            fetch_and_post()
        # 22時ちょうどに振り返り
        if now.hour == 22 and now.minute == 0:
            post_daily_summary()
            # 1分待って再度ループして二重投稿防止
            time.sleep(60)
        time.sleep(60)  # 1分間隔

if __name__ == "__main__":
    main_loop()
