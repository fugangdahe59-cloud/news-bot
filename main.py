import datetime
import time
import feedparser
import requests
import openai

# -----------------------------
# Webhook・API設定
# -----------------------------
WEBHOOK_IT = "https://discord.com/api/webhooks/xxx/yyy"
WEBHOOK_BUSINESS = "https://discord.com/api/webhooks/xxx/yyy"
WEBHOOK_SUMMARY = "https://discord.com/api/webhooks/xxx/yyy"  # IT・ビジネス共通
OPENAI_API_KEY = "sk-..."  # ご自身のOpenAIキー
openai.api_key = OPENAI_API_KEY

# -----------------------------
# ニュース管理用
# -----------------------------
posted_urls = set()     # 重複防止
today_entries = []      # 22時の振り返り用

# -----------------------------
# ヘルパー関数
# -----------------------------
def jst_now():
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)

def post_to_discord(webhook_url, title, content):
    payload = {
        "content": f"**{title}**\n{content}"
    }
    try:
        requests.post(webhook_url, json=payload)
    except Exception as e:
        print(f"[ERROR] Discord投稿失敗: {e}")

# -----------------------------
# ニュース取得・投稿
# -----------------------------
def fetch_and_post_news():
    # ここにRSSフィードURLリスト
    feeds = [
        ("IT", "https://example.com/it/rss", WEBHOOK_IT),
        ("BUSINESS", "https://example.com/business/rss", WEBHOOK_BUSINESS)
    ]
    for category, url, webhook in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if entry.link in posted_urls:
                continue
            now = jst_now()
            hour = now.hour
            # 6時～22時のみ投稿
            if 6 <= hour < 22:
                post_to_discord(webhook, entry.title, entry.summary)
                posted_urls.add(entry.link)
                today_entries.append(entry)
                print(f"[{category}] 投稿: {entry.title}")

# -----------------------------
# 22時振り返り生成
# -----------------------------
def generate_daily_summary():
    if not today_entries:
        print("今日のニュースなし、振り返りスキップ")
        return
    today = jst_now().strftime("%Y-%m-%d")
    news_summary = ""
    for entry in today_entries:
        news_summary += f"- {entry.title}: {entry.summary}\n"
    
    prompt = f"""
今日（{today}）のニュースです:
{news_summary}

上記ニュースをもとに、以下の形式でまとめてください。
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
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        analysis_text = response.choices[0].message.content.strip()
        post_to_discord(WEBHOOK_SUMMARY, f"{today} の振り返り", analysis_text)
        print("振り返り投稿成功")
        today_entries.clear()  # 翌日に備えてリセット
    except Exception as e:
        print(f"[ERROR] 振り返り生成失敗: {e}")

# -----------------------------
# メインループ
# -----------------------------
if __name__ == "__main__":
    while True:
        now = jst_now()
        hour = now.hour
        if hour == 22:  # 22時に振り返り
            generate_daily_summary()
            time.sleep(3600)  # 1時間スキップして再チェック
        else:
            fetch_and_post_news()
            time.sleep(60*5)  # 5分ごとにニュースチェック
