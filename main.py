def generate_daily_summary(daily_news):
    summary_lines = []

    # ITニュース総括
    it_articles = daily_news.get("IT", [])
    if it_articles:
        it_titles = [a.title for a in it_articles]
        summary_lines.append(
            f"ITニュースは「{it_titles[0]}」などが中心"
            + ("、その他話題も含む" if len(it_titles) > 1 else "")
        )

    # BUSINESSニュース総括
    bus_articles = daily_news.get("BUSINESS", [])
    if bus_articles:
        bus_titles = [a.title for a in bus_articles]
        summary_lines.append(
            f"BUSINESSニュースは「{bus_titles[0]}」などが注目"
            + ("、その他話題も含む" if len(bus_titles) > 1 else "")
        )

    # 全体総括
    if it_articles or bus_articles:
        summary_lines.append("全体として社会・経済両面で注目度の高いニュースが集まった日")

    return "\n".join(summary_lines)


def post_daily_review(daily_news):
    now = now_jst().strftime("%Y-%m-%d")
    content = f"📝 1日の振り返り ({now})\n\n"

    # 記事リスト
    for cat in ["IT", "BUSINESS"]:
        entries = daily_news.get(cat, [])
        if entries:
            content += f"【{cat}ニュース】\n"
            for e in entries:
                content += f"💡 {e.title}\n"
                content += f"🔗 {e.link}\n\n"

    # 自動生成総括（切り形）
    content += "【総括】\n"
    content += generate_daily_summary(daily_news)

    send_webhook(WEBHOOK_DAILY_REVIEW, content)
