import feedparser
import requests
import json
import os
import time
import random
from datetime import datetime

# ===== Webhooks =====
WEBHOOKS = {
    "it": os.getenv("https://discord.com/api/webhooks/1470770157617156226/5bjAA3z39qYH5t3BHIUJG0bIrpZBCLtDv7TlCEl_eSi7tT2esf8uGgIdlA0TXxpcmdSfT"),
    "business": os.getenv("https://discord.com/api/webhooks/1470770770329206785/otRtyL8dbJ-zY7wjdA5KdaW_TUZmzpFIhAy0Zvqfj5kAn_5AUlZP_68DrR7pZR9In2Xu")
}

SUMMARY_WEBHOOKS = {
    "it": os.getenv("https://discord.com/api/webhooks/1470952257192202444/ih8l06d2eR25zuN3aU6vRLsDrX0Qs9Ov0PxvKclAO9W9jq5SD8fB-tJH0RWhFy-Tp_HA"),
    "business": os.getenv("https://discord.com/api/webhooks/1470952266230923418/zCuush3D7gYGX63_kaSpDyyuUKGiwM7_t1C-JF25zwcchPTwSIAPQneSZiT7fmdCRnZa")
}

# ===== RSS =====
RSS_FEEDS = {
    "it": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "business": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

HISTORY_FILE = "posted.json"


# ===== 履歴 =====
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history), f, ensure_ascii=False)


# ===== 夜間停止 =====
def night_stop():
    hour = datetime.now().hour
    return hour >= 22 or hour < 6


# ===== 要約生成（簡易）=====
def make_summary(title):
    return f"📝要約:\n{title} に関するニュースです。詳しくは本文をご確認ください。"


# ===== 投稿 =====
def post_news():
    if night_stop():
        print("夜間停止中（22:00〜6:00）")
        return

    history = load_history()

    for category, rss in RSS_FEEDS.items():
        webhook = WEBHOOKS.get(category)
        summary_hook = SUMMARY_WEBHOOKS.get(category)

        if not webhook:
            print(f"{category} Webhook未設定")
            continue

        feed = feedparser.parse(rss)

        for entry in feed.entries:
            link = entry.link.strip()
            title = entry.title.strip()

            if link in history:
                continue

            message = f"**{title}**\n{link}\n出典: Yahoo!ニュース"

            try:
                r = requests.post(webhook, json={"content": message}, timeout=10)

                if r.status_code == 204:
                    print(f"[{category}] 投稿成功:", title)
                    history.add(link)

                    # ===== 要約遅延投稿 =====
                    if summary_hook:
                        delay = random.randint(600, 1800)  # 10〜30分
                        print(f"要約を {delay//60} 分後に投稿予定")
                        time.sleep(delay)

                        summary = make_summary(title)
                        requests.post(summary_hook, json={"content": summary})

                else:
                    print("送信失敗:", r.status_code)

            except Exception as e:
                print("通信エラー:", e)

    save_history(history)


# ===== メインループ =====
print("ニュースBot起動")

while True:
    print("ニュース取得開始")
    post_news()
    print("1時間待機...")
    time.sleep(3600)
