import os
import asyncio
from datetime import datetime, time
import feedparser
import discord
from discord.ext import tasks, commands

# ==== 環境変数からトークン取得 ====
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("環境変数DISCORD_TOKENにトークンを設定してください。")

# ==== Discord Bot 初期化 ====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==== RSSリンク ====
RSS_FEEDS = {
    "IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "BUSINESS": "https://news.yahoo.co.jp/rss/topics/business.xml"
}

# ==== 投稿先チャンネルID（環境に合わせて設定） ====
CHANNELS = {
    "IT": int(os.getenv("CHANNEL_IT", 0)),
    "BUSINESS": int(os.getenv("CHANNEL_BUSINESS", 0)),
    "IT_SUMMARY": int(os.getenv("CHANNEL_IT_SUMMARY", 0)),
    "BUSINESS_SUMMARY": int(os.getenv("CHANNEL_BUSINESS_SUMMARY", 0)),
    "DAILY_REVIEW": int(os.getenv("CHANNEL_DAILY_REVIEW", 0))
}

# ==== 投稿制御 ====
STOP_HOUR = 22  # 22時で配信停止

# ==== RSS取得と投稿関数 ====
async def fetch_and_post(topic):
    feed = feedparser.parse(RSS_FEEDS[topic])
    for entry in feed.entries:
        channel = bot.get_channel(CHANNELS[topic])
        summary_channel = bot.get_channel(CHANNELS[f"{topic}_SUMMARY"])
        url = entry.link
        title = entry.title

        # まずトピック投稿
        await channel.send(f"{topic}トピック\nタイトル：{title}\n原文：{url}\n要約：\n解説：")

        # 要約生成（ここは仮置き。OpenAI API等を呼ぶ場合はtry/exceptで安全に）
        try:
            # 例: 要約生成に失敗することを想定
            raise Exception("要約生成失敗")
        except:
            await summary_channel.send(f"{topic}要約\nタイトル：{title}\n原文：{url}\n要約：\n解説：\n要約解説失敗")

# ==== 1日の振り返り ====
async def post_daily_review():
    channel = bot.get_channel(CHANNELS["DAILY_REVIEW"])
    today = datetime.now().strftime("%Y-%m-%d")
    await channel.send(f"📝 1日の振り返り ({today})\n--- IT ---\n- 本日の投稿まとめ\n--- BUSINESS ---\n- 本日の投稿まとめ")

# ==== 定期タスク ====
@tasks.loop(minutes=10)
async def news_loop():
    now = datetime.now()
    if now.hour >= STOP_HOUR:
        print(f"{STOP_HOUR}時を超えたため配信停止")
        return
    for topic in ["IT", "BUSINESS"]:
        await fetch_and_post(topic)
    # 1日の終わり（例: 21:50頃に振り返り）
    if now.hour == STOP_HOUR - 1 and now.minute >= 50:
        await post_daily_review()

@bot.event
async def on_ready():
    print(f"🔍 ニュースBot起動: {bot.user}")
    news_loop.start()

bot.run(TOKEN)
