import feedparser
import requests
import json
import os

# チャンネル別Webhook
WEBHOOKS = {
    "it": "https://discord.com/api/webhooks/1470586856029683874/7MxWa4lqpgTW5__mxD9TwwwLoB89jxjdA_idOsI7hXD4LMz6Rd74HTzfmUk-KJS12RSC",
    "business": "https://discord.com/api/webhooks/1470362990435110923/iXJBgvElFu0TyrjArHXKc_H3Akf8heu3DIIyDeoNzD-krshd2LMAkZXO-GMhTBLiXydH"
}

RSS_FEEDS = {
    "it": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "business": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

HISTORY_FILE = "posted.json"


def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            return set()
    return set()


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history), f, ensure_ascii=False)


def post_news():
    history = load_history()
    session = requests.Session()

    for category, rss in RSS_FEEDS.items():
        feed = feedparser.parse(rss)
        webhook = WEBHOOKS[category]

        for entry in feed.entries:
            link = entry.link.strip()
            title = entry.title.strip()

            if link in history:
                continue

            message = f"**{title}**\n{link}\n出典: Yahoo!ニュース"

            try:
                r = session.post(webhook, json={"content": message}, timeout=10)

                if r.status_code == 204:
                    print(f"[{category}] 投稿:", title)
                    history.add(link)
                else:
                    print("送信失敗:", r.status_code)

            except Exception as e:
                print("通信エラー:", e)

    save_history(history)


if __name__ == "__main__":
    post_news()
