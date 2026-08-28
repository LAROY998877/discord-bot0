import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"🟢 البوت يعمل الآن: {bot.user}")

@bot.command(name="مسح_الكل")
async def clear_all_commands(ctx):
    try:
        # مسح أوامر السيرفر الحالي
        bot.tree.clear_commands(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        
        # مسح الأوامر العامة على مستوى البوت بالكامل
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        
        await ctx.send("🗑️ **تم مسح وحذف جميع الأوامر بنجاح تام!**")
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ: {e}")

bot.run(os.getenv('TOKEN'))
