import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول: {bot.user}")

# قراءة التوكن من المتغيرات البيئية حصراً
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("تباً! لم يتم العثور على متغير DISCORD_TOKEN في البيئة اللعينة.")

bot.run(token)
