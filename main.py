import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

# ① 先に bot を作る
bot = commands.Bot(command_prefix="!", intents=intents)

# ② そのあとにコマンドを書く
@bot.command()
async def ping(ctx):
    await ctx.send("pong")
