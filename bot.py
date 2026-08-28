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
        # مسح الأوامر القديمة التالفة وتحديثها فوراً للسيرفر
        bot.tree.clear_commands(guild=MY_GUILD)
        bot.tree.copy_global_to(guild=MY_GUILD)
        synced = await bot.tree.sync(guild=MY_GUILD)
        print(f"تمت مزامنة {len(synced)} أمر بنجاح للسيرفر.")
    except Exception as e:
        print(f"خطأ في المزامنة: {e}")

@bot.tree.command(name="test", description="Test bot response")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("البوت شغال 100% 🎯")

@bot.command()
async def t(ctx):
    await ctx.send('البوت شغال 100% 🎯')

bot.run(os.getenv('TOKEN'))
