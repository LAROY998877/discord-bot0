import os
import discord
from discord.ext import commands

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "توكن_البوت_الخاص_بك")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم: {bot.user}")
    
    # 1. حذف الأوامر العامة (Global Commands)
    bot.tree.clear_commands(guild=None)
    await bot.tree.sync(guild=None)
    print("تم مسح الأوامر العامة بنجاح.")
    
    # 2. حذف الأوامر الخاصة بجميع السيرفرات التي يتواجد فيها البوت
    for guild in bot.guilds:
        bot.tree.clear_commands(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"تم مسح الأوامر من السيرفر: {guild.name}")
        
    print("✨ تم تنظيف وحذف جميع الأوامر بالكامل! يمكنك الآن إيقاف البوت وإضافة الكود الجديد الذي تريده.")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
