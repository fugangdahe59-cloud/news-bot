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
        p
