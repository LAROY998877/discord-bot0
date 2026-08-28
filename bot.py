import os
import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"تم مزامنة {len(synced)} أمر بنجاح.")
    except Exception as e:
        print(e)
    print(f'البوت يعمل الآن باسم: {bot.user}')

@bot.tree.command(name="test", description="أمر تجريبي لفحص استجابة البوت عبر السلاش")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message('Hello! The bot is working 100% 🎯')

bot.run(os.getenv('TOKEN'))
