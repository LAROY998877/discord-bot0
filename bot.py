import os
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

# 1. إعداد اتصال قاعدة البيانات (SQLite) وإنشاء الجداول
db_connection = sqlite3.connect("bot_database.db")
cursor = db_connection.cursor()

# جدول بيانات المستخدمين والشروط الجديدة (الاسم، العمر، الجنس)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS user_data (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        is_registered INTEGER DEFAULT 0,
        balance INTEGER DEFAULT 100,
        equipment_score INTEGER DEFAULT 10,
        floors INTEGER DEFAULT 1
    )
"""
)

# جدول المطورين المصرح لهم
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


# دالة للتحقق مما إذا كان المستخدم مسجلاً
def is_registered(user_id: int) -> bool:
    cursor.execute(
        "SELECT is_registered FROM user_data WHERE user_id = ?", (user_id,)
    )
    result = cursor.fetchone()
    if result and result[0] == 1:
        return True
    return False


# ==========================================
# 3. نظام التسجيل (Modal & Command)
# ==========================================


class RegisterModal(discord.ui.Modal, title="نظام التسجيل الإجباري"):

    name_input = discord.ui.TextInput(
        label="الاسم الكامل", placeholder="اكتب اسمك هنا...", required=True
    )
    age_input = discord.ui.TextInput(
        label="العمر", placeholder="اكتب عمرك (أرقام فقط)...", required=True
    )
    gender_input = discord.ui.TextInput(
        label="الجنس", placeholder="ذكر / أنثى", required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        username = str(interaction.user)
        name = self.name_input.value
        age = self.age_input.value
        gender = self.gender_input.value

        # التحقق أن العمر أرقام
        if not age.isdigit():
            await interaction.response.send_message(
                "❌ العمر يجب أن يكون أرقاماً صحيحة! يرجى إعادة المحاولة.",
                ephemeral=True,
            )
            return

        # حفظ البيانات في قاعدة البيانات وتحديث حالة التسجيل
        cursor.execute(
            """
            INSERT INTO user_data (user_id, username, name, age, gender, is_registered)
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
            name=excluded.name, age=excluded.age, gender=excluded.gender, is_registered=1
        """,
            (user_id, username, name, int(age), gender),
        )
        db_connection.commit()

        await interaction.response.send_message(
            f"✅ **تم تسجيلك بنجاح!**\n👤 الاسم: `{name}`\n🎂 العمر: `{age}`\n🚻 الجنس: `{gender}`\n\nالآن يمكنك استخدام جميع أوامر البوت وقوائم المنيو بحرية!",
            ephemeral=True,
        )


@bot.tree.command(name="تسجيل", description="التسجيل في النظام لفتح جميع الأوامر والمنيو")
async def register_command(interaction: discord.Interaction):
    await interaction.response.send_modal(RegisterModal())


# ==========================================
# 4. واجهات المنيو والأوامر (تتطلب التسجيل)
# ==========================================

# منيو البنك والخدمات
class BankMenuView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

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
        cursor.execute(
            "UPDATE user_data SET balance = balance + 50 WHERE user_id = ?",
            (user_id,),
        )
        db_connection.commit()
        cursor.execute(
            "SELECT balance FROM user_data WHERE user_id = ?", (user_id,)
        )
        new_balance = cursor.fetchone()[0]
        await interaction.response.send_message(
            f"✅ تم الإيداع بنجاح! رصيدك الحالي: `{new_balance}` 💎",
            ephemeral=True,
        )

    @discord.ui.button(
        label="المنحة اليومية", style=discord.ButtonStyle.primary, emoji="🎁", row=0
    )
    async def daily_gift(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        user_id = interaction.user.id
        cursor.execute(
            "UPDATE user_data SET balance = balance + 100, floors = floors + 1 WHERE user_id = ?",
            (user_id,),
        )
        db_connection.commit()
        cursor.execute(
            "SELECT balance FROM user_data WHERE user_id = ?", (user_id,)
        )
        new_balance = cursor.fetchone()[0]
        await interaction.response.send_message(
            f"🎉 استلمت المنحة الملكية! رصيدك الآن: `{new_balance}` 💎",
            ephemeral=True,
        )


@bot.tree.command(name="البنك", description="فتح منيو المصرف الإمبراطوري والتفاعل")
async def bank_panel(interaction: discord.Interaction):
    if not is_registered(interaction.user.id):
        await interaction.response.send_message(
            "❌ **عذراً!** لا يمكنك استخدام الأوامر إلا بعد إتمام التسجيل أولاً.\nاستخدم الأمر: `/تسجيل`",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title="✨ منيو المصرف الإمبراطوري",
        description="اختر العملية التي تريد تنفيذها من الأزرار أدناه:",
        color=discord.Color.gold(),
    )
    view = BankMenuView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# منيو ليدربورد (المتصدرين)
class LeaderboardMenuView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(
        label="أغنى اللاعبين", style=discord.ButtonStyle.success, emoji="💰", row=0
    )
    async def lb_money(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute(
            "SELECT name, balance FROM user_data WHERE is_registered=1 ORDER BY balance DESC LIMIT 10"
        )
        data = cursor.fetchall()
        desc = "".join(
            [
                f"{'🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else f'`{i}.`'} **{row[0]}** — `{row[1]}` 💎\n"
                for i, row in enumerate(data, 1)
            ]
        )
        embed = discord.Embed(
            title="💰 منيو أغنى اللاعبين",
            description=desc or "لا توجد بيانات مسجلة.",
            color=discord.Color.gold(),
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="ترتيب المعدات", style=discord.ButtonStyle.primary, emoji="🛡️", row=0
    )
    async def lb_equipment(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute(
            "SELECT name, equipment_score FROM user_data WHERE is_registered=1 ORDER BY equipment_score DESC LIMIT 10"
        )
        data = cursor.fetchall()
        desc = "".join(
            [
                f"{'🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else f'`{i}.`'} **{row[0]}** — قوة: `{row[1]}` 🛡️\n"
                for i, row in enumerate(data, 1)
            ]
        )
        embed = discord.Embed(
            title="🛡️ منيو ترتيب المعدات",
            description=desc or "لا توجد بيانات مسجلة.",
            color=discord.Color.blue(),
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="أعلى الطوابق", style=discord.ButtonStyle.danger, emoji="🏢", row=0
    )
    async def lb_floors(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute(
            "SELECT name, floors FROM user_data WHERE is_registered=1 ORDER BY floors DESC LIMIT 10"
        )
        data = cursor.fetchall()
        desc = "".join(
            [
                f"{'🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else f'`{i}.`'} **{row[0]}** — الطابق: `{row[1]}` 🏢\n"
                for i, row in enumerate(data, 1)
            ]
        )
        embed = discord.Embed(
            title="🏢 منيو أعلى الطوابق",
            description=desc or "لا توجد بيانات مسجلة.",
            color=discord.Color.red(),
        )
        await interaction.response.edit_message(embed=embed, view=self)


@bot.tree.command(name="ليدربورد", description="فتح منيو لوحة المتصدرين المتكاملة")
async def leaderboard_command(interaction: discord.Interaction):
    if not is_registered(interaction.user.id):
        await interaction.response.send_message(
            "❌ **عذراً!** التسجيل إجباري لاستخدام الأوامر.\nيرجى استخدام أمر: `/تسجيل`",
            ephemeral=True,
        )
        return

    cursor.execute(
        "SELECT name, balance FROM user_data WHERE is_registered=1 ORDER BY balance DESC LIMIT 10"
    )
    data = cursor.fetchall()
    desc = "".join(
        [
            f"{'🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else f'`{i}.`'} **{row[0]}** — `{row[1]}` 💎\n"
            for i, row in enumerate(data, 1)
        ]
    )

    embed = discord.Embed(
        title="🏆 منيو لوحة المتصدرين الرئيسية",
        description=(
            "اختر التصنيف المطلوب من الأزرار أدناه:\n\n"
            + (desc or "لا توجد بيانات مسجلة.")
        ),
        color=discord.Color.dark_theme(),
    )
    view = LeaderboardMenuView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==========================================
# 5. لوحة المطورين (مع الأوامر المضافة تلقائياً)
# ==========================================


class DevPanelView(discord.ui.View):

    def __init__(self, author_id):
        super().__init__(timeout=60)
        self.author_id = author_id

    @discord.ui.button(
        label="إحصائيات والأوامر",
        style=discord.ButtonStyle.blurple,
        emoji="📊",
        row=0,
    )
    async def stats_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        cursor.execute("SELECT COUNT(*) FROM user_data WHERE is_registered=1")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM developers")
        total_devs = cursor.fetchone()[0]

        synced_commands = bot.tree.get_commands()
        commands_list = (
            ", ".join([f"`/{cmd.name}`" for cmd in synced_commands])
            if synced_commands
            else "لا توجد"
        )

        embed = discord.Embed(
            title="⚡ منيو لوحة تحكم المطورين",
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="👥 المستخدمين المسجلين",
            value=f"`{total_users}` مسجل",
            inline=True,
        )
        embed.add_field(
            name="🛡️ عدد المطورين", value=f"`{total_devs}` مطور", inline=True
        )
        embed.add_field(
            name="📌 الأوامر المضافة تلقائياً",
            value=commands_list,
            inline=False,
        )
        await interaction.response.edit_message(embed=embed, view=self)


@bot.tree.command(name="مطور", description="فتح منيو لوحة تحكم المطورين")
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
            "❌ عذراً، هذا الأمر مخصص للمطورين فقط.", ephemeral=True
        )
        return

    embed = discord.Embed(
        title="✨ منيو الإدارة المركزية للمطورين",
        description="اختر الخيار المناسب من الأزرار أدناه:",
        color=discord.Color.from_rgb(40, 40, 45),
    )
    view = DevPanelView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="اضافة_مطور", description="إضافة مطور جديد للنظام")
@app_commands.describe(member="العضو المراد ترقيته")
async def add_developer(interaction: discord.Interaction, member: discord.Member):
    cursor.execute("SELECT COUNT(*) FROM developers")
    if cursor.fetchone()[0] > 0 and not is_dev(interaction.user.id):
        await interaction.response.send_message(
            "❌ هذا الأمر للمطورين فقط!", ephemeral=True
        )
        return

    cursor.execute(
        "INSERT OR IGNORE INTO developers (user_id) VALUES (?)", (member.id,)
    )
    db_connection.commit()
    await interaction.response.send_message(
        f"✅ تم تعيين {member.mention} مطوراً بنجاح!", ephemeral=True
    )


# ==========================================
# 6. تشغيل البوت
# ==========================================
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("خطأ: لم يتم العثور على توكن البوت (DISCORD_TOKEN).")
