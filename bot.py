import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print('Bot is online and ready!')

@bot.command()
async def test(ctx):
    await ctx.send('Hello! The bot is working 100% 🎯')

bot.run(os.getenv('TOKEN'))