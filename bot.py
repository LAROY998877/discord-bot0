import os
import random
import asyncio
import io
import discord
from discord.ext import commands
from pymongo import MongoClient
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

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

# ==================== [3] بيانات لعبة المشاهير ====================
CELEBRITIES = [
    {"names": ["عادل امام", "عادل إمام"], "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Adel_Emam_2017.jpg/440px-Adel_Emam_2017.jpg"},
    {"names": ["ميسي", "ليونيل ميسي"], "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Lionel_Messi_20180626.jpg/440px-Lionel_Messi_20180626.jpg"},
    {"names": ["محمد صلاح", "صلاح"], "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Mohamed_Salah_2018.jpg/440px-Mohamed_Salah_2018.jpg"},
    {"names": ["رونالدو", "كريستيانو رونالدو", "كريستيانو"], "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Cristiano_Ronaldo_2018.jpg/440px-Cristiano_Ronaldo_2018.jpg"},
    {"names": ["عمرو دياب"], "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Amr_Diab_2019.jpg/440px-Amr_Diab_2019.jpg"},
    {"names": ["كاظم الساهر"], "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Kadim_Al_Sahir_2018.jpg/440px-Kadim_Al_Sahir_2018.jpg"},
    {"names": ["توم كروز", "Tom Cruise"], "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/Tom_Cruise_by_Gage_Skidmore_2.jpg/440px-Tom_Cruise_by_Gage_Skidmore_2.jpg"},
    {"names": ["جاكي شان", "Jackie Chan"], "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Jackie_Chan_July_2016.jpg/440px-Jackie_Chan_July_2016.jpg"}
]

# ==================== [4] بيانات لعبة أسرع ====================
FAST_WORDS = [
    "قسطنطينية", "موسوعة", "إمبراطورية", "تكنولوجيا", "خوارزمية", 
    "استثنائي", "ديمقراطية", "ميتافيزيقيا", "سيكولوجية", "أوتوماتيكي", 
    "فلسفة", "هندسة", "برمجيات", "مجهرية", "جغرافيا", 
    "الكهروومغناطيسية", "الأنثروبولوجيا", "استراتيجيات", "معالجات", "أتمتة",
    "Developer", "JavaScript", "Keyboard", "Speedrun", "PlayStation", 
    "Minecraft", "Algorithm", "Cybersecurity", "Blockchain", "Artificial",
    "Microscope", "Technology", "Programming", "Database", "Infrastructure"
]


# ==================== دالة توليد صورة الكلمة بحجم كبير وواضح جداً ====================
def create_word_image(word: str) -> discord.File:
    # إنشاء صورة مصغرة برسم مكبر لضمان ضخامة ووضوح الكلمة تماماً
    small_w, small_h = 240, 80
    image = Image.new("RGB", (small_w, small_h), color=(18, 18, 24))
    draw = ImageDraw.Draw(image)
    
    # إطار أزرق جانبي أنيق
    draw.rectangle([0, 0, 5, small_h], fill=(0, 162, 255))
    
    font = ImageFont.load_default()
    
    try:
        reshaped_text = arabic_reshaper.reshape(word)
        display_word = get_display(reshaped_text)
    except:
        display_word = word

    try:
        bbox = draw.textbbox((0, 0), display_word, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except AttributeError:
        text_width, text_height = draw.textsize(display_word, font=font)

    x = (small_w - text_width) // 2
    y = (small_h - text_height) // 2
    
    draw.text((x, y), display_word, fill=(255, 255, 255), font=font)
    
    # تكبير الصورة النهائية بدقة عالية لتظهر الكلمة ضخمة وواضحة جداً في الديسكورد
    final_image = image.resize((700, 220), Image.Resampling.NEAREST)
    
    buffer = io.BytesIO()
    final_image.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(buffer, filename="fast_word.png")


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


# ==================== [اللعبة 3] لعبة المشاهير ====================
async def start_celeb_game_round(interaction: discord.Interaction, host: discord.User):
    celeb = random.choice(CELEBRITIES)
    embed = discord.Embed(
        title="📸 من هو هذا المشهور؟",
        description="💡 **اكتب اسم المشهور في الشات بسرعة!**\n⏰ معك **25 ثانية** للتخمين.",
        color=discord.Color.purple()
    )
    embed.set_image(url=celeb["image"])
    embed.set_footer(text="لعبة المشاهير | جارية الآن...")

    await interaction.response.edit_message(embed=embed, view=None)
    message = await interaction.original_response()

    def check(m):
        if m.channel.id != interaction.channel_id or m.author.bot: return False
        user_msg = m.content.strip().lower()
        return any(alias.lower() in user_msg for alias in celeb["names"])

    try:
        winner_msg = await bot.wait_for("message", check=check, timeout=25.0)
        win_embed = discord.Embed(
            title="🎉 إجابة صحيحة!",
            description=f"🏆 **الفائز السريع:** {winner_msg.author.mention}\n\n👤 **المشهور هو:** `{celeb['names'][0]}`",
            color=discord.Color.green()
        )
        win_embed.set_image(url=celeb["image"])
        view = CelebrityNextView(host=host)
        await message.edit(embed=win_embed, view=view)
    except asyncio.TimeoutError:
        loss_embed = discord.Embed(
            title="⏰ انتهى الوقت!",
            description=f"للأسف محد عرف المشهور! 😅\n\n👤 **المشهور هو:** `{celeb['names'][0]}`",
            color=discord.Color.red()
        )
        loss_embed.set_image(url=celeb["image"])
        view = CelebrityNextView(host=host)
        await message.edit(embed=loss_embed, view=view)


class CelebrityNextView(discord.ui.View):
    def __init__(self, host: discord.User):
        super().__init__(timeout=300)
        self.host = host

    @discord.ui.button(label="جولة تالية 🔄", style=discord.ButtonStyle.success)
    async def next_round_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await start_celeb_game_round(interaction, self.host)

    @discord.ui.button(label="إيقاف 🛑", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = interaction.user.guild_permissions.administrator if interaction.guild else False
        if interaction.user != self.host and not is_admin:
            await interaction.response.send_message("❌ فقط المنظم أو المسؤولين يمكنهم الإيقاف!", ephemeral=True)
            return
        embed = discord.Embed(title="🛑 تم إيقاف لعبة المشاهير", description=f"قام {interaction.user.mention} بالإيقاف.", color=discord.Color.red())
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)


class CelebrityLobbyView(discord.ui.View):
    def __init__(self, host: discord.User):
        super().__init__(timeout=300)
        self.host = host

    def generate_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📸 لعبة المشاهير",
            description="سيظهر لك البوت صورة لمشهور (عربي أو أجنبي).\nأول شخص يكتب اسمه صح بالشات هو الفائز!\n\n**المنظم:** " + self.host.mention,
            color=discord.Color.gold()
        )
        embed.set_footer(text="اضغط على (بدء 🚀) لبدء الجولة!")
        return embed

    @discord.ui.button(label="بدء 🚀", style=discord.ButtonStyle.primary, row=0)
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            await interaction.response.send_message("❌ فقط المنظم يمكنه بدء اللعبة!", ephemeral=True)
            return
        await start_celeb_game_round(interaction, self.host)

    @discord.ui.button(label="إيقاف 🛑", style=discord.ButtonStyle.danger, row=0)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = interaction.user.guild_permissions.administrator if interaction.guild else False
        if interaction.user != self.host and not is_admin:
            await interaction.response.send_message("❌ فقط المنظم أو المسؤولين يمكنهم الإيقاف!", ephemeral=True)
            return
        embed = discord.Embed(title="🛑 تم إيقاف لعبة المشاهير", description=f"قام {interaction.user.mention} بالإيقاف.", color=discord.Color.red())
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)


# ==================== [اللعبة 4] لعبة أسرع ====================
async def start_fast_game_round(interaction: discord.Interaction, host: discord.User):
    word = random.choice(FAST_WORDS)
    file = create_word_image(word)
    
    embed = discord.Embed(
        title="⚡ لعبة أسرع!",
        description="اكتب الكلمة الظاهرة في الصورة أدناه بأسرع وقت!\n⏰ لديك **15 ثانية** فقط.",
        color=discord.Color.teal()
    )
    embed.set_image(url="attachment://fast_word.png")
    embed.set_footer(text="لعبة أسرع | أكتب الكلمة بالضبط كما في الصورة!")

    await interaction.response.edit_message(embed=embed, view=None, attachments=[file])
    message = await interaction.original_response()

    def check(m):
        if m.channel.id != interaction.channel_id or m.author.bot: return False
        return m.content.strip() == word

    try:
        winner_msg = await bot.wait_for("message", check=check, timeout=15.0)
        win_file = create_word_image(word)
        win_embed = discord.Embed(
            title="⚡ فوز ساحق!",
            description=f"🏆 **أسرع شخص:** {winner_msg.author.mention}\n\n📝 **الكلمة كانت:** `{word}`",
            color=discord.Color.green()
        )
        win_embed.set_image(url="attachment://fast_word.png")
        view = FastNextView(host=host)
        await message.edit(embed=win_embed, view=view, attachments=[win_file])

    except asyncio.TimeoutError:
        loss_file = create_word_image(word)
        loss_embed = discord.Embed(
            title="⏰ انتهى الوقت!",
            description=f"للأسف محد كتب الكلمة بسرعة! 🐢\n\n📝 **الكلمة كانت:** `{word}`",
            color=discord.Color.red()
        )
        loss_embed.set_image(url="attachment://fast_word.png")
        view = FastNextView(host=host)
        await message.edit(embed=loss_embed, view=view, attachments=[loss_file])


class FastNextView(discord.ui.View):
    def __init__(self, host: discord.User):
        super().__init__(timeout=300)
        self.host = host

    @discord.ui.button(label="جولة تالية 🔄", style=discord.ButtonStyle.success)
    async def next_round_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await start_fast_game_round(interaction, self.host)

    @discord.ui.button(label="إيقاف 🛑", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = interaction.user.guild_permissions.administrator if interaction.guild else False
        if interaction.user != self.host and not is_admin:
            await interaction.response.send_message("❌ فقط المنظم أو المسؤولين يمكنهم الإيقاف!", ephemeral=True)
            return
        embed = discord.Embed(title="🛑 تم إيقاف لعبة أسرع", description=f"قام {interaction.user.mention} بالإيقاف.", color=discord.Color.red())
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)


class FastLobbyView(discord.ui.View):
    def __init__(self, host: discord.User):
        super().__init__(timeout=300)
        self.host = host

    def generate_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="⚡ لعبة أسرع",
            description="سيظهر لك البوت **صورة تحتوي على الكلمة فقط وبحجم كبير وواضح**.\nأول شخص يكتبها بالشات خلال **15 ثانية** يفوز!\n\n**المنظم:** " + self.host.mention,
            color=discord.Color.teal()
        )
        embed.set_footer(text="اضغط على (بدء 🚀) للبدء!")
        return embed

    @discord.ui.button(label="بدء 🚀", style=discord.ButtonStyle.primary, row=0)
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            await interaction.response.send_message("❌ فقط المنظم يمكنه بدء اللعبة!", ephemeral=True)
            return
        await start_fast_game_round(interaction, self.host)

    @discord.ui.button(label="إيقاف 🛑", style=discord.ButtonStyle.danger, row=0)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = interaction.user.guild_permissions.administrator if interaction.guild else False
        if interaction.user != self.host and not is_admin:
            await interaction.response.send_message("❌ فقط المنظم أو المسؤولين يمكنهم الإيقاف!", ephemeral=True)
            return
        embed = discord.Embed(title="🛑 تم إيقاف لعبة أسرع", description=f"قام {interaction.user.mention} بالإيقاف.", color=discord.Color.red())
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)


# ==================== منيو الاختيار الرئيسي ====================
class MainGameSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="لعبة الأسئلة والصراحة", description="3 مستويات: عادي، متوسط، وجريء جداً", emoji="🎯"),
            discord.SelectOption(label="لعبة لو خيروك", description="خيارات صعبة ومواقف مضحكة", emoji="🆚"),
            discord.SelectOption(label="لعبة المشاهير", description="تخمين صورة المشهور (عرب وأجانب)", emoji="📸"),
            discord.SelectOption(label="لعبة أسرع", description="كتابة الكلمة الكبيرة والواضحة من الصورة (15 ثانية)", emoji="⚡"),
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
        elif "المشاهير" in selected:
            lobby_view = CelebrityLobbyView(host=interaction.user)
            await interaction.response.edit_message(embed=lobby_view.generate_embed(), view=lobby_view)
        elif "أسرع" in selected:
            lobby_view = FastLobbyView(host=interaction.user)
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
    return discord.Embed(
        title="🎮 قائمة الألعاب المتاحة",
        description="اختر إحدى الألعاب التالية من المنيو بالأسفل:\n\n"
                    "🎯 **1. لعبة الأسئلة والصراحة**\n"
                    "أسئلة تفاعلية بـ 3 مستويات (عادي، متوسط، جريء جداً 🔥)\n\n"
                    "🆚 **2. لعبة لو خيروك**\n"
                    "تخيير اللاعبين بين خيارين صعبين ومضحكين!\n\n"
                    "📸 **3. لعبة المشاهير**\n"
                    "تخمين اسم المشهور من الصورة بسرعة قبل انتهاء الوقت!\n\n"
                    "⚡ **4. لعبة أسرع**\n"
                    "تحدي سرعة الكتابة لكلمات ضخمة وواضحة داخل الصورة خلال 15 ثانية!",
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
    print(f"✅ البوت {bot.user} شغال وجاهز بالكلمات الكبيرة والواضحة ⚡!")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
