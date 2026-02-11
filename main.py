import feedparser
import requests
import json
import os
import time
import random
from datetime import datetime

# ===== ニュース用Webhook =====
NEWS_WEBHOOKS = {
    "it": os.getenv("https://discord.com/api/webhooks/1470770157617156226/5bjAA3z39qYH5t3BHIUJG0bIrpZBCLtDv7TlCEl_eSi7tT2esf8uGgIdlA0TXxpcmdSf"),
    "business": os.getenv("https://discord.com/api/webhooks/1470770770329206785/otRtyL8dbJ-zY7wjdA5KdaW_TUZmzpFIhAy0Zvqfj5kAn_5AUlZP_68DrR7pZR9In2Xu")
}

# ===== 要約用Webhook（別チャンネル）=====
SUMMARY_WEBHOOKS = {
    "it": os.getenv("https://discord.com/api/webhooks/1470952257192202444/ih8l06d2eR25zuN3aU6vRLsDrX0Qs9Ov0PxvKclAO9W9jq5SD8fB-tJH0RWhFy-Tp_HA"),
    "business": os.getenv("https://discord.com/api/webhooks/1470952266230923418/zCuush3D7gYGX63_kaSpDyyuUKGiwM7_t1C-JF25zwcchPTwSIAPQneSZiT7fmdCRnZa")
}

RSS_FEEDS = {
    "it": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "business": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

HISTORY_FILE = "posted.json"


def is_sleep_time():
    now = datetime.now().hour
    return now >= 22 or now < 6


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history), f, ensure_ascii=False)


def make_summary(title):
    return f"🧠 解説:\nこの記事は「{title}」についてのニュースです。\n今後の動向が注目されます。"


def send(webhook, text):
    if not webhook:
        print("Webhook未設定")
        return
    try:
        r = requests.post(webhook, json={"content": text}, timeout=10)
        if r.status_code == 204:
            print("投稿成功")
        else:
            print("送信失敗:", r.status_code)
    except Exception as e:
        print("通信エラー:", e)


def post_news():
    if is_sleep_time():
        print("夜間停止中（22:00〜6:00）")
        return

    history = load_history()

    for category, rss in RSS_FEEDS.items():
        news_webhook = NEWS_WEBHOOKS.get(category)
        summary_webhook = SUMMARY_WEBHOOKS.get(category)

        feed = feedparser.parse(rss)

        for entry in feed.entries:
            link = entry.link.strip()
            title = entry.title.strip()

            if link in history:
                continue

            # ニュース投稿
            message = f"📰 **{title}**\n{link}\n出典: Yahoo!ニュース"
            send(news_webhook, message)

            # ランダム待機 10〜30分
            wait = random.randint(600, 1800)
            print(f"{wait//60}分後に要約投稿")
            time.sleep(wait)

            # 要約投稿（別チャンネル）
            summary = make_summary(title)
            send(summary_webhook, summary)

            history.add(link)

    save_history(history)


if __name__ == "__main__":
    print("ニュースBot起動")

    while True:
        print("ニュース取得開始")
        post_news()
        print("1時間待機...")
        time.sleep(3600)
