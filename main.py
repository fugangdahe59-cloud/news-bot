import os
import time
import random
import datetime
import requests
import feedparser
from openai import OpenAI

print("ニュースBot起動")

# ===== 環境変数 =====
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
SUMMARY_IT = os.getenv("SUMMARY_IT")
SUMMARY_BUSINESS = os.getenv("SUMMARY_BUSINESS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ===== RSS =====
RSS_IT = "https://news.yahoo.co.jp/rss/categories/it.xml"
RSS_BUSINESS = "https://news.yahoo.co.jp/rss/categories/business.xml"

posted = set()

def is_night():
    jst = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)
    hour = jst.hour
    return hour >= 22 or hour < 6

def send(webhook, text):
    if not webhook:
        print("Webhook未設定")
        return
    requests.post(webhook, json={"content": text})

def ai_summary(text):
    prompt = f"""
以下のニュースをビジネス視点で分析してください。

・要約（2〜3行）
・企業への影響
・市場への意味
・今後の展開予測

ニュース:
{text}
"""

    res = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )

    return res.choices[0].message.content

def process_feed(feed_url, webhook, summary_webhook, label):
    feed = feedparser.parse(feed_url)

    for entry in feed.entries[:3]:
        if entry.link in posted:
            continue

        posted.add(entry.link)

        title = entry.title
        link = entry.link
        text = f"[{label}] {title}\n{link}"

        send(webhook, text)
        print(f"[{label}] 投稿:", title)

        # 要約をランダム遅延
        delay = random.randint(600, 1800)
        print(f"[{label}] 要約待機 {delay}秒")
        time.sleep(delay)

        try:
            summary = ai_summary(title)
            send(summary_webhook, f"🧠 要約\n{summary}")
            print(f"[{label}] 要約投稿完了")
        except Exception as e:
            print("AIエラー:", e)

while True:
    print("ニュース取得開始")

    if is_night():
        print("夜間停止中（22:00〜6:00）")
        time.sleep(3600)
        continue

    process_feed(RSS_IT, WEBHOOK_IT, SUMMARY_IT, "IT")
    process_feed(RSS_BUSINESS, WEBHOOK_BUSINESS, SUMMARY_BUSINESS, "ビジネス")

    print("1時間待機...")
    time.sleep(3600)
