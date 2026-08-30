import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print("🔄 جاري إزالة جميع أوامر السلاش من سيرفرات ديسكورد...")
    
    # تفريغ شجرة الأوامر بالكامل بدون إضافة أي أمر
    bot.tree.clear_commands(guild=None)
    
    # مزامنة الشجرة الفارغة مع ديسكورد لحذف كل شيء
    await bot.tree.sync()
    
    print(f"✨ تم مسح جميع الأوامر بنجاح! البوت {bot.user} الآن فارغ ونظيف تماماً.")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
