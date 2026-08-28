import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# أمر السلاش
@bot.tree.command(name="ping", description="فحص استجابة البوت")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! البوت شغال 100%")

# أمر عادي لمزامنة أوامر السلاش فوراً في السيرفر الحالي
@bot.command()
async def sync(ctx):
    try:
        bot.tree.copy_global_to(guild=ctx.guild)
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"✅ تمت مزامنة {len(synced)} أمر في هذا السيرفر بنجاح!")
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ أثناء المزامنة: {e}")

@bot.command()
async def t(ctx):
    await ctx.send('البوت شغال 100% 🎯')

bot.run(os.getenv('TOKEN'))
