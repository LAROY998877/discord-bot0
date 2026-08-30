import os
import random
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

# استيراد التوكن بأمان من ملف config.py الخارجي لضمان عدم تسريبه
try:
    from config import TOKEN
except ImportError:
    TOKEN = None

# 1. إعداد مسار ثابت ودائم لقاعدة البيانات في مجلد العمل الحالي
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bot_database.db")

db_connection = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = db_connection.cursor()

# إنشاء الجداول ودعم التحديث التلقائي للحقول إن وجدت مسبقاً
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS user_data (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        is_registered INTEGER DEFAULT 1,
        balance INTEGER DEFAULT 5000,
        equipment_score INTEGER DEFAULT 10,
        floors INTEGER DEFAULT 1,
        max_unlocked_floor INTEGER DEFAULT 1,
        hero_name TEXT DEFAULT 'لم يتم الاختيار',
        equipment_name TEXT DEFAULT 'لم يتم الاختيار',
        title TEXT DEFAULT 'مبتدئ',
        hide_stats INTEGER DEFAULT 0,
        hide_titles INTEGER DEFAULT 0,
        current_game_mode TEXT DEFAULT 'none'
    )
"""
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS developers (
        user_id INTEGER PRIMARY KEY
    )
"""
)
db_connection.commit()

intents = discord.Intents.default()
intents.members = True
intents.guilds = True


class MyBot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("تم مزامنة أوامر السلاش بنجاح!")


bot = MyBot()


@bot.event
async def on_ready():
    print(f"-----------------------------------------")
    print(f"تم تسجيل الدخول بنجاح باسم: {bot.user.name} (ID: {bot.user.id})")
    print(f"البوت متصل حالياً في {len(bot.guilds)} سيرفر/ات.")
    print(f"قاعدة البيانات محفوظة في: {DB_PATH}")
    print(f"-----------------------------------------")


def is_dev(user_id: int) -> bool:
    cursor.execute("SELECT user_id FROM developers WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None


# نظام التحقق والتسجيل التلقائي الخفي (بدون نوافذ إجبار مزعجة)
def ensure_user(user_id: int, username: str):
    cursor.execute(
        "SELECT user_id FROM user_data WHERE user_id = ?", (user_id,)
    )
    if cursor.fetchone() is None:
        cursor.execute(
            """
            INSERT INTO user_data (user_id, username, name, age, gender, is_registered)
            VALUES (?, ?, ?, ?, ?, 1)
        """,
            (user_id, username, "مغامر جديد", 20, "غير محدد"),
        )
        db_connection.commit()


# ==========================================
# 2. الملف الشخصي (ظاهر للكل مع تحكم خاص بصاحب الملف فقط)
# ==========================================


class EditTitleModal(discord.ui.Modal, title="تعديل اللقب الشخصي"):

    new_title = discord.ui.TextInput(
        label="اللقب الجديد",
        placeholder="اكتب لقبك الفانتازي الجديد...",
        required=True,
        max_length=30,
    )

    async def on_submit(self, interaction: discord.Interaction):
        cursor.execute(
            "UPDATE user_data SET title = ? WHERE user_id = ?",
            (self.new_title.value, interaction.user.id),
        )
        db_connection.commit()
        await interaction.response.send_message(
            f"✅ تم تحديث لقبك إلى: **{self.new_title.value}** بنجاح!",
            ephemeral=True,
        )


class ProfileControlView(discord.ui.View):

    def __init__(self, owner_id: int):
        super().__init__(timeout=180)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ عذراً، هذا الملف الشخصي لا يخصك ولا يمكنك التعديل عليه!",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(
        label="تعديل اللقب",
        style=discord.ButtonStyle.primary,
        emoji="✏️",
        row=0,
    )
    async def edit_title_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(EditTitleModal())

    @discord.ui.button(
        label="إخفاء/إظهار المعدلات",
        style=discord.ButtonStyle.secondary,
        emoji="👁️",
        row=0,
    )
    async def toggle_stats_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute(
            "SELECT hide_stats FROM user_data WHERE user_id = ?",
            (interaction.user.id,),
        )
        current = cursor.fetchone()[0]
        new_val = 0 if current == 1 else 1
        cursor.execute(
            "UPDATE user_data SET hide_stats = ? WHERE user_id = ?",
            (new_val, interaction.user.id),
        )
        db_connection.commit()

        status_text = "مخفية 🔒" if new_val == 1 else "ظاهرة 🔓"
        await interaction.response.send_message(
            f"✅ تم تغيير حالة إخفاء المعدلات لتصبح: **{status_text}**",
            ephemeral=True,
        )

    @discord.ui.button(
        label="إخفاء/إظهار الألقاب",
        style=discord.ButtonStyle.secondary,
        emoji="🛡️",
        row=0,
    )
    async def toggle_titles_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute(
            "SELECT hide_titles FROM user_data WHERE user_id = ?",
            (interaction.user.id,),
        )
        current = cursor.fetchone()[0]
        new_val = 0 if current == 1 else 1
        cursor.execute(
            "UPDATE user_data SET hide_titles = ? WHERE user_id = ?",
            (new_val, interaction.user.id),
        )
        db_connection.commit()

        status_text = "مخفي 🔒" if new_val == 1 else "ظاهر 🔓"
        await interaction.response.send_message(
            f"✅ تم تغيير حالة إخفاء الألقاب لتصبح: **{status_text}**",
            ephemeral=True,
        )


@bot.tree.command(name="الملف", description="عرض الملف الشخصي")
@app_commands.describe(member="العضو المراد عرض ملفه (اختياري)")
async def profile_command(
    interaction: discord.Interaction, member: discord.Member = None
):
    target = member if member else interaction.user
    ensure_user(target.id, str(target))

    cursor.execute(
        "SELECT name, age, gender, balance, equipment_score, floors, max_unlocked_floor, hero_name, equipment_name, title, hide_stats, hide_titles FROM user_data WHERE user_id = ?",
        (target.id,),
    )
    data = cursor.fetchone()
    (
        name,
        age,
        gender,
        balance,
        eq_score,
        floors,
        max_unlocked,
        hero,
        equipment,
        title,
        hide_stats,
        hide_titles,
    ) = data

    embed = discord.Embed(
        title=f"📜 الملف الشخصي لـ: {target.display_name}",
        color=discord.Color.dark_purple(),
    )
    embed.set_thumbnail(url=target.display_avatar.url)

    display_title = "مخفي 🔒" if hide_titles == 1 else f"`{title}`"
    embed.add_field(name="🏷️ اللقب الشخصي", value=display_title, inline=False)

    embed.add_field(name="👤 الاسم الحقيقي", value=f"`{name}`", inline=True)
    embed.add_field(name="🎂 العمر", value=f"`{age}`", inline=True)
    embed.add_field(name="🚻 الجنس", value=f"`{gender}`", inline=True)

    if hide_stats == 1:
        embed.add_field(
            name="📊 المعدلات والقوة",
            value="*المعدلات مخفية بواسطة صاحب الملف 🔒*",
            inline=False,
        )
    else:
        embed.add_field(
            name="📊 المعدلات والقوة",
            value=(
                f"• الرصيد: `{balance}` 💎\n"
                f"• نقاط المعدات: `{eq_score}` ⚔️\n"
                f"• الطوابق المكتسحة: `{floors}` 🏢 (أقصى طابق: {max_unlocked}/1000)\n"
                f"• البطل المختار: `{hero}` 🦸‍♂️\n"
                f"• العتاد الحالي: `{equipment}` 🗡️"
            ),
            inline=False,
        )

    view = ProfileControlView(target.id)
    await interaction.response.send_message(embed=embed, view=view)


# ==========================================
# 3. لوحة تحكم المطورين (Developer Panel)
# ==========================================


@bot.tree.command(
    name="dev_add", description="[مطور] إضافة مطور جديد بواسطة الأيدي"
)
@app_commands.describe(user_id="أيدي المستخدم المراد ترقيته لمطور")
async def dev_add(interaction: discord.Interaction, user_id: str):
    # صاحب البوت أو أول مطور فقط يمكنه إضافة مطورين آخرين (أو ضع أيدي حسابك الأساسي هنا كشرط أول)
    cursor.execute("SELECT user_id FROM developers")
    devs = cursor.fetchall()

    if devs and not is_dev(interaction.user.id):
        await interaction.response.send_message(
            "❌ عذراً، هذا الأمر مخصص للمطورين فقط!", ephemeral=True
        )
        return

    try:
        uid = int(user_id)
    except ValueError:
        await interaction.response.send_message(
            "❌ يرجى إدخال أيدي صحيح (أرقام فقط).", ephemeral=True
        )
        return

    cursor.execute(
        "INSERT OR IGNORE INTO developers (user_id) VALUES (?)", (uid,)
    )
    db_connection.commit()
    await interaction.response.send_message(
        f"✅ تم بنجاح إضافة المستخدم صاحب الأيدي `<@{uid}>` إلى قائمة المطورين!",
        ephemeral=True,
    )


@bot.tree.command(
    name="dev_balance", description="[مطور] إضافة عملات لامنهائية أو تعديل رصيد شخص"
)
@app_commands.describe(
    amount="المبلغ المراد إضافته (يمكنك وضع رقم كبير جداً)",
    member="الشخص المراد إرسال العملات له (اختياري، الافتراضي أنت)",
)
async def dev_balance(
    interaction: discord.Interaction, amount: int, member: discord.Member = None
):
    if not is_dev(interaction.user.id):
        await interaction.response.send_message(
            "❌ عذراً، أمر المطورين هذا ليس متاحاً لك!", ephemeral=True
        )
        return

    target = member if member else interaction.user
    ensure_user(target.id, str(target))

    cursor.execute(
        "UPDATE user_data SET balance = balance + ? WHERE user_id = ?",
        (amount, target.id),
    )
    db_connection.commit()

    cursor.execute(
        "SELECT balance FROM user_data WHERE user_id = ?", (target.id,)
    )
    new_balance = cursor.fetchone()[0]

    await interaction.response.send_message(
        f"💎 **[لوحة المطور]** تم تعديل رصيد العضو `{target.display_name}` بنجاح!\n• المبلغ المضاف: `{amount}`\n• الرصيد الحالي الجديد: `{new_balance}`",
        ephemeral=True,
    )


@bot.tree.command(
    name="dev_item", description="[مطور] إعطاء أو تعديل عتاد ونقاط معدات أي شخص"
)
@app_commands.describe(
    equipment_name="اسم العتاد الجديد",
    equipment_score="قيمة نقاط المعدات والقوة",
    member="العضو المراد تعديل عتاده",
)
async def dev_item(
    interaction: discord.Interaction,
    equipment_name: str,
    equipment_score: int,
    member: discord.Member,
):
    if not is_dev(interaction.user.id):
        await interaction.response.send_message(
            "❌ عذراً، أمر المطورين هذا ليس متاحاً لك!", ephemeral=True
        )
        return

    ensure_user(member.id, str(member))
    cursor.execute(
        "UPDATE user_data SET equipment_name = ?, equipment_score = ? WHERE user_id = ?",
        (equipment_name, equipment_score, member.id),
    )
    db_connection.commit()

    await interaction.response.send_message(
        f"⚔️ **[لوحة المطور]** تم تحديث عتاد العضو `<@{member.id}>` بنجاح!\n• العتاد: `{equipment_name}`\n• نقاط القوة: `{equipment_score}`",
        ephemeral=True,
    )


@bot.tree.command(
    name="dev_stats",
    description="[مطور] تعديل الطوابق المكتسحة والمستوى لأي شخص بالكامل",
)
@app_commands.describe(
    floors="عدد الطوابق المكتسحة",
    max_floors="أقصى طابق متاح فتحه",
    member="العضو المراد تعديل معدلاته",
)
async def dev_stats(
    interaction: discord.Interaction,
    floors: int,
    max_floors: int,
    member: discord.Member,
):
    if not is_dev(interaction.user.id):
        await interaction.response.send_message(
            "❌ عذراً، أمر المطورين هذا ليس متاحاً لك!", ephemeral=True
        )
        return

    ensure_user(member.id, str(member))
    cursor.execute(
        "UPDATE user_data SET floors = ?, max_unlocked_floor = ? WHERE user_id = ?",
        (floors, max_floors, member.id),
    )
    db_connection.commit()

    await interaction.response.send_message(
        f"📊 **[لوحة المطور]** تم تعديل إحصائيات وطوابق العضو `<@{member.id}>` بنجاح!\n• الطوابق المكتسحة: `{floors}`\n• أقصى طابق مفتوح: `{max_floors}`",
        ephemeral=True,
    )


# ==========================================
# 4. نظام الألعاب (لعبة صراحة أو جرأة كاملة)
# ==========================================

TRUTH_OR_DARE_QUESTIONS = {
    "normal": [
        {"type": "صراحة", "q": "ما هو أغلى شيء تمتلكه وتخاف خسارته؟"},
        {"type": "جرأة", "q": "قم بتقليد صوت حيوان يختاره أصدقاؤك لمدة دقيقة كاملة."},
        {"type": "صراحة", "q": "من هو الشخص الذي تكذب عليه دائماً ولماذا؟"},
        {"type": "جرأة", "q": "اتصل بآخر شخص اتصلت به وقل له 'أحبك' وأغلق الخط فوراً."},
        {"type": "صراحة", "q": "ما هو أسوأ مقلب قمت به في حياتك؟"},
        {"type": "جرأة", "q": "ارقص رقصة مضحكة جداً أمام الجميع بدون موسيقى."},
        {"type": "صراحة", "q": "ما هو الشيء الذي تفعله سراً وتتمنى ألا يعرفه أحد؟"},
        {"type": "جرأة", "q": "اجعل أصدقاءك يغيرون خلفية هاتفك إلى صورة من اختيارهم."},
        {"type": "صراحة", "q": "من هو الشخص الذي تتمنى أن تعتذر له؟"},
        {"type": "جرأة", "q": "اكتب رسالة طويلة وغريبة لأحد أفراد عائلتك وأرسلها الآن."},
    ],
    "medium": [
        {"type": "صراحة", "q": "ما هو أكبر سر تخفيه عن عائلتك؟"},
        {"type": "جرأة", "q": "أرسل آخر صورة قمت بالتقاطها إلى الدردشة العامة فوراً."},
        {"type": "صراحة", "q": "من هو الشخص الذي تتمنى ألا تقابله مرة أخرى؟"},
        {"type": "جرأة", "q": "اتصل برقم عشوائي وتحدث بلهجة غريبة لمدة دقيقة."},
        {"type": "صراحة", "q": "ما هو الموقف المحرج الذي تعرضت له أمام شخص تحبه؟"},
    ],
    "hard": [
        {"type": "صراحة", "q": "ما هي أكثر شيء ندمت عليه ولن تفرط في فعله مجدداً؟"},
        {
            "type": "جرأة",
            "q": "قم بتغيير اسمك وصورتك في السيرفر لما يختاره أصدقاؤك لمدة يوم كامل.",
        },
        {"type": "صراحة", "q": "من هو الشخص الذي أثر سلباً على حياتك بشكل كبير؟"},
        {
            "type": "جرأة",
            "q": "أرسل آخر رسالة نصية قمت بكتابتها لشخص سري إلى الدردشة العامة.",
        },
    ],
}


class TruthOrDareSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="مستوى عادي",
                description="أسئلة خفيفة وممتعة للجميع",
                emoji="🟢",
                value="normal",
            ),
            discord.SelectOption(
                label="مستوى متوسط",
                description="أسئلة أعمق وأكثر تحدياً",
                emoji="🟡",
                value="medium",
            ),
            discord.SelectOption(
                label="مستوى جريء جداً",
                description="أسئلة جريئة وقوية للصراحة المطلقة",
                emoji="🔴",
                value="hard",
            ),
        ]
        super().__init__(
            placeholder="اختر مستوى الصعوبة...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        level = self.values[0]
        q_data = random.choice(TRUTH_OR_DARE_QUESTIONS[level])

        embed = discord.Embed(
            title=f"🎲 لعبة صراحة أو جرأة ({q_data['type']})",
            description=f"**السؤال:**\n{q_data['q']}",
            color=discord.Color.orange(),
        )
        embed.set_footer(
            text=f"طلب بواسطة: {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class GamesView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(TruthOrDareSelect())


@bot.tree.command(name="العاب", description="فتح قائمة الألعاب والتحديات")
async def games_command(interaction: discord.Interaction):
    ensure_user(interaction.user.id, str(interaction.user))
    embed = discord.Embed(
        title="🎮 مركز ألعاب المغامرين",
        description="اختر المستوى المناسب لك من القائمة أدناه للبدء في لعبة **صراحة أو جرأة**:",
        color=discord.Color.blue(),
    )
    view = GamesView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# التحقق من التوكن بأمان من ملف config.py الخارجي
if not TOKEN or TOKEN == "هنا_ضع_توكن_بوتك_الخاص_بسرية_تامة":
    print("خطأ: لم يتم العثور على توكن البوت في ملف config.py")
else:
    bot.run(TOKEN)
