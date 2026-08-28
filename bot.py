import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"تمت مزامنة {len(synced)} أمر بنجاح.")
    except Exception as e:
        print(e)
    print(f'البوت شغال الآن: {bot.user}')

@bot.tree.command(name="test", description="أمر تجريبي لفحص البوت")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("شغال 100% 🎯")

bot.run(os.getenv('TOKEN'))
