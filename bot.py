import os
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

# 1. إعداد اتصال قاعدة البيانات (SQLite) وإنشاء الجداول
db_connection = sqlite3.connect("bot_database.db")
cursor = db_connection.cursor()

# جدول بيانات المستخدمين والرصيد (الحفظ التلقائي)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS user_data (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 100
    )
"""
)

# جدول المطورين المصرح لهم باستخدام لوحة التحكم
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS developers (
        user_id INTEGER PRIMARY KEY
    )
"""
)
db_connection.commit()

# 2. إعداد البوت والصلاحيات
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
    print(f"-----------------------------------------")


def is_dev(user_id: int) -> bool:
    cursor.execute("SELECT user_id FROM developers WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None


# دالة مساعدة لجلب رصيد المستخدم أو إنشائه تلقائياً بقاعدة البيانات
def get_or_create_user(user_id, username):
    cursor.execute(
        "SELECT balance FROM user_data WHERE user_id = ?", (user_id,)
    )
    result = cursor.fetchone()
    if result is None:
        # إذا لم يكن موجوداً، يتم حفظه تلقائياً برصيد افتراضي 100
        cursor.execute(
            "INSERT INTO user_data (user_id, username, balance) VALUES (?, ?, 100)",
            (user_id, username),
        )
        db_connection.commit()
        return 100
    return result[0]


# دالة لتحديث الرصيد وحفظه تلقائياً
def update_balance(user_id, amount):
    cursor.execute(
        "UPDATE user_data SET balance = balance + ? WHERE user_id = ?",
        (amount, user_id),
    )
    db_connection.commit()


# ==========================================
# 3. واجهة الألعاب والمصرف (أزرار تفاعلية مع حفظ تلقائي)
# ==========================================


class BankView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)  # أزرار دائمية لا تنتهي

    @discord.ui.button(
        label="إيداع بالتوفير",
        style=discord.ButtonStyle.success,
        emoji="📥",
        row=0,
    )
    async def deposit(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        user_id = interaction.user.id
        username = str(interaction.user)
        get_or_create_user(
            user_id, username
        )  # التأكد من وجوده وحفظه تلقائياً

        update_balance(user_id, 50)  # إضافة 50 رصيد كمثال للحفظ التلقائي
        cursor.execute(
            "SELECT balance FROM user_data WHERE user_id = ?", (user_id,)
        )
        new_balance = cursor.fetchone()[0]

        await interaction.response.send_message(
            f"✅ تم الإيداع بنجاح! رصيدك الحالي المحفوظ تلقائياً: `{new_balance}` جوهرة 💎",
            ephemeral=True,
        )

    @discord.ui.button(
        label="المنحة الملكية اليومية",
        style=discord.ButtonStyle.primary,
        emoji="🎁",
        row=0,
    )
    async def daily_gift(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        user_id = interaction.user.id
        username = str(interaction.user)
        get_or_create_user(user_id, username)

        update_balance(user_id, 100)  # منح 100 جوهرة وحفظها تلقائياً
        cursor.execute(
            "SELECT balance FROM user_data WHERE user_id = ?", (user_id,)
        )
        new_balance = cursor.fetchone()[0]

        await interaction.response.send_message(
            f"🎉 استلمت المنحة الملكية (100 جوهرة)! رصيدك الآن: `{new_balance}` 💎",
            ephemeral=True,
        )

    @discord.ui.button(
        label="رصيدي", style=discord.ButtonStyle.secondary, emoji="💰", row=1
    )
    async def check_balance(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        user_id = interaction.user.id
        username = str(interaction.user)
        balance = get_or_create_user(
            user_id, username
        )  # جلب البيانات المحفوظة تلقائياً

        await interaction.response.send_message(
            f"💼 رصيدك المحفوظ في بنك الإمبراطورية: `{balance}` جوهرة 💎",
            ephemeral=True,
        )


# أمر لإرسال قائمة البنك والأزرار التفاعلية في الشات
@bot.tree.command(
    name="البنك", description="فتح المصرف الإمبراطورري للخدمات والأزرار التلقائية"
)
async def bank_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="✨ المصرف الإمبراطوري - الأمان المطلق",
        description=(
            "**الرفاهية المالية لجميع المغامرس.**\n\n"
            "اضغط على الأزرار بالأسفل لتنفيذ العمليات، وسيتم **حفظ بياناتك ورصيدك تلقائياً** في قاعدة البيانات بشكل دائم ولا ينحذف أبداً! 🛡️"
        ),
        color=discord.Color.gold(),
    )
    embed.set_footer(text="نظام SQLite التلقائي - آمن ومحدث فورياً")

    view = BankView()
    await interaction.response.send_message(embed=embed, view=view)


# ==========================================
# 4. لوحة المطورين الفخمة (بنظام السلاش /)
# ==========================================


class DevPanelView(discord.ui.View):

    def __init__(self, author_id):
        super().__init__(timeout=60)
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.author_id or is_dev(
            interaction.user.id
        ):
            return True
        await interaction.response.send_message(
            "عذراً، هذه الأزرار ليست مخصصة لك!", ephemeral=True
        )
        return False

    @discord.ui.button(
        label="إحصائيات البوت",
        style=discord.ButtonStyle.blurple,
        emoji="📊",
        row=0,
    )
    async def stats_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute("SELECT COUNT(*) FROM user_data")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM developers")
        total_devs = cursor.fetchone()[0]

        embed = discord.Embed(
            title="⚡ لوحة تحكم المطور - الإحصائيات",
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="👥 المستخدمين المسجلين تلقائياً",
            value=f"`{total_users}` مستخدم",
            inline=True,
        )
        embed.add_field(
            name="🛡️ عدد المطورين", value=f"`{total_devs}` مطور", inline=True
        )
        embed.add_field(
            name="🌐 السيرفرات", value=f"`{len(bot.guilds)}` سيرفر", inline=True
        )
        embed.set_footer(text="حفظ تلقائي SQLite 100%")
        await interaction.response.edit_message(embed=embed, view=self)


@bot.tree.command(name="مطور", description="فتح لوحة تحكم المطورين الفخمة")
async def dev_panel(interaction: discord.Interaction):
    cursor.execute("SELECT COUNT(*) FROM developers")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT OR IGNORE INTO developers (user_id) VALUES (?)",
            (interaction.user.id,),
        )
        db_connection.commit()

    if (
        not is_dev(interaction.user.id)
        and interaction.user.id != interaction.guild.owner_id
    ):
        await interaction.response.send_message(
            "❌ عذراً، أنت لست مدرجاً في قائمة مطوري هذا البوت.", ephemeral=True
        )
        return

    embed = discord.Embed(
        title="✨ لوحة تحكم المطورين المركزية",
        description=(
            "مرحباً بك يا فنان.\n"
            "من خلال هذه الواجهة يمكنك مراقبة النظام وحالة الحفظ التلقائي.\n\n"
            "📌 **اختر من الأزرار أدناه:**"
        ),
        color=discord.Color.from_rgb(40, 40, 45),
    )
    view = DevPanelView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(
    name="اضافة_مطور", description="إضافة مطور جديد للنظام عن طريق تحديد العضو"
)
@app_commands.describe(member="العضو الذي تريد ترقيته لمطور")
async def add_developer(interaction: discord.Interaction, member: discord.Member):
    cursor.execute("SELECT COUNT(*) FROM developers")
    total_devs = cursor.fetchone()[0]

    if total_devs > 0 and not is_dev(interaction.user.id):
        await interaction.response.send_message(
            "❌ عذراً، هذا الأمر مخصص للمطورين المعتمدين فقط!", ephemeral=True
        )
        return

    cursor.execute(
        "INSERT OR IGNORE INTO developers (user_id) VALUES (?)", (member.id,)
    )
    db_connection.commit()

    await interaction.response.send_message(
        f"✅ تم بنجاح تعيين {member.mention} مطوراً جديداً وحفظه في النظام بقاعدة البيانات!"
    )


# ==========================================
# 5. تشغيل البوت
# ==========================================
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("خطأ: لم يتم العثور على توكن البوت في متغيرات البيئة (DISCORD_TOKEN).")

import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

# 1. إعداد اتصال قاعدة البيانات (SQLite) وإنشاء الجداول
db_connection = sqlite3.connect("bot_database.db")
cursor = db_connection.cursor()

# جدول بيانات المستخدمين والنقاط
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS user_data (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        points INTEGER DEFAULT 0
    )
"""
)

# جدول المطورين المصرح لهم باستخدام لوحة التحكم
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS developers (
        user_id INTEGER PRIMARY KEY
    )
"""
)
db_connection.commit()

# 2. إعداد البوت والصلاحيات
intents = discord.Intents.default()
intents.members = True
intents.guilds = True

# استبدلنا commands.Bot بـ Bot مع مزامنة السلاش
class MyBot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # مزامنة أوامر السلاش مع دسكورد لكي تظهر فوراً
        await self.tree.sync()
        print("تم مزامنة أوامر السلاش (Slash Commands) بنجاح!")


bot = MyBot()


@bot.event
async def on_ready():
    print(f"-----------------------------------------")
    print(f"تم تسجيل الدخول بنجاح باسم: {bot.user.name} (ID: {bot.user.id})")
    print(f"البوت متصل حالياً في {len(bot.guilds)} سيرفر/ات.")
    print(f"-----------------------------------------")


# دالة للتحقق مما إذا كان المستخدم مطوراً
def is_dev(user_id: int) -> bool:
    cursor.execute("SELECT user_id FROM developers WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None


# ==========================================
# 3. الأوامر القديمة (محفوظة بالكامل بنظام السلاش /)
# ==========================================


@bot.tree.command(
    name="حفظ", description="يقوم بحفظ أو تحديث نقاطك في قاعدة بيانات SQLite"
)
@app_commands.describe(points="عدد النقاط التي تريد حفظها")
async def save_data(interaction: discord.Interaction, points: int):
    user_id = interaction.user.id
    username = str(interaction.user)

    cursor.execute(
        """
        INSERT INTO user_data (user_id, username, points) 
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) 
        DO UPDATE SET points = ?, username = ?
    """,
        (user_id, username, points, points, username),
    )
    db_connection.commit()

    await interaction.response.send_message(
        f"تم حفظ بياناتك بنجاح يا {interaction.user.mention}! النقاط المسجلة: {points}"
    )


@bot.tree.command(
    name="بياناتي", description="يعرض بياناتك المخزنة في قاعدة البيانات"
)
async def get_data(interaction: discord.Interaction):
    user_id = interaction.user.id

    cursor.execute("SELECT points FROM user_data WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        await interaction.response.send_message(
            f"رصيدك المحفوظ هو: {result[0]} نقطة."
        )
    else:
        await interaction.response.send_message(
            "لا توجد بيانات مخزنة لك حتى الآن. استخدم أمر `/حفظ` أولاً.",
            ephemeral=True,
        )


# ==========================================
# 4. لوحة المطورين الفخمة (بنظام السلاش /)
# ==========================================


class DevPanelView(discord.ui.View):

    def __init__(self, author_id):
        super().__init__(timeout=60)
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.author_id or is_dev(
            interaction.user.id
        ):
            return True
        await interaction.response.send_message(
            "عذراً، هذه الأزرار ليست مخصصة لك!", ephemeral=True
        )
        return False

    @discord.ui.button(
        label="إحصائيات البوت",
        style=discord.ButtonStyle.blurple,
        emoji="📊",
        row=0,
    )
    async def stats_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute("SELECT COUNT(*) FROM user_data")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM developers")
        total_devs = cursor.fetchone()[0]

        embed = discord.Embed(
            title="⚡ لوحة تحكم المطور - الإحصائيات",
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="👥 المستخدمين المسجلين",
            value=f"`{total_users}` مستخدم",
            inline=True,
        )
        embed.add_field(
            name="🛡️ عدد المطورين", value=f"`{total_devs}` مطور", inline=True
        )
        embed.add_field(
            name="🌐 السيرفرات", value=f"`{len(bot.guilds)}` سيرفر", inline=True
        )
        embed.set_footer(text="نظام الحفظ الفوري SQLite - متصل وآمن")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="قائمة المطورين", style=discord.ButtonStyle.grey, emoji="📜", row=0
    )
    async def list_devs(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute("SELECT user_id FROM developers")
        devs = cursor.fetchall()
        dev_list = (
            "\n".join([f"<@{d[0]}> (`{d[0]}`)" for d in devs])
            if devs
            else "لا يوجد مطورين مضافين بعد."
        )

        embed = discord.Embed(
            title="📜 قائمة المطورين المصرح لهم",
            description=dev_list,
            color=discord.Color.gold(),
        )
        await interaction.response.edit_message(embed=embed, view=self)


@bot.tree.command(name="مطور", description="فتح لوحة تحكم المطورين الفخمة")
async def dev_panel(interaction: discord.Interaction):
    # إضافة أول شخص يكتب الأمر كأول مطور تلقائياً إذا لم يكن هناك مطورين
    cursor.execute("SELECT COUNT(*) FROM developers")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT OR IGNORE INTO developers (user_id) VALUES (?)",
            (interaction.user.id,),
        )
        db_connection.commit()

    if (
        not is_dev(interaction.user.id)
        and interaction.user.id != interaction.guild.owner_id
    ):
        await interaction.response.send_message(
            "❌ عذراً، أنت لست مدرجاً في قائمة مطوري هذا البوت.", ephemeral=True
        )
        return

    embed = discord.Embed(
        title="✨ لوحة تحكم المطورين المركزية",
        description=(
            "مرحباً بك يا فنان في لوحة التحكم الخاصة بالبوت.\n"
            "من خلال هذه الواجهة يمكنك مراقبة النظام وإدارة الصلاحيات بكفاءة عالية.\n\n"
            "📌 **اختر أحد الخيارات أدناه من الأزرار للتنقل:**"
        ),
        color=discord.Color.from_rgb(40, 40, 45),
    )
    if bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)
    if interaction.user.avatar:
        embed.set_footer(
            text=f"طلب بواسطة: {interaction.user.name}",
            icon_url=interaction.user.avatar.url,
        )

    view = DevPanelView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(
    name="اضافة_مطور", description="إضافة مطور جديد للنظام عن طريق تحديد العضو"
)
@app_commands.describe(member="العضو الذي تريد ترقيته لمطور")
async def add_developer(interaction: discord.Interaction, member: discord.Member):
    cursor.execute("SELECT COUNT(*) FROM developers")
    total_devs = cursor.fetchone()[0]

    if total_devs > 0 and not is_dev(interaction.user.id):
        await interaction.response.send_message(
            "❌ عذراً، هذا الأمر مخصص للمطورين المعتمدين فقط!", ephemeral=True
        )
        return

    cursor.execute(
        "INSERT OR IGNORE INTO developers (user_id) VALUES (?)", (member.id,)
    )
    db_connection.commit()

    await interaction.response.send_message(
        f"✅ تم بنجاح تعيين {member.mention} مطوراً جديداً في النظام وحفظه في قاعدة البيانات!"
    )


# ==========================================
# 5. تشغيل البوت
# ==========================================
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("خطأ: لم يتم العثور على توكن البوت في متغيرات البيئة (DISCORD_TOKEN).")
