import feedparser
import requests
import json
import os

WEBHOOK_URL = "https://discord.com/api/webhooks/1470362990435110923/iXJBgvElFu0TyrjArHXKc_H3Akf8heu3DIIyDeoNzD-krshd2LMAkZXO-GMhTBLiXydH"

RSS_LIST = [
    "https://news.yahoo.co.jp/rss/topics/it.xml",
    "https://news.yahoo.co.jp/rss/topics/business.xml"
]

KEYWORDS = ["AI", "IT", "金融", "投資", "企業", "スタートアップ", "テック", "資産"]
HISTORY_FILE = "posted.json"


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                return set(json.load(f))
            except:
                return set()
    return set()


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history), f, ensure_ascii=False)


def contains_keyword(title):
    return any(k.lower() in title.lower() for k in KEYWORDS)


def post_news():
    history = load_history()

    for rss in RSS_LIST:
        feed = feedparser.parse(rss)

        for entry in feed.entries:
            title = entry.title.strip()

            if title in history:
                continue
            if not contains_keyword(title):
                continue

            message = f"**{title}**\n{entry.link}"
            r = requests.post(WEBHOOK_URL, json={"content": message})

            if r.status_code == 204:
                history.add(title)

    save_history(history)


post_news()
