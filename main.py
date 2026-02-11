import os
import time
import random
import datetime
import requests
import feedparser

# ===== 環境変数 =====
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
SUMMARY_IT = os.getenv("SUMMARY_IT")
SUMMARY_BUSINESS = os.getenv("SUMMARY_BUSINESS")

# ===== RSS =====
RSS_IT = "https://news.yahoo.co.jp/rss/topics/it.xml"
RSS_BUSINESS = "https://news.yahoo.co.jp/rss/topics/business.xml"

# ===== 夜間停止（日本時間）=====
def is_night():
    jst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    hour = jst.hour
    return hour >= 22 or hour < 6


def send(webhook, text):
    if not webhook:
        print("Webhook未設定")
        return
    try:
        requests.post(webhook, json={"content": text}, timeout=10)
    except Exception as e:
        print("送信エラー:", e)


def summarize(title):
    # 簡易要約（あとでAI要約にも変更可能）
    return f"要約: {title} に関する注目ニュースです。"


def process_feed(rss, webhook, summary_hook, label):
    feed = feedparser.parse(rss)

    for entry in feed.entries[:3]:
        title = entry.title
        link = entry.link

        msg = f"[{label}] {title}\n{link}"
        send(webhook, msg)
        print(f"[{label}] 投稿:", title)

        # 10〜30分ランダム待機
        wait = random.randint(600, 1800)
        print(f"[{label}] 要約待機 {wait}秒")
        time.sleep(wait)

        summary = summarize(title)
        send(summary_hook, f"[{label}要約] {summary}")


# ===== メインループ =====
print("ニュースBot起動")

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
