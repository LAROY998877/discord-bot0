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

# إنشاء الجداول الأساسية وجداول النقابات الجديدة
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
        guild_name TEXT DEFAULT NULL
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

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS guilds (
        guild_name TEXT PRIMARY KEY,
        leader_id INTEGER,
        level INTEGER DEFAULT 1,
        coins_donated INTEGER DEFAULT 0,
        equipment_donations_count INTEGER DEFAULT 0,
        members_count INTEGER DEFAULT 1
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
# نظام النقابات (إنشاء، تبرع، منيو نقابتي)
# ==========================================


class CreateGuildModal(discord.ui.Modal, title="تأسيس نقابة جديدة"):
    guild_input_name = discord.ui.TextInput(
        label="اسم النقابة",
        placeholder="اكتب اسم نقابتك الأسطورية...",
        required=True,
        max_length=40,
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        ensure_user(user_id, str(interaction.user))
        g_name = self.guild_input_name.value.strip()

        # التحقق من رصيد المستخدم (تكلفة الإنشاء 300 عملة)
        cursor.execute(
            "SELECT balance, guild_name FROM user_data WHERE user_id = ?",
            (user_id,),
        )
        balance, current_guild = cursor.fetchone()

        if current_guild:
            await interaction.response.send_message(
                "❌ أنت تنتمي بالفعل إلى نقابة! يجب عليك مغادرتها أولاً لتأسيس نقابة جديدة.",
                ephemeral=True,
            )
            return

        if balance < 300:
            await interaction.response.send_message(
                f"❌ رصيدك الحالي (`{balance} 💎`) لا يكفي! تأسيس النقابة يكلف `300 💎`.",
                ephemeral=True,
            ) خصم
            return

        # التحقق إن كان اسم النقابة مستخدماً مسبقاً
        cursor.execute(
            "SELECT guild_name FROM guilds WHERE guild_name = ?", (g_name,)
        )
        if cursor.fetchone() is not None:
            await interaction.response.send_message(
                "❌ اسم هذه النقابة مستخدم مسبقاً، يجدر بك اختيار اسم فريد آخر!",
                ephemeral=True,
            )
            return

        # خصم العملات وتحديث بيانات المستخدم والنقابة
        cursor.execute(
            "UPDATE user_data SET balance = balance - 300, guild_name = ? WHERE user_id = ?",
            (g_name, user_id),
        )
        cursor.execute(
            """
            INSERT INTO guilds (guild_name, leader_id, level, coins_donated, equipment_donations_count, members_count)
            VALUES (?, ?, 1, 0, 0, 1)
        """,
            (g_name, user_id),
        )
        db_connection.commit()

        embed = discord.Embed(
            title=f"🏰 تم تأسيس النقابة بنجاح: {g_name}!",
            description=(
                f"مبروك يا {interaction.user.mention}! لقد أصبحت قائداً لنقابتك الجديدة.\n"
                f"• تكلفة التأسيس: `300 💎`\n"
                f"• مستوى النقابة الابتدائي: `1/500`\n\n"
                "يمكنك الآن استخدام أمر `/نقابتي` لإدارة شؤون النقابة والتبرع لها!"
            ),
            color=discord.Color.dark_gold(),
        )
        await interaction.response.send_message(embed=embed)


class DonateCoinsModal(discord.ui.Modal, title="التبرع بالعملات للنقابة"):
    coins_amount = discord.ui.TextInput(
        label="عدد العملات للتبرع",
        placeholder="أدخل عدد العملات المراد التبرع بها...",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        cursor.execute(
            "SELECT guild_name, balance FROM user_data WHERE user_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        if not row or not row[0]:
            await interaction.response.send_message(
                "❌ أنت لست عضواً في أي نقابة لتتبرع لها!", ephemeral=True
            )
            return

        g_name, balance = row
        try:
            amount = int(self.coins_amount.value)
        except ValueError:
            await interaction.response.send_message(
                "❌ يرجى إدخال أرقام صحيحة فقط!", ephemeral=True
            )
            return

        if amount <= 0:
            await interaction.response.send_message(
                "❌ المبلغ غير صالح!", ephemeral=True
            )
            return

        if balance < amount:
            await interaction.response.send_message(
                f"❌ رصيدك الحالي (`{balance} 💎`) لا يكفي لهذا التبرع!",
                ephemeral=True,
            )
            return

        # خصم العملات من المستخدم وإضافتها لرصيد النقابة وتطوير مستواها (كل 1000 عملة متبرع بها ترفع المستوى بـ 1، وبحد أقصى 500)
        cursor.execute(
            "UPDATE user_data SET balance = balance - ? WHERE user_id = ?",
            (amount, user_id),
        )
        cursor.execute(
            "UPDATE guilds SET coins_donated = coins_donated + ? WHERE guild_name = ?",
            (amount, g_name),
        )

        # حساب وترقية مستوى النقابة (أقصى مستوى 500)
        cursor.execute(
            "SELECT coins_donated, level FROM guilds WHERE guild_name = ?",
            (g_name,),
        )
        total_coins, current_level = cursor.fetchone()
        new_level = min(500, 1 + (total_coins // 1000))

        if new_level > current_level:
            cursor.execute(
                "UPDATE guilds SET level = ? WHERE guild_name = ?",
                (new_level, g_name),
            )

        db_connection.commit()

        embed = discord.Embed(
            title="💰 تم التبرع بالعملات بنجاح!",
            description=(
                f"لقد تبرعت بـ `💎 {amount}` لنقابتك **{g_name}**.\n"
                f"• إجمالي تبرعات العملات للنقابة: `💎 {total_coins}`\n"
                f"• مستوى النقابة الحالي: `{new_level}/500` 🌟"
            ),
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class GuildMenuView(discord.ui.View):

    def __init__(self, user_id: int, guild_name: str):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.guild_name = guild_name

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ هذه القائمة لا تخصك!", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="التبرع بالعملات",
        style=discord.ButtonStyle.success,
        emoji="💎",
        row=0,
    )
    async def donate_coins_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(DonateCoinsModal())

    @discord.ui.button(
        label="التبرع بالعتاد",
        style=discord.ButtonStyle.primary,
        emoji="⚔️",
        row=0,
    )
    async def donate_equipment_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        user_id = interaction.user.id
        cursor.execute(
            "SELECT equipment_name, equipment_score FROM user_data WHERE user_id = ?",
            (user_id,),
        )
        eq_name, eq_score = cursor.fetchone()

        if eq_name == "لم يتم الاختيار" or eq_score <= 10:
            await interaction.response.send_message(
                "❌ ليس لديك عتاد قوي بما يكفي للتبرع به لنقابتك!",
                ephemeral=True,
            )
            return

        # خصم العتاد من المستخدم وإعادته لمستواه الأساسي، وزيادة عداد تبرعات العتاد للنقابة
        cursor.execute(
            "UPDATE user_data SET equipment_name = 'لم يتم الاختيار', equipment_score = 10 WHERE user_id = ?",
            (user_id,),
        )
        cursor.execute(
            "UPDATE guilds SET equipment_donations_count = equipment_donations_count + 1 WHERE guild_name = ?",
            (self.guild_name,),
        )
        db_connection.commit()

        embed = discord.Embed(
            title="🛡️ تم التبرع بالعتاد بنجاح!",
            description=(
                f"لقد قمت بالتبرع بعتادك (`{eq_name}`) لصالح خزينة نقابة **{self.guild_name}**!\n"
                "• ساهم هذا التبرع في تقوية مستودع النقابة العسكري."
            ),
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="انشاء_نقابة", description="تأسيس نقابة جديدة بتكلفة 300 عملة")
async def create_guild_command(interaction: discord.Interaction):
    ensure_user(interaction.user.id, str(interaction.user))
    cursor.execute(
        "SELECT guild_name FROM user_data WHERE user_id = ?",
        (interaction.user.id,),
    )
    current_guild = cursor.fetchone()[0]

    if current_guild:
        await interaction.response.send_message(
            "❌ أنت تنتمي بالفعل إلى نقابة ولا يمكنك إنشاء أخرى جديدة!",
            ephemeral=True,
        )
        return

    await interaction.response.send_modal(CreateGuildModal())


@bot.tree.command(name="نقابتي", description="عرض منيو نقابتك وإدارتها والتبرع لها")
async def my_guild_command(interaction: discord.Interaction):
    user_id = interaction.user.id
    ensure_user(user_id, str(interaction.user))

    cursor.execute(
        "SELECT guild_name FROM user_data WHERE user_id = ?", (user_id,)
    )
    res = cursor.fetchone()
    if not res or not res[0]:
        embed = discord.Embed(
            title="🏰 لا توجد نقابة",
            description=(
                "أنت لست منضماً لأي نقابة حالياً.\n"
                "استخدم أمر `/انشاء_نقابة` لتأسيس نقابتك الخاصة مقابل `300 💎`!"
            ),
            color=discord.Color.dark_red(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    g_name = res[0]
    cursor.execute(
        "SELECT leader_id, level, coins_donated, equipment_donations_count, members_count FROM guilds WHERE guild_name = ?",
        (g_name,),
    )
    g_data = cursor.fetchone()
    if not g_data:
        await interaction.response.send_message(
            "❌ حدث خطأ، بيانات النقابة غير موجودة.", ephemeral=True
        )
        return

    leader_id, level, coins_donated, eq_donations, members_count = g_data
    leader_user = bot.get_user(leader_id)
    leader_name = leader_user.display_name if leader_user else f"ID: {leader_id}"

    embed = discord.Embed(
        title=f"🏰 لوحة تحكم النقابة: {g_name}",
        description=(
            f"• 👑 **القائد:** `{leader_name}`\n"
            f"• 🌟 **مستوى النقابة:** `{level}/500`\n"
            f"• 💎 **رصيد العملات المتبرع به:** `{coins_donated}`\n"
            f"• ⚔️ **إجمالي تبرعات العتاد:** `{eq_donations}`\n"
            f"• 👥 **عدد الأعضاء:** `{members_count}`\n\n"
            "استخدم الأزرار بالأسفل للتبرع بالعملات أو العتاد لتطوير نقابتك:"
        ),
        color=discord.Color.dark_gold(),
    )
    embed.set_thumbnail(
        url="https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800"
    )

    view = GuildMenuView(user_id, g_name)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==========================================
# 2. الملف الشخصي
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
        "SELECT name, age, gender, balance, bank_balance, loan_amount, equipment_score, floors, max_unlocked_floor, hero_name, equipment_name, title, hide_stats, hide_titles, guild_name FROM user_data WHERE user_id = ?",
        (target.id,),
    )
    data = cursor.fetchone()
    (
        name,
        age,
        gender,
        balance,
        bank_balance,
        loan,
        eq_score,
        floors,
        max_unlocked,
        hero,
        equipment,
        title,
        hide_stats,
        hide_titles,
        guild_name,
    ) = data

    embed = discord.Embed(
        title=f"📜 الملف الشخصي لـ: {target.display_name}",
        color=discord.Color.dark_purple(),
    )
    embed.set_thumbnail(url=target.display_avatar.url)

    display_title = "مخفي 🔒" if hide_titles == 1 else f"`{title}`"
    embed.add_field(name="🏷️ اللقب الشخصي", value=display_title, inline=False)
    embed.add_field(
        name="🏰 النقابة",
        value=f"`{guild_name}`" if guild_name else "لا توجد نقابة",
        inline=False,
    )

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
                f"• الرصيد البنكي: `{bank_balance}` 🏦\n"
                f"• القروض النشطة: `{loan}` 📜\n"
                f"• نقاط المعدات: `{eq_score}` ⚔️\n"
                f"• الطابق الحالي: `{floors}` 🏢 (أقصى طابق: {max_unlocked}/1000)\n"
                f"• البطل المختار: `{hero}` 🦸‍♂️\n"
                f"• العتاد الحالي: `{equipment}` 🗡️"
            ),
            inline=False,
        )

    view = ProfileControlView(target.id)
    await interaction.response.send_message(embed=embed, view=view)


# ==========================================
# 3. أمر الحقيبة المنفصل
# ==========================================


@bot.tree.command(name="الحقيبة", description="عرض حقيبتك والمعدات والعتاد الحالي")
async def inventory_command(interaction: discord.Interaction):
    ensure_user(interaction.user.id, str(interaction.user))

    cursor.execute(
        "SELECT equipment_name, equipment_score, balance, floors, max_unlocked_floor FROM user_data WHERE user_id = ?",
        (interaction.user.id,),
    )
    eq_name, eq_score, balance, floors, max_unlocked = cursor.fetchone()

    embed = discord.Embed(
        title=f"🎒 حقيبة المغامر: {interaction.user.display_name}",
        description=(
            f"• 🗡️ **العتاد الحالي:** `{eq_name}`\n"
            f"• ⚔️ **نقاط قوة العتاد:** `{eq_score}`\n"
            f"• 💎 **العملات:** `{balance}`\n"
            f"• 🏢 **الطابق الحالي:** `{floors}` (أقصى طابق متاح: `{max_unlocked}/1000`)"
        ),
        color=discord.Color.blue(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==========================================
# 4. أوامر التحويل والإهداء
# ==========================================


@bot.tree.command(
    name="تحويل_عملات", description="إرسال عملات معدنية أو جواهر لأي مستخدم آخر"
)
@app_commands.describe(
    member="الشخص المراد التحويل له", amount="عدد العملات المراد إرسالها"
)
async def transfer_coins(
    interaction: discord.Interaction, member: discord.Member, amount: int
):
    if member.id == interaction.user.id:
        await interaction.response.send_message(
            "❌ لا يمكنك تحويل العملات لنفسك!", ephemeral=True
        )
        return

    if amount <= 0:
        await interaction.response.send_message(
            "❌ يرجى إدخال مبلغ صحيح أكبر من الصفر!", ephemeral=True
        )
        return

    ensure_user(interaction.user.id, str(interaction.user))
    ensure_user(member.id, str(member))

    cursor.execute(
        "SELECT balance FROM user_data WHERE user_id = ?", (interaction.user.id,)
    )
    sender_bal = cursor.fetchone()[0]

    if sender_bal < amount:
        await interaction.response.send_message(
            f"❌ رصيدك الحالي (`{sender_bal} 💎`) لا يكفي لإتمام عملية التحويل!",
            ephemeral=True,
        )
        return

    cursor.execute(
        "UPDATE user_data SET balance = balance - ? WHERE user_id = ?",
        (amount, interaction.user.id),
    )
    cursor.execute(
        "UPDATE user_data SET balance = balance + ? WHERE user_id = ?",
        (amount, member.id),
    )
    db_connection.commit()

    await interaction.response.send_message(
        f"✅ تمت عملية التحويل بنجاح! تم إرسال `💎 {amount}` إلى العضو {member.mention}."
    )


@bot.tree.command(
    name="إهداء_عتاد_الظلام",
    description="[مطور] إعطاء مجموعة متجر الظلام الكاملة لشخص عبر المنشن",
)
@app_commands.describe(member="الشخص المراد إعطاؤه عتاد متجر الظلام")
async def give_dark_gear_to_member(
    interaction: discord.Interaction, member: discord.Member
):
    if (
        not is_dev(interaction.user.id)
        and interaction.user.id != interaction.guild.owner_id
    ):
        await interaction.response.send_message(
            "❌ هذا الأمر مخصص للمطور حصرياً!", ephemeral=True
        )
        return

    ensure_user(member.id, str(member))
    dark_bundle = "مجموعة متجر الظلام الكاملة (درع، خوذة، ساق، حذاء، سيف، مطرقة، خنجر)"

    cursor.execute(
        "UPDATE user_data SET equipment_name = ?, equipment_score = equipment_score + 7000 WHERE user_id = ?",
        (dark_bundle, member.id),
    )
    db_connection.commit()

    embed = discord.Embed(
        title="🌑 تم منح عتاد متجر الظلام بنجاح!",
        description=(
            f"قام المطور بمنح العضو {member.mention} ترسانة متجر الظلام الأسطورية الكاملة:\n\n"
            "• 🛡️ **درع الظلام الملكي**\n"
            "• ⛑️ **خوذة الهلاك المظلم**\n"
            "• 🦾 **درع الساق الشيطاني**\n"
            "• 🥾 **حذاء الظلال السريع**\n"
            "• ⚔️ **سيف الموت المحرم**\n"
            "• 🔨 **مطرقة الدمار الكوني**\n"
            "• 🗡️ **خنجر الاغتيال المظلم**\n\n"
            "⚡ **تمت إضافة قوة خارقة (`+7000`) إلى رصيد عتاده!**"
        ),
        color=discord.Color.dark_red(),
    )
    embed.set_image(
        url="https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=800"
    )
    await interaction.response.send_message(embed=embed)


# ==========================================
# 5. أمر الليدربورد المحدث (يشمل النقابات)
# ==========================================


@bot.tree.command(
    name="ليدربورد",
    description="لوحة الصدارة لأقوى اللاعبين، الأغنياء، وأقوى النقابات",
)
async def leaderboard_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏆 لوحة الشرف وصدارة الأكوان",
        color=discord.Color.gold(),
    )

    # 1. أقوى النقابات
    cursor.execute(
        "SELECT guild_name, level, coins_donated, equipment_donations_count FROM guilds ORDER BY level DESC, coins_donated DESC LIMIT 5"
    )
    guilds_top = cursor.fetchall()
    guilds_text = ""
    for idx, (g_name, lvl, c_donated, eq_donated) in enumerate(
        guilds_top, start=1
    ):
        total_donations = c_donated + eq_donated
        guilds_text += (
            f"**{idx}. {g_name}**\n"
            f"  • المستوى: `{lvl}/500` 🌟 | العملات: `💎 {c_donated}`\n"
            f"  • التبرعات الكلية: `{total_donations}` 📦\n\n"
        )
    embed.add_field(
        name="🏰 أعلى النقابات قوة",
        value=guilds_text if guilds_text else "لا توجد نقابات مسجلة بعد.",
        inline=False,
    )

    # 2. أغنى اللاعبين
    cursor.execute(
        "SELECT name, balance FROM user_data ORDER BY balance DESC LIMIT 3"
    )
    rich_top = cursor.fetchall()
    rich_text = ""
    for idx, (name, bal) in enumerate(rich_top, start=1):
        rich_text += f"**{idx}.** `{name}` — `💎 {bal}`\n"
    embed.add_field(
        name="💎 أغنى المغامرين",
        value=rich_text if rich_text else "لا توجد بيانات.",
        inline=False,
    )

    # 3. أقوى اللاعبين عتاداً
    cursor.execute(
        "SELECT name, equipment_score FROM user_data ORDER BY equipment_score DESC LIMIT 3"
    )
    power_top = cursor.fetchall()
    power_text = ""
    for idx, (name, score) in enumerate(power_top, start=1):
        power_text += f"**{idx}.** `{name}` — `⚔️ {score}`\n"
    embed.add_field(
        name="⚔️ أبطال القوة والعتاد",
        value=power_text if power_text else "لا توجد بيانات.",
        inline=False,
    )

    embed.set_footer(text="استمر في تطوير نقابتك ورفع مستواها لتعتلي القمة!")
    await interaction.response.send_message(embed=embed)


# ==========================================
# 6. لوحة المطورين
# ==========================================

BUTCHER_HERO = {
    "title": "السفاح - كابوس الأكوان المظلمة",
    "power": 9999,
    "defense": 9999,
    "story": "كيان شيطاني مرعب ولد من رحم الدماء والظلام الأبدي، لا ينام ولا يرحم. تلامس خطاه أراضي الموتى فيرتجف لرهبتها ملوك الطوابق. يحمل منجل المنون المقطر بالسموم الفتاكة، وقوته تتجاوز حدود العقل والبشر.",
    "image": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=800",
}


class DevPanelView(discord.ui.View):

    def __init__(self, author_id):
        super().__init__(timeout=60)
        self.author_id = author_id

    @discord.ui.button(
        label="💎 تفعيل العملات اللانهائية",
        style=discord.ButtonStyle.success,
        row=0,
    )
    async def infinite_coins_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if (
            not is_dev(interaction.user.id)
            and interaction.user.id != interaction.guild.owner_id
        ):
            await interaction.response.send_message(
                "❌ هذا الزر مخصص للمطور حصرياً!", ephemeral=True
            )
            return

        cursor.execute(
            "UPDATE user_data SET balance = 999999999, bank_balance = 999999999 WHERE user_id = ?",
            (interaction.user.id,),
        )
        db_connection.commit()
        await interaction.response.send_message(
            "✨ تم تفعيل العملات اللانهائية بنجاح! رصيدك أصبح `999,999,999 💎`.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="⚒️ التطوير الكامل والشامل للعتاد",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def full_upgrade_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if (
            not is_dev(interaction.user.id)
            and interaction.user.id != interaction.guild.owner_id
        ):
            await interaction.response.send_message(
                "❌ هذا الزر مخصص للمطور حصرياً!", ephemeral=True
            )
            return

        cursor.execute(
            "UPDATE user_data SET equipment_score = 9999, equipment_name = 'درع وسلاح الإمبراطور الأسطوري المطلق' WHERE user_id = ?",
            (interaction.user.id,),
        )
        db_connection.commit()
        await interaction.response.send_message(
            "🔥 تم ترقية عتادك بالكامل إلى أقصى حد ممكن (`9999` نقطة قوة) وأقوى سلاح فانتزي في الوجود!",
            ephemeral=True,
        )

    @discord.ui.button(
        label="عتاد", style=discord.ButtonStyle.secondary, emoji="🌑", row=1
    )
    async def gear_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if (
            not is_dev(interaction.user.id)
            and interaction.user.id != interaction.guild.owner_id
        ):
            await interaction.response.send_message(
                "❌ هذا الزر مخصص للمطور حصرياً!", ephemeral=True
            )
            return

        user_id = interaction.user.id
        dark_bundle = (
            "ترسانة متجر الظلام الكاملة: (درع، خوذة، ساق، حذاء، سيف، مطرقة، خنجر)"
        )

        cursor.execute(
            "UPDATE user_data SET equipment_name = ?, equipment_score = equipment_score + 7000 WHERE user_id = ?",
            (dark_bundle, user_id),
        )
        db_connection.commit()

        embed = discord.Embed(
            title="🌑 تم استلام عتاد متجر الظلام الكامل بنجاح!",
            description=(
                "لقد أضفت إلى حقيبتك من لوحة المطورين جميع القطع المطلوبة من **متجر الظلام**:\n\n"
                "• 🛡️ **درع الظلام الملكي**\n"
                "• ⛑️ **خوذة الهلاك المظلم**\n"
                "• 🦾 **درع الساق الشيطاني**\n"
                "• 🥾 **حذاء الظلال السريع**\n"
                "• ⚔️ **سيف الموت المحرم**\n"
                "• 🔨 **مطرقة الدمار الكوني**\n"
                "• 🗡️ **خنجر الاغتيال المظلم**\n\n"
                "⚡ **تمت إضافة قوة عتاد بقيمة `+7000` إلى ملفك الشخصي!**"
            ),
            color=discord.Color.dark_red(),
        )
        embed.set_image(
            url="https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=800"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="مطور", description="فتح منيو لوحة تحكم المطورين السرية")
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
        description=(
            "مرحباً بك في لوحة تحكم المطور السرية.\n"
            "يمكنك تفعيل العملات، زر **عتاد** للحصول على عتاد الظلام الشامل، أو ترقية النظام:"
        ),
        color=discord.Color.from_rgb(40, 40, 45),
    )
    view = DevPanelView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==========================================
# 7. تشغيل البوت
# ==========================================
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("خطأ: لم يتم العثور على توكن البوت (DISCORD_TOKEN).")
