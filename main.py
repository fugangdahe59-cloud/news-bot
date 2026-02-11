import os
import datetime
import time
import random
import requests
import feedparser

# Webhook設定
WEBHOOK_IT = os.getenv("WEBHOOK_IT")
WEBHOOK_BUSINESS = os.getenv("WEBHOOK_BUSINESS")
WEBHOOK_IT_SUMMARY = os.getenv("SUMMARY_IT")
WEBHOOK_BUSINESS_SUMMARY = os.getenv("SUMMARY_BUSINESS")

# 投稿間隔（秒）
WAIT_HOURS = 1
MIN_SUMMARY_DELAY = 600  # 10分
MAX_SUMMARY_DELAY = 1800 # 30分

# JST取得関数（警告対応済み）
def jst_now():
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)

# 6時〜22時チェック
def is_posting_time():
    hour = jst_now().hour
    return 6 <= hour < 22

# Discord Webhook送信
def post_to_discord(webhook_url, title, content):
    if not webhook_url:
        print("Webhook未設定")
        return
    data = {
        "content": f"【ニュース】{title}\n{content}"
    }
    try:
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()
        print(f"投稿成功: {title}")
    except Exception as e:
        print(f"[ERROR] 投稿失敗: {e}")

# AI要約（ダミー関数、OpenAI等に置き換え可）
def generate_summary(title, content):
    # 実際にはOpenAI API等を使って要約を生成
    summary_template = f"""【ニュース要約】
{title}

【影響】
{content[:50]}...

【チャンス】
可能性あり

【ひとこと解説】
簡単な解説をここに"""
    return summary_template

# メインループ
def main():
    print("ニュースBot起動")
    while True:
        if is_posting_time():
            # RSS例（置き換え可）
            feed = feedparser.parse("https://example.com/rss") # 実際のRSSに変更
            posted_titles = set()  # 同じニュースの二重投稿防止

            for entry in feed.entries:
                if entry.title in posted_titles:
                    continue
                posted_titles.add(entry.title)

                post_to_discord(WEBHOOK_IT, entry.title, entry.summary)
                
                # ランダム待機後に要約を別チャンネルに投稿
                delay = random.randint(MIN_SUMMARY_DELAY, MAX_SUMMARY_DELAY)
                print(f"[IT] 要約待機 {delay}秒")
                time.sleep(delay)
                
                summary = generate_summary(entry.title, entry.summary)
                post_to_discord(WEBHOOK_IT_SUMMARY, entry.title, summary)

                post_to_discord(WEBHOOK_BUSINESS, entry.title, entry.summary)
                print(f"[BUSINESS] 要約待機 {delay}秒")
                time.sleep(delay)
                post_to_discord(WEBHOOK_BUSINESS_SUMMARY, entry.title, summary)

        else:
            print(f"夜間停止中（{jst_now().hour}:00）")
        print(f"{WAIT_HOURS}時間待機...")
        time.sleep(WAIT_HOURS * 3600)

if __name__ == "__main__":
    main()
