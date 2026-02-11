import requests
import time
import random
import os
from datetime import datetime, timezone, timedelta
import feedparser

JST = timezone(timedelta(hours=9))

WEBHOOK_IT = os.getenv("https://discord.com/api/webhooks/1470770157617156226/5bjAA3z39qYH5t3BHIUJG0bIrpZBCLtDv7TlCEl_eSi7tT2esf8uGgIdlA0TXxpcmdSf")
WEBHOOK_BUSINESS = os.getenv("https://discord.com/api/webhooks/1470770770329206785/otRtyL8dbJ-zY7wjdA5KdaW_TUZmzpFIhAy0Zvqfj5kAn_5AUlZP_68DrR7pZR9In2Xu")
WEBHOOK_IT_SUMMARY = os.getenv("https://discord.com/api/webhooks/1470952257192202444/ih8l06d2eR25zuN3aU6vRLsDrX0Qs9Ov0PxvKclAO9W9jq5SD8fB-tJH0RWhFy-Tp_HA")
WEBHOOK_BUSINESS_SUMMARY = os.getenv("https://discord.com/api/webhooks/1470952266230923418/zCuush3D7gYGX63_kaSpDyyuUKGiwM7_t1C-JF25zwcchPTwSIAPQneSZiT7fmdCRnZa")

print("ニュースBot起動")

# ✅ テスト用：夜間停止なし
def is_night():
    return False


def send_webhook(url, title, link):
    if not url:
        print("Webhook未設定")
        return

    try:
        requests.post(url, json={
            "content": f"{title}\n{link}"
        })
        print(f"投稿成功: {title}")
    except Exception as e:
        print("通信エラー:", e)


def send_summary(url, title):
    if not url:
        return

    summary = f"📰要約解説\n{title} に関するニュースです。\n詳しくはリンクを確認してください。"

    try:
        requests.post(url, json={"content": summary})
        print("要約投稿成功")
    except Exception as e:
        print("要約通信エラー:", e)


def process_feed(feed_url, webhook, summary_webhook, label):
    feed = feedparser.parse(feed_url)

    for entry in feed.entries[:5]:
        title = entry.title
        link = entry.link

        send_webhook(webhook, title, link)

        delay = random.randint(600, 1800)  # 10〜30分
        print(f"{label} 要約待機 {delay}秒")
        time.sleep(delay)

        send_summary(summary_webhook, title)


while True:
    print("ニュース取得開始")

    if not is_night():
        process_feed(
            "https://news.yahoo.co.jp/rss/categories/it.xml",
            WEBHOOK_IT,
            WEBHOOK_IT_SUMMARY,
            "[IT]"
        )

        process_feed(
            "https://news.yahoo.co.jp/rss/categories/business.xml",
            WEBHOOK_BUSINESS,
            WEBHOOK_BUSINESS_SUMMARY,
            "[BUSINESS]"
        )
    else:
        print("夜間停止中")

    print("1時間待機...")
    time.sleep(3600)
