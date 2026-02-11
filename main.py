import os
import time
import random
import requests
import feedparser
import datetime
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

WEBHOOK_IT = os.getenv("WEBHOOK_IT")
SUMMARY_IT = os.getenv("SUMMARY_IT")

RSS_IT = "https://news.yahoo.co.jp/rss/categories/it.xml"


def is_active_time():
    jst = datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=9)
    hour = jst.hour
    return 6 <= hour < 22  # 6時〜22時だけ動く


def send(webhook, text):
    if not webhook:
        print("Webhook未設定")
        return
    requests.post(webhook, json={"content": text})


def ai_summary(title, link, description):
    prompt = f"""
以下のニュースを人間っぽく要約＋解説してください。

【条件】
・3〜5行
・中学生でも分かる
・ニュースの意味や背景も軽く説明
・SNSで読むような自然な文章

タイトル: {title}
内容: {description}
URL: {link}
"""

    res = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    return res.choices[0].message.content


print("ニュースBot起動")

while True:

    if not is_active_time():
        print("時間外 → 1時間待機")
        time.sleep(3600)
        continue

    print("ニュース取得開始")

    feed = feedparser.parse(RSS_IT)

    if not feed.entries:
        print("ニュースなし")
        time.sleep(3600)
        continue

    entry = feed.entries[0]

    title = entry.title
    link = entry.link
    description = entry.get("summary", "")

    send(WEBHOOK_IT, f"📰 {title}\n{link}")
    print("投稿:", title)

    wait = random.randint(600, 1800)
    print(f"要約待機 {wait} 秒")
    time.sleep(wait)

    summary = ai_summary(title, link, description)
    send(SUMMARY_IT, f"🤖 解説付き要約\n{summary}")

    print("要約投稿完了")

    time.sleep(3600)
