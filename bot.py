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

# ==================== بيانات اللعبة الأولى: الأسئلة ====================
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

# ==================== بيانات اللعبة الثانية: لو خيروك ====================
WOULD_YOU_RATHER = [
    ("تاكل بصلة كاملة نية 🧅", "تاكل ليمونة كاملة بقشرها 🍋"),
    ("تسافر للمستقبل وتشوف حياتك 🚀", "ترجع للماضي وتصلح أغلاطك ⏳"),
    ("تكون عندك قدرة الطيران 🦅", "تكون عندك قدرة الاختفاء 👻"),
    ("تعيش بسيرفر بدون صوت نهائياً 🔇", "تعيش بسيرفر بدون شات نهائياً 🔕"),
    ("تخسر كل فلوسك بالبوت 💰", "يتصفر مستواك والرتبة مالتك 📉"),
    ("تعيش بقصر وحدك مدى الحياة 🏰", "تعيش بيت صغير بس مع أصدقائك 🏠"),
    ("تصير مشهور جداً وكل الناس تعرفك 🌟", "تصير غني جداً بس محد يعرفك 💵")
]


# ==================== [اللعبة 1] لابي الأسئلة والصراحة ====================
class QuestionsLobbyView(discord.ui.View):
    def __init__(self, host: discord.User):
        super().__init__(timeout=300)
        self.host = host
        self.players = [host]
        self.mode = "🟢 عادي"

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

    def generate_embed(self) -> discord.Embed:
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

    @discord.ui.button(label="إيقاف 🛑", style=discord.ButtonStyle.danger, row=1)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # التحقق إذا كان الضاغط هو المنظم أو أدمن في السيرفر
        is_admin = interaction.user.guild_permissions.administrator if interaction.guild else False
        if interaction.user != self.host and not is_admin:
            await interaction.response.send_message("❌ فقط منظم اللعبة أو المسؤولين يمكنهم إيقاف اللعبة!", ephemeral=True)
            return

        embed = discord.Embed(
            title="🛑 تم إيقاف اللعبة",
            description=f"قام {interaction.user.mention} بإيقاف وإلغاء الجلسة الحالية.",
            color=discord.Color.red()
        )
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)


# ==================== [اللعبة 2] لابي لعبة لو خيروك ====================
class WouldYouRatherLobbyView(discord.ui.View):
    def __init__(self, host: discord.User):
        super().__init__(timeout=300)
        self.host = host
        self.players = [host]

    def generate_embed(self) -> discord.Embed:
        players_list = "\n".join([f"• {p.display_name}" for p in self.players])
        embed = discord.Embed(
            title="🆚 لعبة لو خيروك",
            description=f"اختر قرارك المصيري الصعب!\n\n👥 **اللاعبين المنضمين ({len(self.players)})**\n{players_list}\n\n**المنظم:** {self.host.mention}",
            color=discord.Color.from_rgb(255, 140, 0)
        )
        return embed

    async def update_lobby(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="انضمام 🏃", style=discord.ButtonStyle.success, row=0)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            await interaction.response.send_message("❌ أنت منضم بالفعل!", ephemeral=True)
            return
        self.players.append(interaction.user)
        await self.update_lobby(interaction)

    @discord.ui.button(label="خروج 🚪", style=discord.ButtonStyle.secondary, row=0)
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.players:
            await interaction.response.send_message("❌ أنت لست بالقائمة!", ephemeral=True)
            return
        if interaction.user == self.host:
            await interaction.response.send_message("❌ المنظم لا يمكنه الخروج!", ephemeral=True)
            return
        self.players.remove(interaction.user)
        await self.update_lobby(interaction)

    @discord.ui.button(label="بدء 🚀", style=discord.ButtonStyle.primary, row=0)
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            await interaction.response.send_message("❌ فقط المنظم يمكنه بدء اللعبة!", ephemeral=True)
            return

        chosen_player = random.choice(self.players)
        option_a, option_b = random.choice(WOULD_YOU_RATHER)

        embed = discord.Embed(
            title=f"🆚 لو خيروك يا {chosen_player.display_name}",
            description=f"**الخيار الأول (🔵):**\n`{option_a}`\n\n**الخيار الثاني (🔴):**\n`{option_b}`",
            color=discord.Color.gold()
        )
        embed.set_footer(text="اختر أحد الخيارين وبدون تراجع!")
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="إيقاف 🛑", style=discord.ButtonStyle.danger, row=0)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = interaction.user.guild_permissions.administrator if interaction.guild else False
        if interaction.user != self.host and not is_admin:
            await interaction.response.send_message("❌ فقط منظم اللعبة أو المسؤولين يمكنهم إيقاف اللعبة!", ephemeral=True)
            return

        embed = discord.Embed(
            title="🛑 تم إيقاف اللعبة",
            description=f"قام {interaction.user.mention} بإيقاف وإلغاء الجلسة الحالية.",
            color=discord.Color.red()
        )
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)


# ==================== منيو الاختيار الرئيسي ====================
class MainGameSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="لعبة الأسئلة والصراحة", description="3 مستويات: عادي، متوسط، وجريء جداً", emoji="🎯"),
            discord.SelectOption(label="لعبة لو خيروك", description="خيارات صعبة ومواقف محرمة", emoji="🆚"),
            discord.SelectOption(label="قريباً...", description="مكان مخصص للعبتك القادمة", emoji="⏳")
        ]
        super().__init__(placeholder="اختر لعبة من المنيو لتشغيلها...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        if "الأسئلة" in selected:
            lobby_view = QuestionsLobbyView(host=interaction.user)
            await interaction.response.edit_message(embed=lobby_view.generate_embed(), view=lobby_view)
        elif "لو خيروك" in selected:
            lobby_view = WouldYouRatherLobbyView(host=interaction.user)
            await interaction.response.edit_message(embed=lobby_view.generate_embed(), view=lobby_view)
        else:
            await interaction.response.send_message("⏳ هذه الخانة مخصصة للعبة القادمة!", ephemeral=True)


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
        title="🎮 قائمة الألعاب المتاحة",
        description="اختر إحدى الألعاب التالية من المنيو بالأسفل:\n\n"
                    "🎯 **1. لعبة الأسئلة والصراحة**\n"
                    "أسئلة تفاعلية بـ 3 مستويات (عادي، متوسط، جريء جداً 🔥)\n\n"
                    "🆚 **2. لعبة لو خيروك**\n"
                    "تخيير اللاعبين بين خيارين صعبين ومضحكين!",
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
    print(f"✅ البوت {bot.user} جاهز ومزود بـ زر إيقاف اللعبة 🛑!")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
