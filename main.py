import discord
from discord.ext import tasks
import os

TOKEN = os.getenv("DISCORD_TOKEN")

# ▼ ここに自分のチャンネルIDを入れる
IT_CHANNEL_ID = 123456789012345678
BUSINESS_CHANNEL_ID = 123456789012345678

intents = discord.Intents.default()
bot = discord.Client(intents=intents)


async def safe_send(channel_id, message):
    channel = bot.get_channel(channel_id)

    if channel is None:
        print(f"[ERROR] チャンネル取得失敗: {channel_id}")
        return

    try:
        await channel.send(message)
        print("[OK] 投稿成功")
    except Exception as e:
        print(f"[ERROR] 送信失敗: {e}")


async def fetch_and_post(topic):
    # ▼ 仮のニュース（ここにRSS処理を入れる）
    title = "サンプルニュース"
    url = "https://example.com"

    template = f"""{topic}トピック
タイトル：{title}
原文：{url}
要約：
解説："""

    if topic == "IT":
        await safe_send(IT_CHANNEL_ID, template)

    if topic == "BUSINESS":
        await safe_send(BUSINESS_CHANNEL_ID, template)


@tasks.loop(minutes=10)
async def news_loop():
    print("🔍 ニュース取得開始")

    await fetch_and_post("IT")
    await fetch_and_post("BUSINESS")

    print("🔍 投稿完了")


@bot.event
async def on_ready():
    print(f"✅ ログイン成功: {bot.user}")
    news_loop.start()


bot.run(TOKEN)

