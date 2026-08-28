import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"🟢 البوت يعمل الآن: {bot.user}")

# أمر جذري لمسح جميع الأوامر بالكامل
@bot.command(name="مسح_الكل")
async def clear_all_commands(ctx):
    try:
        # 1. مسح الأوامر الخاصة بالسيرفر الحالي
        bot.tree.clear_commands(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        
        # 2. مسح الأوامر العامة على مستوى البوت بالكامل
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        
        await ctx.send("🗑️ **تم مسح وحذف جميع الأوامر القديمة بنجاح تام!** البوت الآن خالي تماماً من أي أوامر سابقة.")
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ أثناء الحذف: {e}")

bot.run(os.getenv('TOKEN'))
