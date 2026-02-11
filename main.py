import asyncio
import feedparser
import datetime
import discord
from discord.ext import tasks, commands
import openai
import os

# ==== Discord設定 ====
TOKEN = "YOUR_DISCORD_BOT_TOKEN"
IT_CHANNEL_ID = 123456789012345678       # ITニュース投稿チャンネル
BUSINESS_CHANNEL_ID = 234567890123456789 # ビジネスニュース投稿チャンネル
IT_SUMMARY_CHANNEL_ID = 345678901234567890   # IT要約解説チャンネル
BUSINESS_SUMMARY_CHANNEL_ID = 456789012345678901 # ビジネス要約解説チャンネル

# ==== OpenAI設定 ====
openai.api_key = os.getenv("OPENAI_API_KEY")  # 環境変数にAPIキーを設定

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ==== RSS URL ====
IT_RSS = "https://news.yahoo.co.jp/rss/topics/it.xml"
BUSINESS_RSS = "https://news.yahoo.co.jp/rss/topics/business.xml"

# ==== 配信終了時刻 ====
END_HOUR = 22

# ニュース保持用
posted_news = {"IT": set(), "BUSINESS": set()}

# ==== 要約・解説生成 ====
async def generate_summary_and_analysis(title, url):
    """
    OpenAI GPTで要約と解説を生成
    失敗した場合は None を返す
    """
    try:
        prompt = f"""
        以下のニュースタイトルとURLをもとに要約と解説を作成してください。
        ニュースタイトル: {title}
        URL: {url}

        フォーマット:
        要約: <ここに要約>
        解説: <ここに解説>
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.5
        )
        text = response.choices[0].message.content.strip()
        # 分割して要約・解説に
        if "要約:" in text and "解説:" in text:
            summary = text.split("要約:")[1].split("解説:")[0].strip()
            analysis = text.split("解説:")[1].strip()
            return summary, analysis
        else:
            return None, None
    except Exception as e:
        print(f"[ERROR] 要約生成失敗: {e}")
        return None, None

# ==== ニュース取得と投稿 ====
async def fetch_and_post_news(topic):
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

    failed_posts = []

    for entry in feed.entries:
        title = entry.title
        url = entry.link

        # 重複投稿チェック
        if url in posted_news[topic]:
            continue
        posted_news[topic].add(url)

        # まずニューステンプレ投稿
        news_message = f"{topic}トピック\nタイトル：{title}\n原文：{url}\n要約：\n解説："
        await channel.send(news_message)

        # 要約解説生成
        summary, analysis = await generate_summary_and_analysis(title, url)

        if summary and analysis:
            message = f"{topic}要約\nタイトル：{title}\n原文：{url}\n要約：{summary}\n解説：{analysis}"
            await summary_channel.send(message)
        else:
            # 失敗時は一番下にまとめる
            failed_posts.append(f"{topic}トピック\nタイトル：{title}\n原文：{url}\n要約：\n解説：\n要約解説失敗")

    # 失敗分は最後にまとめて送信
    for fail_msg in failed_posts:
        await summary_channel.send(fail_msg)

# ==== 定期タスク ====
@tasks.loop(minutes=5)
async def news_loop():
    now = datetime.datetime.now()
    if now.hour >= END_HOUR:
        print(f"🔍 {END_HOUR}時を超えたため配信停止中")
        return

    await fetch_and_post_news("IT")
    await fetch_and_post_news("BUSINESS")

    # 最後に1日の振り返り（22時前55分以降）
    if now.hour == END_HOUR - 1 and now.minute >= 55:
        today = now.strftime("%Y-%m-%d")
        it_summary = "📝 1日の振り返り ITトピック\n" + "\n".join(posted_news["IT"])
        business_summary = "📝 1日の振り返り BUSINESSトピック\n" + "\n".join(posted_news["BUSINESS"])
        it_channel = bot.get_channel(IT_CHANNEL_ID)
        business_channel = bot.get_channel(BUSINESS_CHANNEL_ID)
        await it_channel.send(it_summary)
        await business_channel.send(business_summary)

@bot.event
async def on_ready():
    print("🔍 ニュースBot起動")
    news_loop.start()

bot.run(TOKEN)
