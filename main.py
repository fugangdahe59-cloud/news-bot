async def main_loop():
    print("ニュースBot起動")
    
    # 起動直後に投稿
    await fetch_and_post()
    
    while True:
        now = now_jst()
        # 22時の振り返りチェック
        if now.hour == 22 and now.minute == 0:
            if daily_news:
                content = f"【今日の振り返り】{now.year}年{now.month}月{now.day}日\n\n"
                content += "\n".join([f"[{c}] {t} ({l})" for c, t, l in daily_news])
                await send_webhook(SUMMARY_DAILY, content)
                daily_news.clear()
            await asyncio.sleep(60)

        # 6時〜22時のニュース取得
        if 6 <= now.hour < 22:
            await fetch_and_post()
        
        await asyncio.sleep(60) # 1分ごとにループ
