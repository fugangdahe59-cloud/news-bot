import os
import discord
import asyncio
import random
from datetime import datetime, timezone, timedelta
from openai import OpenAI
import aiohttp

# 環境変数
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
SUMMARY_IT = os.getenv("SUMMARY_IT")
SUMMARY_BUSINESS = os.getenv("SUMMARY_BUSINESS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai = OpenAI(api_key=OPENAI_API_KEY)

async def generate_summary(title, link):
    prompt = f"""ニュースタイトル: {title}
URL: {link}

以下のテンプレでニュースをまとめてください。人間っぽく、具体的に。

【ニュース要約】
〜〜〜

【影響】
〜〜〜

【チャンス】
〜〜〜

【ひとこと解説】
〜〜〜
"""
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
    )
    return response.choices[0].message.content

# SyncWebhook + aiohttp で非同期に投稿
async def send_webhook(url, content):
    async with aiohttp.ClientSession() as session:
        webhook = discord.SyncWebhook.from_url(url, adapter=discord.RequestsWebhookAdapter())
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: webhook.send(content))

async def test_post():
    news_list = [
        ("IT", "GeForce RTX 50シリーズ購入キャンペーン", "https://example.com/news1"),
        ("BUSINESS", "シャープ亀山第2工場 売却不成立", "https://example.com/news2")
    ]

    for category, title, link in news_list:
        target_webhook = WEBHOOK_IT if category == "IT" else WEBHOOK_BUSINESS
        summary_webhook = SUMMARY_IT if category == "IT" else SUMMARY_BUSINESS

        # ニュース投稿
        await send_webhook(target_webhook, f"[{category}] 投稿: {title} ({link})")
        print(f"[{category}] 投稿済み: {title}")

        # 待機
        await asyncio.sleep(random.randint(10, 30))

        # 要約投稿
        summary = await generate_summary(title, link)
        await send_webhook(summary_webhook, summary)
        print(f"[{category}] 要約投稿済み: {title}")

if __name__ == "__main__":
    asyncio.run(test_post())
