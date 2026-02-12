import json

CONFIG_FILE = "config.json"

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

config = load_config()

@bot.command()
async def setit(ctx):
    guild_id = str(ctx.guild.id)
    if guild_id not in config:
        config[guild_id] = {}

    config[guild_id]["it"] = ctx.channel.id
    save_config(config)

    await ctx.send("✅ ITニュースの投稿先を登録しました")
