import os
import feedparser
import asyncio
import datetime
import discord
import random
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
WEBHOOK_IT_SUMMARY = os.getenv("WEBHOOK_IT_SUMMARY")
WEBHOOK_BUSINESS_SUMMARY = os.getenv("WEBHOOK_BUSINESS_SUMMARY")
WEBHOOK_DAILY_REVIEW = os.getenv("WEBHOOK_DAILY_REVIEW")

FEEDS = {
    "IT": [
        "https://news.yahoo.co.jp/rss/topics/it.xml"
    ],
    "BUSINESS": [
        "https://news.yahoo.co.jp/rss/topics/business.xml",
        "https://news.yahoo.co.jp/rss/topics/economy.xml"  # 予備RSS
    ]
}

def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def send_webhook(url, content):
    if not url:
        print("[WARNING] Webhook未設定")
        return
    try:
        webhook = discord.SyncWebhook.from_url(url)
        webhook.send(content)
        print("[OK] 投稿:", c
