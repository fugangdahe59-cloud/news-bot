import os
import time
import random
import requests
import feedparser
import datetime
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")

# 1日振り返り専用チャット
SUMMARY_IT = os.getenv("SUMMARY_IT")  # IT振り返り
SUMMARY_BUSINESS = os.getenv("SUMMARY_BUSINESS")  # 経済振り返り

RSS_IT = "https://news.yahoo.co.jp/rss/categories/it.xml"
RSS_BUSINESS = "https://news.yahoo.co.jp/rss/categories/business.xml"

LOG_FILE = "today_log.json"

# ---------------- 時間判定 ----------------
def jst_now():
    return datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=9)

def active_time():
    h = jst_now().hour
    return 6 <= h < 22

# ---------------- ログ保存 ----------------
def load_log():
    if not os.path.exists(LOG_FILE):
        return {"it": [], "biz": [], "date": str(jst_now().date())}
    with open(LOG_FILE, "r") as f:
        return json.load(f)

def save_log(data):
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False)

def reset_if_new_day(log):
    today = str(jst_now().date())
    if log["date"] != today:
        return {"it": [], "biz": [], "date": today}
    return log

# ---------------- Webhook送信 ----------------
def send(webhook, text):
    if not webhook:
        print("Webhook未設定")
        return
    requests.post(webhook, json={"content": text})

# ---------------- AI要約テンプレ ----------------
def ai_template_summary(title, desc, link):
    prompt = f"""
以下のニュースをテンプレ形式で書いてください。

【ニュース要約】
→ 何が起きたか

【影響】
→ 社会・業界への影響

【チャンス】
→ ビジネスや投資の視点

【ひとこと解説】
→ 人間っぽい一言コメント

ニュース:
タイトル: {title}
内容: {desc}
URL: {link}
"""
    res = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return res.choices[0].message.content

# ---------------- 22時まとめ ----------------
def ai_daily_summary(log, log_type):
    today = jst_now()
    date_str = f"{today.year}年{today.month}月{today.day}日"

    news_list = log["it"] if log_type == "it" else log["biz"]

    prompt = f"""
今日のニュースを振り返って、
「{date_str} の { 'IT' if log_type=='it' else '経済' }まとめ」を作ってください。
ニュース一覧:
{news_list}
読みやすく、要点だけまとめてください。
"""

    res = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    return res.choices[0].message.content

# ---------------- ニュース処理 ----------------
def process_feed(rss, webhook_news, webhook_summary, log_key):
    feed = feedparser.parse(rss)
    if not feed.entries:
        return
    entry = feed.entries[0]
    title = entry.title
    link = entry.link
    desc = entry.get("summary", "")

    send(webhook_news, f"📰 {title}\n{link}")

    log = load_log()
    log = reset_if_new_day(log)
    log[log_key].append(title)
    save_log(log)

    wait = random.randint(600, 1800)  # 10〜30分ランダム
    print("要約待機", wait)
    time.sleep(wait)

    summary = ai_template_summary(title, desc, link)
    send(webhook_summary, summary)

# ---------------- メインループ ----------------
print("ニュースBot起動")

while True:
    now = jst_now()
    hour = now.hour
    minute = now.minute

    log = load_log()
    log = reset_if_new_day(log)
    save_log(log)

    # 🔥 22時の振り返り
    if hour == 22 and minute < 5:
        print("22時まとめ投稿")
        summary_it = ai_daily_summary(log, "it")
        summary_biz = ai_daily_summary(log, "biz")
        send(SUMMARY_IT, f"📊 {now.year}年{now.month}月{now.day}日 ITまとめ\n{summary_it}")
        send(SUMMARY_BUSINESS, f"📊 {now.year}年{now.month}月{now.day}日 経済まとめ\n{summary_biz}")

        # 二重投稿防止
        time.sleep(600)
        continue

    # 通常ニュース時間
    if active_time():
        print("ニュース取得開始")
        process_feed(RSS_IT, WEBHOOK_IT, SUMMARY_IT, "it")
        process_feed(RSS_BUSINESS, WEBHOOK_BUSINESS, SUMMARY_BUSINESS, "biz")
    else:
        print("時間外")

    time.sleep(3600)
