import os
import random
import asyncio
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

# ==================== [1] بيانات لعبة الأسئلة ====================
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

# ==================== [2] بيانات لعبة لو خيروك ====================
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
            min_values=1, max_values=1,
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
        if "عادي" in selected: self.mode = "🟢 عادي"
        elif "متوسط" in selected: self.mode = "🟡 متوسط"
        else: self.mode = "🔴 جريء جداً 🔥"
        await self.update_lobby(interaction)

    def generate_embed(self) -> discord.Embed:
        players_list = "\n".join([f"• {p.display_name}" for p in self.players])
        return discord.Embed(
            title="🎯 لعبة الأسئلة والصراحة",
            description=f"**المود:** `{self.mode}`\n\n👥 **اللاعبين ({len(self.players)})**\n{players_list}\n\n**المنظم:** {self.host.mention}",
            color=discord.Color.from_rgb(255, 105, 180)
        )

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
        if interaction.user not in self.players or interaction.user == self.host:
            await interaction.response.send_message("❌ لا يمكنك الخروج!", ephemeral=True)
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
        is_admin = interaction.user.guild_permissions.administrator if interaction.guild else False
        if interaction.user != self.host and not is_admin:
            await interaction.response.send_message("❌ فقط المنظم أو المسؤولين يمكنهم الإيقاف!", ephemeral=True)
            return
        embed = discord.Embed(title="🛑 تم إيقاف اللعبة", description=f"قام {interaction.user.mention} بالإيقاف.", color=discord.Color.red())
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
        return discord.Embed(
            title="🆚 لعبة لو خيروك",
            description=f"اختر قرارك المصيري الصعب!\n\n👥 **اللاعبين ({len(self.players)})**\n{players_list}\n\n**المنظم:** {self.host.mention}",
            color=discord.Color.from_rgb(255, 140, 0)
        )

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
        if interaction.user not in self.players or interaction.user == self.host:
            await interaction.response.send_message("❌ لا يمكنك الخروج!", ephemeral=True)
            return
        self.players.remove(interaction.user)
        await self.update_lobby(interaction)

    @discord.ui.button(label="بدء 🚀", style=discord.ButtonStyle.primary, row=0)
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            await interaction.response.send_message("❌ فقط المنظم يمكنه البدء!", ephemeral=True)
            return
        chosen_player = random.choice(self.players)
        option_a, option_b = random.choice(WOULD_YOU_RATHER)
        embed = discord.Embed(
            title=f"🆚 لو خيروك يا {chosen_player.display_name}",
            description=f"**الخيار الأول (🔵):**\n`{option_a}`\n\n**الخيار الثاني (🔴):**\n`{option_b}`",
            color=discord.Color.gold()
        )
        embed.set_footer(text="اختر وبدون تراجع!")
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="إيقاف 🛑", style=discord.ButtonStyle.danger, row=0)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = interaction.user.guild_permissions.administrator if interaction.guild else False
        if interaction.user != self.host and not is_admin:
            await interaction.response.send_message("❌ فقط المنظم أو المسؤولين يمكنهم الإيقاف!", ephemeral=True)
            return
        embed = discord.Embed(title="🛑 تم إيقاف اللعبة", description=f"قام {interaction.user.mention} بالإيقاف.", color=discord.Color.red())
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)


# ==================== [اللعبة 3] الروليت الملكي 👑 ====================
class NumberSelect(discord.ui.Select):
    def __init__(self, game_view):
        self.game_view = game_view
        options = [discord.SelectOption(label=str(i), emoji="🎲") for i in range(1, 21)]
        super().__init__(placeholder="اختر رقمك المحظوظ من 1 إلى 20...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        chosen_num = int(self.values[0])
        
        # التأكد إذا كان الرقم محجوزاً من لاعب آخر
        for p_id, num in self.game_view.player_numbers.items():
            if num == chosen_num and p_id != interaction.user.id:
                await interaction.response.send_message(f"❌ الرقم `{chosen_num}` محجوز من قبل لاعب آخر! اختر رقماً غيره.", ephemeral=True)
                return

        self.game_view.player_numbers[interaction.user.id] = chosen_num
        if interaction.user not in self.game_view.players:
            self.game_view.players.append(interaction.user)

        await interaction.response.send_message(f"✨ تم اختيار الرقم **{chosen_num}** بنجاح في الروليت الملكي!", ephemeral=True)
        await self.game_view.update_message(interaction)

class RoyalKickSelect(discord.ui.Select):
    def __init__(self, players, winner, host):
        self.winner = winner
        self.host = host
        options = []
        for p in players:
            if p.id != winner.id:
                options.append(discord.SelectOption(label=p.display_name, value=str(p.id), emoji="👢"))
        if not options:
            options.append(discord.SelectOption(label="لا يوجد لاعبان آخرون", value="none", emoji="❌"))
        super().__init__(placeholder="👑 أيها الملك، اختر لاعباً لطرده...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.winner.id:
            await interaction.response.send_message("❌ هذا القرار للملك الفائز فقط!", ephemeral=True)
            return

        val = self.values[0]
        if val == "none":
            await interaction.response.send_message("❌ لا يوجد أحد لطرده!", ephemeral=True)
            return

        target_id = int(val)
        target_user = interaction.guild.get_member(target_id) or bot.get_user(target_id)
        target_name = target_user.display_name if target_user else "اللاعب"

        embed = discord.Embed(
            title="⚡ صدر الحكم الملكي!",
            description=f"👑 الملك {self.winner.mention} أصدر قراره الحاسم!\n👢 تم طرد **{target_name}** من ساحة الروليت الملكي بنجاح!",
            color=discord.Color.dark_red()
        )
        view = RoyalRouletteNextView(self.host)
        await interaction.response.edit_message(embed=embed, view=view)

class RoyalKickView(discord.ui.View):
    def __init__(self, winner: discord.User, players: list, host: discord.User):
        super().__init__(timeout=30)
        self.winner = winner
        self.host = host
        self.add_item(RoyalKickSelect(players, winner, host))

class RoyalRouletteNextView(discord.ui.View):
    def __init__(self, host: discord.User):
        super().__init__(timeout=300)
        self.host = host

    @discord.ui.button(label="جولة ملكية جديدة 🔄", style=discord.ButtonStyle.success)
    async def new_round(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            await interaction.response.send_message("❌ فقط المنظم يمكنه بدء جولة جديدة!", ephemeral=True)
            return
        lobby = RoyalRouletteLobbyView(self.host)
        embed = lobby.generate_embed()
        await interaction.response.edit_message(embed=embed, view=lobby)

    @discord.ui.button(label="إيقاف 🛑", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = interaction.user.guild_permissions.administrator if interaction.guild else False
        if interaction.user != self.host and not is_admin:
            await interaction.response.send_message("❌ فقط المنظم أو المسؤولين يمكنهم الإيقاف!", ephemeral=True)
            return
        embed = discord.Embed(title="🛑 تم إيقاف الروليت الملكي", description=f"قام {interaction.user.mention} بإيقاف اللعبة.", color=discord.Color.red())
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)

class RoyalRouletteLobbyView(discord.ui.View):
    def __init__(self, host: discord.User):
        super().__init__(timeout=300)
        self.host = host
        self.players = [host]
        self.player_numbers = {} # {user_id: number}
        self.add_item(NumberSelect(self))

    def generate_embed(self) -> discord.Embed:
        desc = "⚜️ **قاعة الروليت الملكي الفخمة**\n\nاختر رقمك المحظوظ من القائمة أدناه (من 1 إلى 20).\nعندما يبدأ الدوران، ستختار العجلة رقماً، ومن يملكه يصبح **الملك** ويختار من يُطرد!\n\n**المنظم:** " + self.host.mention + "\n\n👥 **المشاركون والأرقام المحجوزة:**\n"
        if self.players:
            for p in self.players:
                num = self.player_numbers.get(p.id, "لم يختر رقم بعد ⏳")
                desc += f"• {p.mention} ➔ الرقم: `{num}`\n"
        else:
            desc += "_لا توجد مشاركات بعد_"
            
        return discord.Embed(
            title="👑 الروليت الملكي 👑",
            description=desc,
            color=discord.Color.from_rgb(218, 165, 32) # لون ذهبي فخم
        )

    async def update_message(self, interaction: discord.Interaction):
        try:
            await interaction.message.edit(embed=self.generate_embed(), view=self)
        except Exception:
            pass

    @discord.ui.button(label="تدوير العجلة الملكية 🎡", style=discord.ButtonStyle.success, row=1)
    async def spin_wheel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            await interaction.response.send_message("❌ فقط المنظم يمكنه تدوير العجلة الملكية!", ephemeral=True)
            return
        if not self.player_numbers:
            await interaction.response.send_message("❌ يجب أن يختار اللاعبون أرقامهم أولاً!", ephemeral=True)
            return

        # تأثير الحركة والتشويق للعجلة
        await interaction.response.defer()
        msg = interaction.message

        anim_embeds = [
            discord.Embed(title="🎡 جاري تدوير العجلة الملكية...", description="🎲 العجلة الملكية تدور بسرعة البرق...\n`[░░░░░░░░░░] 10%`", color=discord.Color.gold()),
            discord.Embed(title="🎡 جاري تدوير العجلة الملكية...", description="🎲 تقترب العجلة من الاستقرار...\n`[█████░░░░░] 50%`", color=discord.Color.gold()),
            discord.Embed(title="🎡 جاري تدوير العجلة الملكية...", description="🎲 العداد يستقر والأرقام تتطاير...\n`[█████████░] 90%`", color=discord.Color.gold())
        ]

        for emb in anim_embeds:
            await msg.edit(embed=emb, view=None)
            await asyncio.sleep(0.7)

        # اختيار رقم عشوائي من 1 لـ 20
        winning_number = random.randint(1, 20)

        # البحث عن اللاعب الفائز بهذا الرقم
        winner = None
        for p_id, num in self.player_numbers.items():
            if num == winning_number:
                winner = interaction.guild.get_member(p_id) or bot.get_user(p_id)
                break

        if winner and winner in self.players:
            res_embed = discord.Embed(
                title="👑 نتيجة الروليت الملكي الملكية!",
                description=f"🎯 استقرت العجلة على الرقم الفائز: **`{winning_number}`**\n\n🏆 **الملك المتوج لهذه الجولة:** {winner.mention}\n\n⏳ أمام الملك 30 ثانية لاختيار شخص ليتم طرده!",
                color=discord.Color.from_rgb(255, 215, 0)
            )
            view = RoyalKickView(winner, self.players, self.host)
            await msg.edit(embed=res_embed, view=view)
        else:
            res_embed = discord.Embed(
                title="👑 نتيجة الروليت الملكي الملكية!",
                description=f"🎯 استقرت العجلة على الرقم الفائز: **`{winning_number}`**\n\n❌ عذراً، لم يختار أي لاعب هذا الرقم في هذه الجولة! الحظ غاضب اليوم.",
                color=discord.Color.red()
            )
            view = RoyalRouletteNextView(self.host)
            await msg.edit(embed=res_embed, view=view)

    @discord.ui.button(label="إيقاف 🛑", style=discord.ButtonStyle.danger, row=1)
    async def stop_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = interaction.user.guild_permissions.administrator if interaction.guild else False
        if interaction.user != self.host and not is_admin:
            await interaction.response.send_message("❌ فقط المنظم أو المسؤولين يمكنهم الإيقاف!", ephemeral=True)
            return
        embed = discord.Embed(title="🛑 تم إيقاف الروليت الملكي", description=f"قام {interaction.user.mention} بإيقاف اللعبة.", color=discord.Color.red())
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)


# ==================== منيو الاختيار الرئيسي ====================
class MainGameSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="لعبة الأسئلة والصراحة", description="3 مستويات: عادي، متوسط، وجريء جداً", emoji="🎯"),
            discord.SelectOption(label="لعبة لو خيروك", description="خيارات صعبة ومواقف مضحكة", emoji="🆚"),
            discord.SelectOption(label="الروليت الملكي", description="اختر رقماً من 1 لـ 20 ودوّر العجلة الملكية", emoji="👑"),
            discord.SelectOption(label="قريباً...", description="مكان مخصص للعبتك القادمة", emoji="⏳")
        ]
        super().__init__(placeholder="اختر لعبة من المنيو الفخم لتشغيلها...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        if "الأسئلة" in selected:
            lobby_view = QuestionsLobbyView(host=interaction.user)
            await interaction.response.edit_message(embed=lobby_view.generate_embed(), view=lobby_view)
        elif "لو خيروك" in selected:
            lobby_view = WouldYouRatherLobbyView(host=interaction.user)
            await interaction.response.edit_message(embed=lobby_view.generate_embed(), view=lobby_view)
        elif "الروليت الملكي" in selected:
            lobby_view = RoyalRouletteLobbyView(host=interaction.user)
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
            await interaction.response.send_message("❌ القائمة ليست لك! اكتب `/العاب` لفتح قائمتك الخاصة.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="الرئيسية 🏠", style=discord.ButtonStyle.secondary, row=1)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = generate_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)


def generate_main_embed() -> discord.Embed:
    return discord.Embed(
        title="🎮 قائمة الألعاب الفخمة",
        description="اختر إحدى الألعاب الرائعة التالية من المنيو بالأسفل:\n\n"
                    "🎯 **1. لعبة الأسئلة والصراحة**\n"
                    "أسئلة تفاعلية بـ 3 مستويات (عادي، متوسط، جريء جداً 🔥)\n\n"
                    "🆚 **2. لعبة لو خيروك**\n"
                    "تخيير اللاعبين بين خيارين صعبين ومضحكين!\n\n"
                    "👑 **3. الروليت الملكي**\n"
                    "اختر رقماً من 1 إلى 20، دوّر العجلة الملكية، وليكن للملك حق الطرد!",
        color=discord.Color.from_rgb(255, 105, 180)
    )


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
    print(f"✅ البوت {bot.user} شغال وجميع الألعاب جاهزة بنجاح!")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
