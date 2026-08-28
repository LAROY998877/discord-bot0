import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

# ضع آي دي سيرفرك هنا بين القوسين بدلاً من الصفر
MY_GUILD = discord.Object(id=1297951366261510186)

@bot.event
async def on_ready():
    try:
        bot.tree.copy_global_to(guild=MY_GUILD)
        synced = await bot.tree.sync(guild=MY_GUILD)
        print(f"تمت مزامنة {len(synced)} أمر في السيرفر فوراً.")
    except Exception as e:
        print(e)
    print(f'البوت شغال الآن: {bot.user}')

@bot.tree.command(name="test", description="أمر تجريبي لفحص البوت")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("شغال 100% 🎯")

@bot.tree.command(name="لوحة_المطور", description="لوحة التحكم الخاصة بالمطور")
async def developer_board(interaction: discord.Interaction):
    await interaction.response.send_message("أهلاً بك في لوحة المطور 🛠️")

bot.run(os.getenv('TOKEN'))
