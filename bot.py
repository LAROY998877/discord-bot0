import os
import discord
from discord.ext import commands
from discord.ui import Select, View

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# قائمة الألعاب المنسقة والتفاعلية
class GamesSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="لعبة X-O", description="لعبة التحدي الكلاسيكية", emoji="❌"),
            discord.SelectOption(label="حجر ورقة مقص", description="اللعبة السريعة الشهيرة", emoji="✂️"),
            discord.SelectOption(label="تخمين الرقم", description="اختبر حظك وذكائك", emoji="🔢"),
        ]
        super().__init__(placeholder="اختر اللعبة اللعينة التي تريدها...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        game_name = self.values[0]
        await interaction.response.send_message(f"لقد اخترت: **{game_name}**! سيتم تفعيلها قريباً يا العظيم لار.", ephemeral=True)

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
    await bot.tree.sync()
    print(f"تم تسجيل الدخول بنجاح: {bot.user} والأوامر تعمل بكفاءة!")

token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("تباً! لم يتم العثور على متغير DISCORD_TOKEN في البيئة.")

bot.run(token)
