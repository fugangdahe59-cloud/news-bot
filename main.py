import os
import time
import datetime
import feedparser
import requests
import random
# OpenAIライブラリ
from openai import OpenAI

# 環境変数 or 直接埋め込み
WEBHOOK_IT = os.getenv("WEBHOOK_IT") or "https://discord.com/api/webhooks/XXXX/XXXX"
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS") or "https://discord.com/api/webhooks/XXXX/XXXX"
WEBHOOK_SUMMARY = os.getenv("WEBHOOK_SUMMARY") or "https://discord.com/api/webhooks/XXXX/XXXX"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or "sk-XXXX"

client = OpenAI(api_key=OPENAI_API_KEY)

# RSSフィードURL
RSS_IT = "https://example.com/it.rss"
RSS_BUSINESS = "https://example.com/business.rss"

# 投稿済みニュース管理
posted_news = set()
daily_news_summary = []

def jst_now():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=9)

def post_to_discord(webhook_url, content):
    if webhook_url:
        requests.post(webhook_url, json={"content": content})

def generate_summary(news_title, news_link):
    # AIで要約生成
    prompt = f"ニュースタイトル: {news_title}\nリンク: {news_link}\n\n上記ニュースを以下の形式で日本語で作ってください:\n【ニュース要約】\n【影響】\n【チャンス】\n【ひとこと解説】"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    summary_text = response.choices[0].message.content
    return summary_text

def fetch_and_post_rss(rss_url, webhook_main, webhook_summary):
    feed = feedparser.parse(rss_url)
    for entry in feed.entries:
        news_id = entry.get("id") or entry.link
        if news_id in posted_news:
            continue  # 既に投稿済みならスキップ
        title = entry.title
        link = entry.link
        # 通常投稿
        post_to_discord(webhook_main, f"[ニュース] {title}\n{link}")
        # 要約生成は10〜30分ランダム待機
        wait_sec = random.randint(600, 1800)
        time.sleep(wait_sec)
        summary = generate_summary(title, link)
        post_to_discord(webhook_summary, summary)
        # 投稿済み管理
        posted_news.add(news_id)
        daily_news_summary.append(summary)

def daily_summary_post():
    now = jst_now()
    if now.hour == 22:  # 22時に一日の振り返り
        if daily_news_summary:
            content = f"【{now.year}年{now.month}月{now.day}日の振り返り】\n\n" + "\n\n".join(daily_news_summary)
            post_to_discord(WEBHOOK_SUMMARY, content)
            daily_news_summary.clear()  # 投稿後はリセット

def main_loop():
    while True:
        now = jst_now()
        # 6時〜22時のみニュース取得
        if 6 <= now.hour < 22:
            fetch_and_post_rss(RSS_IT, WEBHOOK_IT, WEBHOOK_SUMMARY)
            fetch_and_post_rss(RSS_BUSINESS, WEBHOOK_BUSINESS, WEBHOOK_SUMMARY)
        # 22時は振り返り投稿
        daily_summary_post()
        print(f"[{now}] 1時間待機...")
        time.sleep(3600)

if __name__ == "__main__":
    print("ニュースBot起動")
    main_loop()
