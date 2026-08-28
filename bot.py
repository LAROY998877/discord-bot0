import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

MY_GUILD = discord.Object(id=1297951366261510186)

# أمر السلاش الجديد باسم مختلف تماماً
@discord.app_commands.command(name="ping", description="فحص استجابة البوت")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! البوت شغال 100%")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        # 1. مسح جميع الأوامر العامة القديمة
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        
        # 2. مسح أوامر السيرفر وإضافة الأمر الجديد
        bot.tree.clear_commands(guild=MY_GUILD)
        bot.tree.add_command(ping, guild=MY_GUILD)
        
        synced = await bot.tree.sync(guild=MY_GUILD)
        print(f"تم مسح القديم ومزامنة {len(synced)} أمر جديد.")
    except Exception as e:
        print(f"خطأ: {e}")

@bot.command()
async def t(ctx):
    await ctx.send('البوت شغال 100% 🎯')

bot.run(os.getenv('TOKEN'))
