import os
import discord
from discord.ext import commands
from discord.ui import Select, View

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# معرف سيرفرك بدقة لضمان ظهور الأمر فوراً
MY_GUILD_ID = discord.Object(id=456075967165890562)

class GamesSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="لعبة X-O", description="لعبة التحدي الكلاسيكية", emoji="❌"),
            discord.SelectOption(label="حجر ورقة مقص", description="اللعبة السريعة الشهيرة", emoji="✂️"),
            discord.SelectOption(label="تخمين الرقم", description="اختبر حظك وذكائك", emoji="🔢"),
        ]
        super().__init__(placeholder="اختر اللعبة...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"لقد اخترت لعبة: **{self.values[0]}**", ephemeral=True)

class GamesView(View):
    def __init__(self):
        super().__init__()
        self.add_item(GamesSelect())

@bot.tree.command(name="games-menu", description="قائمة الألعاب المركزية", guild=MY_GUILD_ID)
async def games_menu(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 قائمة الألعاب المركزية",
        description="اختر إحدى الألعاب من القائمة أدناه:",
        color=discord.Color.blue()
    )
    embed.set_footer(text="تم التطوير لصالح العظيم لار")
    await interaction.response.send_message(embed=embed, view=GamesView())

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح: {bot.user}")
    try:
        synced = await bot.tree.sync(guild=MY_GUILD_ID)
        print(f"تم بنجاح مزامنة {len(synced)} أمر في السيرفر!")
    except Exception as e:
        print(f"خطأ في المزامنة: {e}")

token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("تباً! لم يتم العثور على متغير البيئة DISCORD_TOKEN.")

bot.run(token)
