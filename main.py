import os

print("IT:", os.getenv("WEBHOOK_IT"))
print("BUS:", os.getenv("WEBHOOK_BUSINESS"))

import feedparser
import requests
import os
import time

WEBHOOKS = {
    "it": os.getenv("https://discord.com/api/webhooks/1470586856029683874/7MxWa4lqpgTW5__mxD9TwwwLoB89jxjdA_idOsI7hXD4LMz6Rd74HTzfmUk-KJS12RSC"),
    "business": os.getenv("https://discord.com/api/webhooks/1470362990435110923/iXJBgvElFu0TyrjArHXKc_H3Akf8heu3DIIyDeoNzD-krshd2LMAkZXO-GMhTBLiXydH")
}

RSS_FEEDS = {
    "it": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "business": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

posted_links = set()


def post_news():
    print("ニュース取得開始")

    session = requests.Session()

    for category, rss in RSS_FEEDS.items():
        feed = feedparser.parse(rss)
        webhook = WEBHOOKS.get(category)

        if not webhook:
            print(f"{category} Webhook未設定")
            continue

        for entry in feed.entries:
            link = entry.link.strip()
            title = entry.title.strip()

            if link in posted_links:
                continue

            message = f"**{title}**\n{link}\n出典: Yahoo!ニュース"

            try:
                r = session.post(webhook, json={"content": message}, timeout=10)

                print("送信結果:", r.status_code)

                if r.status_code == 204:
                    print(f"[{category}] 投稿成功:", title)
                    posted_links.add(link)

                time.sleep(2)

            except Exception as e:
                print("通信エラー:", e)


print("ニュースBot起動")

while True:
    post_news()
    print("1時間待機...")
    time.sleep(3600)
