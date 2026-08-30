import os
import random
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

# قراءة التوكن بأمان من متغيرات البيئة أو ملف محلي إن وجد
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    try:
        from config import TOKEN
    except ImportError:
        TOKEN = None

# 1. إعداد مسار ثابت ودائمقاعدة البيانات
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bot_database.db")

db_connection = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = db_connection.cursor()

# إنشاء الجداول الأساسية وجدول البنك والقروض
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
        bank_balance INTEGER DEFAULT 0,
        loan_amount INTEGER DEFAULT 0,
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
# 2. الملف الشخصي والأزرار
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
                f"• الرصيد اليدوي: `{balance}` 💎\n"
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
# 3. نظام البنك المطور والقروض الفاخرة
# ==========================================


class LoanModal(discord.ui.Modal, title="طلب قرض بنكي"):
    amount = discord.ui.TextInput(
        label="مبلغ القرض المطلوب",
        placeholder="اكتب المبلغ الذي تريد اقتراضه...",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            loan_val = int(self.amount.value)
        except ValueError:
            await interaction.response.send_message(
                "❌ يرجى إدخال أرقام صحيحة فقط!", ephemeral=True
            )
            return

        if loan_val <= 0:
            await interaction.response.send_message(
                "❌ المبلغ غير صالح!", ephemeral=True
            )
            return

        cursor.execute(
            "SELECT loan_amount FROM user_data WHERE user_id = ?",
            (interaction.user.id,),
        )
        current_loan = cursor.fetchone()[0]

        if current_loan > 0:
            await interaction.response.send_message(
                "❌ لديك قرض قديم لم تقم بسداده بعد! لا يمكنك أخذ قرض جديد.",
                ephemeral=True,
            )
            return

        if loan_val > 50000:
            await interaction.response.send_message(
                "❌ الحد الأقصى للقرض الواحد هو `50,000` عملة!", ephemeral=True
            )
            return

        # إضافة القرض وزيادة الرصيد البنكي
        cursor.execute(
            "UPDATE user_data SET bank_balance = bank_balance + ?, loan_amount = loan_amount + ? WHERE user_id = ?",
            (loan_val, loan_val, interaction.user.id),
        )
        db_connection.commit()

        embed = discord.Embed(
            title="🏦 صندوق البنك المركزي - تمت الموافقة على القرض",
            description=(
                f"لقد حصلت على قرض بنكي بقيمة `💎 {loan_val}` بنجاح.\n\n"
                "⚠️ **تنبيه هام:** يجب عليك سداد القرض في أقرب وقت عبر زر **سداد القرض**، وفي حال تخلفك عن السداد أو تفعيل الإنذار، سيتم بيع عتادك وأغراضك تلقائياً لتسوية الدين!"
            ),
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class BankView(discord.ui.View):

    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ هذه اللوحة لا تخصك، قم بفتح لوحتك الخاصة عبر `/البنك`!",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(
        label="اقتراض مبلغ",
        style=discord.ButtonStyle.danger,
        emoji="📜",
        row=0,
    )
    async def take_loan(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(LoanModal())

    @discord.ui.button(
        label="سداد القرض",
        style=discord.ButtonStyle.success,
        emoji="💸",
        row=0,
    )
    async def pay_loan(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        ensure_user(interaction.user.id, str(interaction.user))
        cursor.execute(
            "SELECT balance, bank_balance, loan_amount FROM user_data WHERE user_id = ?",
            (interaction.user.id,),
        )
        balance, bank_balance, loan = cursor.fetchone()

        if loan <= 0:
            await interaction.response.send_message(
                "✨ ليس لديك أي قروض مسجلة لتسديدها!", ephemeral=True
            )
            return

        # الأفضلية للسداد من الرصيد اليدوي أو البنكي
        total_available = balance + bank_balance
        if total_available < loan:
            await interaction.response.send_message(
                f"❌ رصيدك الإجمالي (اليدوي + البنك = {total_available}) لا يكفي لسداد قيمة القرض البالغة `💎 {loan}`!",
                ephemeral=True,
            )
            return

        # خصم المبلغ من الرصيد وتصفير القرض
        remaining_loan = loan
        new_balance = balance
        new_bank = bank_balance

        if new_bank >= remaining_loan:
            new_bank -= remaining_loan
            remaining_loan = 0
        else:
            remaining_loan -= new_bank
            new_bank = 0
            new_balance -= remaining_loan
            remaining_loan = 0

        cursor.execute(
            "UPDATE user_data SET balance = ?, bank_balance = ?, loan_amount = 0 WHERE user_id = ?",
            (new_balance, new_bank, interaction.user.id),
        )
        db_connection.commit()

        await interaction.response.send_message(
            "✅ تم سداد كامل القرض بنجاح وأصبح سجلك البنكي نظيفاً وآمناً!",
            ephemeral=True,
        )

    @discord.ui.button(
        label="فحص الإنذار والعقوبات",
        style=discord.ButtonStyle.secondary,
        emoji="🚨",
        row=1,
    )
    async def check_warning(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        ensure_user(interaction.user.id, str(interaction.user))
        cursor.execute(
            "SELECT loan_amount, equipment_score, equipment_name FROM user_data WHERE user_id = ?",
            (interaction.user.id,),
        )
        loan, eq_score, eq_name = cursor.fetchone()

        if loan > 0:
            embed = discord.Embed(
                title="🚨 نظام الإنذار البنكي الخطر",
                description=(
                    f"لديك قرض نشط بقيمة: `💎 {loan}`\n"
                    f"العتاد الحالي المعرض للخطر في حال عدم السداد: **{eq_name}** (قوة: `{eq_score}`)\n\n"
                    "⚠️ **تحذير نهائي:** إذا استمر التخلف عن السداد، ستقوم إدارة البنك بتفعيل نظام الحجز وبيع أغراضك تلقائياً لاسترداد الأموال!"
                ),
                color=discord.Color.red(),
            )
        else:
            embed = discord.Embed(
                title="🛡️ الحالة المالية آمنة",
                description=(
                    "حسابك نظيف تماماً وليس عليك أي قروض أو إنذارات مالية حالية."
                ),
                color=discord.Color.green(),
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(
    name="البنك", description="فتح لوحة البنك الفاخرة وإدارة الحسابات والقروض"
)
async def bank_command(interaction: discord.Interaction):
    ensure_user(interaction.user.id, str(interaction.user))
    cursor.execute(
        "SELECT balance, bank_balance, loan_amount, equipment_name, equipment_score FROM user_data WHERE user_id = ?",
        (interaction.user.id,),
    )
    balance, bank_balance, loan, eq_name, eq_score = cursor.fetchone()

    embed = discord.Embed(
        title="🏛️ البنك المركزي الملكي - لوحة المعاملات الفاخرة",
        description=(
            "مرحباً بك في المؤسسة المالية الرسمية للمغامرين.\n"
            "إليك ملخص حسابك المصرفي والخدمات المتاحة:"
        ),
        color=discord.Color.dark_gold(),
    )
    embed.set_thumbnail(
        url="https://cdn-icons-png.flaticon.com/512/2830/2830284.png"
    )

    embed.add_field(
        name="💰 الأرصدة المالية",
        value=(
            f"• الرصيد اليدوي (الكاش): `💎 {balance}`\n"
            f"• الرصيد البنكي الآمن: `💎 {bank_balance}`\n"
            f"• إجمالي الثروة: `💎 {balance + bank_balance}`"
        ),
        inline=False,
    )

    loan_status = (
        f"`💎 {loan}` (يوجد إنذار خطر!) 🚨" if loan > 0 else "لا يوجد (سجل نظيف) ✅"
    )
    embed.add_field(
        name="📜 حالة القروض والديون",
        value=(
            f"• قيمة القرض الحالي: {loan_status}\n"
            f"• العتاد المرهون للضمان: **{eq_name}**"
        ),
        inline=False,
    )

    embed.set_footer(
        text=(
            "استخدم الأزرار بالأسفل لإدارة القروض، السداد، أو فحص الإنذارات."
        ),
        icon_url=interaction.user.display_avatar.url,
    )

    view = BankView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==========================================
# 4. لوحة تحكم المطورين (Developer Panel)
# ==========================================


@bot.tree.command(
    name="dev_add", description="[مطور] إضافة مطور جديد بواسطة الأيدي"
)
@app_commands.describe(user_id="أيدي المستخدم المراد ترقيته لمطور")
async def dev_add(interaction: discord.Interaction, user_id: str):
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
    amount="المبلغ المراد إضافته",
    member="الشخص المراد إرسال العملات له (اختياري)",
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
        f"💎 **[لوحة المطور]** تم تعديل رصيد العضو `{target.display_name}` بنجاح!\n• المبلغ المضاف: `{amount}`\n• الرصيد اليدوي الحالي: `{new_balance}`",
        ephemeral=True,
    )


# ==========================================
# 5. نظام الألعاب
# ==========================================

TRUTH_OR_DARE_QUESTIONS = {
    "normal": [
        {"type": "صراحة", "q": "ما هو أغلى شيء تمتلكه وتخاف خسارته؟"},
        {"type": "جرأة", "q": "قم بتقليد صوت حيوان يختاره أصدقاؤك لمدة دقيقة كاملة."},
        {"type": "صراحة", "q": "من هو الشخص الذي تكذب عليه دائماً ولماذا؟"},
    ],
    "medium": [
        {"type": "صراحة", "q": "ما هو أكبر سر تخفيه عن عائلتك؟"},
        {"type": "جرأة", "q": "أرسل آخر صورة قمت بالتقاطها إلى الدردشة العامة فوراً."},
    ],
    "hard": [
        {"type": "صراحة", "q": "ما هي أكثر شيء ندمت عليه ولن تفرط في فعله مجدداً؟"},
        {
            "type": "جرأة",
            "q": "قم بتغيير اسمك وصورتك في السيرفر لما يختاره أصدقاؤك لمدة يوم كامل.",
        },
    ],
}


class TruthOrDareSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="مستوى عادي",
                description="أسئلة خفيفة وممتعة",
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


# تشغيل البوت
if not TOKEN:
    print("خطأ: لم يتم العثور على توكن البوت في متغيرات البيئة أو ملف التكوين!")
else:
    bot.run(TOKEN)
