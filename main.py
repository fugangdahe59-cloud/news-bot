import datetime
import time
import feedparser
import requests
import json
import random

# =========================
# Webhook 設定
# =========================
WEBHOOK_IT = "YOUR_WEBHOOK_IT"
WEBHOOK_BUSINESS = "YOUR_WEBHOOK_BUSINESS"
SUMMARY_WEBHOOK = "YOUR_WEBHOOK_SUMMARY"  # 22時振り返り用

# ニュースRSSリスト
FEEDS_IT = ["https://example.com/it.rss"]
FEEDS_BUSINESS = ["https://example.com/business.rss"]

# 投稿済みニュース管理
posted_titles = set()

# 投稿可能時間判定（日本時間6:00〜22:00）
def is_post_time():
    jst = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    return 6 <= jst.hour < 22

# ニュースをDiscordに送信
def post_to_discord(webhook, title, link):
    data = {"content": f"{title}\n{link}"}
    requests.post(webhook, json=data)

# AI要約付き投稿（擬似例）
def post_summary(webhook, title, link):
    # ここでAI要約処理を追加できます
    summary = f"【ニュース要約】\n{title}\n\n【影響】\n影響の分析\n\n【チャンス】\nチャンスの分析\n\n【ひとこと解説】\n簡単解説"
    data = {"content": f"{summary}\n{link}"}
    requests.post(webhook, json=data)

# ニュース取得と投稿
def fetch_and_post(feeds, webhook, summary_webhook=None):
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if entry.title not in posted_titles:
                if is_post_time():
                    post_to_discord(webhook, entry.title, entry.link)
                    if summary_webhook:
                        # 10〜30分後に要約投稿
                        delay = random.randint(600, 1800)
                        time.sleep(delay)
                        post_summary(summary_webhook, entry.title, entry.link)
                posted_titles.add(entry.title)

# 22時振り返り投稿
def daily_summary():
    jst = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    if jst.hour == 22 and jst.minute < 5:  # 22:00前後5分で一度だけ投稿
        summary_text = f"【本日の振り返り】 {jst.strftime('%Y-%m-%d')}\n今日のIT・経済ニュースまとめと今後の対策案"
        requests.post(SUMMARY_WEBHOOK, json={"content": summary_text})

# =========================
# メインループ
# =========================
while True:
    try:
        fetch_and_post(FEEDS_IT, WEBHOOK_IT, SUMMARY_WEBHOOK)
        fetch_and_post(FEEDS_BUSINESS, WEBHOOK_BUSINESS, SUMMARY_WEBHOOK)
        daily_summary()
    except Exception as e:
        print("エラー:", e)
    time.sleep(60)  # 1分ごとにチェック
