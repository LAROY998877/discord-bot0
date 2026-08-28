import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

MY_GUILD = discord.Object(id=1297951366261510186)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        bot.tree.copy_global_to(guild=MY_GUILD)
        synced = await bot.tree.sync(guild=MY_GUILD)
        print(f"Synced {len(synced)} commands successfully.")
    except Exception as e:
        print(f"Sync error: {e}")

@bot.tree.command(name="test", description="Test bot response")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("Bot is working 100%!")

@bot.tree.command(name="dev", description="Developer panel")
async def dev(interaction: discord.Interaction):
    await interaction.response.send_message("Welcome to developer panel!")

bot.run(os.getenv('TOKEN'))
