import asyncio
import feedparser
import datetime
import discord
from discord.ext import tasks, commands
from openai import OpenAI
import os

# ==== Discord設定 ====
TOKEN = "YOUR_DISCORD_BOT_TOKEN"

IT_CHANNEL_ID = 123456789012345678
BUSINESS_CHANNEL_ID = 234567890123456789
IT_SUMMARY_CHANNEL_ID = 345678901234567890
BUSINESS_SUMMARY_CHANNEL_ID = 456789012345678901

# ==== OpenAI設定 ====
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==== Discord Bot ====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==== RSS URL ====
IT_RSS = "https://news.yahoo.co.jp/rss/topics/it.xml"
BUSINESS_RSS = "https://news.yahoo.co.jp/rss/topics/business.xml"

END_HOUR = 22

posted_news = {"IT": set(), "BUSINESS": set()}

# ==== GPT 要約 ====
async def generate_summary_and_analysis(title, url):
    try:
        prompt = f"""
以下のニュースを短く要約し、背景を簡単に解説してください。

タイトル: {title}
URL: {url}

形式:
要約:
解説:
"""

        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )

        text = response.choices[0].message.content.strip()

        if "要約:" in text and "解説:" in text:
            summary = text.split("要約:")[1].split("解説:")[0].strip()
            analysis = text.split("解説:")[1].strip()
            return summary, analysis

        return None, None

    except Exception as e:
        print(f"[ERROR] GPT生成失敗: {e}")
        return None, None


# ==== ニュース取得 ====
async def fetch_and_post_news(topic):
    try:
        if topic == "IT":
            rss_url = IT_RSS
            channel_id = IT_CHANNEL_ID
            summary_channel_id = IT_SUMMARY_CHANNEL_ID
        else:
            rss_url = BUSINESS_RSS
            channel_id = BUSINESS_CHANNEL_ID
            summary_channel_id = BUSINESS_SUMMARY_CHANNEL_ID

        feed = feedparser.parse(rss_url)

        channel = bot.get_channel(channel_id)
        summary_channel = bot.get_channel(summary_channel_id)

        if channel is None or summary_channel is None:
            print("[ERROR] チャンネル取得失敗")
            return

        for entry in feed.entries[:3]:  # 投稿多すぎ防止
            title = entry.title
            url = entry.link

            if url in posted_news[topic]:
                continue

            posted_news[topic].add(url)

            await channel.send(
                f"{topic}ニュース\nタイトル：{title}\n原文：{url}"
            )

            summary, analysis = await generate_summary_and_analysis(title, url)

            if summary and analysis:
                await summary_channel.send(
                    f"{topic}要約\nタイトル：{title}\n要約：{summary}\n解説：{analysis}"
                )
            else:
                await summary_channel.send(
                    f"{topic}要約失敗\nタイトル：{title}\n{url}"
                )

    except Exception as e:
        print(f"[ERROR] fetch失敗: {e}")


# ==== 定期ループ ====
@tasks.loop(minutes=5)
async def news_loop():
    now = datetime.datetime.now()

    if now.hour >= END_HOUR:
        print("🔒 夜間停止中")
        return

    await fetch_and_post_news("IT")
    await fetch_and_post_news("BUSINESS")

    # 21:55以降に1日まとめ
    if now.hour == END_HOUR - 1 and now.minute >= 55:
        it_channel = bot.get_channel(IT_CHANNEL_ID)
        business_channel = bot.get_channel(BUSINESS_CHANNEL_ID)

        await it_channel.send(
            "📝 今日のITニュースまとめ\n" + "\n".join(posted_news["IT"])
        )
        await business_channel.send(
            "📝 今日のビジネスニュースまとめ\n"
            + "\n".join(posted_news["BUSINESS"])
        )


@bot.event
async def on_ready():
    print("✅ ニュースBot起動")
    news_loop.start()


bot.run(TOKEN)
