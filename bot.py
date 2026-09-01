import os
import asyncio
import discord
from discord.ext import commands

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "ضع_توكن_البوت_هنا")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول باسم: {bot.user}")
    
    try:
        # مسح جميع الأوامر العامة من ذاكرة البوت
        bot.tree.clear_commands(guild=None)
        
        # مزامنة الشجرة الفارغة مع ديسكورد لحذف الأوامر المباشرة (Global Slash Commands)
        await bot.tree.sync()
        print("✅ تم مسح جميع الأوامر العامة (Global Commands) بنجاح من ديسكورد!")

        # مسح الأوامر المسجلة داخل السيرفرات المحددة (إن وجدت)
        for guild in bot.guilds:
            bot.tree.clear_commands(guild=guild)
            await bot.tree.sync(guild=guild)
        print("✅ تم مسح أوامر السيرفرات الخاصة (Guild Commands) بنجاح!")

    except Exception as e:
        print(f"❌ حدث خطأ أثناء مسح الأوامر: {e}")
    
    finally:
        await bot.close()

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
