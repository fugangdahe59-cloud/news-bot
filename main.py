import os
import time
import datetime
import requests
import feedparser

WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
SUMMARY_IT = os.getenv("SUMMARY_IT")
SUMMARY_BUSINESS = os.getenv("SUMMARY_BUSINESS")

IT_FEED = "https://news.yahoo.co.jp/rss/topics/it.xml"
BUSINESS_FEED = "https://news.yahoo.co.jp/rss/topics/business.xml"


def is_active_time():
    # 日本時間取得
    jst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    hour = jst.hour

    # 6:00〜22:00のみ動作
    return 6 <= hour < 22


def send(webhook, message):
    if not webhook:
        print("Webhook未設定")
        return
    requests.post(webhook, json={"content": message})


def fetch_news(feed_url):
    feed = feedparser.parse(feed_url)
    if feed.entries:
        entry = feed.entries[0]
        return entry.title, entry.link
    return None, None


def main():
    print("ニュースBot起動")

    while True:
        print("ニュース取得開始")

        if not is_active_time():
            print("夜間停止中（22:00〜6:00）")
            time.sleep(3600)
            continue

        # --- ITニュース ---
        title, link = fetch_news(IT_FEED)
        if title:
            msg = f"[IT] {title}\n{link}"
            print("投稿:", title)
            send(WEBHOOK_IT, msg)

            wait = 900 + int(os.urandom(1)[0])  # 15〜20分ランダム
            print(f"[IT] 要約待機 {wait}秒")
            time.sleep(wait)
            send(SUMMARY_IT, f"【要約待機中】{title}")

        # --- ビジネスニュース ---
        title, link = fetch_news(BUSINESS_FEED)
        if title:
            msg = f"[Business] {title}\n{link}"
            print("投稿:", title)
            send(WEBHOOK_BUSINESS, msg)

            wait = 900 + int(os.urandom(1)[0])
            print(f"[Business] 要約待機 {wait}秒")
            time.sleep(wait)
            send(SUMMARY_BUSINESS, f"【要約待機中】{title}")

        time.sleep(3600)


if __name__ == "__main__":
    main()
