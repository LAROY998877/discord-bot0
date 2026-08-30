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

# ==================== بنك الأسئلة ====================
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

# ==================== منيو اختيار مود اللعبة ====================
class TruthOrDareModeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="عادي", description="أسئلة خفيفة ولطيفة للجميع", emoji="🟢"),
            discord.SelectOption(label="متوسط", description="أسئلة تحتاج شوية صراحة وشجاعة", emoji="🟡"),
            discord.SelectOption(label="جريء جداً 🔥", description="أسئلة قوية وقوية جداً وخاصة", emoji="🔴")
        ]
        super().__init__(placeholder="اختر المود...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        view: TruthOrDareLobbyView = self.view
        selected_mode = self.values[0]
        if "عادي" in selected_mode:
            view.mode = "🟢 عادي"
        elif "متوسط" in selected_mode:
            view.mode = "🟡 متوسط"
        else:
            view.mode = "🔴 جريء جداً 🔥"
            
        await view.update_lobby(interaction)

# ==================== لوحة تحكم لعبة صراحة أو جرأة ====================
class TruthOrDareLobbyView(discord.ui.View):
    def __init__(self, host: discord.User):
        super().__init__(timeout=300)
        self.host = host
        self.players = [host]
        self.mode = "🟢 عادي"
        self.add_item(TruthOrDareModeSelect())

    def generate_embed(self) -> discord.Embed:
        players_list = "\n".join([f"• {p.display_name}" for p in self.players])
        embed = discord.Embed(
            title="🍾 صراحة أو جرأة",
            description=f"**المود:** `{self.mode}`\n\n👥 **اللاعبين ({len(self.players)})**\n{players_list}\n\n**المنظم:** {self.host.mention}",
            color=discord.Color.from_rgb(255, 105, 180)
        )
        return embed

    async def update_lobby(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="انضمام 🏃", style=discord.ButtonStyle.success, row=1)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            await interaction.response.send_message("❌ أنت منضم بالفعل للعبة!", ephemeral=True)
            return
        self.players.append(interaction.user)
        await self.update_lobby(interaction)

    @discord.ui.button(label="خروج 🚪", style=discord.ButtonStyle.secondary, row=1)
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.players:
            await interaction.response.send_message("❌ أنت لست ضمن قائمة اللاعبين!", ephemeral=True)
            return
        if interaction.user == self.host:
            await interaction.response.send_message("❌ المنظم لا يمكنه الخروج من اللعبة!", ephemeral=True)
            return
        self.players.remove(interaction.user)
        await self.update_lobby(interaction)

    @discord.ui.button(label="الشرح 📜", style=discord.ButtonStyle.secondary, row=1)
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg = "📖 **طريقة اللعب:**\nتنضم المجموعة للعبة، وعند الضغط على زر (بدء) يختار البوت لاعباً عشوائياً ويوجه له سؤال صراحة بناءً على المود المحدد!"
        await interaction.response.send_message(msg, ephemeral=True)

    @discord.ui.button(label="بدء 🚀", style=discord.ButtonStyle.primary, row=1)
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            await interaction.response.send_message("❌ فقط المنظم يمكنه لبدء اللعبة!", ephemeral=True)
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


# ==================== منيو الأقسام الرئيسي ====================
class MainCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="اجتماعية وضحك", description="صراحة أو جرأة، لو خيروك، شكلي لو", emoji="🎭"),
            discord.SelectOption(label="ذكاء وسرعة", description="لعبة الحرف، لونا قالت، زر", emoji="🧠"),
            discord.SelectOption(label="حظ وإثارة", description="الروليت الملكي، المافيا، العجلة", emoji="💀"),
            discord.SelectOption(label="سريعة وإيفنتات", description="أسرع، أعلام، عواصم", emoji="⚡")
        ]
        super().__init__(placeholder="اختر قسم من المنيو...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        if "اجتماعية" in selected:
            # فتح غطاء لعبة صراحة أو جرأة
            lobby_view = TruthOrDareLobbyView(host=interaction.user)
            await interaction.response.edit_message(embed=lobby_view.generate_embed(), view=lobby_view)
        else:
            await interaction.response.send_message(f"⚙️ قسم **{selected}** تحت التطوير حالياً وسنضيف ألعابه قريباً!", ephemeral=True)

# ==================== الواجهة الرئيسية للألعاب ====================
class GamesMainView(discord.ui.View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=180)
        self.author = author
        self.add_item(MainCategorySelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ هذه القائمة ليست لك! استخدم `/العاب` لفتح القائمة الخاصة بك.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="الرئيسية 🏠", style=discord.ButtonStyle.secondary, row=1)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = generate_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="لعبة عشوائية 🎲", style=discord.ButtonStyle.success, row=1)
    async def random_game_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        lobby_view = TruthOrDareLobbyView(host=interaction.user)
        await interaction.response.edit_message(embed=lobby_view.generate_embed(), view=lobby_view)

# ==================== دالة إنشاء الإمبيد الرئيسي ====================
def generate_main_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎮 أقسام الألعاب",
        description="اختر قسم من المنيو، وبعدها شغّل أي لعبة مباشرة من القائمة.\n\n"
                    "🎭 **اجتماعية وضحك — `1 لعبة`**\n"
                    "صراحة أو جرأة، شكلي لو، لو خيروك\n\n"
                    "🧠 **ذكاء وسرعة — `قريباً`**\n"
                    "لعبة الحرف، لونا قالت، زر\n\n"
                    "💀 **حظ وإثارة — `قريباً`**\n"
                    "الروليت الملكي، روليت العجلة، المافيا\n\n"
                    "⚡ **سريعة وإيفنتات — `قريباً`**\n"
                    "أسرع، أعلام، عواصم\n\n"
                    "💡 **ملاحظة:** جرب زر العشوائية إذا ما قدرتوا تتفقون!",
        color=discord.Color.from_rgb(255, 105, 180)
    )
    return embed

# ==================== أمر السلاش الرئيسي ====================
@bot.tree.command(name="العاب", description="عرض منيو الألعاب الفخم والسريع")
async def games_command(interaction: discord.Interaction):
    embed = generate_main_embed()
    view = GamesMainView(author=interaction.user)
    await interaction.response.send_message(embed=embed, view=view)

# ==================== التشغيل ====================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ البوت {bot.user} جاهز ومتصل بـ MongoDB المنيو الفخم شغال!")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
