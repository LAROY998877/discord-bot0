import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

MY_GUILD = discord.Object(id=1297951366261510186)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync(guild=MY_GUILD)
        print(f"Synced {len(synced)} commands to guild successfully.")
    except Exception as e:
        print(f"Sync error: {e}")

# أمر السلاش الأول
@bot.tree.command(name="test", description="Test bot response", guild=MY_GUILD)
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("Bot is working 100% with Slash! 🎯")

# أمر السلاش الثاني
@bot.tree.command(name="dev", description="Developer panel", guild=MY_GUILD)
async def dev(interaction: discord.Interaction):
    await interaction.response.send_message("Welcome to developer panel! 🛠️")

# الأمر العادي الاحتياطي
@bot.command()
async def t(ctx):
    await ctx.send('Hello! The bot is working 100% 🎯')

bot.run(os.getenv('TOKEN'))
