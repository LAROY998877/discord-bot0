import os
import discord
from discord.ext import commands
from discord.ui import Select, View

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

MY_GUILD_ID = discord.Object(id=456075967165890562)

class GamesSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="لعبة X-O", description="لعبة التحدي الكلاسيكية", emoji="❌"),
            discord.SelectOption(label="حجر ورقة مقص", description="اللعبة السريعة الشهيرة", emoji="✂️"),
            discord.SelectOption(label="تخمين الرقم", description="اختبر حظك وذكائك", emoji="🔢"),
        ]
        super().__init__(placeholder="اختر اللعبة التي تريدها...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        game_name = self.values[0]
        await interaction.response.send_message(f"لقد اخترت لعبة: **{game_name}**! سيتم تفعيلها قريباً يا العظيم لار.", ephemeral=True)

class GamesView(View):
    def __init__(self):
        super().__init__()
        self.add_item(GamesSelect())

@bot.tree.command(name="الألعاب", description="قائمة منيو تفاعلية لاختيار الألعاب المتاحة في البوت")
async def games_menu(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 قائمة الألعاب المركزية",
        description="اختر إحدى اللعبات من القائمة المنسدلة أدناه للبدء بالتحدي:",
        color=discord.Color.from_rgb(255, 100, 150)
    )
    embed.set_footer(text="تم التطوير لصالح العظيم لار")
    await interaction.response.send_message(embed=embed, view=GamesView())

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح: {bot.user}")
    
    # مسح الأوامر العالمية القديمة من ديسكورد
    bot.tree.clear_commands(guild=None)
    await bot.tree.sync(guild=None)
    
    # تفريغ الأوامر وزرع أمر الألعاب حصراً في سيرفرك
    bot.tree.clear_commands(guild=MY_GUILD_ID)
    bot.tree.copy_global_to(guild=MY_GUILD_ID)
    await bot.tree.sync(guild=MY_GUILD_ID)
    print("تم تنظيف السيرفر ونسف الأوامر القديمة وزرع أمر الألعاب بنجاح!")

token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("تباً! لم يتم العثور على متغير البيئة DISCORD_TOKEN.")

bot.run(token)
