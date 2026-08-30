import os
import random
import discord
from discord.ext import commands
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

# ==================== أسئلة اللعبة (المستويات الثلاثة) ====================
QUESTIONS = {
    "🟢 عادي": [
        "شنو أكثر شيء تحبه بشخصيتك وترتاحله؟",
        "شنو طموحك المستقبلي اللي محد يعرفه عنك؟",
        "شنو أكره أكلة عندك ومستحيل تأكلها؟",
        "شنو الموقف المحرج اللي صار وياك بالمدرسة أو الكلية؟"
    ],
    "🟡 متوسط": [
        "شنو أكبر سر خبيته عن أهلك لحد هسّه؟",
        "شنو الكذبة اللي كذبتها ومحد اكتشفها لحد اليوم؟",
        "منو الشخص الموجود بالسيرفر وتتمنى تحجي وياه بس مستحي؟",
        "هل قد فتحت جهاز شخص قريب عليك وبحثت برسائله بدون علمه؟"
    ],
    "🔴 جريء جداً 🔥": [
        "شنو الشي المحرج أو العيب اللي سويته بحياتك وبقى سر بس بينك وبين نفسك؟",
        "منو أكثر شخص موجود بالسيرفر تحس عندك انجذاب خاص إله؟",
        "شنو أغرب شيء سويته لما كنت وحدك بالبيت ومحد يشوفك؟",
        "هل خنت ثقة شخص قريب منك جداً وما اعترفتله لحد هسّه؟"
    ]
}

# ==================== لابي (غرفة انتظار) لعبة الأسئلة ====================
class QuestionsLobbyView(discord.ui.View):
    def __init__(self, host: discord.User):
        super().__init__(timeout=300)
        self.host = host
        self.players = [host]
        self.mode = "🟢 عادي"

        # منيو تحديد المود بنفس ستايل الصورة
        mode_select = discord.ui.Select(
            placeholder="اختر المود / المستوى...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="عادي", description="أسئلة خفيفة ولطيفة للجميع", emoji="🟢"),
                discord.SelectOption(label="متوسط", description="أسئلة تحتاج صراحة وشجاعة", emoji="🟡"),
                discord.SelectOption(label="جريء جداً 🔥", description="أسئلة قوية وقوية جداً وخاصة", emoji="🔴")
            ]
        )
        mode_select.callback = self.mode_callback
        self.add_item(mode_select)

    async def mode_callback(self, interaction: discord.Interaction):
        selected = interaction.data["values"][0]
        if "عادي" in selected:
            self.mode = "🟢 عادي"
        elif "متوسط" in selected:
            self.mode = "🟡 متوسط"
        else:
            self.mode = "🔴 جريء جداً 🔥"
        await self.update_lobby(interaction)

    def generate_embed() -> discord.Embed:
        players_list = "\n".join([f"• {p.display_name}" for p in self.players])
        embed = discord.Embed(
            title="🎯 لعبة الأسئلة والصراحة",
            description=f"**المود:** `{self.mode}`\n\n👥 **اللاعبين ({len(self.players)})**\n{players_list}\n\n**المنظم:** {self.host.mention}",
            color=discord.Color.from_rgb(255, 105, 180)
        )
        return embed

    async def update_lobby(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="انضمام 🏃", style=discord.ButtonStyle.success, row=1)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            await interaction.response.send_message("❌ أنت منضم بالفعل!", ephemeral=True)
            return
        self.players.append(interaction.user)
        await self.update_lobby(interaction)

    @discord.ui.button(label="خروج 🚪", style=discord.ButtonStyle.secondary, row=1)
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.players:
            await interaction.response.send_message("❌ أنت لست في قائمة اللاعبين!", ephemeral=True)
            return
        if interaction.user == self.host:
            await interaction.response.send_message("❌ المنظم لا يمكنه الخروج!", ephemeral=True)
            return
        self.players.remove(interaction.user)
        await self.update_lobby(interaction)

    @discord.ui.button(label="الشرح 📜", style=discord.ButtonStyle.secondary, row=1)
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg = "📖 **طريقة اللعب:** ينضم اللاعبون، وعند ضغط المنظم على (بدء) يختار البوت لاعباً عشوائياً ويطلعله سؤال صراحة حسَب المود المحدد!"
        await interaction.response.send_message(msg, ephemeral=True)

    @discord.ui.button(label="بدء 🚀", style=discord.ButtonStyle.primary, row=1)
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            await interaction.response.send_message("❌ فقط المنظم يمكنه بدء اللعبة!", ephemeral=True)
            return

        chosen_player = random.choice(self.players)
        question = random.choice(QUESTIONS[self.mode])

        embed = discord.Embed(
            title=f"🎯 الدور على: {chosen_player.display_name}",
            description=f"**المود:** `{self.mode}`\n\n💬 **السؤال:**\n`{question}`",
            color=discord.Color.purple()
        )
        embed.set_footer(text="جاوب بصراحة أمام الجميع!")
        await interaction.response.edit_message(embed=embed, view=None)


# ==================== منيو اختيار الألعاب الرئيسي ====================
class MainGameSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="لعبة الأسئلة والصراحة", description="3 مستويات: عادي، متوسط، جريء جداً", emoji="🎯"),
            discord.SelectOption(label="قريباً... (لعبة جديدة)", description="مكان مخصص للعبتك القادمة", emoji="⏳")
        ]
        super().__init__(placeholder="اختر لعبة من المنيو لتشغيلها...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        if "الأسئلة" in selected:
            lobby_view = QuestionsLobbyView(host=interaction.user)
            await interaction.response.edit_message(embed=lobby_view.generate_embed(), view=lobby_view)
        else:
            await interaction.response.send_message("⏳ هذه القائمة جاهزة لإضافة لعبتك القادمة فوراً!", ephemeral=True)


# ==================== الواجهة الرئيسية للألعاب ====================
class MainGamesView(discord.ui.View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=180)
        self.author = author
        self.add_item(MainGameSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ القائمة ليست لك! اكتب `/العاب` لفتح قائمتك.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="الرئيسية 🏠", style=discord.ButtonStyle.secondary, row=1)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = generate_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)


def generate_main_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎮 قائمة الألعاب",
        description="اختر لعبة من المنيو أدناه لتبدأ اللعب فوراً بالتصميم الفخم!\n\n"
                    "🎯 **لعبة الأسئلة والصراحة**\n"
                    "تشمل 3 مستويات (عادي، متوسط، وجريء جداً 🔥)\n\n"
                    "💡 **ملاحظة:** اختر اللعبة من المنيو بالأسفل وستفتح لك غرفة الانتظار المخصصة.",
        color=discord.Color.from_rgb(255, 105, 180)
    )
    return embed


# ==================== أمر السلاش الرئيسي ====================
@bot.tree.command(name="العاب", description="عرض منيو الألعاب الفخم")
async def games_command(interaction: discord.Interaction):
    embed = generate_main_embed()
    view = MainGamesView(author=interaction.user)
    await interaction.response.send_message(embed=embed, view=view)


# ==================== التشغيل ====================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ البوت {bot.user} جاهز وشغال بالتصميم المطابق 100%!")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
