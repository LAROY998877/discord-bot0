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
        print(f"تمت مزامنة {len(synced)} أمر بنجاح.")
    except Exception as e:
        print(f"خطأ في المزامنة: {e}")

# ربط الأمر بالسيرفر مباشرة من خلال المعرف (guild=MY_GUILD)
@bot.tree.command(name="test", description="Test bot response", guild=MY_GUILD)
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("البوت شغال 100% 🎯")

@bot.command()
async def t(ctx):
    await ctx.send('البوت شغال 100% 🎯')

bot.run(os.getenv('TOKEN'))
