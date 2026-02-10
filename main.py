import feedparser
import requests
import json
import os
import time

# 環境変数から Webhook URL を読み込む
WEBHOOKS = {
    "it": os.getenv("https://discord.com/api/webhooks/1470586856029683874/7MxWa4lqpgTW5__mxD9TwwwLoB89jxjdA_idOsI7hXD4LMz6Rd74HTzfmUk-KJS12RSC"),
    "business": os.getenv("https://discord.com/api/webhooks/1470362990435110923/iXJBgvElFu0TyrjArHXKc_H3Akf8heu3DIIyDeoNzD-krshd2LMAkZXO-GMhTBLiXydH")
}

RSS_FEEDS = {
    "it": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "business": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

HISTORY_FILE = "posted.json"

# 履歴の読み込み
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                return set(json.load(f))
            except:
                return set()
    return set()

# 履歴の保存
def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history), f, ensure_ascii=False)

# ニュースを投稿
def post_news():
    print("ニュース取得開始")
    history = load_history()
    session = requests.Session()

    for category, rss in RSS_FEEDS.items():
        webhook = WEBHOOKS.get(category)

        # Webhook が設定されていなければスキップ
        if not webhook:
            print(f"{category} Webhook未設定")
            continue

        feed = feedparser.parse(rss)

        for entry in feed.entries:
            link = entry.link.strip()
            title = entry.title.strip()

            # 重複はスキップ
            if link in history:
                continue

            message = f"**{title}**\n{link}\n出典: Yahoo!ニュース"

            try:
                r = session.post(webhook, json={"content": message}, timeout=10)
                if r.status_code == 204:
                    print(f"[{category}] 投稿成功: {title}")
                    history.add(link)
                else:
                    print(f"[{category}] 投稿失敗: {r.status_code}")
            except Exception as e:
                print(f"[{category}] 通信エラー: {e}")

    save_history(history)

# メイン処理
print("ニュースBot起動")

while True:
    post_news()
    print("1時間待機...")
    time.sleep(3600)
