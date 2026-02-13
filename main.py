import os
import feedparser
import asyncio
import datetime
import discord
import random
import requests
import openai
from bs4 import BeautifulSoup

# ===== 環境変数 =====
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
WEBHOOK_IT_SUMMARY = os.getenv("WEBHOOK_IT_SUMMARY")
WEBHOOK_BUSINESS_SUMMARY = os.getenv("WEBHOOK_BUSINESS_SUMMARY")
WEBHOOK_DAILY_REVIEW = os.getenv("WEBHOOK_DAILY_REVIEW")
openai.api_key = os.getenv("OPENAI_API_KEY")

# ===== 制限 =====
AI_LIMIT_PER_HOUR = 10
ai_calls_this_hour = 0
last_reset_hour = -1

summary_cache = {}
queue = asyncio.Queue()

# RSS
FEEDS = {
    "IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "BUSINESS": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

# JST時間
def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# Webhook送信
def send_webhook(url, content):
    if not url:
        return
    try:
        webhook = discord.SyncWebhook.from_url(url)
        webhook.send(content)
        print("[OK] 投稿:", content[:80])
    except Exception as e:
        print("[ERROR]", e)

# 記事本文取得
def fetch_article_text(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text() for p in paragraphs)
        return text[:4000]
    except:
        return ""

# AI要約
def generate_summary(entry):
    global ai_calls_this_hour, last_reset_hour

    now = now_jst()

    if now.hour != last_reset_hour:
        ai_calls_this_hour = 0
        last_reset_hour = now.hour

    if entry.link in summary_cache:
        return summary_cache[entry.link]

    if ai_calls_this_hour >= AI_LIMIT_PER_HOUR:
        return ("要約制限中", ["次の時間に再開", "", ""])

    article = fetch_article_text(entry.link)
    if not article:
        return ("本文取得失敗", ["リンク参照", "", ""])

    prompt = f"""
ニュースを短く要約してください。
3行以内＋ポイント3つ。

{article}
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.choices[0].message.content.strip()
        lines = text.split("\n")

        summary = lines[0] if lines else "要約失敗"
        points = [l.replace("・", "").strip() for l in lines[1:4]]

        while len(points) < 3:
            points.append("")

        result = (summary, points)
        summary_cache[entry.link] = result
        ai_calls_this_hour += 1

        return result

    except Exception as e:
        print("[AI ERROR]", e)
        return ("AI要約失敗", ["再試行予定", "", ""])

# 要約テンプレ
def format_summary(category, entry, summary, points):
    text = (
        f"{category}トピック\n"
        f"タイトル：{entry.title}\n"
        f"原文：{entry.link}\n"
        f"要約：{summary}\n"
        f"解説：\n"
    )

    if summary in ["AI要約失敗", "本文取得失敗", "要約制限中"]:
        text += "要約解説失敗"

    return text

# 投稿系
def post_news(category, entry):
    url = WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS
    send_webhook(url, f"{category}トピック: {entry.title}\n{entry.link}")

def post_summary(category, text):
    url = WEBHOOK_IT_SUMMARY if category == "IT" else WEBHOOK_BUSINESS_SUMMARY
    send_webhook(url, text)

# ワーカー
async def worker():
    while True:
        category, entry = await queue.get()
        await process_entry(category, entry)
        queue.task_done()

# 記事処理
async def process_entry(category, entry):
    post_news(category, entry)
    await asyncio.sleep(random.randint(600, 1800))

    summary, points = generate_summary(entry)
    text = format_summary(category, entry, summary, points)
    post_summary(category, text)

# 1日振り返り
def post_daily_review(daily_news):
    now = now_jst().strftime("%Y-%m-%d")
    content = f"📝 1日の振り返り ({now})\n\n"

    for cat in ["IT", "BUSINESS"]:
        entries = daily_news.get(cat, [])
        if entries:
            content += f"【{cat}ニュース】\n"
            for e in entries:
                content += f"💡 {e.title}\n🔗 {e.link}\n\n"

    send_webhook(WEBHOOK_DAILY_REVIEW, content)

# メイン
async def main_loop():
    daily_news = {"IT": [], "BUSINESS": []}
    posted = set()

    print("🔍 AIニュースBot起動")
    print("🧠 要約ワーカー起動")

    # ワーカー起動（最大3並列）
    for _ in range(3):
        asyncio.create_task(worker())

    while True:
        now = now_jst()

        if 6 <= now.hour < 22:
            for cat, url in FEEDS.items():
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    if entry.link in posted:
                        continue
                    posted.add(entry.link)
                    daily_news[cat].append(entry)
                    await queue.put((cat, entry))

        if now.hour >= 22 and any(daily_news.values()):
            await queue.join()
            post_daily_review(daily_news)
            daily_news = {"IT": [], "BUSINESS": []}
            posted.clear()
            await asyncio.sleep(3600)
        else:
            await asyncio.sleep(600)

# 実行
if __name__ == "__main__":
    asyncio.run(main_loop())
