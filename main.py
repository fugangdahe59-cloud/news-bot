import os
import time
import random
import datetime
import requests
import feedparser
from openai import OpenAI

# ===== 環境変数 =====
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_SUMMARY = os.getenv("SUMMARY_IT")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_KEY)

RSS_URL = "https://news.yahoo.co.jp/rss/topics/it.xml"

posted_links = set()

# ===== 稼働時間チェック =====
def is_active_time():
    jst = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)
    hour = jst.hour
    return 6 <= hour < 22

# ===== Discord投稿 =====
def send_discord(webhook, text):
    if not webhook:
        print("Webhook未設定")
        return
    requests.post(webhook, json={"content": text})

# ===== AI要約 =====
def summarize(text):
    try:
        res = client.responses.create(
            model="gpt-5-mini",
            input=f"次のニュースを短く要約してください:\n{text}"
        )
        return res.output_text
    except Exception as e:
        print("AI要約エラー:", e)
        return "要約失敗"

# ===== メインループ =====
print("ニュースBot起動")

while True:

    if not is_active_time():
        print("夜間停止中（6:00〜22:00のみ動作）")
        time.sleep(3600)
        continue

    print("ニュース取得開始")

    feed = feedparser.parse(RSS_URL)

    for entry in feed.entries[:1]:

        if entry.link in posted_links:
            continue

        title = entry.title
        link = entry.link

        message = f"📰 {title}\n{link}"
        send_discord(WEBHOOK_IT, message)
        print("投稿:", title)

        wait = random.randint(600, 1800)
        print("要約待機", wait, "秒")
        time.sleep(wait)

        summary = summarize(title)
        send_discord(WEBHOOK_SUMMARY, f"🤖 要約:\n{summary}")

        posted_links.add(link)

    sleep_time = random.randint(1800, 3600)
    print("待機", sleep_time, "秒")
    time.sleep(sleep_time)
