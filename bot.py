import os
import random
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

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
# 3. نظام الألعاب (الألعاب الأساسية)
# ==========================================

# بنك الأسئلة (تم تصحيح الخطأ وإضافة 50 سؤال لكل مستوى)
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
        {"type": "صراحة", "q": "ما هي أكبر كذبة كذبتها في هذا السيرفر؟"},
        {"type": "جرأة", "q": "صور نفسك سيلفي بوضعية مضحكة جداً وأرسلها في الدردشة العامة."},
        {"type": "صراحة", "q": "من هو العضو المفضل لديك في هذا السيرفر؟"},
        {"type": "جرأة", "q": "قم بغناء أغنية بصوت عالٍ ومزعج لمدة دقيقتين."},
        {"type": "صراحة", "q": "ما هو أكثر شيء محرج حدث لك أمام الناس؟"},
        {"type": "جرأة", "q": "غيّر اسمك المستعار في السيرفر إلى 'بطة مطاطية' لمدة ساعة."},
        {"type": "صراحة", "q": "ما هو رأيك الحقيقي في صديقك المفضل؟"},
        {"type": "جرأة", "q": "قم بعمل 20 ضغطة (Push-ups) الآن."},
        {"type": "صراحة", "q": "ما هو الشيء الذي تندم على فعله بشدة؟"},
        {"type": "جرأة", "q": "أخرج كل ما في حقيبتك أو جيوبك وأرها للجميع."},
        {"type": "صراحة", "q": "ما هو أول شيء تفكر فيه عندما تستيقظ؟"},
        {"type": "جرأة", "q": "تكلم بلهجة غريبة لا يفهمها أحد لمدة 5 دقائق."},
        {"type": "صراحة", "q": "من هو الشخص الذي تراقبه سراً على مواقع التواصل الاجتماعي؟"},
        {"type": "جرأة", "q": "ارسم شارباً وشاربين على وجهك بقلم قابل للمسح والتقط صورة."},
        {"type": "صراحة", "q": "ما هو أسوأ طعام تذوقته في حياتك؟"},
        {"type": "جرأة", "q": "اذهب إلى المطبخ (أو أي مكان) واحضر أغرب شيء تجده للأكل."},
        {"type": "صراحة", "q": "ما هي العادة السيئة التي لا تستطيع التخلص منها؟"},
        {"type": "جرأة", "q": "تحدث عن نفسك بالصيغة الثالثة (هو/هي) لمدة 10 دقائق."},
        {"type": "صراحة", "q": "من هو الشخص الذي تعتبره قدوة لك ولماذا؟"},
        {"type": "جرأة", "q": "قم بتحويل لغة هاتفك إلى لغة صينية أو يابانية لمدة ساعة."},
        {"type": "صراحة", "q": "ما هو أسوأ سر أفشيت به؟"},
        {"type": "جرأة", "q": "ارفع صوتك عند التحدث في المايك حتى نهاية اللعبة."},
        {"type": "صراحة", "q": "ما هي أسوأ صفة في شخصيتك وتتمنى تغييرها؟"},
        {"type": "جرأة", "q": "أغمض عينيك واكتب جملة طويلة في الدردشة العامة وأرسلها."},
        {"type": "صراحة", "q": "من هو الشخص الذي تكرهه من كل قلبك؟"},
        {"type": "جرأة", "q": "اقفز على قدم واحدة لمدة دقيقة كاملة."},
        {"type": "صراحة", "q": "ما هو الشيء الذي تفعله دائماً بالرغم من أنه يضايقك؟"},
        {"type": "جرأة", "q": "غيّر صورة حسابك الشخصي إلى صورة كرتونية مضحكة لمدة 24 ساعة."},
        {"type": "صراحة", "q": "من هو الشخص الذي تعتبره منافسك الأول؟"},
        {"type": "جرأة", "q": "اجعل أصدقاءك يختارون لك اسماً مستعاراً جديداً واستخدمه لمدة يوم."},
        {"type": "صراحة", "q": "ما هو الشيء الذي تخاف من الاعتراف به؟"},
        {"type": "جرأة", "q": "قم بالغناء أثناء التحدث في الهاتف."},
        {"type": "صراحة", "q": "ما هو الشخص الذي تعتبره أفضل صديق لك؟"},
        {"type": "جرأة", "q": "افعل حركة يوغا صعبة واحتفظ بها لمدة 30 ثانية."},
        {"type": "صراحة", "q": "ما هو الشيء الذي تندم على عدم فعله؟"},
        {"type": "جرأة", "q": "اتصل بصديق وقل له إنك ستقابله بعد 5 دقائق وأغلق الخط."},
        {"type": "صراحة", "q": "من هو الشخص الذي تعتبره أسوأ عدو لك؟"},
        {"type": "جرأة", "q": "اذهب إلى الخارج (أو الشرفة) واصرخ 'أنا أحب البطاطا المقلية' بأعلى صوت."},
        {"type": "صراحة", "q": "ما هو الشيء الذي تفعله بالرغم من أنه يضايقك؟"},
        {"type": "جرأة", "q": "ابدأ كل جملة بكلمة 'حسناً' حتى نهاية اللعبة."},
    ],
    "medium": [
        {"type": "صراحة", "q": "ما هو أكبر سر تخفيه عن عائلتك؟"},
        {"type": "جرأة", "q": "أرسل آخر صورة قمت بالتقاطها إلى الدردشة العامة فوراً."},
