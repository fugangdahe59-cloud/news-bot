import feedparser
import requests
import json
import os
import time

# 環境変数から Webhook URL を読み込む
WEBHOOKS = {
    "it": os.getenv("https://discord.com/api/webhooks/1470770157617156226/5bjAA3z39qYH5t3BHIUJG0bIrpZBCLtDv7TlCEl_eSi7tT2esf8uGgIdlA0TXxpcmdSf"),
    "business": os.getenv("https://discord.com/api/webhooks/1470770770329206785/otRtyL8dbJ-zY7wjdA5KdaW_TUZmzpFIhAy0Zvqfj5kAn_5AUlZP_68DrR7pZR9In2Xu")
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
        # 空白や改行を削除して正確に取得
        webhook = WEBHOOKS.get(category, "")
        if webhook:
            webhook = webhook.strip()

        # Webhook が設定されていなければスキップ
        if webhook == "":
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
