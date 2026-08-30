import os
import random
import discord
from discord.ext import commands
from discord import app_commands
from pymongo import MongoClient

# ==================== الاتصال بـ MongoDB ====================
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["discord_bot_db"]
users_col = db["users"]

# ==================== إعدادات البوت ====================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# ==================== بنك الأسئلة للمستويات ====================
QUESTIONS = {
    "normal": [
        "شنو أكثر شيء تحبه بشخصيتك وترتاحله؟",
        "شنو طموحك المستقبلي اللي محد يعرفه عنك؟",
        "شنو أكره أكلة عندك ومستحيل تأكلها؟",
        "شنو الموقف المحرج اللي صار وياك بالمدرسة أو الكلية؟",
        "شنو أكثر موقف ضحكت عليه من قلبك وما تنساه؟",
        "شنو هو البلد اللي تتمنى تسافرله وتعيش بيه؟",
        "شنو أول شيء تسويه أول ما تقعد من النوم؟"
    ],
    "medium": [
        "شنو أكبر سر خبيته عن أهلك لحد هسّه؟",
        "شنو الكذبة اللي كذبتها ومحد اكتشفها لحد اليوم؟",
        "منو الشخص الموجود بالسيرفر وتتمنى تحجي وياه بس مستحي؟",
        "شنو الموقف اللي ندمت عليه بحياتك وتتمنى تمسحه تماماً؟",
        "هل دخلت بعلاقة بعمرك وحسيت نفسك مظلوم بيها؟",
        "شنو الصفة اللي بيك واللي كل الناس تشتكي منها؟",
        "هل قد فتحت جهاز شخص قريب عليك وبحثت برسائله بدون علمه؟"
    ],
    "bold": [
        "شنو الشي المحرج أو العيب اللي سويته بحياتك وبقى سر بس بينك وبين نفسك؟",
        "هل قد حبيت شخص من طرف واحد وتعرّضت للرفض؟ شنو صار؟",
        "منو أكثر شخص موجود بالسيرفر تحس عندك انجذاب خاص إله؟",
        "شنو الصفة الخاصة والجريئة جداً اللي تدورها بشريك حياتك ومستحي تعترف بيها؟",
        "شنو أغرب شيء سويته لما كنت وحدك بالبيت ومحد يشوفك؟",
        "هل جربت تبكي بالليل بسبب شخص وتظاهرت باللامبالاة ثاني يوم أمام الناس؟",
        "هل خنت ثقة شخص قريب منك جداً وما اعترفتله لحد هسّه؟",
        "شنو أجرأ تصرف سويته بحياتك وما تقدر تقوله لأهلك إطلاقاً؟"
    ]
}

# ==================== واجهة اختيار مستويات الأسئلة ====================
class QuestionsLevelView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=60)
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ هذه القائمة ليست لك! استخدم أمر `/العاب` الخاص بك.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🟢 مستوى عادي", style=discord.ButtonStyle.success)
    async def normal_level(self, interaction: discord.Interaction, button: discord.ui.Button):
        q = random.choice(QUESTIONS["normal"])
        embed = discord.Embed(
            title="🎯 لعبة الأسئلة - المستوى العادي",
            description=f"**سؤالك هو:**\n\n💬 `{q}`",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"اللاعب: {interaction.user.display_name}")
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="🟡 مستوى متوسط", style=discord.ButtonStyle.warning)
    async def medium_level(self, interaction: discord.Interaction, button: discord.ui.Button):
        q = random.choice(QUESTIONS["medium"])
        embed = discord.Embed(
            title="🎯 لعبة الأسئلة - المستوى المتوسط",
            description=f"**سؤالك هو:**\n\n💬 `{q}`",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"اللاعب: {interaction.user.display_name}")
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="🔴 مستوى جريء جداً 🔥", style=discord.ButtonStyle.danger)
    async def bold_level(self, interaction: discord.Interaction, button: discord.ui.Button):
        q = random.choice(QUESTIONS["bold"])
        embed = discord.Embed(
            title="🔥 لعبة الأسئلة - المستوى الجريء جداً",
            description=f"**سؤالك الجريء هو:**\n\n😈 `{q}`",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"اللاعب: {interaction.user.display_name} | جاوب بصراحة!")
        await interaction.response.edit_message(embed=embed, view=None)


# ==================== القائمة الرئيسية للألعاب ====================
class MainGamesView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=60)
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ هذه القائمة ليست لك! استخدم أمر `/العاب` الخاص بك.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="❓ لعبة الأسئلة (صراحة / جرأة)", style=discord.ButtonStyle.primary, emoji="🎯")
    async def questions_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎯 لعبة الأسئلة والصراحة",
            description="اختر المستوى الذي تجرؤ على الإجابة عليه من الأزرار أدناه:",
            color=discord.Color.purple()
        )
        view = QuestionsLevelView(author=self.author)
        await interaction.response.edit_message(embed=embed, view=view)


# ==================== أمر السلاش الرئيسي للألعاب ====================
@bot.tree.command(name="العاب", description="قائمة الألعاب التفاعلية في السيرفر")
async def games_menu(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 قائمة الألعاب",
        description="مرحباً بك في قسم الألعاب! اختر اللعبة التي تريدها من الأزرار في الأسفل:",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    
    view = MainGamesView(author=interaction.user)
    await interaction.response.send_message(embed=embed, view=view)


# ==================== المزامنة والتشغيل ====================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ البوت شغال وجاهز كـ {bot.user} ومربوط بـ MongoDB!")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
